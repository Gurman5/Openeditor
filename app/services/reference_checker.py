import html
import json
import os
import re
import time
import unicodedata
import zipfile
from difflib import SequenceMatcher
from pathlib import Path

import requests
from lxml import etree

from app.domain.canonical_jultp_template import strip_leading_section_number
from app.services.ai.llm_client import LLMError, call_llm_json
from app.services.document_analysis_services import extract_main_sections, load_paragraphs
from app.services.reference_reconstructor import (
    references_are_equivalent,
)
from app.services.reference_type_checker import check_reference_type_style

# ── Disk cache for CrossRef API responses ────────────────────────────────────
# Enabled by default; set CROSSREF_CACHE=0 to disable (e.g. in production).
# Cache file lives next to this file so it's easy to find and delete.
_CACHE_ENABLED = os.environ.get("CROSSREF_CACHE", "1") != "0"
_CACHE_PATH = Path(__file__).parent / ".crossref_cache.json"
_cache_data: dict = {}

def _cache_load() -> None:
    global _cache_data
    if not _CACHE_ENABLED or not _CACHE_PATH.exists():
        return
    try:
        _cache_data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        _cache_data = {}

def _cache_get(key: str):
    return _cache_data.get(key)

def _cache_set(key: str, value) -> None:
    if not _CACHE_ENABLED:
        return
    _cache_data[key] = value
    try:
        _CACHE_PATH.write_text(
            json.dumps(_cache_data, ensure_ascii=False, indent=None),
            encoding="utf-8",
        )
    except Exception:
        pass

_cache_load()

REFERENCE_STYLE = "APA 7 Reference List Entry"
CROSSREF_API = "https://api.crossref.org/works"
CROSSREF_HEADERS = {"User-Agent": "CopyEditorAI/1.0 (mailto:copyeditor@oapa.org)"}
SCORE_THRESHOLD = 50.0

YEAR_RE = re.compile(r'\(\d{4}[a-z]?\)')
AUTHOR_RE = re.compile(r'^[A-ZÀ-Ö][a-zA-ZÀ-ÿ\-\'’]+,\s+[A-Z]\.')

# An appendix heading such as "Appendix", "Appendix A", "Appendix 1.",
# "Appendices". JUTLP requires References to be the LAST section, so anything
# that looks like an appendix heading closes the reference-checking window —
# regardless of its paragraph style. Authors frequently leave appendix
# headings unstyled (or carrying the reference style), so we must NOT rely on
# a Heading-1 style to detect the boundary.
_APPENDIX_HEADING_RE = re.compile(r'^\s*appendi(?:x|ces)\b', re.IGNORECASE)


def _is_appendix_heading(text: str) -> bool:
    return bool(_APPENDIX_HEADING_RE.match(text or ""))

# Curly quotes that Word's autocorrect inserts. We pre-normalise body text
# to the straight forms before regex matching so a surname like ``O'Hagan``
# with a smart apostrophe doesn't end up captured as just ``Hagan``.
_SMART_QUOTE_MAP = str.maketrans({
    "‘": "'", "’": "'",  # left/right single
    "“": '"', "”": '"',  # left/right double
    "′": "'",                 # prime
})


def _normalise_text(text: str) -> str:
    """Replace curly quotes with their straight ASCII equivalents."""
    return (text or "").translate(_SMART_QUOTE_MAP)

_WQ = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_HL_TYPE = f"{_R_NS}/hyperlink"
_R_NS_Q = f"{{{_R_NS}}}"

_REF_STYLES = {
    "APA7ReferenceListEntry",
    "APA 7 Reference List Entry",
    "APA7 Reference List Entry",
    "APAReferenceListEntry",
    "Reference List Entry",
}

# Matches a DOI embedded anywhere in a URL (DOIs always start with 10.)
_DOI_IN_URL = re.compile(r'10\.\d{4,9}/[^\s,;>\"\']+')

# Strips any https?:// URL from a string (used when comparing CrossRef APA
# against the author's reference — the author may not have included the DOI,
# so we compare content without the URL to avoid false "DOI may not match" warnings).
_URL_STRIP_RE = re.compile(r'\s*https?://\S+')

# Citation patterns — parenthetical (Crawford, 2024) and narrative Crawford (2024).
# Both patterns capture the FIRST-AUTHOR surname only; the optional non-capturing
# group consumes a `& X` / `and X` co-author when present so the regex doesn't
# accidentally anchor on the second author. The character class accepts
# apostrophes (straight ' AND curly ’) so names like O'Hagan and O’Hagan both
# match in full instead of collapsing to "Hagan".
#
# Parenthetical citations are extracted in two stages:
#
#   1. Find every ``(...)`` group that contains a 4-digit year. This catches
#      both single citations ``(Smith, 2020)`` and multi-citation groups
#      ``(Smith, 2020; Jones, 2021; Doe et al., 2022)``.
#   2. Split the group's content on ``;`` and run ``_CITE_PAREN_INNER_RE``
#      on each segment. The earlier ``_CITE_PAREN_RE`` required a literal
#      closing ``)`` immediately after the year, so the regex failed to
#      match ANY citation inside a multi-citation group — all four
#      citations in ``(Alkhawaja, 2024; Belhassen et al., 2025; ...)``
#      were silently lost, falsely failing CONS001 for each one.
_PAREN_WITH_YEAR_RE = re.compile(r'\(([^()]*\d{4}[a-z]?[^()]*)\)')
_CITE_PAREN_INNER_RE = re.compile(
    r'([A-ZÀ-Ö][a-zA-ZÀ-ÿ\-\'’ ]+?)'
    r'(?:(?:,?\s*)(?:&|and)\s+[A-ZÀ-Ö][a-zA-ZÀ-ÿ\-\'’ ]+?)?'
    r'(?:,?\s*et\s+al\.?)?'
    r',\s*(\d{4}[a-z]?)'
)
_CITE_NARRATIVE_RE = re.compile(
    r'([A-ZÀ-Ö][a-zA-ZÀ-ÿ\-\'’]+)'
    r'(?:\s*(?:&|and)\s+[A-ZÀ-Ö][a-zA-ZÀ-ÿ\-\'’]+)?'
    r'(?:\s+et\s+al\.?)?\s+\(\d{4}[a-z]?\)'
)


# ── LLM fallback helpers ────────────────────────────────────────────────────

_LLM_MISMATCH_SYSTEM = "You are a precise academic reference verifier. Return valid JSON only."

_LLM_MISMATCH_SCHEMA = {
    "name": "ref_mismatch_check",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "same_paper": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["same_paper", "reason"],
        "additionalProperties": False,
    },
}

_LLM_CREF_SYSTEM = "You are a precise academic reference verifier. Return valid JSON only."

_LLM_CREF_SCHEMA = {
    "name": "cref_llm_check",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "appears_complete": {"type": "boolean"},
            "issues": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"},
        },
        "required": ["appears_complete", "issues", "reason"],
        "additionalProperties": False,
    },
}


def _cr_item_summary(cr_item: dict) -> str:
    """Format the most identifying fields of a CrossRef record for an LLM prompt."""
    title   = (cr_item.get("title") or [""])[0]
    journal = (cr_item.get("container-title") or [""])[0]
    date    = cr_item.get("issued", {}).get("date-parts", [[]])
    year    = str(date[0][0]) if date and date[0] else ""
    authors = cr_item.get("author", [])
    author_str = ", ".join(
        f"{a.get('family', '')} {a.get('given', '')}".strip()
        for a in authors[:3]
    )
    return f"Title: {title}\nJournal: {journal}\nYear: {year}\nAuthors: {author_str}"


def _llm_resolve_mismatch(ref_text: str, cr_item: dict, mismatches: list[str]) -> dict | None:
    """Ask the LLM whether the CrossRef title/journal confirms the same paper
    despite a year or surname mismatch (CrossRef metadata can be wrong).
    Returns {"same_paper": bool, "reason": str} or None on LLM failure.
    """
    prompt = (
        f"Reference text from document:\n{ref_text}\n\n"
        f"CrossRef record for the DOI:\n{_cr_item_summary(cr_item)}\n\n"
        f"Mismatch detected: {'; '.join(mismatches)}\n\n"
        "CrossRef metadata is sometimes wrong — especially the year (online-first vs print). "
        "Compare the TITLE and JOURNAL NAME to decide if this is the same paper. "
        "Return same_paper: true if confident it is the same work despite the mismatch."
    )
    try:
        result = call_llm_json(_LLM_MISMATCH_SYSTEM, prompt, _LLM_MISMATCH_SCHEMA)
        return result["content"]
    except (LLMError, Exception):
        return None


def _llm_check_reference(ref_text: str, top_cr_result: dict | None) -> dict | None:
    """Use the LLM to assess a reference that CrossRef could not verify.
    Returns {"appears_complete": bool, "issues": [...], "reason": str} or None on failure.
    """
    cr_context = ""
    if top_cr_result:
        score = top_cr_result.get("score", 0)
        cr_context = (
            f"\nClosest CrossRef match (confidence score {score:.0f}/100):\n"
            f"{_cr_item_summary(top_cr_result)}"
        )
    prompt = (
        f"Reference entry:\n{ref_text}"
        f"{cr_context}\n\n"
        "CrossRef could not confidently verify this reference. "
        "Assess: (1) Is this a structurally complete APA 7 reference? "
        "(2) List any specific issues (missing authors, wrong year format, etc.). "
        "Return appears_complete: true only if it looks like a valid, complete reference."
    )
    try:
        result = call_llm_json(_LLM_CREF_SYSTEM, prompt, _LLM_CREF_SCHEMA)
        return result["content"]
    except (LLMError, Exception):
        return None


def _iter_paren_citations(text: str):
    """Yield ``(surname, year)`` tuples for every parenthetical citation.

    Handles single citations ``(Smith, 2020)`` and multi-citation
    parentheses ``(Smith, 2020; Jones, 2021; Doe et al., 2022)``.
    See the module-level comment on the regex pair for the rationale.
    """
    for paren_m in _PAREN_WITH_YEAR_RE.finditer(text):
        for segment in paren_m.group(1).split(';'):
            segment = segment.strip()
            if not segment:
                continue
            inner = _CITE_PAREN_INNER_RE.search(segment)
            if inner is None:
                continue
            yield inner.group(1), inner.group(2)


def _normalise_surname(text: str) -> str:
    """Lowercase, strip accents, punctuation, and possessive 's for fuzzy match.

    Examples:
      "O'Hagan"          -> "ohagan"
      "O’Mathúna"        -> "omathuna"     (curly apostrophe + accent both gone)
      "Kiraly's"         -> "kiraly"       (possessive stripped, not "kiralys")
      "Drugan, J., & Megone" -> "drugan"   (first author only)
    """
    text = re.split(r',|\s+&|\s+and\b|\s+et\b', text)[0].strip()
    # Possessive `'s` and `’s` are NOT part of the surname.
    text = re.sub(r"['’]s$", "", text)
    # Decompose accented characters so ú → u + combining acute, then drop
    # the combining mark. Without this, `[^a-z]` strips the accented letter
    # entirely, mangling Mathúna → mathna.
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", text.lower())


def _extract_body_citations(docx_path: str) -> dict[str, str]:
    """Return {normalised_surname: readable_label} for all in-text citations in the body."""
    paragraphs = load_paragraphs(docx_path)
    # Strip a leading section number so numbered headings ("1. Introduction",
    # "8. References") still bound the body-citation window before the
    # heading-correction pass removes the numbers.
    refs_idx = next(
        (p.index for p in paragraphs
         if p.style == "Heading 1"
         and strip_leading_section_number(p.text).strip().lower() == "references"),
        len(paragraphs),
    )
    intro_idx = next(
        (p.index for p in paragraphs
         if p.style == "Heading 1"
         and strip_leading_section_number(p.text).strip().lower().startswith("introduction")),
        0,
    )
    body = " ".join(
        p.text for p in paragraphs
        if p.index >= intro_idx and p.index < refs_idx and not p.is_empty
    )
    # Convert smart quotes to straight ASCII before regex matching — Word's
    # autocorrect turns ' into ’ and the regex char class only accepted '
    # historically, so `O’Hagan (2020)` previously matched as just `Hagan`.
    body = _normalise_text(body)
    citations: dict[str, str] = {}
    for surname, year in _iter_paren_citations(body):
        key = _normalise_surname(surname)
        if key and key not in citations:
            citations[key] = f"{surname.split(',')[0].strip()} ({year})"
    for m in _CITE_NARRATIVE_RE.finditer(body):
        key = _normalise_surname(m.group(1))
        if key and key not in citations:
            year_m = re.search(r'\d{4}[a-z]?', m.group(0))
            year = year_m.group() if year_m else "n.d."
            citations[key] = f"{m.group(1)} ({year})"
    return citations


def _extract_body_citation_keys(docx_path: str) -> set[str]:
    """Return set of normalised first-author surnames found in body citations."""
    return set(_extract_body_citations(docx_path).keys())


def _extract_ref_author_part(ref: str) -> str:
    """Return the author/group-author portion of a reference entry.

    Slices everything before the first ``(YYYY)`` year token, then strips
    trailing punctuation/whitespace. Handles three reference shapes:

    * Person:    ``Drugan, J., & Megone, C. (2011)…``  -> ``Drugan, J., & Megone, C``
    * Org/group: ``PACTE. (2003)…``                    -> ``PACTE``
    * Org/group: ``European Master's in Translation. (2022)…``
                                                       -> ``European Master's in Translation``

    Splitting on ``,`` alone (the previous behaviour) returned the entire
    reference string for the org cases above, which then got normalised
    into a huge meaningless "surname" that never matched any body
    citation.
    """
    ref = _normalise_text(ref)
    year_m = YEAR_RE.search(ref)
    if year_m is None:
        return ref.strip()
    return ref[: year_m.start()].rstrip(". ").strip()


def _ref_surname_keys(ref: str) -> set[str]:
    """Return every normalised surname-key a reference can plausibly match.

    For person refs, that's just the first-author surname. For multi-word
    organisational refs, we ALSO accept the acronym formed by the
    capitalised initials — so ``European Master's in Translation`` can be
    cited in body text as ``EMT (2022)`` and still be recognised.
    """
    author_part = _extract_ref_author_part(ref)
    keys = set()
    primary = _normalise_surname(author_part)
    if primary:
        keys.add(primary)

    # Organisational author acronym: ``European Master's in Translation``
    # -> ``EMT``. Build by taking the first letter of each uppercase-
    # starting word in the cleaned author_part. Skip when the author_part
    # already looks like a personal name (has a comma — "Surname, F.").
    if "," not in author_part:
        cleaned = re.sub(r"[^A-Za-zÀ-ÿ\s]", " ", author_part)
        initials = [
            w[0].upper()
            for w in cleaned.split()
            if w and w[0].isupper() and len(w) > 1
        ]
        if len(initials) >= 2:
            acronym_key = _normalise_surname("".join(initials))
            if acronym_key:
                keys.add(acronym_key)
    return keys


def check_reference_citations(docx_path: str, refs: list[str]) -> list[dict]:
    """CONS001: Every reference should be cited somewhere in the body text."""
    if not refs:
        return []
    body_keys = _extract_body_citation_keys(docx_path)
    uncited: list[str] = []
    for ref in refs:
        year_m = YEAR_RE.search(ref)
        if not year_m:
            continue
        year = year_m.group().strip('()')[:4]
        surname_raw = _extract_ref_author_part(ref)
        # Show a tight label in the comment — first segment of author_part
        # for person refs, full org name for organisational refs.
        if "," in surname_raw:
            display = surname_raw.split(",")[0].strip()
        else:
            display = surname_raw
        ref_keys = _ref_surname_keys(ref)
        if not ref_keys:
            continue
        if ref_keys.isdisjoint(body_keys):
            uncited.append(f"{display} ({year})")
    if not uncited:
        return [_result("CONS001", "pass", "All references appear to be cited in the text")]
    items = "; ".join(uncited)
    return [_result("CONS001", "warn",
        f"{len(uncited)} reference(s) not found cited in the body text: {items}")]


def check_orphan_citations(docx_path: str, refs: list[str]) -> list[dict]:
    """CONS002: Every in-text citation should appear in the reference list."""
    body_citations = _extract_body_citations(docx_path)
    if not body_citations:
        return []
    ref_keys: set[str] = set()
    for ref in refs:
        ref_keys.update(_ref_surname_keys(ref))
    missing = {k: v for k, v in body_citations.items() if k not in ref_keys}
    if not missing:
        return [_result("CONS002", "pass", "All in-text citations have a corresponding reference list entry")]
    items = "; ".join(sorted(missing.values()))
    return [_result("CONS002", "warn",
        f"{len(missing)} in-text citation(s) have no corresponding reference list entry: {items}")]


def _result(rule_id: str, status: str, message: str) -> dict:
    return {"rule_id": rule_id, "status": status, "message": message}


def _references_window(paragraphs: list) -> tuple[int | None, int]:
    """Return ``(start_index, end_index)`` bounding the References section.

    ``start`` is the document index of the ``References`` / ``Reference List``
    Heading-1; ``end`` (exclusive) is the index of the next Heading-1 after it,
    or ``len(paragraphs)`` if none follows. Returns ``(None, len(paragraphs))``
    when the document has no References heading at all.

    JUTLP requires References to be the LAST section, so the window normally
    runs to the end of the document — but if a paper (incorrectly) places an
    appendix after References, the next Heading-1 closes the window so the
    appendix is excluded from reference checking.
    """
    start = None
    for p in paragraphs:
        # Strip a leading section number so a numbered "8. References" heading is
        # still recognised (the heading-correction pass removes the number only
        # later, in Phase 3).
        heading = strip_leading_section_number(p.text).strip().lower()
        if (
            p.style == "Heading 1"
            and not p.is_empty
            and heading in ("references", "reference list", "bibliography")
        ):
            start = p.index
            break
    if start is None:
        return None, len(paragraphs)

    end = len(paragraphs)
    for p in paragraphs:
        if p.is_empty or p.index <= start:
            continue
        # Close the window at the next Heading-1 OR at an appendix heading
        # detected by text (style-independent) — appendix content that JUTLP
        # doesn't allow is then excluded from reference checking even when its
        # heading isn't styled as a Heading-1.
        if p.style == "Heading 1" or _is_appendix_heading(p.text):
            end = p.index
            break
    return start, end


def _select_reference_entries(window: list) -> list[str]:
    """Two-tier reference selection used by BOTH extraction and comment
    anchoring so entry numbering stays identical.

    Tier 1: paragraphs styled as a reference entry (``REFERENCE_STYLE``).
    Tier 2 (only if Tier 1 is empty): year+length heuristic — a non-empty
    paragraph containing a ``(YYYY)`` token and longer than 20 chars.
    """
    styled = [p.text for p in window if p.style == REFERENCE_STYLE and not p.is_empty]
    if styled:
        return styled
    return [
        p.text for p in window
        if not p.is_empty and YEAR_RE.search(p.text) and len(p.text) > 20
    ]


def extract_references(docx_path: str) -> list[str]:
    paragraphs = load_paragraphs(docx_path)
    start, end = _references_window(paragraphs)

    if start is not None:
        # Bound strictly to the References section: only paragraphs after the
        # References heading and before the next Heading-1. Appendix content
        # (which JUTLP doesn't allow but some papers include) is excluded.
        window = [p for p in paragraphs if start < p.index < end]
        return _select_reference_entries(window)

    # No References heading anywhere → preserve the historical doc-wide style
    # collection so papers with reference entries but a missing/mis-styled
    # heading don't regress.
    return [p.text for p in paragraphs if p.style == REFERENCE_STYLE and not p.is_empty]


def check_references_section(docx_path: str) -> list[dict]:
    paragraphs = load_paragraphs(docx_path)
    sections = extract_main_sections(paragraphs)
    refs = extract_references(docx_path)
    results = []

    if "References" in sections:
        results.append(_result("REF001", "pass", "References section found"))
    else:
        results.append(_result("REF001", "fail", "References section not found"))

    if refs:
        results.append(_result("REF002", "pass", f"{len(refs)} reference entry/entries found"))
    else:
        results.append(_result("REF002", "fail", "No reference entries found — expected style 'APA 7 Reference List Entry'"))

    return results


def _fingerprint_ref(ref: str) -> str:
    """Collapse a reference to a normalised fingerprint for duplicate detection."""
    text = _normalise_text(ref).lower()
    text = re.sub(r'[^a-z0-9]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def check_duplicate_references(refs: list[str]) -> list[dict]:
    """REF004: Flag reference entries that appear more than once."""
    if len(refs) < 2:
        return [_result("REF004", "pass", "No duplicate references detected")]

    # Group entry numbers by normalised text fingerprint
    fp_groups: dict[str, list[int]] = {}
    for i, ref in enumerate(refs, start=1):
        fp_groups.setdefault(_fingerprint_ref(ref), []).append(i)

    # Also group by DOI — catches the same paper formatted differently
    doi_groups: dict[str, list[int]] = {}
    for i, ref in enumerate(refs, start=1):
        doi_m = _DOI_IN_URL.search(ref)
        if doi_m:
            doi = doi_m.group(0).rstrip(".,;:)").lower()
            doi_groups.setdefault(doi, []).append(i)

    seen: set[frozenset] = set()
    duplicates: list[str] = []
    for entries in [*fp_groups.values(), *doi_groups.values()]:
        if len(entries) < 2:
            continue
        key = frozenset(entries)
        if key in seen:
            continue
        seen.add(key)
        labels = ", ".join(f"Entry {n}" for n in sorted(entries))
        duplicates.append(f"{labels}: {refs[entries[0] - 1][:70]}")

    if not duplicates:
        return [_result("REF004", "pass", "No duplicate references detected")]
    items = "; ".join(duplicates)
    return [_result("REF004", "warn",
        f"{len(duplicates)} duplicate reference(s) detected: {items}")]



def check_entry_year(entry_num: int, ref: str) -> dict:
    rule_id = f"REFE{entry_num:03d}_YEAR"
    if YEAR_RE.search(ref):
        return _result(rule_id, "pass", f"Entry {entry_num}: year found")
    return _result(rule_id, "fail", f"Entry {entry_num}: missing year in parentheses — {ref[:80]}")


def check_entry_author(entry_num: int, ref: str) -> dict:
    rule_id = f"REFE{entry_num:03d}_AUTH"
    if AUTHOR_RE.match(ref):
        return _result(rule_id, "pass", f"Entry {entry_num}: author format OK")
    return _result(rule_id, "warn", f"Entry {entry_num}: author format may not follow APA 7 (Surname, F.) — {ref[:80]}")


def _query_crossref(reference_text: str) -> dict | None:
    cache_key = f"search:{reference_text}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached if cached != "__none__" else None
    try:
        resp = requests.get(
            CROSSREF_API,
            params={"query": reference_text, "rows": 1},
            headers=CROSSREF_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("message", {}).get("items", [])
        result = items[0] if items else None
    except requests.RequestException:
        result = None
    _cache_set(cache_key, result if result is not None else "__none__")
    return result


_APA_CN_HEADERS = {
    "User-Agent": CROSSREF_HEADERS["User-Agent"],
    "Accept": "text/x-bibliography; style=apa",
}


def _get_apa_via_content_negotiation(doi: str) -> str | None:
    """Return the CrossRef-formatted APA 7 string for a DOI, or None on failure."""
    cache_key = f"cn:{doi}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached if cached != "__none__" else None
    try:
        resp = requests.get(
            f"https://doi.org/{doi}",
            headers=_APA_CN_HEADERS,
            timeout=10,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            _cache_set(cache_key, "__none__")
            return None
        # CrossRef CN responses are UTF-8 but the Content-Type header often
        # omits the charset, causing requests to default to ISO-8859-1 and
        # mangle non-ASCII characters (en-dashes → â + garbage bytes).
        text = resp.content.decode('utf-8', errors='replace').strip()
        # CrossRef CN output sometimes contains HTML entities; decode them.
        text = html.unescape(text)
        # Ensure a space separates the trailing period from the URL.
        text = re.sub(r'\.(\s*)(https?://)', r'. \2', text)
        _cache_set(cache_key, text)
        return text
    except requests.RequestException:
        _cache_set(cache_key, "__none__")
        return None


_YEAR_IN_REF = re.compile(r'\((\d{4})[a-z]?\)')


def _rough_similarity(a: str, b: str) -> float:
    """Character-level similarity after aggressive normalisation (lowercase, strip non-alnum)."""
    def _norm(t: str) -> str:
        t = re.sub(r'[^a-z0-9]', ' ', t.lower())
        return re.sub(r'\s+', ' ', t).strip()
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def _verify_with_doi(
    rule_id: str,
    entry_num: int,
    ref: str,
    doi: str,
    doi_from_text: bool = True,
) -> dict:
    """Verify a reference using CrossRef content negotiation for the given DOI.

    Returns a CREF result dict.  Sets 'reconstructed' + 'format_issues' when
    the content-negotiated APA 7 string differs enough from the submitted ref
    to warrant a tracked change.

    doi_from_text: True  → the DOI was written in the reference by the author.
                           Year-mismatch warnings are appropriate (author's DOI
                           may be wrong).
                  False  → the DOI came from a CrossRef search result.
                           Year mismatches just mean the search found the wrong
                           edition; return None so the caller can fall through
                           to the LLM check instead of generating a confusing
                           warning about a DOI the author never wrote.
    """
    apa = _get_apa_via_content_negotiation(doi)
    doi_url = f"https://doi.org/{doi}"

    if apa is None:
        return _result(rule_id, "fail",
            f"Entry {entry_num}: DOI not found in CrossRef ({doi})")

    # ── Sanity-check the APA output before trusting it ────────────────────────
    # CrossRef CN occasionally returns garbled output (leading comma, empty
    # author slot like "& .") — reject these immediately.
    if not apa or not apa[0].isalpha() or re.search(r',\s*&\s*\.\s', apa):
        return _result(rule_id, "warn",
            f"Entry {entry_num}: CrossRef returned malformed APA output — "
            f"please verify the DOI manually ({doi})")

    # ── Year-mismatch guard ────────────────────────────────────────────────────
    # A DOI that resolves to a completely different year indicates the author's
    # DOI points to the wrong publication (common with JSTOR reprints and
    # chapter DOIs that get reassigned). Flag as warn rather than applying a
    # potentially wrong tracked change.
    year_ref_m = _YEAR_IN_REF.search(ref)
    year_apa_m = _YEAR_IN_REF.search(apa)
    if year_ref_m and year_apa_m:
        year_diff = abs(int(year_ref_m.group(1)) - int(year_apa_m.group(1)))
        if year_diff >= 2:
            if not doi_from_text:
                # DOI came from a search result, not the author — a year
                # mismatch just means the search found the wrong edition.
                # Return None so the caller falls through to the LLM check.
                return None  # type: ignore[return-value]
            return _result(rule_id, "warn",
                f"Entry {entry_num}: CrossRef returned a different year "
                f"({year_ref_m.group(1)} in reference vs {year_apa_m.group(1)} from DOI) "
                f"— DOI may point to a different edition or publication; please verify")

    r = _result(rule_id, "pass", f"Entry {entry_num}: verified")
    r["doi_url"] = doi_url

    # Compare without the DOI URL: the author's reference typically has no DOI,
    # so its absence should not be treated as a content difference.  We still
    # apply the full APA string (with DOI) as the correction if needed.
    apa_no_url = _URL_STRIP_RE.sub("", apa).strip().rstrip(".")
    if not references_are_equivalent(ref, apa_no_url):
        sim = _rough_similarity(ref, apa_no_url)
        if sim >= 0.70:
            # Same paper, formatting differs — apply correction with full APA (incl. DOI).
            r["reconstructed"] = apa
            r["format_issues"] = ["apa7-correction"]
        else:
            # Low similarity even without the URL: DOI likely resolves to a different work.
            # Flag for manual review rather than replacing the reference.
            r["status"] = "warn"
            r["message"] = (
                f"Entry {entry_num}: DOI may not match this reference "
                f"(CrossRef returned different content) — please verify the DOI is correct"
            )

    return r


def verify_reference(entry_num: int, ref: str) -> dict:
    rule_id = f"CREF{entry_num:03d}"

    # ── Fast path: reference already contains a DOI URL ──────────────────────
    # Skip the CrossRef search and go straight to content negotiation.
    doi_m = _DOI_IN_URL.search(ref)
    if doi_m:
        doi = doi_m.group(0).rstrip(".,;:)")
        result = _verify_with_doi(rule_id, entry_num, ref, doi)
        if result["status"] != "fail":
            return result
        # Content negotiation failed for the submitted DOI — fall through to
        # a search-based attempt in case the DOI in the text is malformed.

    # ── Search path: no DOI in text, or content negotiation above failed ─────
    match = _query_crossref(ref)

    doi_hint = ""
    if doi_m:
        doi_raw = doi_m.group(0).rstrip(".,;:)")
        doi_hint = f" — please check https://doi.org/{doi_raw}"

    score     = match.get("score", 0) if match else 0
    found_doi = (match.get("DOI", "") or "") if match else ""

    if match is not None and score >= SCORE_THRESHOLD and found_doi:
        # Use the DOI CrossRef returned for content negotiation so we get
        # a properly formatted APA 7 string without manual reconstruction.
        # doi_from_text=False: this DOI came from the search result, not the
        # author. If _verify_with_doi detects a year mismatch it returns None
        # (the search found the wrong edition) and we fall through to LLM.
        result = _verify_with_doi(rule_id, entry_num, ref, found_doi, doi_from_text=False)
        if result is not None:
            return result
        # Year mismatch from a search DOI → bad search result, fall through.

    if match is not None and score >= SCORE_THRESHOLD:
        # CrossRef verified the paper but didn't return a DOI — just pass.
        return _result(rule_id, "pass", f"Entry {entry_num}: verified in CrossRef")

    # CrossRef couldn't verify — ask the LLM for a second opinion
    llm = _llm_check_reference(ref, match)
    if llm is not None:
        if llm.get("appears_complete"):
            return _result(rule_id, "warn",
                f"Entry {entry_num}: not found in CrossRef but reference appears complete — "
                f"{llm.get('reason', '')}: {ref[:80]}{doi_hint}")
        issues_str = "; ".join(llm.get("issues", [])) or llm.get("reason", "")
        return _result(rule_id, "fail",
            f"Entry {entry_num}: could not verify — {issues_str}: {ref[:80]}{doi_hint}")

    return _result(rule_id, "fail",
        f"Entry {entry_num}: could not verify — reference may not exist: {ref[:80]}{doi_hint}")


def check_references(docx_path: str, delay: float = 0.5) -> list[dict]:
    results = []
    results += check_references_section(docx_path)

    refs = extract_references(docx_path)
    if not refs:
        return results

    results += check_duplicate_references(refs)
    results += check_reference_citations(docx_path, refs)
    results += check_orphan_citations(docx_path, refs)

    for i, ref in enumerate(refs, start=1):
        results.append(check_entry_year(i, ref))
        results.append(check_entry_author(i, ref))
        results.extend(check_reference_type_style(i, ref))
        results.append(verify_reference(i, ref))
        if i < len(refs):
            time.sleep(delay)

    return results


def build_reference_report(results: list[dict]) -> dict:
    return {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "warn": sum(1 for r in results if r["status"] == "warn"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
        "results": results,
    }


def _extract_ref_hyperlinks(docx_path: str) -> list[tuple[int, str, str]]:
    """Return (entry_num, ref_text, url) for reference entries that already have a hyperlink."""
    with zipfile.ZipFile(docx_path, "r") as z:
        doc_xml  = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")

    rels_root = etree.fromstring(rels_xml)
    rid_to_url: dict[str, str] = {
        rel.get("Id", ""): rel.get("Target", "")
        for rel in rels_root
        if rel.get("Type") == _HL_TYPE
    }

    doc_root = etree.fromstring(doc_xml)
    results: list[tuple[int, str, str]] = []
    entry_num = 0
    in_refs = False

    for para_el in doc_root.iter(f"{_WQ}p"):
        pPr   = para_el.find(f"{_WQ}pPr")
        style = ""
        if pPr is not None:
            ps = pPr.find(f"{_WQ}pStyle")
            if ps is not None:
                style = ps.get(f"{_WQ}val", "")

        text = "".join(t.text or "" for t in para_el.iter(f"{_WQ}t")).strip()

        if style in ("Heading 1", "Heading1") and text.lower() in ("references", "reference list"):
            in_refs = True
            continue
        if in_refs and (style in ("Heading 1", "Heading1") or _is_appendix_heading(text)):
            break

        is_ref = style in _REF_STYLES or (
            in_refs and len(text) > 20 and bool(YEAR_RE.search(text))
        )
        if not is_ref or not text:
            continue

        entry_num += 1
        for hl_el in para_el.iter(f"{_WQ}hyperlink"):
            rid = hl_el.get(f"{_R_NS_Q}id", "")
            url = rid_to_url.get(rid, "")
            if url:
                results.append((entry_num, text, url))
                break

    return results


def _lookup_doi(doi: str) -> dict | None:
    """Query CrossRef by DOI and return the work item, or None on failure."""
    try:
        resp = requests.get(
            f"{CROSSREF_API}/{doi}",
            headers=CROSSREF_HEADERS,
            timeout=10,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json().get("message", {})
    except requests.RequestException:
        return None


def check_submitted_hyperlinks(docx_path: str, delay: float = 0.5) -> list[dict]:
    """HREF: Verify that user-submitted hyperlinks point to the cited work.

    For each reference entry that already contains a Word hyperlink:
    - Extracts the DOI from the URL if present
    - Looks it up directly on CrossRef by DOI
    - Checks the author surname and year match the reference text
    """
    entries = _extract_ref_hyperlinks(docx_path)
    if not entries:
        return []

    results = []
    for i, (entry_num, ref_text, url) in enumerate(entries):
        rule_id = f"HREF{entry_num:03d}"

        doi_m = _DOI_IN_URL.search(url)
        if not doi_m:
            results.append(_result(
                rule_id, "warn",
                f"Entry {entry_num}: submitted URL has no DOI — cannot verify: {url[:80]}"
            ))
        else:
            doi = doi_m.group(0).rstrip(".,;:)")
            cr_item = _lookup_doi(doi)

            if cr_item is None:
                results.append(_result(
                    rule_id, "fail",
                    f"Entry {entry_num}: DOI from submitted URL not found in CrossRef ({doi})"
                ))
            else:
                date_parts = cr_item.get("issued", {}).get("date-parts", [[]])
                cr_year    = str(date_parts[0][0]) if date_parts and date_parts[0] else ""
                authors    = cr_item.get("author", [])
                cr_surname = _normalise_surname(authors[0].get("family", "")) if authors else ""

                year_m     = YEAR_RE.search(ref_text)
                ref_year   = year_m.group().strip("()") if year_m else ""
                ref_surname = _normalise_surname(ref_text.split(",")[0].strip())

                year_ok    = not ref_year or not cr_year or ref_year == cr_year
                surname_ok = not ref_surname or not cr_surname or ref_surname == cr_surname

                if year_ok and surname_ok:
                    results.append(_result(
                        rule_id, "pass",
                        f"Entry {entry_num}: submitted URL verified — DOI matches reference"
                    ))
                else:
                    mismatches = []
                    if not year_ok:
                        mismatches.append(f"year in reference: {ref_year}, year at URL: {cr_year}")
                    if not surname_ok:
                        mismatches.append(f"author in reference: '{ref_surname}', author at URL: '{cr_surname}'")

                    # CrossRef metadata can be wrong — use LLM to compare titles
                    llm = _llm_resolve_mismatch(ref_text, cr_item, mismatches)
                    if llm is not None and llm.get("same_paper"):
                        results.append(_result(
                            rule_id, "warn",
                            f"Entry {entry_num}: minor mismatch but LLM confirms same paper "
                            f"({'; '.join(mismatches)}) — {llm.get('reason', '')}: {url[:80]}"
                        ))
                    else:
                        results.append(_result(
                            rule_id, "fail",
                            f"Entry {entry_num}: submitted URL may point to wrong paper — "
                            f"{'; '.join(mismatches)}: {url[:80]}"
                        ))

        if i < len(entries) - 1:
            time.sleep(delay)

    return results


def check_text_dois(refs: list[str], delay: float = 0.5) -> list[dict]:
    """DOIT: Validate every DOI-shaped substring found in the plain text
    of each reference, regardless of whether it is hyperlinked.

    Pairs with ``check_submitted_hyperlinks`` (HREF***): the hyperlink
    path catches DOIs the author typed AND made clickable; this path
    catches plain-text DOIs (``doi:10.xxxx/...``, raw ``10.xxxx/...``,
    or ``https://doi.org/10.xxxx/...`` left as plain text). Between the
    two passes every DOI in the bibliography gets a CrossRef round-trip.

    A reference with no DOI-shaped substring emits no row — older works
    legitimately lack DOIs and nagging on each one would flood the panel.
    """
    results: list[dict] = []
    lookups_total = 0

    for entry_num, ref in enumerate(refs, start=1):
        seen: set[str] = set()
        ordered: list[str] = []
        for raw in _DOI_IN_URL.findall(ref):
            doi = raw.rstrip(".,;:)\"'")
            if doi in seen:
                continue
            seen.add(doi)
            ordered.append(doi)

        if not ordered:
            continue

        multi = len(ordered) > 1
        for idx, doi in enumerate(ordered, start=1):
            rule_id = (
                f"DOIT{entry_num:03d}_{idx}" if multi
                else f"DOIT{entry_num:03d}"
            )
            if lookups_total > 0:
                time.sleep(delay)
            lookups_total += 1

            cr_item = _lookup_doi(doi)
            if cr_item is None:
                results.append(_result(
                    rule_id, "fail",
                    f"Entry {entry_num}: DOI not found in CrossRef ({doi})"
                ))
                continue

            date_parts = cr_item.get("issued", {}).get("date-parts", [[]])
            cr_year    = str(date_parts[0][0]) if date_parts and date_parts[0] else ""
            authors    = cr_item.get("author", [])
            cr_surname = _normalise_surname(authors[0].get("family", "")) if authors else ""

            year_m     = YEAR_RE.search(ref)
            ref_year   = year_m.group().strip("()") if year_m else ""
            ref_surname = _normalise_surname(ref.split(",")[0].strip())

            year_ok    = not ref_year or not cr_year or ref_year == cr_year
            surname_ok = not ref_surname or not cr_surname or ref_surname == cr_surname

            if year_ok and surname_ok:
                results.append(_result(
                    rule_id, "pass",
                    f"Entry {entry_num}: DOI verified ({doi})"
                ))
                continue

            mismatches = []
            if not year_ok:
                mismatches.append(f"year in reference: {ref_year}, year at DOI: {cr_year}")
            if not surname_ok:
                mismatches.append(
                    f"author in reference: '{ref_surname}', author at DOI: '{cr_surname}'"
                )

            # CrossRef metadata can be wrong — use LLM to compare titles
            llm = _llm_resolve_mismatch(ref, cr_item, mismatches)
            if llm is not None and llm.get("same_paper"):
                results.append(_result(
                    rule_id, "warn",
                    f"Entry {entry_num}: minor mismatch but LLM confirms same paper "
                    f"({'; '.join(mismatches)}) — {llm.get('reason', '')}: {doi}"
                ))
            else:
                results.append(_result(
                    rule_id, "fail",
                    f"Entry {entry_num}: DOI may point to wrong paper ({doi}) — "
                    f"{'; '.join(mismatches)}"
                ))

    return results


def check_and_report(docx_path: str) -> dict:
    return build_reference_report(check_references(docx_path))


if __name__ == "__main__":
    import sys
    from pprint import pprint

    path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "tests/jutlp_sample_docx_test_pack/01_valid_identified.docx"
    )
    pprint(check_and_report(path))
