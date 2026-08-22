"""Grammar corrections as Word tracked changes using LLM.

The LLM returns a list of {original, replacement} pairs where `original` is
the exact text as it appears in the manuscript.  Each pair is applied as a
<w:del>/<w:ins> tracked change so the editor can accept or reject it in Word.
"""

import os
import re
import zipfile
from copy import deepcopy

from lxml import etree

from app.services.acronym_corrections import (
    _make_comment_element,
    _patch_content_types,
    _patch_rels,
    _split_run_for_action,
)
from app.services.ai.llm_client import LLMError, call_llm_json
from app.services.document_analysis_services import load_paragraphs
from app.services.document_zones import iter_paragraphs_with_zone, should_skip_paragraph
from app.services.language_corrections import AU_CORRECTIONS
from app.services.timestamps import now_sydney_iso

# Reverse lookup: AU spelling → US spelling (for au→us guard)
_AU_TO_US: dict[str, str] = {v.lower(): k for k, v in AU_CORRECTIONS.items()}
_STYLE_WORD_PAIRS = {
    ("people", "peoples"), ("peoples", "people"),
    ("language", "languages"), ("languages", "language"),
    ("culture", "cultures"), ("cultures", "culture"),
    ("knowledge", "knowledges"), ("knowledges", "knowledge"),
}

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"
AUTHOR = "CopyEditor AI"
DATE = now_sydney_iso()

# Styles whose paragraphs are NOT sent for grammar review
_SKIP_STYLES = {
    "Heading 1", "Heading 2", "Heading 3", "Heading 4",
    "APA 7 Reference List Entry",
    "Article Title",
}

_GRAMMAR_SCHEMA = {
    "name": "grammar_corrections",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "corrections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "original":    {"type": "string"},
                        "replacement": {"type": "string"},
                        "reason":      {"type": "string"},
                    },
                    "required": ["original", "replacement", "reason"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["corrections"],
        "additionalProperties": False,
    },
}

_SYSTEM_PROMPT = """\
You are a professional Australian English grammar checker reviewing an academic
manuscript accepted for publication in the Journal of University Teaching and
Learning Practice (JUTLP).

Your ONLY task is to identify STRUCTURAL grammar errors. Do NOT correct vocabulary
or word choice under any circumstances.

Rules:
1. Flag ONLY these specific grammar error types:
   - Subject-verb agreement (e.g. "data was" → "data were")
   - Incorrect verb tense within a sentence
   - Missing or wrong article (a/an/the) where grammatically required
   - Dangling or misplaced modifier
   - Pronoun-antecedent number mismatch
   - Comma splice between two independent clauses
2. DO NOT flag anything else. This explicitly excludes:
   - Spelling, vocabulary, or word choice (do not suggest synonyms)
   - Stylistic changes between knowledge and knowledges
   - Singular/plural changes between people/peoples, language/languages,
     culture/cultures, or knowledge/knowledges
   - Indigenous/indigenous capitalisation; retain the author's preference
   - Hyphenation, punctuation style, capitalisation
   - Australian vs American English spelling differences
   - Compound words, technical terms, domain jargon
3. DO NOT touch: proper nouns, surnames, institution names, acronyms, camelCase
   terms, URLs, or any text inside citation placeholders marked (REF).
   DO NOT flag anything inside DIRECT QUOTATIONS — text enclosed in
   "double quotation marks" or curly double quotes must retain the
   source's original wording, even if it contains a grammar error.
4. The "original" field MUST be copied VERBATIM from the text.
   HARD LIMIT: "original" must be 6 words or fewer.
5. If you are uncertain whether something is a grammar error, do NOT flag it.
6. Return an empty corrections array if there are no clear grammar errors.
"""



_CITATION_RE = re.compile(r'\([^)]*\d{4}[^)]*\)')
_URL_RE = re.compile(r'https?://\S+|www\.\S+')

# Words that are legitimately capitalised at sentence start but are NOT proper nouns.
# Any word starting uppercase that is NOT in this set is treated as a proper noun.
_SENTENCE_START_WORDS = frozenset({
    'a', 'an', 'the', 'this', 'these', 'that', 'those',
    'it', 'its', 'they', 'their', 'we', 'our', 'he', 'she', 'his', 'her',
    'in', 'on', 'at', 'by', 'for', 'to', 'of', 'as', 'with', 'from',
    'and', 'but', 'or', 'not', 'if', 'when', 'while', 'although',
    'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'has', 'have', 'had', 'do', 'does', 'did',
    'students', 'higher', 'many', 'most', 'some', 'all', 'each', 'both',
    'more', 'less', 'other', 'further', 'however', 'therefore',
})

# Matches acronyms like GCs, COVID, LMS, EOI — 2+ consecutive uppercase letters,
# optionally followed by lowercase plural 's'.
_ACRONYM_RE = re.compile(r'\b[A-Z]{2,}s?\b')

_SINGULAR_ACADEMIC_SUBJECT_NOUNS = (
    "analysis",
    "approach",
    "article",
    "chapter",
    "contribution",
    "discussion",
    "evidence",
    "finding",
    "framework",
    "intervention",
    "method",
    "model",
    "paper",
    "programme",
    "program",
    "project",
    "research",
    "result",
    "study",
    "work",
)

_CONTINGENT_SVA_RE = re.compile(
    r"\b(?P<subject>"
    r"(?:the|this|that|its|their|our|his|her)\s+"
    r"(?:(?:central|current|important|main|overall|present|primary|proposed|"
    r"reported|specific|theoretical|practical)\s+){0,2}"
    rf"(?:{'|'.join(_SINGULAR_ACADEMIC_SUBJECT_NOUNS)})"
    r")\s+(?P<verb>are|were|have)\b",
    re.IGNORECASE,
)

_SVA_VERB_SUGGESTIONS = {
    "are": "is",
    "were": "was",
    "have": "has",
}


def _contingent_sva_comment(subject: str, verb: str) -> str:
    suggestion = _SVA_VERB_SUGGESTIONS.get(verb.lower(), "")
    if suggestion:
        return (
            "Please check the subject-verb agreement here. "
            f"The subject phrase '{subject}' appears to be singular, so "
            f"'{verb}' may need to be revised to '{suggestion}'."
        )
    return (
        "Please check the subject-verb agreement here. "
        f"The subject phrase '{subject}' appears to be singular."
    )


def _strip_citations(text: str) -> str:
    """Remove parenthetical citations and URLs before sending to LLM."""
    text = _CITATION_RE.sub('(REF)', text)
    text = _URL_RE.sub('[URL]', text)
    return text


def _is_proper_noun_correction(original: str) -> bool:
    """Return True if original looks like a proper noun, surname, acronym, or tech term."""
    words = re.findall(r'\b[A-Za-z]+\b', original.strip())
    if not words:
        return False
    # Acronym-like: 2+ consecutive uppercase letters, optionally plural (GCs, COVID, LMS, EOI)
    if _ACRONYM_RE.search(original):
        return True
    # camelCase technical term: lowercase letter immediately followed by uppercase (ePortfolio, eLearning)
    if re.search(r'[a-z][A-Z]', original):
        return True
    # Any word starting uppercase that isn't a known sentence-start word = proper noun / surname
    # This catches: single names (Ravet, Jaekel), multi-word names (Van Zile-Tamsen),
    # mixed phrases (Kohler & Van Zile-Tamsen), and mixed-case acronyms (GCs already caught above)
    if any(w[0].isupper() and w.lower() not in _SENTENCE_START_WORDS for w in words):
        return True
    return False


_US_SPELLINGS: frozenset[str] = frozenset(AU_CORRECTIONS.keys())

_AU_US_EXTRA_PAIRS = frozenset({
    ("whilst", "while"),
    ("focussed", "focused"),
    ("licence", "license"),
    ("licences", "licenses"),
    ("practise", "practice"),
    ("practises", "practices"),
    ("practised", "practiced"),
    ("practising", "practicing"),
    ("microcredentialling", "microcredentialing"),
})

_AU_DOUBLE_L = re.compile(r'\b\w+ll(?:ing|ed|er|ers|ment|ments|s)?\b', re.I)
_AU_US_SUFFIX_PAIRS = (
    ("isability", "izability"),
    ("isations", "izations"),
    ("isation", "ization"),
    ("isable", "izable"),
    ("ising", "izing"),
    ("ised", "ized"),
    ("ises", "izes"),
    ("ise", "ize"),
    ("ysing", "yzing"),
    ("ysed", "yzed"),
    ("yses", "yzes"),
    ("yse", "yze"),
    ("ence", "ense"),
    ("ogue", "og"),
    ("our", "or"),
    ("re", "er"),
)


def _has_au_us_suffix_swap(au_word: str, us_word: str) -> bool:
    for au_suffix, us_suffix in _AU_US_SUFFIX_PAIRS:
        if not au_word.endswith(au_suffix) or not us_word.endswith(us_suffix):
            continue
        au_stem = au_word[:-len(au_suffix)]
        if au_stem == us_word[:-len(us_suffix)] and len(au_stem) >= 2:
            return True
    return False


def _is_au_to_us_replacement(original: str, replacement: str) -> bool:
    """Return True if the correction would flip Australian English to American English."""
    orig_words = set(re.findall(r"\b\w+\b", original.lower()))
    repl_words = set(re.findall(r"\b\w+\b", replacement.lower()))

    # Dict-based check (~300 AU/US pairs)
    for au_word in orig_words:
        us_word = _AU_TO_US.get(au_word)
        if us_word and us_word in repl_words:
            return True

    for au_word, us_word in _AU_US_EXTRA_PAIRS:
        if au_word in orig_words and us_word in repl_words:
            return True

    for au_word in orig_words:
        if any(_has_au_us_suffix_swap(au_word, us_word) for us_word in repl_words):
            return True

    # General double-l (AU) → single-l (US)
    for w in {m.group().lower() for m in _AU_DOUBLE_L.finditer(original)}:
        single_l = re.sub(r'll(ing|ed|er|ers|ment|ments|s)?$', r'l\1', w)
        if single_l in repl_words:
            return True

    # Backstop: block if replacement introduces any US spelling not in original
    if (repl_words - orig_words) & _US_SPELLINGS:
        return True

    return False


def _fix_au_spellings(text: str) -> str:
    """Replace any US spellings in text with AU equivalents using AU_CORRECTIONS."""
    def _replace(m: re.Match) -> str:
        word = m.group(0)
        au = AU_CORRECTIONS.get(word.lower())
        if au is None:
            return word
        if word.isupper():
            return au.upper()
        if word[0].isupper():
            return au[0].upper() + au[1:]
        return au
    return re.sub(r'\b[A-Za-z]+\b', _replace, text)


def _build_user_prompt(paragraphs: list[str]) -> str:
    numbered = "\n".join(f"[{i + 1}] {_strip_citations(p)}" for i, p in enumerate(paragraphs))
    return (
        "Review the following paragraphs for grammar errors.\n"
        "Return only the corrections — no commentary.\n\n"
        f"{numbered}"
    )


def get_grammar_corrections(docx_path: str) -> list[dict]:
    """Call LLM and return a list of {original, replacement, reason} dicts."""
    para_records = load_paragraphs(docx_path)
    body_paras = [
        p.text for p in para_records
        if p.style not in _SKIP_STYLES and not p.is_empty and len(p.text) > 20
    ]
    if not body_paras:
        return []

    try:
        result = call_llm_json(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=_build_user_prompt(body_paras),
            response_schema=_GRAMMAR_SCHEMA,
        )
        corrections = result["content"].get("corrections", [])
        out = []
        for c in corrections:
            original = (c.get("original") or "").strip()
            replacement = (c.get("replacement") or "").strip()
            reason = (c.get("reason") or "").strip()
            if len(original.split()) > 6:
                continue
            if _is_proper_noun_correction(original):
                continue
            if (original.lower(), replacement.lower()) in _STYLE_WORD_PAIRS:
                continue
            if _is_au_to_us_replacement(original, replacement):
                continue
            # Fix any US spellings the LLM put in the replacement
            replacement = _fix_au_spellings(replacement)
            # If fixing spelling makes it identical to original, it was a pure spelling flip — discard
            if not replacement or replacement.lower() == original.lower():
                continue
            # Reject hyphen-strip edits (`Two-stage → Twostage`,
            # `Evidences-Based → evidencesbased`). The prompt forbids
            # hyphenation decisions; this is a hard guard for when the
            # LLM ignores it. Mirrors the guard in body_llm_edits._validate_edit
            # but localised here because grammar pass has its own apply
            # path that doesn't go through body validation.
            if (
                ("-" in original or "-" in replacement)
                and original.lower().replace("-", "") == replacement.lower().replace("-", "")
            ):
                continue
            out.append({"original": original, "replacement": replacement, "reason": reason})
        return out
    except LLMError:
        return []


# ---------------------------------------------------------------------------
# XML helpers — phrase-level del/ins tracked changes
# ---------------------------------------------------------------------------

def _run_texts(para_el: etree._Element) -> list[tuple[etree._Element, str]]:
    """Return (run_el, text) for every plain run (not inside del/ins)."""
    out = []
    for child in para_el:
        if child.tag != f"{WQ}r":
            continue
        parent = child.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        t = child.find(f"{WQ}t")
        out.append((child, t.text or "" if t is not None else ""))
    return out


def _find_phrase_in_runs(
    runs: list[tuple[etree._Element, str]],
    phrase: str,
) -> tuple[int, int, int, int] | None:
    """Locate *phrase* in the concatenated run texts.

    Returns (run_start_idx, char_start, run_end_idx, char_end) or None.
    """
    combined = "".join(text for _, text in runs)
    idx = combined.lower().find(phrase.lower())
    if idx == -1:
        # Try normalising internal whitespace
        norm_combined = re.sub(r"\s+", " ", combined)
        norm_phrase   = re.sub(r"\s+", " ", phrase)
        idx = norm_combined.lower().find(norm_phrase.lower())
        if idx == -1:
            return None
        combined = norm_combined

    end = idx + len(phrase)
    # Map global char positions back to (run_idx, char_offset)
    pos = 0
    r_start = r_end = None
    c_start = c_end = 0
    for i, (_, text) in enumerate(runs):
        run_end = pos + len(text)
        if r_start is None and pos <= idx < run_end:
            r_start = i
            c_start = idx - pos
        if r_start is not None and pos < end <= run_end:
            r_end = i
            c_end = end - pos
            break
        pos = run_end

    if r_start is None or r_end is None:
        return None
    return r_start, c_start, r_end, c_end


def _apply_phrase_correction(
    para_el: etree._Element,
    original: str,
    replacement: str,
    change_id: int,
) -> int:
    """Replace *original* phrase in para_el with del+ins tracked changes.

    Returns the next available change_id.
    """
    nsmap = {"w": W}
    runs = _run_texts(para_el)
    loc = _find_phrase_in_runs(runs, original)
    if loc is None:
        return change_id

    r_start, c_start, r_end, c_end = loc
    # Collect all run elements involved
    involved = [runs[i][0] for i in range(r_start, r_end + 1)]
    # Collect rPr from the first involved run
    rPr = involved[0].find(f"{WQ}rPr")

    # Find position of first involved run in paragraph children
    children = list(para_el)
    insert_at = children.index(involved[0])

    # Remove all involved runs from the paragraph
    for run_el in involved:
        para_el.remove(run_el)

    def _text_run(text: str) -> etree._Element:
        r = etree.Element(f"{WQ}r", nsmap=nsmap)
        if rPr is not None:
            r.append(deepcopy(rPr))
        t = etree.SubElement(r, f"{WQ}t")
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return r

    def _del_run(text: str) -> etree._Element:
        r = etree.Element(f"{WQ}r", nsmap=nsmap)
        if rPr is not None:
            r.append(deepcopy(rPr))
        dt = etree.SubElement(r, f"{WQ}delText")
        dt.text = text
        dt.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return r

    pos = insert_at

    # 1. Before text (from first run, before c_start)
    first_text = runs[r_start][1]
    if c_start > 0:
        para_el.insert(pos, _text_run(first_text[:c_start]))
        pos += 1

    # 2. <w:del> containing all phrase text across runs
    del_el = etree.Element(f"{WQ}del", nsmap=nsmap)
    del_el.set(f"{WQ}id", str(change_id))
    del_el.set(f"{WQ}author", AUTHOR)
    del_el.set(f"{WQ}date", DATE)

    if r_start == r_end:
        del_el.append(_del_run(first_text[c_start:c_end]))
    else:
        del_el.append(_del_run(first_text[c_start:]))
        for i in range(r_start + 1, r_end):
            del_el.append(_del_run(runs[i][1]))
        last_text = runs[r_end][1]
        del_el.append(_del_run(last_text[:c_end]))

    para_el.insert(pos, del_el)
    pos += 1
    change_id += 1

    # 3. <w:ins> with replacement
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
    para_el.insert(pos, ins_el)
    pos += 1
    change_id += 1

    # 4. After text (from last run, after c_end)
    last_text = runs[r_end][1]
    if c_end < len(last_text):
        para_el.insert(pos, _text_run(last_text[c_end:]))

    return change_id


def apply_grammar_corrections(
    input_path: str,
    output_path: str,
    corrections: list[dict],
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Apply grammar corrections as tracked changes. Returns (next_id, applied)."""
    if not corrections:
        return next_change_id, []

    with zipfile.ZipFile(input_path, "r") as z:
        doc_xml = z.read("word/document.xml")

    doc_root = etree.fromstring(doc_xml)
    applied: list[dict] = []

    for correction in corrections:
        original    = (correction.get("original") or "").strip()
        replacement = (correction.get("replacement") or "").strip()
        reason      = (correction.get("reason") or "").strip()
        if not original or not replacement or original == replacement:
            continue

        for para_el in doc_root.iter(f"{WQ}p"):
            plain = "".join(
                (t.text or "")
                for r in para_el
                if r.tag == f"{WQ}r"
                for t in r.findall(f"{WQ}t")
            )
            if original.lower() not in plain.lower():
                continue
            prev_id = next_change_id
            next_change_id = _apply_phrase_correction(
                para_el, original, replacement, next_change_id
            )
            if next_change_id > prev_id:
                applied.append({"original": original, "replacement": replacement, "reason": reason})
            break

    new_doc_xml = etree.tostring(doc_root, xml_declaration=True, encoding="UTF-8", standalone=True)

    tmp = output_path + ".gram.tmp"
    try:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return next_change_id, applied


def _visible_text_units(para_el: etree._Element) -> list[dict]:
    """Return visible text units, including insertions but excluding deletions.

    Late grammar checks need to inspect the text as the editor will see it
    after earlier tracked insertions, while ignoring text already marked for
    deletion. Each unit keeps enough run/offset metadata for comment anchoring.
    """
    units: list[dict] = []
    cursor = 0
    for t_el in para_el.iter(f"{WQ}t"):
        run_el = t_el.getparent()
        if run_el is None or run_el.tag != f"{WQ}r":
            continue
        parent = run_el.getparent()
        if parent is not None and parent.tag == f"{WQ}del":
            continue
        text = t_el.text or ""
        if not text:
            continue
        units.append(
            {
                "run": run_el,
                "text": text,
                "start": cursor,
                "end": cursor + len(text),
            }
        )
        cursor += len(text)
    return units


def _anchor_visible_span(
    para_el: etree._Element,
    units: list[dict],
    start: int,
    end: int,
    comment_id: int,
) -> bool:
    """Anchor a comment to a visible span when it falls inside one text run."""
    for unit in units:
        if unit["start"] <= start and end <= unit["end"]:
            local_start = start - unit["start"]
            local_end = end - unit["start"]
            _split_run_for_action(
                unit["run"],
                local_start,
                local_end,
                expansion=None,
                comment_id=comment_id,
                change_id=0,
            )
            return True
    return False


def apply_contingent_grammar_comments(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Add comments for grammar errors exposed by earlier partial fixes.

    This pass is intentionally deterministic and narrow. It catches cases like
    ``their work are`` after prior tracked changes have transformed nearby
    wording, a case the first-pass LLM grammar review can miss because the
    final visible phrase did not exist yet.
    """
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
            int(el.get(f"{WQ}id", 0))
            for el in comments_root.findall(f"{WQ}comment")
        ]
        next_comment_id = max(existing, default=0) + 1
    else:
        comments_root = etree.Element(f"{WQ}comments", nsmap={"w": W})
        next_comment_id = 1

    actions: list[dict] = []
    seen_paragraphs: set[int] = set()

    for para_idx, (para_el, zone) in enumerate(iter_paragraphs_with_zone(doc_root)):
        if should_skip_paragraph(para_el, zone):
            continue
        units = _visible_text_units(para_el)
        visible_text = "".join(unit["text"] for unit in units)
        if not visible_text:
            continue
        match = _CONTINGENT_SVA_RE.search(visible_text)
        if match is None:
            continue
        if para_idx in seen_paragraphs:
            continue

        verb_start, verb_end = match.span("verb")
        if not _anchor_visible_span(
            para_el,
            units,
            verb_start,
            verb_end,
            next_comment_id,
        ):
            continue

        message = _contingent_sva_comment(match.group("subject"), match.group("verb"))
        comments_root.append(
            _make_comment_element(next_comment_id, message)
        )
        actions.append(
            {
                "rule": "CONTINGENT_SVA",
                "phrase": match.group(0),
                "subject": match.group("subject"),
                "verb": match.group("verb"),
                "comment_id": next_comment_id,
            }
        )
        seen_paragraphs.add(para_idx)
        next_comment_id += 1

    if not actions:
        if input_path != output_path:
            with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
                output_path, "w", zipfile.ZIP_DEFLATED
            ) as zout:
                for item in zin.infolist():
                    zout.writestr(item, zin.read(item.filename))
        return next_change_id, actions

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_comments_xml = etree.tostring(
        comments_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_rels_xml = _patch_rels(rels_xml)
    new_ct_xml = _patch_content_types(ct_xml)

    tmp = output_path + ".grammar-comments.tmp"
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
