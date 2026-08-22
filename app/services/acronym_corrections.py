"""Detect acronym usage problems and emit one consolidated Word comment.

Journal style: every acronym should be introduced on first use as
``full term (ACRO)`` and used as the bare acronym thereafter. The abstract
and the body are treated as **independent zones** — an introduction in the
abstract does not satisfy the body's first-use requirement.

Per-occurrence rules:

* **Manuscript title** — out of scope. Title acronyms are NOT flagged and
  NOT expanded; the title is Sam's territory (title-case only). The
  acronym pass only runs from the abstract through the body.
* **Abstract zone** — allow-listed acronyms are silent; anything else is
  flagged only if no inline ``Full Term (ACRO)`` definition appears for it
  anywhere in the document.
* **Body zone** — every acronym needs an inline introduction in the body
  before its first bare use. Allow-listed acronyms get the same first-use
  check; the allow-list only supplies the suggested expansion for the
  comment, it does not silence the check.
* **Outside (Acknowledgements / References onwards)** — silent.

All issues across the document are collected into a single Word comment.
The comment is anchored to the first problematic acronym occurrence. Each
issue appears as a bullet listing the acronym, its zone, and a suggested
expansion when known.

When an issue is in the body and the bot knows the full form (from an
inline definition or the allow-list), the **first** body occurrence of
that acronym also receives a tracked-change replacement
``<w:del>ACRO</w:del><w:ins>full term (ACRO)</w:ins>`` so accept-all gives
a proper introduction.

Skipped paragraph styles: headings, reference list entries, captions, etc.
(reused from ``language_corrections._SKIP_STYLES``). Acronyms inside
parentheses or brackets are skipped to avoid flagging the definition
itself.
"""

from __future__ import annotations

import os
import re
import zipfile
from copy import deepcopy

from lxml import etree

from app.services.document_zones import (
    END_BODY_HEADINGS as _SHARED_END_BODY_HEADINGS,
)
from app.services.document_zones import (
    INTRO_HEADINGS as _SHARED_INTRO_HEADINGS,
)
from app.services.document_zones import (
    heading_zone_transition as _shared_heading_zone_transition,
)
from app.services.document_zones import (
    initial_zone as _shared_initial_zone,
)
from app.services.document_zones import (
    normalise_heading as _shared_normalise_heading,
)
from app.services.language_corrections import _SKIP_STYLES, AUTHOR, DATE, WQ, W

COMMENT_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
)
COMMENT_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
)

# Intro text for the consolidated comment (paragraph 1). The bold
# "Author Query N. " prefix is prepended automatically by
# ``_append_author_query_runs``.
_CONSOLIDATED_INTRO = (
    "Please check use of acronyms. Each acronym should be introduced on "
    "first use as “full term (ACRO)”, with later uses as the "
    "acronym only. The abstract and body are checked separately — "
    "the body needs its own introduction even if the acronym was "
    "introduced in the abstract."
)

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# An acronym candidate: any word-boundaried token that contains at least 2
# consecutive uppercase ASCII letters somewhere inside it. Matches LMS
# (the whole token is uppercase), GenAI (the inner "AI"), and SoTL (the
# inner "TL"). The flanking ``[A-Za-z0-9]*`` allow lowercase letters around
# the all-caps run so the *whole* token is captured, not just the caps.
_ACRONYM_PATTERN = re.compile(r"\b[A-Za-z0-9]*[A-Z]{2,}[A-Za-z0-9]*\b")

# Tokens that match ``_ACRONYM_PATTERN`` but should NEVER be flagged. These
# fall into three buckets:
#
# * Well-known country / org / institution names that academic readers parse
#   without expansion — flagging them creates noise.
# * Common English short-forms (OK, ID, OS, AM/PM, TV) that happen to satisfy
#   the "≥2 consecutive caps" rule.
# * Tech-world proper nouns with internal caps (iOS, JavaScript, GitHub)
#   whose lowercase prefix would otherwise be captured by the trailing
#   ``[A-Za-z0-9]*`` in the pattern.
#
# Distinct from the editor-managed allow-list: the allow-list still expects
# a first-use introduction (and supplies the expansion). The block-list is
# unconditional EXCEPT that allow-listed tokens always take precedence — see
# the scanner. This handles the OECD/UNESCO overlap (both well-known orgs
# AND on the client's approved-acronyms list) and future-proofs against an
# editor adding e.g. NASA to the allow-list.
_ACRONYM_BLOCKLIST: frozenset[str] = frozenset({
    # Country and geopolitical short forms
    "USA", "US", "UK", "EU", "UN", "NZ", "AU",
    # Major orgs commonly referenced in academic writing.
    # OECD and UNESCO are intentionally OMITTED — they are on the client's
    # approved-acronyms list and follow the first-use rule like LMS/TEQSA.
    "NASA", "NATO", "WHO", "FBI", "CIA", "IMF", "WTO",
    "ASEAN", "APEC", "OPEC",
    # Universities / academic short-forms readers parse without expansion
    "MIT", "UCLA", "USC", "UC", "ANU", "UNSW",
    # Degree titles — journal style permits these as bare tokens
    "PhD", "MSc", "BSc", "BA", "MA", "MBA",
    # Common English 2-3 letter abbreviations that aren't really acronyms
    "OK", "ID", "OS", "AM", "PM", "TV", "DVD", "CD", "DJ", "AC", "DC",
    "NA", "TBD", "FYI", "TODO", "FIXME",
    # Creative Commons licence designators. The paragraph-level
    # _is_cc_licence_paragraph() check catches the main copyright-block
    # case; these blocklist entries are a fallback so a bare "CC BY-ND"
    # mention elsewhere still doesn't trigger three separate "undefined
    # acronym" flags.
    "CC", "BY", "ND", "SA", "NC",
    # AI-era proper nouns that frequently appear alongside allow-listed
    # acronyms (GenAI, ChatGPT, …) but aren't themselves journal acronyms
    "OpenAI", "ChatGPT", "GPT",
    # Tech proper nouns with internal caps
    "iOS", "iPadOS", "macOS", "MacOS", "iPhone", "iPad", "iMac",
    "JavaScript", "TypeScript", "GitHub", "GitLab",
    "PostgreSQL", "MySQL", "SQLite", "MongoDB",
})


# Matches a Creative Commons licence shortcode anywhere in a paragraph.
# When this pattern hits, the acronym scanner skips the entire paragraph —
# CC / BY / ND / SA / NC are licence-string fragments here, not acronyms.
_CC_LICENCE_PATTERN = re.compile(
    r"\bCC\s+BY(?:[-\s](?:NC|ND|SA))*(?:[-\s]\d+(?:\.\d+)?)?\b",
    re.IGNORECASE,
)


def _is_cc_licence_paragraph(text: str) -> bool:
    """Return True if the paragraph is (or contains) a CC-licence string.

    Used to suppress acronym scanning on copyright notices where ``CC``,
    ``BY``, ``ND`` etc. would otherwise be flagged as never-introduced
    acronyms.
    """
    if _CC_LICENCE_PATTERN.search(text):
        return True
    lower = text.lower()
    return "creative commons" in lower

# "Full Term (ACRO)" inline-definition pattern.
# Captures up to 11 preceding words (any case) and a parenthesised acronym.
_DEF_PATTERN = re.compile(
    r"((?:[A-Za-z][\w\-]*\s+){1,11})\(([A-Za-z0-9]*[A-Z]{2,}[A-Za-z0-9]*)\)"
)

# Words skipped when matching an acronym's letters to a candidate phrase.
_SMALL_WORDS = {
    "and", "of", "the", "in", "for", "to", "by", "a", "an", "or", "&",
    "on", "at", "with",
}

_TITLE_STYLES: frozenset[str] = frozenset({
    "Article Title",
    "ArticleTitle",
    "Title",
})

_NON_TITLE_FRONT_STYLES: frozenset[str] = frozenset({
    "Authors",
    "Author Affiliations",
})

_NON_TITLE_FRONT_HEADINGS: frozenset[str] = frozenset({
    "abstract",
    "practitioner notes",
    "keywords",
})


def _try_match_definition(words: list[str], letters: list[str]) -> str | None:
    """Attempt to align ``letters`` against the leading section of ``words``.

    Walks the letters left-to-right; small words (``of``, ``and``, ...) may
    be skipped when their first letter doesn't match. Returns the trimmed
    phrase if every letter aligns, else ``None``.
    """
    word_idx = 0
    first_match: int | None = None
    last_match: int | None = None
    for letter in letters:
        while word_idx < len(words):
            w = words[word_idx]
            if w.lower() in _SMALL_WORDS and (not w or w[0].lower() != letter):
                word_idx += 1
                continue
            break
        if word_idx >= len(words):
            return None
        if not words[word_idx] or words[word_idx][0].lower() != letter:
            return None
        if first_match is None:
            first_match = word_idx
        last_match = word_idx
        word_idx += 1
    if first_match is None or last_match is None:
        return None
    return " ".join(words[first_match : last_match + 1])


def _matches_definition(words: list[str], acro: str) -> str | None:
    """If `words` contain a valid full form for `acro`, return the phrase.

    Walks the acronym's letters left-to-right, advancing through ``words``.
    A small word (``of``, ``and``, etc.) may be skipped if its first letter
    doesn't match the next acronym letter — that's how cases like
    ``Scholarship of Teaching and Learning (SoTL)`` work.

    Tries every starting position in ``words`` so that preamble before the
    actual full form (e.g. ``"...has significantly advanced machine
    translation (MT)..."``) doesn't prevent the match. Returns the
    rightmost successful match, which is the alignment closest to the
    parenthesised acronym and therefore most likely to be the actual
    full form.

    Returns ``None`` when no alignment succeeds — the parenthesised token
    is not a clean initialism of any prefix of the surrounding words.
    """
    letters = [c.lower() for c in acro if c.isalpha()]
    if len(letters) < 2 or not words:
        return None

    best: str | None = None
    for start in range(len(words)):
        result = _try_match_definition(words[start:], letters)
        if result is not None:
            best = result
    return best


def _collect_inline_definitions(
    doc_root: etree._Element,
) -> dict[str, tuple[str, tuple[int, int]]]:
    """Scan the document for ``Capitalised Words (ACRO)`` definitions.

    Returns a mapping of acronym → (full form, position) where position is
    ``(para_index, char_offset_in_para)`` of the parenthesised ``(ACRO)``
    match. Position is used by the caller so subsequent bare uses of the
    acronym are silenced (the author has already defined it).

    When the same acronym is defined multiple times the first definition
    wins — its position is what matters for the silencing rule.
    """
    defs: dict[str, tuple[str, tuple[int, int]]] = {}
    for para_idx, para_el in enumerate(doc_root.iter(f"{WQ}p")):
        # Read both visible run text (<w:t>) AND citation-field instruction
        # text (<w:instrText>). Mendeley/Zotero embed the cited title inside
        # an instrText block; an in-citation introduction like
        # "machine translation (MT)" buried in a reference title still
        # counts as the author having defined the acronym for the reader.
        text = "".join(
            (t.text or "")
            for r in para_el.iter(f"{WQ}r")
            for t in (
                r.findall(f"{WQ}t") + r.findall(f"{WQ}instrText")
            )
            if not _should_skip_run(r)
        )
        for m in _DEF_PATTERN.finditer(text):
            words = [w for w in re.split(r"\s+", m.group(1).strip()) if w]
            acro = m.group(2)
            phrase = _matches_definition(words, acro)
            if phrase is not None and acro not in defs:
                # m.start(2) is the char offset of the parenthesised ACRO
                # token within the paragraph plain text.
                defs[acro] = (phrase, (para_idx, m.start(2)))
    return defs


def _bracketed_spans(text: str) -> list[tuple[int, int]]:
    """Character spans (start, end) inside paren/bracket pairs.

    Used to skip acronyms appearing as ``(LMS)`` — these are usually inline
    definitions or citation labels, not running prose to be flagged.
    """
    spans: list[tuple[int, int]] = []
    stack: list[int] = []
    for i, ch in enumerate(text):
        if ch in "([{":
            stack.append(i)
        elif ch in ")]}":
            if stack:
                spans.append((stack.pop(), i + 1))
    return spans


def _in_any_span(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(s <= pos < e for s, e in spans)


def _should_skip_run(run_el: etree._Element) -> bool:
    """Return True if the acronym scanner should ignore this ``<w:r>``.

    Runs nested inside ``<w:del>`` are tracked deletions — their text is
    about to disappear from the document, so flagging acronyms there
    would produce phantom issues for content the editor has already
    decided to drop.

    Runs nested inside ``<w:ins>`` are tracked insertions from earlier
    pipeline passes (Sam's title-case fix, LLM body edits, Sam-added
    Practitioner-Notes paragraphs, …). The text in those runs IS the
    final state of the document, so the acronym scanner DOES read them
    — otherwise an acronym added or rewrapped by an upstream pass would
    be silently missed and never flagged in the consolidated comment.

    Bracketed-span de-duplication (the ``(ACRO)`` skip in
    :func:`_scan_issues`) still prevents a previously-emitted introduction
    like ``<w:ins>full term (LMS)</w:ins>`` from re-flagging its own
    acronym.
    """
    parent = run_el.getparent()
    return parent is not None and parent.tag == f"{WQ}del"


def _para_plain_text(para_el: etree._Element) -> str:
    """Concatenate run text, excluding only tracked deletions.

    Tracked deletions live inside ``<w:del>`` and use ``<w:delText>`` for
    their content (not ``<w:t>``), so the simple ``iter("{WQ}t")`` already
    skips them automatically. Tracked insertions use ``<w:t>`` inside
    ``<w:ins>`` and ARE included, matching the run-level scan policy in
    :func:`_should_skip_run`.
    """
    return "".join(t.text or "" for t in para_el.iter(f"{WQ}t") if t.text)


def _get_style_name(para_el: etree._Element) -> str:
    pPr = para_el.find(f"{WQ}pPr")
    if pPr is None:
        return ""
    pStyle = pPr.find(f"{WQ}pStyle")
    if pStyle is None:
        return ""
    return pStyle.get(f"{WQ}val", "")


# ---------------------------------------------------------------------------
# Zone detection
#
# The pipeline fires acronym actions at most once per acronym per zone, where:
#   * "front"   = everything before the Introduction heading (title, abstract,
#                 keywords, etc.).
#   * "body"    = from Introduction up to but not including
#                 Acknowledgements / References / end-of-doc.
#   * "outside" = anything from Acknowledgements / References onwards. Skipped
#                 entirely so the bot doesn't comment on reference-list
#                 acronyms or acknowledgement names.
#
# If the document has no Introduction heading we treat everything before
# Acknowledgements as "body" (front-matter rolls into body), so the first
# occurrence still fires somewhere instead of being silently lost.
# ---------------------------------------------------------------------------

# Zone-detection constants and helpers live in app.services.document_zones
# so the four prose-mutating passes (acronym, decimal, number-word, AU
# spelling) share one source of truth. Local thin aliases below preserve
# the existing private names this module previously used.
_INTRO_HEADINGS = _SHARED_INTRO_HEADINGS
_END_BODY_HEADINGS = _SHARED_END_BODY_HEADINGS
_normalise_heading = _shared_normalise_heading
_initial_zone = _shared_initial_zone


def _heading_zone_transition(
    style: str, text: str, current_zone: str, intro_seen: bool = False
) -> str:
    """Compatibility shim — the shared helper has no ``intro_seen`` arg.

    The acronym pass historically passed ``intro_seen=False`` because of an
    earlier prototype that planned a different transition rule. Keep the
    keyword to avoid touching every call-site, but ignore it.
    """
    del intro_seen
    return _shared_heading_zone_transition(style, text, current_zone)


def _format_author_query_text(comment_id: int, text: str) -> str:
    prefix, query_text = _author_query_parts(comment_id, text)
    return prefix + query_text


def _author_query_parts(comment_id: int, text: str) -> tuple[str, str]:
    clean_text = (text or "").strip()
    match = re.match(r"^(Author Query\s+\d+\.\s*)(.*)$", clean_text, flags=re.IGNORECASE)
    if match is not None:
        return match.group(1), match.group(2)
    return f"Author Query {comment_id}. ", clean_text


def _append_author_query_runs(parent: etree._Element, comment_id: int, text: str) -> None:
    prefix, query_text = _author_query_parts(comment_id, text)

    prefix_run = etree.SubElement(parent, f"{WQ}r")
    prefix_rPr = etree.SubElement(prefix_run, f"{WQ}rPr")
    etree.SubElement(prefix_rPr, f"{WQ}b")
    prefix_t = etree.SubElement(prefix_run, f"{WQ}t")
    prefix_t.text = prefix
    prefix_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    text_run = etree.SubElement(parent, f"{WQ}r")
    t = etree.SubElement(text_run, f"{WQ}t")
    t.text = query_text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def _make_comment_element(comment_id: int, text: str) -> etree._Element:
    nsmap = {"w": W}
    comment = etree.Element(f"{WQ}comment", nsmap=nsmap)
    comment.set(f"{WQ}id", str(comment_id))
    comment.set(f"{WQ}author", AUTHOR)
    comment.set(f"{WQ}date", DATE)
    comment.set(f"{WQ}initials", "AI")

    p = etree.SubElement(comment, f"{WQ}p")
    pPr = etree.SubElement(p, f"{WQ}pPr")
    pStyle = etree.SubElement(pPr, f"{WQ}pStyle")
    pStyle.set(f"{WQ}val", "CommentText")

    _append_author_query_runs(p, comment_id, text)
    return comment


def _patch_rels(rels_xml: bytes) -> bytes:
    tree = etree.fromstring(rels_xml)
    ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    for rel in tree:
        if rel.get("Type") == COMMENT_REL_TYPE:
            return rels_xml
    new_rel = etree.SubElement(tree, f"{{{ns}}}Relationship")
    new_rel.set("Id", "rIdComments")
    new_rel.set("Type", COMMENT_REL_TYPE)
    new_rel.set("Target", "comments.xml")
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)


def _patch_content_types(ct_xml: bytes) -> bytes:
    tree = etree.fromstring(ct_xml)
    ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    for override in tree.findall(f"{{{ns}}}Override"):
        if override.get("PartName") == "/word/comments.xml":
            return ct_xml
    new_override = etree.SubElement(tree, f"{{{ns}}}Override")
    new_override.set("PartName", "/word/comments.xml")
    new_override.set("ContentType", COMMENT_CONTENT_TYPE)
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)


# ---------------------------------------------------------------------------
# Per-paragraph application
# ---------------------------------------------------------------------------


def _split_run_for_action(
    run_el: etree._Element,
    start: int,
    end: int,
    expansion: str | None,
    comment_id: int,
    change_id: int,
) -> int:
    """Replace the run with (before | comment-anchored content | after).

    When ``expansion`` is provided, the matched text is replaced with a
    ``<w:del>old</w:del><w:ins>new</w:ins>`` pair so the editor sees a
    tracked change. Otherwise the text stays put inside the comment range.

    Returns the updated change-id counter.
    """
    nsmap = {"w": W}
    t_el = run_el.find(f"{WQ}t")
    if t_el is None:
        return change_id
    full_text = t_el.text or ""
    before = full_text[:start]
    matched = full_text[start:end]
    after = full_text[end:]

    rPr = run_el.find(f"{WQ}rPr")
    parent = run_el.getparent()
    if parent is None:
        return change_id
    pos = list(parent).index(run_el)
    parent.remove(run_el)
    insert_at = pos

    def _text_run(text: str) -> etree._Element:
        r = etree.Element(f"{WQ}r", nsmap=nsmap)
        if rPr is not None:
            r.append(deepcopy(rPr))
        t = etree.SubElement(r, f"{WQ}t")
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return r

    if before:
        parent.insert(insert_at, _text_run(before))
        insert_at += 1

    # Comment range start.
    range_start = etree.Element(f"{WQ}commentRangeStart", nsmap=nsmap)
    range_start.set(f"{WQ}id", str(comment_id))
    parent.insert(insert_at, range_start)
    insert_at += 1

    if expansion:
        # Tracked-change replacement of the acronym with its full form.
        del_el = etree.Element(f"{WQ}del", nsmap=nsmap)
        del_el.set(f"{WQ}id", str(change_id))
        del_el.set(f"{WQ}author", AUTHOR)
        del_el.set(f"{WQ}date", DATE)
        del_run = etree.SubElement(del_el, f"{WQ}r")
        if rPr is not None:
            del_run.append(deepcopy(rPr))
        del_t = etree.SubElement(del_run, f"{WQ}delText")
        del_t.text = matched
        del_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        parent.insert(insert_at, del_el)
        insert_at += 1
        change_id += 1

        ins_el = etree.Element(f"{WQ}ins", nsmap=nsmap)
        ins_el.set(f"{WQ}id", str(change_id))
        ins_el.set(f"{WQ}author", AUTHOR)
        ins_el.set(f"{WQ}date", DATE)
        ins_run = etree.SubElement(ins_el, f"{WQ}r")
        if rPr is not None:
            ins_run.append(deepcopy(rPr))
        ins_t = etree.SubElement(ins_run, f"{WQ}t")
        ins_t.text = expansion
        ins_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        parent.insert(insert_at, ins_el)
        insert_at += 1
        change_id += 1
    else:
        # Keep the matched text in place.
        parent.insert(insert_at, _text_run(matched))
        insert_at += 1

    # Comment range end + reference run.
    range_end = etree.Element(f"{WQ}commentRangeEnd", nsmap=nsmap)
    range_end.set(f"{WQ}id", str(comment_id))
    parent.insert(insert_at, range_end)
    insert_at += 1

    ref_run = etree.Element(f"{WQ}r", nsmap=nsmap)
    ref_rPr = etree.SubElement(ref_run, f"{WQ}rPr")
    ref_rStyle = etree.SubElement(ref_rPr, f"{WQ}rStyle")
    ref_rStyle.set(f"{WQ}val", "CommentReference")
    comment_ref = etree.SubElement(ref_run, f"{WQ}commentReference")
    comment_ref.set(f"{WQ}id", str(comment_id))
    parent.insert(insert_at, ref_run)
    insert_at += 1

    if after:
        parent.insert(insert_at, _text_run(after))

    return change_id


def _split_run_for_track_change_only(
    run_el: etree._Element,
    start: int,
    end: int,
    replacement: str,
    change_id: int,
) -> int:
    """Replace `run_el` with (before | <w:del> | <w:ins> | after).

    Like ``_split_run_for_action`` but does NOT wrap with a comment range —
    used for body issues whose explanation lives in the single consolidated
    comment, while the rewrite itself is still emitted as a tracked change.

    Returns the updated change-id counter.
    """
    nsmap = {"w": W}
    t_el = run_el.find(f"{WQ}t")
    if t_el is None:
        return change_id
    full_text = t_el.text or ""
    before = full_text[:start]
    matched = full_text[start:end]
    after = full_text[end:]

    rPr = run_el.find(f"{WQ}rPr")
    parent = run_el.getparent()
    if parent is None:
        return change_id
    pos = list(parent).index(run_el)
    parent.remove(run_el)
    insert_at = pos

    def _text_run(text: str) -> etree._Element:
        r = etree.Element(f"{WQ}r", nsmap=nsmap)
        if rPr is not None:
            r.append(deepcopy(rPr))
        t = etree.SubElement(r, f"{WQ}t")
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return r

    if before:
        parent.insert(insert_at, _text_run(before))
        insert_at += 1

    del_el = etree.Element(f"{WQ}del", nsmap=nsmap)
    del_el.set(f"{WQ}id", str(change_id))
    del_el.set(f"{WQ}author", AUTHOR)
    del_el.set(f"{WQ}date", DATE)
    del_run = etree.SubElement(del_el, f"{WQ}r")
    if rPr is not None:
        del_run.append(deepcopy(rPr))
    del_t = etree.SubElement(del_run, f"{WQ}delText")
    del_t.text = matched
    del_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    parent.insert(insert_at, del_el)
    insert_at += 1
    change_id += 1

    ins_el = etree.Element(f"{WQ}ins", nsmap=nsmap)
    ins_el.set(f"{WQ}id", str(change_id))
    ins_el.set(f"{WQ}author", AUTHOR)
    ins_el.set(f"{WQ}date", DATE)
    ins_run = etree.SubElement(ins_el, f"{WQ}r")
    if rPr is not None:
        ins_run.append(deepcopy(rPr))
    ins_t = etree.SubElement(ins_run, f"{WQ}t")
    ins_t.text = replacement
    ins_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    parent.insert(insert_at, ins_el)
    insert_at += 1
    change_id += 1

    if after:
        parent.insert(insert_at, _text_run(after))

    return change_id


def _make_consolidated_comment_element(
    comment_id: int, intro: str, bullets: list[str]
) -> etree._Element:
    """Build a ``<w:comment>`` containing an intro paragraph + one bullet
    paragraph per issue. The intro carries the bold ``Author Query N.``
    prefix; bullet paragraphs are plain text and start with ``• `` so they
    visually render as a list inside Word's comments pane.
    """
    nsmap = {"w": W}
    comment = etree.Element(f"{WQ}comment", nsmap=nsmap)
    comment.set(f"{WQ}id", str(comment_id))
    comment.set(f"{WQ}author", AUTHOR)
    comment.set(f"{WQ}date", DATE)
    comment.set(f"{WQ}initials", "AI")

    p_intro = etree.SubElement(comment, f"{WQ}p")
    pPr = etree.SubElement(p_intro, f"{WQ}pPr")
    pStyle = etree.SubElement(pPr, f"{WQ}pStyle")
    pStyle.set(f"{WQ}val", "CommentText")
    _append_author_query_runs(p_intro, comment_id, intro)

    for bullet in bullets:
        p = etree.SubElement(comment, f"{WQ}p")
        pPr = etree.SubElement(p, f"{WQ}pPr")
        pStyle = etree.SubElement(pPr, f"{WQ}pStyle")
        pStyle.set(f"{WQ}val", "CommentText")
        r = etree.SubElement(p, f"{WQ}r")
        t = etree.SubElement(r, f"{WQ}t")
        t.text = bullet
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    return comment


def _build_replacement(token: str, expansion: str) -> str:
    """Return the introduction text ``full term (ACRO)`` for a track change."""
    return f"{expansion} ({token})"


def _build_bullet(issue: dict) -> str:
    """Render one issue as a single bullet line for the consolidated comment.

    Title issues are never produced by the scanner (the manuscript title is
    out of scope — see module docstring), so only ``"body"`` and ``"front"``
    zones appear here.
    """
    token = issue["token"]
    zone = issue["zone"]
    expansion = issue.get("expansion")
    zone_label = "body, first use" if zone == "body" else "abstract"

    if expansion:
        suggested = _build_replacement(token, expansion)
        suffix = f" suggested: “{suggested}”."
        if issue.get("needs_track_change"):
            suffix += " A tracked change has been proposed."
        return f"• {token} ({zone_label}) —{suffix}"
    return (
        f"• {token} ({zone_label}) — not recognised in the approved "
        f"list and not introduced in the document. Please verify and "
        f"expand on first use."
    )


def _build_zone_map(doc_root: etree._Element) -> list[str]:
    """Return zone-per-paragraph in document order.

    The zone of a heading paragraph is the zone it transitions INTO. So
    ``Introduction`` itself counts as ``body`` content, not ``front``.
    """
    zones: list[str] = []
    zone = _initial_zone(doc_root)
    for para_el in doc_root.iter(f"{WQ}p"):
        style = _get_style_name(para_el)
        if style.startswith("Heading"):
            zone = _heading_zone_transition(
                style, _para_plain_text(para_el), zone, intro_seen=False
            )
        zones.append(zone)
    return zones


def _find_title_paragraph_indices(doc_root: etree._Element, zones: list[str]) -> set[int]:
    """Return paragraph indices that represent the manuscript title.

    Primary signal is explicit title styles. As a fallback, protect the first
    non-empty front-zone paragraph that is not an authors/affiliations line or
    a front-page label heading.
    """
    title_idxs: set[int] = set()
    first_front_candidate: int | None = None

    for para_idx, para_el in enumerate(doc_root.iter(f"{WQ}p")):
        style = _get_style_name(para_el)
        text = _para_plain_text(para_el).strip()
        if style in _TITLE_STYLES and text:
            title_idxs.add(para_idx)
            continue

        if first_front_candidate is not None:
            continue
        if para_idx >= len(zones) or zones[para_idx] != "front":
            continue
        if not text:
            continue
        if style in _NON_TITLE_FRONT_STYLES:
            continue
        if style.startswith("Heading"):
            continue
        if _normalise_heading(text) in _NON_TITLE_FRONT_HEADINGS:
            continue
        first_front_candidate = para_idx

    if first_front_candidate is not None:
        title_idxs.add(first_front_candidate)

    return title_idxs


def _scan_issues(
    doc_root: etree._Element,
    allow_list: dict[str, list[str]],
    inline_defs: dict[str, tuple[str, tuple[int, int]]],
) -> list[dict]:
    """Walk the document and collect every acronym issue (no mutations).

    Returns issues in document order. Each issue dict carries enough info
    for Phase 2 to apply the right mutation:
      - token, zone
      - para_idx, para_el
      - para_offset, start, end  (visible-text offsets within the paragraph;
        ``start``/``end`` are absolute paragraph offsets too — Phase 2
        re-locates the containing run by ``start`` after right-to-left
        mutations may have split the original run)
      - expansion: str | None
      - needs_track_change: True only for the FIRST body issue per acronym
        when an expansion is known
    """
    zones = _build_zone_map(doc_root)
    title_para_idxs = _find_title_paragraph_indices(doc_root, zones)
    seen_per_zone: dict[str, set[str]] = {"front": set(), "body": set()}
    issues: list[dict] = []

    for para_idx, para_el in enumerate(doc_root.iter(f"{WQ}p")):
        zone = zones[para_idx]
        if zone == "outside":
            continue
        # Manuscript title is out of scope: Sam handles title case, and the
        # acronym pass deliberately never touches the title — no flag, no
        # tracked expansion, no bullet. Includes the fallback "first
        # non-empty front paragraph" detection so untemplated docs are
        # treated the same way.
        if para_idx in title_para_idxs:
            continue
        style = _get_style_name(para_el)
        if style in _SKIP_STYLES:
            continue
        para_text = _para_plain_text(para_el)
        if not para_text:
            continue
        # Suppress on Creative Commons licence strings — CC / BY / ND / SA / NC
        # are licence-shortcode fragments here, not novel acronyms.
        if _is_cc_licence_paragraph(para_text):
            continue
        bracket_spans = _bracketed_spans(para_text)

        # Walk runs to map (run, intra_offset) → paragraph-relative offset.
        # We READ inserted runs (final document state) and SKIP deleted ones
        # — see _should_skip_run for the rationale.
        run_offset = 0
        for r in para_el.iter(f"{WQ}r"):
            if _should_skip_run(r):
                continue
            t_el = r.find(f"{WQ}t")
            if t_el is None:
                continue
            run_text = t_el.text or ""

            for m in _ACRONYM_PATTERN.finditer(run_text):
                token = m.group(0)
                para_pos = run_offset + m.start()
                # Skip occurrences inside parens / brackets — they're
                # definitions or citations, not running prose.
                if _in_any_span(para_pos, bracket_spans):
                    continue
                # Block-listed tokens (USA, OK, iOS, …) are never flagged
                # UNLESS the editor has also put them on the allow-list,
                # in which case the allow-list wins and the token still
                # follows the first-use rule. See _ACRONYM_BLOCKLIST
                # docstring for the rationale.
                if token in _ACRONYM_BLOCKLIST and token not in allow_list:
                    continue

                # Skip if already fired in this zone — only the FIRST
                # problematic occurrence per (acronym, zone) becomes an
                # issue.
                if token in seen_per_zone[zone]:
                    continue

                # Inline-definition lookup. The def's zone is the zone of
                # its containing paragraph (from our pre-built zone map).
                def_entry = inline_defs.get(token)
                def_zone: str | None = None
                def_position: tuple[int, int] | None = None
                if def_entry is not None:
                    _, def_position = def_entry
                    def_para_idx = def_position[0]
                    if 0 <= def_para_idx < len(zones):
                        def_zone = zones[def_para_idx]

                # Body: silenced only by an in-body def appearing earlier
                # in document order. Body needs its OWN introduction; a def
                # in the abstract doesn't count.
                if zone == "body":
                    if (
                        def_zone == "body"
                        and def_position is not None
                        and def_position < (para_idx, para_pos)
                    ):
                        continue
                # Front (abstract): an independent zone that needs its OWN
                # introduction — symmetric to the body rule above. Silenced by
                # the allow-list, or by an inline definition that is itself in
                # the FRONT zone and appears earlier in document order. A
                # definition that lives only in the body does NOT satisfy the
                # abstract (e.g. "AI" expanded in the Introduction but used
                # bare in the abstract is still flagged). The known expansion
                # is still surfaced in the bullet so the editor can introduce
                # it in the abstract.
                else:  # zone == "front"
                    if token in allow_list:
                        continue
                    if (
                        def_zone == "front"
                        and def_position is not None
                        and def_position < (para_idx, para_pos)
                    ):
                        continue

                # This is an issue. Determine the suggested expansion.
                expansion: str | None = None
                if def_entry is not None:
                    expansion = def_entry[0]
                elif token in allow_list:
                    expansion = allow_list[token][0]

                # Track-change-eligible iff body + we know what to write.
                needs_tc = zone == "body" and expansion is not None

                issues.append(
                    {
                        "token": token,
                        "zone": zone,
                        "para_idx": para_idx,
                        "para_el": para_el,
                        "start": para_pos,
                        "end": para_pos + (m.end() - m.start()),
                        "expansion": expansion,
                        "needs_track_change": needs_tc,
                    }
                )
                seen_per_zone[zone].add(token)
            run_offset += len(run_text)

    return issues


def _find_run_at_offset(
    para_el: etree._Element, target_offset: int
) -> tuple[etree._Element, int] | None:
    """Return ``(run_el, intra_run_offset)`` for the visible character at
    ``target_offset`` within ``para_el``'s plain text. Returns ``None`` if
    the offset falls past the paragraph's visible text.
    """
    # Iterate with the same skip policy as _scan_issues so the offset we
    # compute lands on the run the scanner found the acronym in.
    cumulative = 0
    for r in para_el.iter(f"{WQ}r"):
        if _should_skip_run(r):
            continue
        t_el = r.find(f"{WQ}t")
        if t_el is None:
            continue
        run_text = t_el.text or ""
        run_len = len(run_text)
        if cumulative + run_len > target_offset:
            return r, target_offset - cumulative
        cumulative += run_len
    return None


def _apply_mutations(
    issues: list[dict],
    anchor_comment_id: int,
    next_change_id: int,
) -> int:
    """Apply tracked-change rewrites and the comment-range anchor.

    Mutations are applied **right-to-left within each paragraph** so each
    mutation's location (a paragraph-relative visible offset) remains valid
    for the next mutation. The anchor is the leftmost issue in document
    order — it's applied last (rightmost paragraph processing already done
    by then for its paragraph) and additionally wraps with the
    ``commentRangeStart``/``commentRangeEnd`` markers via
    ``_split_run_for_action``.
    """
    if not issues:
        return next_change_id

    anchor = issues[0]  # first issue in document order

    # Group by paragraph so we can sort right-to-left independently per
    # paragraph. Order across paragraphs doesn't matter for offset validity.
    by_para: dict[int, list[dict]] = {}
    for issue in issues:
        by_para.setdefault(issue["para_idx"], []).append(issue)

    for para_idx, para_issues in by_para.items():
        para_issues.sort(key=lambda i: i["start"], reverse=True)
        for issue in para_issues:
            location = _find_run_at_offset(issue["para_el"], issue["start"])
            if location is None:
                continue
            run_el, intra_offset = location
            match_len = issue["end"] - issue["start"]
            is_anchor = issue is anchor
            replacement = (
                _build_replacement(issue["token"], issue["expansion"])
                if issue.get("needs_track_change")
                else None
            )
            if is_anchor:
                next_change_id = _split_run_for_action(
                    run_el,
                    intra_offset,
                    intra_offset + match_len,
                    replacement,
                    anchor_comment_id,
                    next_change_id,
                )
            elif replacement is not None:
                next_change_id = _split_run_for_track_change_only(
                    run_el,
                    intra_offset,
                    intra_offset + match_len,
                    replacement,
                    next_change_id,
                )
            # else: no mutation — the issue is reflected in the comment
            # bullet only (e.g. an abstract issue with no known expansion).

    return next_change_id


def apply_acronym_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
    accepted_acronyms: dict[str, list[str]] | None = None,
) -> tuple[int, list[dict]]:
    """Run the full acronym pass against ``input_path``, writing to ``output_path``.

    Returns ``(next_change_id, actions)`` where each action is a dict with
    keys ``acronym``, ``zone``, ``expansion`` (may be ``None``),
    ``comment_id`` (the single consolidated comment all actions share), and
    ``needs_track_change``.
    """
    if accepted_acronyms is None:
        # Lazy import keeps unit tests of this module independent of the
        # storage layer.
        from app.services.acronym_store import load_acronyms
        accepted_acronyms = load_acronyms()

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
        existing = [
            int(el.get(f"{WQ}id", 0)) for el in comments_root.findall(f"{WQ}comment")
        ]
        next_comment_id = max(existing, default=0) + 1
    else:
        comments_root = etree.Element(f"{WQ}comments", nsmap={"w": W})
        next_comment_id = 1

    inline_defs = _collect_inline_definitions(doc_root)
    issues = _scan_issues(doc_root, accepted_acronyms, inline_defs)

    if not issues:
        # No changes at all — nothing to write. Still copy file through if
        # input != output to keep callers' contract simple.
        if input_path != output_path:
            with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
                output_path, "w", zipfile.ZIP_DEFLATED
            ) as zout:
                for item in zin.infolist():
                    zout.writestr(item, zin.read(item.filename))
        return next_change_id, []

    # Build and append the single consolidated comment.
    anchor_comment_id = next_comment_id
    bullets = [_build_bullet(issue) for issue in issues]
    comments_root.append(
        _make_consolidated_comment_element(
            anchor_comment_id, _CONSOLIDATED_INTRO, bullets
        )
    )

    next_change_id = _apply_mutations(issues, anchor_comment_id, next_change_id)

    actions = [
        {
            "acronym": issue["token"],
            "zone": issue["zone"],
            "expansion": issue["expansion"],
            "comment_id": anchor_comment_id,
            "needs_track_change": issue["needs_track_change"],
        }
        for issue in issues
    ]

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_comments_xml = etree.tostring(
        comments_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_rels_xml = _patch_rels(rels_xml)
    new_ct_xml = _patch_content_types(ct_xml)

    tmp = output_path + ".acro.tmp"
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
            if not has_comments:
                zout.writestr("word/comments.xml", new_comments_xml)
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return next_change_id, actions
