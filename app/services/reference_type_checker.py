"""APA 7 reference type classification and type-specific style checking."""

import re

# ── Shared helpers (defined locally to avoid circular imports) ────────────────

_SMART_QUOTE_MAP = str.maketrans({
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
    "′": "'",
})

def _normalise(text: str) -> str:
    return (text or "").translate(_SMART_QUOTE_MAP)

def _result(rule_id: str, status: str, message: str) -> dict:
    return {"rule_id": rule_id, "status": status, "message": message}

_YEAR_RE    = re.compile(r'\(\d{4}[a-z]?\)')
_DOI_RE     = re.compile(r'10\.\d{4,9}/[^\s,;>"\']+')
_DOI_URL_RE = re.compile(r'https?://doi\.org/10\.\d{4,9}/', re.IGNORECASE)

# ── Structural patterns ───────────────────────────────────────────────────────

# ", 12(3)" — volume(issue)
_VOL_ISSUE = re.compile(r',\s*\d+\s*\(\d+\)')
# ", 12, 45–67" — volume + page range (no issue number)
_VOL_PAGE  = re.compile(r',\s*\d{1,4},\s*\d+\s*[-–—]\s*\d+')
# Traditional page range e.g. 45–67 (matches hyphen, en dash, em dash)
_PAGE_RANGE = re.compile(r'\b\d+\s*[-–—]\s*\d+\b')
# Single article number directly after vol(issue) — catches JUTLP/open-access
# style like "18(4), 10", "21(09), 01", or "18(4), e65" (issue 1–3 digits to
# avoid matching years; IGNORECASE for lowercase letter prefixes like 'e')
_POST_ISSUE_ID = re.compile(r'\(\d{1,3}\),\s*[A-Z]?\d{1,6}(?=[.,\s]|$)', re.IGNORECASE)
# "pp. NNN" or "pp. NNN–NNN"; also "p. NNN" (singular) for single-page refs
_PP_PAGES   = re.compile(r'\bpp?\.\s*\d+')
# "In A. Editor" — book chapter opener
_IN_EDITOR  = re.compile(r'\bIn\s+[A-ZÀ-Ö]')
# "(Ed.)" or "(Eds.)"
_EDITOR_CREDIT = re.compile(r'\(Eds?\.?\)')
# "Proceedings" — conference
_PROCEEDINGS = re.compile(r'\bProceedings\b', re.IGNORECASE)
# Report/publication number
_REPORT_NO  = re.compile(
    r'\((?:Report\s+No\.?|Technical\s+Report|Publication\s+No\.?|No\.)\s*[\w\-]+\)',
    re.IGNORECASE,
)
# Any URL
_URL        = re.compile(r'https?://')
# Date with month "(2024, March" — websites often include the retrieval date
_DATED_MONTH = re.compile(r'\(\d{4},\s+[A-Z][a-z]+')
# Article/entry number used by some journals instead of pages
# Covers: "Article 10", "e20231", "[A-Z]\d{1,5}" (e.g. "A4"), and "e\d{4,}"
_ARTICLE_NUM = re.compile(r'\b(?:Article\s+\d+|e\d{4,}|[A-Z]\d{1,5})\b', re.IGNORECASE)
# n.d. — no date
_ND          = re.compile(r'\(n\.d\.?\)')

# ── APA 7 format templates — shown in warning messages to guide authors ───────

_APA7_FORMAT = {
    "journal":      (
        "Author, A. A., & Author, B. B. (Year). Title of article. "
        "Journal Name, Volume(Issue), pp. X–Y. https://doi.org/..."
    ),
    "book":         (
        "Author, A. A. (Year). Title of book. Publisher."
    ),
    "book_chapter": (
        "Author, A. A. (Year). Chapter title. "
        "In E. Editor (Ed.), Book title (pp. X–Y). Publisher."
    ),
    "website":      (
        "Author, A. A. (Year, Month Day). Title. Site Name. URL"
    ),
    "video":        (
        "Creator, A. A. (Year). Title [Video]. Platform. URL"
    ),
    "dataset":      (
        "Author, A. A. (Year). Title [Data set]. Publisher. https://doi.org/..."
    ),
    "thesis":       (
        "Author, A. A. (Year). Title [Doctoral dissertation, University Name]. "
        "https://doi.org/..."
    ),
    "report":       (
        "Author, A. A. (Year). Title (Report No. X). Publisher."
    ),
    "conference":   (
        "Author, A. A. (Year). Title. "
        "In Proceedings of Conference Name (pp. X–Y). Publisher."
    ),
    "software":     (
        "Author, A. A. (Year). Title (Version X) [Software]. Publisher/URL"
    ),
    "podcast":      (
        "Host, A. A. (Year, Month Day). Episode title [Podcast episode]. "
        "In Show Name. URL"
    ),
}

# ── Explicit bracket-label → type map (checked first, highest priority) ──────

_BRACKET_TYPES: list[tuple[str, str]] = [
    (r'\[Video\b',                                        "video"),
    (r'\[Film\b',                                         "video"),
    (r'\[TV\s+series',                                    "video"),
    (r'\[Streaming\s+video',                              "video"),
    (r'\[Data\s*set\]',                                   "dataset"),
    (r'\[Dataset\]',                                      "dataset"),
    (r'\[Doctoral\s+dissertation',                        "thesis"),
    (r'\[PhD\s+dissertation',                             "thesis"),
    (r'\[Master.s\s+thesis',                              "thesis"),
    (r'\[Unpublished\s+(?:doctoral|master|manuscript)',   "thesis"),
    (r'\[Software\]',                                     "software"),
    (r'\[Computer\s+software\]',                          "software"),
    (r'\[Mobile\s+app\]',                                 "software"),
    (r'\[Podcast\b',                                      "podcast"),
    (r'\[Blog\s+post\]',                                  "website"),
    (r'\[Infographic\]',                                  "website"),
]

# ── Type labels for display ───────────────────────────────────────────────────

TYPE_LABELS: dict[str, str] = {
    "journal":      "Journal article",
    "book":         "Book",
    "book_chapter": "Book chapter",
    "website":      "Webpage/website",
    "video":        "Streaming video",
    "dataset":      "Dataset",
    "thesis":       "Thesis/dissertation",
    "report":       "Report",
    "conference":   "Conference paper",
    "software":     "Software",
    "podcast":      "Podcast",
    "other":        "Unknown/other",
}


# ── Classifier ────────────────────────────────────────────────────────────────

def classify_reference(ref: str) -> str:
    """Return the APA 7 reference type for a single reference entry.

    Priority order: explicit bracket labels → structural patterns → fallback.
    Possible return values match the keys of TYPE_LABELS.
    """
    text = _normalise(ref)

    # 1. Bracket labels are unambiguous — check first
    for pattern, ref_type in _BRACKET_TYPES:
        if re.search(pattern, text, re.IGNORECASE):
            return ref_type

    # 2. Thesis/dissertation catch-all (bracket present but not matched above)
    if re.search(r'\[(?:Doctoral|PhD|Master|Unpublished)', text, re.IGNORECASE):
        return "thesis"

    # 3. Book chapter: "In X. Editor (Ed.)" + "pp."
    if _IN_EDITOR.search(text) and _EDITOR_CREDIT.search(text) and _PP_PAGES.search(text):
        return "book_chapter"

    # 4. Conference proceedings
    if _PROCEEDINGS.search(text):
        return "conference"

    # Compute URL flags early — needed by both the journal and website checks.
    has_url     = bool(_URL.search(text))
    has_doi_url = bool(_DOI_URL_RE.search(text))
    plain_url   = has_url and not has_doi_url  # non-DOI URL → website signal

    # 5. Journal article: volume(issue) or volume + page range.
    # Require no plain URL: a reference with a non-DOI URL is a website even if
    # it happens to contain a vol(issue)-like pattern in the title or URL path.
    if not plain_url and (_VOL_ISSUE.search(text) or _VOL_PAGE.search(text)):
        return "journal"

    # 6. Report: explicit report/publication number
    if _REPORT_NO.search(text):
        return "report"

    # 7. Website: non-DOI URL, or date that includes a month
    if plain_url or (_DATED_MONTH.search(text) and not _VOL_ISSUE.search(text)):
        return "website"

    # 8. Book: no journal markers, no URL → assume monograph
    if not _VOL_ISSUE.search(text) and not has_url:
        return "book"

    return "other"


# ── Type-specific style checkers ──────────────────────────────────────────────

def _check_journal(n: int, ref: str) -> list[dict]:
    pid = f"REFE{n:03d}_JRNL"
    tip = _APA7_FORMAT["journal"]
    results = []

    # Volume/issue — distinguish "has both", "volume only", and "neither"
    if _VOL_ISSUE.search(ref):
        results.append(_result(f"{pid}_VOL", "pass",
            f"Entry {n} [Journal article]: volume and issue number present"))
    elif _VOL_PAGE.search(ref):
        results.append(_result(f"{pid}_VOL", "warn",
            f"Entry {n} [Journal article]: volume number found but issue number appears to be missing — "
            f"add the issue number in parentheses after the volume if the journal uses one. "
            f"APA 7 format: {tip}"))
    else:
        results.append(_result(f"{pid}_VOL", "warn",
            f"Entry {n} [Journal article]: volume and issue number appear to be missing. "
            f"APA 7 format: {tip}"))

    # Page range or article number — accepts range (101–114), single ID after
    # vol(issue) like JUTLP-style "18(4), 10", explicit article labels, pp.,
    # or a DOI (DOI-only pagination is valid APA 7 for online-first journals).
    has_pages = (
        _PAGE_RANGE.search(ref)
        or _ARTICLE_NUM.search(ref)
        or _POST_ISSUE_ID.search(ref)
        or _PP_PAGES.search(ref)
        or _DOI_RE.search(ref)
    )
    if has_pages:
        results.append(_result(f"{pid}_PG", "pass",
            f"Entry {n} [Journal article]: page range or article number present"))
    else:
        results.append(_result(f"{pid}_PG", "warn",
            f"Entry {n} [Journal article]: page range or article number appears to be missing. "
            f"APA 7 format: {tip}"))

    if _DOI_RE.search(ref):
        results.append(_result(f"{pid}_DOI", "pass",
            f"Entry {n} [Journal article]: DOI present"))
    else:
        results.append(_result(f"{pid}_DOI", "warn",
            f"Entry {n} [Journal article]: no DOI found — include the DOI if one is available (APA 7). "
            f"APA 7 format: {tip}"))

    return results


def _check_book(n: int, ref: str) -> list[dict]:
    pid = f"REFE{n:03d}_BOOK"
    tip = _APA7_FORMAT["book"]
    if _VOL_ISSUE.search(ref):
        return [_result(f"{pid}_FMT", "warn",
            f"Entry {n} [Book]: reference contains a volume/issue pattern — "
            f"verify this is not a journal article. "
            f"APA 7 book format: {tip}")]
    return [_result(f"{pid}_FMT", "pass",
        f"Entry {n} [Book]: structure appears consistent with APA 7 book format")]


def _check_book_chapter(n: int, ref: str) -> list[dict]:
    pid = f"REFE{n:03d}_CHAP"
    tip = _APA7_FORMAT["book_chapter"]
    results = []

    if _IN_EDITOR.search(ref):
        results.append(_result(f"{pid}_IN", "pass",
            f"Entry {n} [Book chapter]: 'In [Editor]' attribution present"))
    else:
        results.append(_result(f"{pid}_IN", "warn",
            f"Entry {n} [Book chapter]: missing 'In [Editor name]' attribution. "
            f"APA 7 format: {tip}"))

    if _EDITOR_CREDIT.search(ref):
        results.append(_result(f"{pid}_EDLBL", "pass",
            f"Entry {n} [Book chapter]: (Ed.)/(Eds.) label present"))
    else:
        results.append(_result(f"{pid}_EDLBL", "warn",
            f"Entry {n} [Book chapter]: missing (Ed.) or (Eds.) label after editor name. "
            f"APA 7 format: {tip}"))

    if _PP_PAGES.search(ref):
        results.append(_result(f"{pid}_PP", "pass",
            f"Entry {n} [Book chapter]: page range (pp.) present"))
    else:
        results.append(_result(f"{pid}_PP", "warn",
            f"Entry {n} [Book chapter]: missing page range — use 'pp. XX–XX' format. "
            f"APA 7 format: {tip}"))

    return results


def _check_website(n: int, ref: str) -> list[dict]:
    pid = f"REFE{n:03d}_WEB"
    tip = _APA7_FORMAT["website"]
    results = []

    if _URL.search(ref):
        results.append(_result(f"{pid}_URL", "pass",
            f"Entry {n} [Webpage/website]: URL present"))
    else:
        results.append(_result(f"{pid}_URL", "fail",
            f"Entry {n} [Webpage/website]: a URL is required for website references (APA 7). "
            f"APA 7 format: {tip}"))

    if not _YEAR_RE.search(ref) and not _ND.search(ref):
        results.append(_result(f"{pid}_DATE", "warn",
            f"Entry {n} [Webpage/website]: no date found — "
            f"use (n.d.) if no publication date is available (APA 7). "
            f"APA 7 format: {tip}"))

    return results


def _check_video(n: int, ref: str) -> list[dict]:
    pid = f"REFE{n:03d}_VID"
    tip = _APA7_FORMAT["video"]
    results = []

    if re.search(r'\[(?:Video|Film|TV\s+series|Streaming\s+video)\]', ref, re.IGNORECASE):
        results.append(_result(f"{pid}_LBL", "pass",
            f"Entry {n} [Streaming video]: [Video] label present"))
    else:
        results.append(_result(f"{pid}_LBL", "warn",
            f"Entry {n} [Streaming video]: missing [Video] label after the title. "
            f"APA 7 format: {tip}"))

    if _URL.search(ref):
        results.append(_result(f"{pid}_URL", "pass",
            f"Entry {n} [Streaming video]: URL present"))
    else:
        results.append(_result(f"{pid}_URL", "fail",
            f"Entry {n} [Streaming video]: a URL is required for video references (APA 7). "
            f"APA 7 format: {tip}"))

    return results


def _check_dataset(n: int, ref: str) -> list[dict]:
    pid = f"REFE{n:03d}_DATA"
    tip = _APA7_FORMAT["dataset"]
    results = []

    if re.search(r'\[Data\s*set\]', ref, re.IGNORECASE):
        results.append(_result(f"{pid}_LBL", "pass",
            f"Entry {n} [Dataset]: [Data set] label present"))
    else:
        results.append(_result(f"{pid}_LBL", "warn",
            f"Entry {n} [Dataset]: missing [Data set] label after the title. "
            f"APA 7 format: {tip}"))

    if _DOI_RE.search(ref):
        results.append(_result(f"{pid}_DOI", "pass",
            f"Entry {n} [Dataset]: DOI present"))
    else:
        results.append(_result(f"{pid}_DOI", "warn",
            f"Entry {n} [Dataset]: no DOI found — include if available (APA 7). "
            f"APA 7 format: {tip}"))

    return results


def _check_thesis(n: int, ref: str) -> list[dict]:
    pid = f"REFE{n:03d}_THES"
    tip = _APA7_FORMAT["thesis"]
    results = []

    bracket_m = re.search(
        r'\[(?:Doctoral\s+dissertation|Master.s\s+thesis|PhD\s+dissertation|Unpublished[^\]]*)[^\]]*\]',
        ref, re.IGNORECASE,
    )
    if not bracket_m:
        results.append(_result(f"{pid}_LBL", "warn",
            f"Entry {n} [Thesis/dissertation]: missing type label — "
            f"add [Doctoral dissertation, Institution Name] or [Master's thesis, Institution Name] "
            f"after the title. APA 7 format: {tip}"))
    else:
        bracket_text = bracket_m.group(0)
        if "," in bracket_text:
            results.append(_result(f"{pid}_LBL", "pass",
                f"Entry {n} [Thesis/dissertation]: label with institution present"))
        else:
            results.append(_result(f"{pid}_INST", "warn",
                f"Entry {n} [Thesis/dissertation]: label is missing the institution name — "
                f"add it after a comma, e.g. [Doctoral dissertation, University Name]. "
                f"APA 7 format: {tip}"))

    return results


def _check_report(n: int, ref: str) -> list[dict]:
    pid = f"REFE{n:03d}_REP"
    tip = _APA7_FORMAT["report"]
    if _REPORT_NO.search(ref):
        return [_result(f"{pid}_NO", "pass",
            f"Entry {n} [Report]: report/publication number present")]
    return [_result(f"{pid}_NO", "warn",
        f"Entry {n} [Report]: report/publication number may be missing — "
        f"add it in parentheses, e.g. (Report No. XX). APA 7 format: {tip}")]


def _check_conference(n: int, ref: str) -> list[dict]:
    pid = f"REFE{n:03d}_CONF"
    tip = _APA7_FORMAT["conference"]
    results = []

    if _PROCEEDINGS.search(ref):
        results.append(_result(f"{pid}_SRC", "pass",
            f"Entry {n} [Conference paper]: proceedings source present"))
    else:
        results.append(_result(f"{pid}_SRC", "warn",
            f"Entry {n} [Conference paper]: proceedings source information appears to be missing. "
            f"APA 7 format: {tip}"))

    if _PAGE_RANGE.search(ref) or _DOI_RE.search(ref):
        results.append(_result(f"{pid}_LOC", "pass",
            f"Entry {n} [Conference paper]: page range or DOI present"))
    else:
        results.append(_result(f"{pid}_LOC", "warn",
            f"Entry {n} [Conference paper]: page range or DOI appears to be missing. "
            f"APA 7 format: {tip}"))

    return results


def _check_software(n: int, ref: str) -> list[dict]:
    pid = f"REFE{n:03d}_SOFT"
    tip = _APA7_FORMAT["software"]
    results = []

    if re.search(r'\[(?:Software|Computer\s+software|Mobile\s+app)\]', ref, re.IGNORECASE):
        results.append(_result(f"{pid}_LBL", "pass",
            f"Entry {n} [Software]: [Software] label present"))
    else:
        results.append(_result(f"{pid}_LBL", "warn",
            f"Entry {n} [Software]: missing [Software] or [Computer software] label after the title. "
            f"APA 7 format: {tip}"))

    if _URL.search(ref) or _DOI_RE.search(ref):
        results.append(_result(f"{pid}_URL", "pass",
            f"Entry {n} [Software]: URL or DOI present"))
    else:
        results.append(_result(f"{pid}_URL", "warn",
            f"Entry {n} [Software]: a URL or DOI is required for software references (APA 7). "
            f"APA 7 format: {tip}"))

    return results


def _check_podcast(n: int, ref: str) -> list[dict]:
    pid = f"REFE{n:03d}_POD"
    tip = _APA7_FORMAT["podcast"]
    results = []

    if re.search(r'\[Podcast', ref, re.IGNORECASE):
        results.append(_result(f"{pid}_LBL", "pass",
            f"Entry {n} [Podcast]: [Podcast] label present"))
    else:
        results.append(_result(f"{pid}_LBL", "warn",
            f"Entry {n} [Podcast]: missing [Podcast] or [Podcast episode] label after the episode title. "
            f"APA 7 format: {tip}"))

    if _URL.search(ref):
        results.append(_result(f"{pid}_URL", "pass",
            f"Entry {n} [Podcast]: URL present"))
    else:
        results.append(_result(f"{pid}_URL", "warn",
            f"Entry {n} [Podcast]: a URL is required for podcast references (APA 7). "
            f"APA 7 format: {tip}"))

    return results


_TYPE_CHECKERS = {
    "journal":      _check_journal,
    "book":         _check_book,
    "book_chapter": _check_book_chapter,
    "website":      _check_website,
    "video":        _check_video,
    "dataset":      _check_dataset,
    "thesis":       _check_thesis,
    "report":       _check_report,
    "conference":   _check_conference,
    "software":     _check_software,
    "podcast":      _check_podcast,
}


# ── Public API ────────────────────────────────────────────────────────────────

def check_reference_type_style(entry_num: int, ref: str) -> list[dict]:
    """Classify a reference by type and run APA 7 type-specific style checks.

    Returns a list of result dicts. The first entry is always a TYPE info row
    (rule_id REFE###_TYPE) giving the detected type, followed by zero or more
    pass/warn/fail rows for type-specific field requirements.
    """
    ref_type = classify_reference(ref)
    label    = TYPE_LABELS.get(ref_type, "Unknown")

    results = [
        _result(
            f"REFE{entry_num:03d}_TYPE",
            "pass",
            f"Entry {entry_num}: detected type — {label}",
        )
    ]

    checker = _TYPE_CHECKERS.get(ref_type)
    if checker:
        results.extend(checker(entry_num, ref))

    return results
