"""Sentence-coherence LLM pass — flag sentences that fail to parse.

Joey's feedback asked for "obvious syntax errors where the sentence does not
make sense". The existing grammar pass (`grammar_corrections.py`) explicitly
excludes vocabulary / clarity issues and only catches a fixed list of
structural rules (subject-verb agreement, tense, articles, modifiers,
pronouns, comma splices). This pass complements it by flagging sentences
that read as fragments, dropped words, mid-sentence topic switches, or
otherwise garbled syntax.

Design choices:

* **Comments, not tracked rewrites.** "This sentence doesn't make sense" is
  editorial judgement; a tracked-change rewrite would risk introducing new
  errors. The LLM returns ``(original, reason)`` — no replacement — and the
  apply pass anchors a comment at ``original`` with ``reason`` as the body.
* **Hard cap of 6 flags per document.** When sorting by ``len(reason)``
  ascending we keep the most confident / least hedged calls first.
* **Min paragraph length 80 chars.** Captions, labels, and Practitioner
  Notes are already filtered by the shared zone helpers; this is a defensive
  belt-and-braces guard against false positives on short cells.
* **De-dupe vs ``grammar_corrections``.** When a grammar correction already
  fires on the same ``original`` substring the coherence flag is dropped to
  avoid stacking two comments on one phrase.
"""

from __future__ import annotations

import os
import zipfile

from lxml import etree

from app.services.acronym_corrections import (
    _make_comment_element,
    _patch_content_types,
    _patch_rels,
    _split_run_for_action,
)
from app.services.ai.llm_client import LLMError, call_llm_json
from app.services.document_analysis_services import load_paragraphs
from app.services.document_zones import (
    iter_paragraphs_with_zone,
    should_skip_paragraph,
)
from app.services.grammar_corrections import _strip_citations
from app.services.language_corrections import WQ, W
from app.services.quotation_utils import is_in_quote

# Hard caps -----------------------------------------------------------------

# Maximum number of coherence flags per document. The pass produces comments
# anchored at sentences, so a high count quickly drowns the result panel.
_MAX_FLAGS_PER_DOC = 6

# Skip paragraphs shorter than this many characters. Body prose passes the
# threshold easily; table cells, captions, and labels — already filtered by
# document_zones — would fail it too.
_MIN_PARAGRAPH_CHARS = 80

# Word-count cap on the ``original`` field returned by the LLM. Anything
# longer than this is almost certainly a multi-sentence span we wouldn't be
# able to anchor cleanly. Mirrors the grammar pass's 6-word limit but
# allows full sentences (the unit of analysis here).
_MAX_ORIGINAL_WORDS = 30

# Minimum quality bar for the ``reason`` field. A genuine coherence
# explanation names the problem — terse ones like "garbled" or "missing main
# verb" are fine — but a degenerate yes/no answer like "No" is the model
# answering the wrong question and must not surface as a comment. We apply a
# small character floor (kills "No"/"Yes"/"ok"/"n/a") plus a blocklist of
# bare verdict/filler tokens that are long enough to clear the floor.
_MIN_REASON_CHARS = 4
_BARE_REASON_TOKENS = frozenset({
    "no", "yes", "n/a", "na", "none", "ok", "okay",
    "fine", "good", "bad", "correct", "incorrect",
})


def _is_usable_reason(reason: str) -> bool:
    """True if ``reason`` is a real explanation, not a degenerate verdict.

    Guards against the LLM returning a bare "No" (or similar) that the
    shortest-reason-first sort would otherwise prioritise into a useless
    "Author Query: No" comment. Legitimate terse reasons ("garbled",
    "fragment", "missing main verb") still pass.
    """
    cleaned = reason.strip().strip(".!?,:;").strip()
    if len(cleaned) < _MIN_REASON_CHARS:
        return False
    if cleaned.lower() in _BARE_REASON_TOKENS:
        return False
    return True


_COHERENCE_SCHEMA = {
    "name": "sentence_coherence",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "flags": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "original": {"type": "string"},
                        "reason":   {"type": "string"},
                    },
                    "required": ["original", "reason"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["flags"],
        "additionalProperties": False,
    },
}


_SYSTEM_PROMPT = """\
You are an editor reviewing an academic manuscript accepted by the Journal of
University Teaching and Learning Practice (JUTLP).

Your ONLY task is to flag sentences whose meaning is unclear because the
sentence fails to parse — fragments, missing or dropped words, a sudden
mid-sentence topic switch, missing subject or predicate, garbled syntax.

Rules:
1. Flag ONLY sentences that a careful reader would re-read and still not
   understand. If the sentence is grammatical but stylistically clunky,
   verbose, or has minor errors — do NOT flag it.
2. DO NOT flag the following (they belong to other passes):
   - Subject-verb agreement, verb tense, articles, dangling modifiers,
     pronoun-antecedent number, comma splices.
   - Spelling, vocabulary, word choice, hyphenation, capitalisation.
   - Australian vs American English.
   - Tone, voice, or vague editorial judgements ("could be clearer",
     "consider rephrasing").
   - Sentences inside DIRECT QUOTATIONS (text enclosed in "double
     quotation marks" or curly double quotes). Quoted text must
     retain the source's original wording, even if the sentence
     itself is garbled.
3. The "original" field MUST be copied VERBATIM from the manuscript and
   contain ONE sentence (single sentence terminator inside, no leading
   ellipses).
4. The "reason" field MUST be ONE short sentence (under 20 words) that
   names the specific problem ("missing main verb", "two clauses fused
   without conjunction", "object of `provide` dropped").
5. If you are uncertain whether the sentence is incoherent or merely
   awkward — do NOT flag it. False positives are worse than misses.
6. Return an empty flags array if nothing meets bar (5).
"""


def _build_user_prompt(paragraphs: list[str]) -> str:
    numbered = "\n".join(
        f"[{i + 1}] {_strip_citations(p)}" for i, p in enumerate(paragraphs)
    )
    return (
        "Review the paragraphs below for sentences that fail to parse.\n"
        "Return only flags — no commentary.\n\n"
        f"{numbered}"
    )


def get_sentence_coherence_flags(
    docx_path: str,
    *,
    grammar_originals: set[str] | None = None,
) -> list[dict]:
    """Call the LLM and return a list of ``{original, reason}`` dicts.

    ``grammar_originals``, when supplied, contains the lower-cased
    ``original`` strings of any tracked-change grammar corrections that have
    already fired on the same document. A coherence flag whose ``original``
    overlaps any of these is dropped — the editor already has a marker on
    that phrase.
    """
    para_records = load_paragraphs(docx_path)
    body_paras: list[str] = []
    for p in para_records:
        if p.is_empty:
            continue
        if len(p.text) < _MIN_PARAGRAPH_CHARS:
            continue
        # Reuse the shared skip set used by the grammar pass — same
        # rationale: headings, references, captions, front-matter labels.
        if p.style in {
            "Heading 1", "Heading 2", "Heading 3", "Heading 4",
            "APA 7 Reference List Entry",
            "APA7 Reference List Entry",
            "APA7ReferenceListEntry",
            "Article Title",
            "Authors",
            "Author Affiliations",
            "Figure Number", "Figure Title",
            "Figure/Table Number", "Figure/Table Title",
            "FigureTableNumber", "FigureTableTitle",
            "Table Number", "Table Title",
        }:
            continue
        body_paras.append(p.text)

    if not body_paras:
        return []

    try:
        result = call_llm_json(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=_build_user_prompt(body_paras),
            response_schema=_COHERENCE_SCHEMA,
        )
    except LLMError:
        return []

    raw_flags = result.get("content", {}).get("flags", []) or []
    grammar_lc = grammar_originals or set()

    # Build a lookup of paragraph_text → its quote spans (computed once)
    # so the post-validation can drop any flag whose original sits inside
    # a direct quotation in the source paragraph.
    para_lookup = list(body_paras)

    cleaned: list[dict] = []
    seen_originals: set[str] = set()
    for f in raw_flags:
        original = (f.get("original") or "").strip()
        reason = (f.get("reason") or "").strip()
        if not original or not reason:
            continue
        # Reject degenerate reasons (bare "No"/"Yes"/etc.) — these are the
        # model answering the wrong question, and the shortest-reason-first
        # sort below would otherwise surface them as a useless comment.
        if not _is_usable_reason(reason):
            continue
        if len(original.split()) > _MAX_ORIGINAL_WORDS:
            continue
        # Note: we deliberately do NOT reuse grammar_corrections'
        # `_is_proper_noun_correction` here. That helper flags any phrase
        # whose first word is capitalised — which is true of every
        # sentence and therefore rejects every legitimate flag. Sentence
        # coherence anchors are full sentences, so the proper-noun gate
        # used for 6-word grammar phrases does not apply.
        key = original.lower()
        if key in seen_originals:
            continue
        if any(go and go in key for go in grammar_lc):
            continue
        if any(key in go for go in grammar_lc):
            continue
        # Drop flags whose ``original`` sits inside a direct quotation
        # in any source paragraph. The prompt already tells the LLM to
        # avoid this; the guard is for when it doesn't.
        in_quoted_region = False
        for para_text in para_lookup:
            idx = para_text.find(original)
            if idx == -1:
                continue
            if is_in_quote(para_text, idx, idx + len(original)):
                in_quoted_region = True
            break
        if in_quoted_region:
            continue
        seen_originals.add(key)
        cleaned.append({"original": original, "reason": reason})

    # Keep the shortest-reason flags — empirically the LLM is more confident
    # when it can name the issue tersely ("missing main verb") than when it
    # hedges ("the sentence might be a bit awkward because...").
    cleaned.sort(key=lambda f: len(f["reason"]))
    return cleaned[:_MAX_FLAGS_PER_DOC]


# ---------------------------------------------------------------------------
# Comment-anchoring (DOCX rewrite)
# ---------------------------------------------------------------------------


def _iter_text_runs(para_el: etree._Element):
    """Yield (run_element, text) for body-text runs we may safely modify.

    Mirrors the helper used by ``decimal_corrections`` / ``abbreviation``:
    skip tracked-change wrappers and runs already inside an open comment
    range so we don't anchor a new comment on top of an existing one.
    """
    for r in para_el.iter(f"{WQ}r"):
        parent = r.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        prev_sibling = r.getprevious()
        if prev_sibling is not None and prev_sibling.tag == f"{WQ}commentRangeStart":
            continue
        t_el = r.find(f"{WQ}t")
        if t_el is None:
            continue
        yield r, t_el.text or ""


def _anchor_flag(
    para_el: etree._Element,
    original: str,
    next_comment_id: int,
    comments_root: etree._Element,
    reason: str,
) -> bool:
    """Locate ``original`` inside ``para_el`` and wrap it in a comment range.

    Returns True on success. We anchor only on a within-single-run match —
    cross-run anchoring would need the phrase-finder from
    ``grammar_corrections`` which is overkill for a sentence-length anchor
    and risks misalignment when runs carry different formatting. When the
    sentence spans multiple runs we fall back to anchoring on the first
    matching run prefix.
    """
    needle = original.strip()
    if not needle:
        return False

    # Try within a single run first.
    for run_el, run_text in _iter_text_runs(para_el):
        idx = run_text.find(needle)
        if idx == -1:
            # Try case-insensitive
            idx = run_text.lower().find(needle.lower())
        if idx == -1:
            continue
        comments_root.append(_make_comment_element(next_comment_id, reason))
        _split_run_for_action(
            run_el,
            idx,
            idx + len(needle),
            expansion=None,
            comment_id=next_comment_id,
            change_id=0,
        )
        return True

    # Fallback: anchor on the first N words within whichever run holds them.
    prefix_words = needle.split()[:4]
    prefix = " ".join(prefix_words)
    for run_el, run_text in _iter_text_runs(para_el):
        idx = run_text.lower().find(prefix.lower())
        if idx == -1:
            continue
        comments_root.append(_make_comment_element(next_comment_id, reason))
        _split_run_for_action(
            run_el,
            idx,
            idx + len(prefix),
            expansion=None,
            comment_id=next_comment_id,
            change_id=0,
        )
        return True

    return False


def apply_sentence_coherence_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
    *,
    flags: list[dict] | None = None,
    grammar_originals: set[str] | None = None,
) -> tuple[int, list[dict]]:
    """Anchor a comment at every coherence flag for ``input_path``.

    ``flags`` may be pre-computed by the caller (e.g. so a single LLM call
    can fan out across two write paths). When omitted the pass calls
    ``get_sentence_coherence_flags`` itself.

    Mirrors sibling apply-pass signatures: returns
    ``(next_change_id, applied_actions)``. ``next_change_id`` is threaded
    unchanged — this pass emits no tracked changes.
    """
    if flags is None:
        flags = get_sentence_coherence_flags(
            input_path, grammar_originals=grammar_originals
        )
    if not flags:
        if input_path != output_path:
            with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
                output_path, "w", zipfile.ZIP_DEFLATED
            ) as zout:
                for item in zin.infolist():
                    zout.writestr(item, zin.read(item.filename))
        return next_change_id, []

    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")
        ct_xml = z.read("[Content_Types].xml")
        has_comments = "word/comments.xml" in names
        comments_xml = z.read("word/comments.xml") if has_comments else None

    doc_root = etree.fromstring(doc_xml)

    if comments_xml:
        comments_root = etree.fromstring(comments_xml)
        existing_ids = [
            int(el.get(f"{WQ}id", 0))
            for el in comments_root.findall(f"{WQ}comment")
        ]
        next_comment_id = max(existing_ids, default=0) + 1
    else:
        comments_root = etree.Element(f"{WQ}comments", nsmap={"w": W})
        next_comment_id = 1

    applied: list[dict] = []
    # Build the paragraph list once; for each flag we walk it until we land
    # an anchor. A single coherence flag can only attach to one paragraph.
    paragraphs = list(iter_paragraphs_with_zone(doc_root))

    for flag in flags:
        anchored = False
        original = flag["original"]
        reason = flag["reason"]
        for para_el, zone in paragraphs:
            if should_skip_paragraph(para_el, zone):
                continue
            if _anchor_flag(para_el, original, next_comment_id, comments_root, reason):
                applied.append(
                    {
                        "original": original,
                        "reason": reason,
                        "comment_id": next_comment_id,
                    }
                )
                next_comment_id += 1
                anchored = True
                break
        # If we couldn't anchor it the flag is silently dropped — comments
        # without a range start float orphaned in Word, which is worse than
        # missing one flag.
        if not anchored:
            continue

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_comments_xml = etree.tostring(
        comments_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_rels_xml = _patch_rels(rels_xml)
    new_ct_xml = _patch_content_types(ct_xml)

    tmp = output_path + ".coh.tmp"
    try:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
            tmp, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item.filename == "word/_rels/document.xml.rels":
                    zout.writestr(item, new_rels_xml)
                elif item.filename == "[Content_Types].xml":
                    zout.writestr(item, new_ct_xml)
                elif item.filename == "word/comments.xml":
                    zout.writestr(item, new_comments_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
            if not has_comments and applied:
                zout.writestr("word/comments.xml", new_comments_xml)
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return next_change_id, applied
