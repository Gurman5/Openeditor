"""Reconstruct APA 7 reference strings from CrossRef metadata and detect
format issues in submitted references.

Public API
----------
build_apa7_from_crossref(cr_item)
    Build a full APA 7 string from a CrossRef work item dict.
    Returns None when the type is unknown or required fields are missing.

detect_format_issues(original, reconstructed, cr_item)
    Compare the submitted reference against the CrossRef-derived reconstruction
    and return a list of specific format problem labels.
    Returns an empty list when the reference appears correctly formatted
    (or when differences are in fields we cannot safely auto-check).

format_author_list(authors)
format_editor_list(editors)
    Build APA 7 author / editor strings from CrossRef author dicts.
    Exported so tests and the type checker can call them directly.
"""

import html
import re
import unicodedata
from difflib import SequenceMatcher

# ── Shared normalisation helpers ──────────────────────────────────────────────

_SMART_QUOTE_MAP = str.maketrans({
    "‘": "'", "’": "'",   # left / right single
    "“": '"', "”": '"',   # left / right double
    "′": "'",                   # prime
})

_WS = re.compile(r'\s+')

# Matches a DOI anywhere (bare or inside a URL)
_DOI_BARE   = re.compile(r'10\.\d{4,9}/\S+')
# Matches the full https://doi.org/... form
_DOI_HTTPS  = re.compile(r'https?://doi\.org/10\.\d{4,9}/\S+', re.IGNORECASE)
# Page range with a hyphen (not en dash) between numbers
_HYPHEN_PAGE = re.compile(r'(\d)\s*-\s*(\d)')
# Volume(issue) correct form e.g. "35(1)"
_VOL_ISSUE_CORRECT = re.compile(r',\s*\d+\s*\(\d+\)')
# Any http/https URL
_URL_RE = re.compile(r'https?://')


def _strip_html(text: str) -> str:
    """Decode HTML entities (CrossRef uses &amp; etc.) and strip whitespace."""
    return html.unescape(text or '').strip()


def _normalise_name_key(name: str) -> str:
    """Lowercase, remove accents and non-alpha chars for fuzzy surname matching."""
    nfkd = unicodedata.normalize('NFKD', name)
    without_combining = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r'[^a-z]', '', without_combining.lower())


# ── Author / editor formatting ────────────────────────────────────────────────

def _format_given_to_initials(given: str) -> str:
    """Convert a CrossRef 'given' field to APA 7 initials.

    CrossRef 'given' values are inconsistent:
      "Dorit"        -> "D."
      "Jason D."     -> "J. D."
      "V. E."        -> "V. E."
      "Jean-Baptiste"-> "J.-B."
      "Mary Ann"     -> "M. A."
    """
    if not given:
        return ''
    parts: list[str] = []
    for segment in given.strip().split():
        if '-' in segment:
            # Hyphenated segment: "Jean-Baptiste" -> "J.-B."
            sub: list[str] = []
            for piece in segment.split('-'):
                piece = piece.strip()
                if not piece:
                    continue
                # Already an initial?
                if len(piece) <= 2 and piece.rstrip('.').isalpha():
                    sub.append(piece[0].upper() + '.')
                else:
                    sub.append(piece[0].upper() + '.')
            parts.append('-'.join(sub))
        elif len(segment) == 1:
            # Single bare letter
            parts.append(segment.upper() + '.')
        elif len(segment) <= 2 and segment.endswith('.'):
            # Already "D." or "V."
            parts.append(segment[0].upper() + '.')
        else:
            # Full given name word: take first letter
            parts.append(segment[0].upper() + '.')
    return ' '.join(parts)


def _format_single_author(author: dict) -> str:
    """Format one CrossRef author/editor dict as APA 7 'Surname, F. I.'

    Handles:
    - personal authors:      {'family': 'Smith', 'given': 'John D.'}  -> 'Smith, J. D.'
    - organisational:        {'name': 'World Health Organization'}     -> 'World Health Organization'
    - with suffix:           {'family': 'King', 'given': 'M.', 'suffix': 'Jr.'} -> 'King, M., Jr.'
    """
    # Organisational author — no family name
    if 'name' in author and 'family' not in author:
        return _strip_html(author['name'])

    family  = _strip_html(author.get('family', ''))
    given   = _strip_html(author.get('given', ''))
    suffix  = _strip_html(author.get('suffix', ''))

    if not family:
        # Fall back to 'name' or given-only
        return _strip_html(author.get('name', given))

    initials = _format_given_to_initials(given)
    result   = f'{family}, {initials}' if initials else family

    if suffix:
        result += f', {suffix}'

    return result


def format_author_list(authors: list[dict]) -> str:
    """Format a CrossRef author list as an APA 7 author string.

    Rules (APA 7 §9.7–9.8):
      1 author  : Smith, J.
      2–20      : Smith, J., Jones, A., & Brown, C.
      21+       : first 19, ellipsis (…), final author — NO ampersand
    """
    if not authors:
        return ''
    formatted = [_format_single_author(a) for a in authors]
    n = len(formatted)
    if n == 1:
        return formatted[0]
    if n <= 20:
        return ', '.join(formatted[:-1]) + ', & ' + formatted[-1]
    # 21+ authors
    return ', '.join(formatted[:19]) + ', … ' + formatted[-1]


def format_editor_list(editors: list[dict]) -> str:
    """Format a CrossRef editor list as an APA 7 'A. Editor (Ed.)' string.

    Same count rules as format_author_list; appends (Ed.) or (Eds.).
    """
    if not editors:
        return ''
    formatted = [_format_single_author(e) for e in editors]
    n      = len(formatted)
    suffix = '(Ed.)' if n == 1 else '(Eds.)'
    if n == 1:
        return f'{formatted[0]} {suffix}'
    if n <= 20:
        return ', '.join(formatted[:-1]) + ', & ' + formatted[-1] + f' {suffix}'
    return ', '.join(formatted[:19]) + ', … ' + formatted[-1] + f' {suffix}'


# ── Field helpers ─────────────────────────────────────────────────────────────

def _get_year(cr: dict) -> str:
    date_parts = cr.get('issued', {}).get('date-parts', [[]])
    if date_parts and date_parts[0]:
        return str(date_parts[0][0])
    return 'n.d.'


def _get_title(cr: dict, key: str = 'title') -> str:
    titles = cr.get(key) or []
    raw    = titles[0] if titles else ''
    return _strip_html(raw).rstrip('.')


def _format_page_range(page_str: str, prefix: bool = False) -> str:
    """Convert CrossRef page string to APA 7 format.

    CrossRef uses a plain hyphen ('172-188'); APA 7 requires an en dash (–).
    Optionally prefix with 'pp. ' for book chapters and conference papers.
    """
    if not page_str:
        return ''
    # Replace hyphen between digit pairs with en dash
    fixed = _HYPHEN_PAGE.sub(r'\1–\2', page_str.strip())
    return f'pp. {fixed}' if prefix else fixed


def _format_doi_url(doi: str) -> str:
    """Normalise any DOI representation to the canonical https://doi.org/... form."""
    if not doi:
        return ''
    doi = doi.strip()
    lower = doi.lower()
    if lower.startswith('https://doi.org/'):
        return doi
    if lower.startswith('http://doi.org/'):
        return 'https://doi.org/' + doi[len('http://doi.org/'):]
    if lower.startswith('doi:'):
        return 'https://doi.org/' + doi[4:].lstrip('/')
    if doi.startswith('10.'):
        return 'https://doi.org/' + doi
    return doi


# ── Per-type APA 7 reconstruction ─────────────────────────────────────────────
#
# Each builder receives the full CrossRef item dict and returns either a
# formatted string or None when required fields are absent.

def _build_journal_article(cr: dict) -> str | None:
    """Author(s). (Year). Title. *Journal*, *Vol*(Issue), pages. DOI"""
    author_str = format_author_list(cr.get('author', []))
    if not author_str:
        return None

    year    = _get_year(cr)
    title   = _get_title(cr)
    journal = _strip_html(_get_title(cr, 'container-title'))
    if not title or not journal:
        return None

    volume  = str(cr.get('volume', '') or '')
    issue   = str(cr.get('issue',  '') or '')
    pages   = _format_page_range(cr.get('page', '') or '')
    doi_url = _format_doi_url(cr.get('DOI', ''))

    # Build source segment: Journal, Vol(Issue), pages
    source = journal
    if volume and issue:
        source += f', {volume}({issue})'
    elif volume:
        source += f', {volume}'
    if pages:
        source += f', {pages}'

    sep    = '' if author_str.endswith('.') else '.'
    result = f'{author_str}{sep} ({year}). {title}. {source}.'
    if doi_url:
        result += f' {doi_url}'
    return result


def _build_book(cr: dict) -> str | None:
    """Author(s) or Editor(s). (Year). *Title* (ed.). Publisher. DOI"""
    authors   = cr.get('author', [])
    editors   = cr.get('editor', [])
    year      = _get_year(cr)
    title     = _get_title(cr)
    publisher = _strip_html(cr.get('publisher', '') or '')
    doi_url   = _format_doi_url(cr.get('DOI', ''))

    if not title:
        return None

    if authors:
        agent_str = format_author_list(authors)
    elif editors:
        agent_str = format_editor_list(editors)
    else:
        return None

    sep    = '' if agent_str.endswith('.') else '.'
    result = f'{agent_str}{sep} ({year}). {title}.'
    if publisher:
        result += f' {publisher}.'
    if doi_url:
        result += f' {doi_url}'
    return result


def _build_edited_book(cr: dict) -> str | None:
    """Editor(s). (Year). *Title*. Publisher. DOI"""
    editors = cr.get('editor', [])
    if not editors:
        # Some CrossRef records store editors under 'author'
        editors = cr.get('author', [])
    if not editors:
        return None

    year      = _get_year(cr)
    title     = _get_title(cr)
    publisher = _strip_html(cr.get('publisher', '') or '')
    doi_url   = _format_doi_url(cr.get('DOI', ''))

    if not title:
        return None

    editor_str = format_editor_list(editors)
    sep        = '' if editor_str.endswith('.') else '.'
    result     = f'{editor_str}{sep} ({year}). {title}.'
    if publisher:
        result += f' {publisher}.'
    if doi_url:
        result += f' {doi_url}'
    return result


def _build_book_chapter(cr: dict) -> str | None:
    """Author(s). (Year). Chapter. In Editor(s), *Book* (pp. X–Y). Publisher. DOI"""
    author_str = format_author_list(cr.get('author', []))
    if not author_str:
        return None

    year       = _get_year(cr)
    chapter    = _get_title(cr)
    book_title = _strip_html(_get_title(cr, 'container-title'))
    editors    = cr.get('editor', [])
    pages      = _format_page_range(cr.get('page', '') or '', prefix=True)
    publisher  = _strip_html(cr.get('publisher', '') or '')
    doi_url    = _format_doi_url(cr.get('DOI', ''))

    if not chapter or not book_title:
        return None

    if editors:
        ed_str  = format_editor_list(editors)
        in_part = f'In {ed_str}, {book_title}'
    else:
        in_part = f'In {book_title}'

    if pages:
        in_part += f' ({pages})'

    sep    = '' if author_str.endswith('.') else '.'
    result = f'{author_str}{sep} ({year}). {chapter}. {in_part}.'
    if publisher:
        result += f' {publisher}.'
    if doi_url:
        result += f' {doi_url}'
    return result


def _build_proceedings_article(cr: dict) -> str | None:
    """Author(s). (Year). Title. In Editor(s), *Proceedings* (pp. X–Y). Publisher. DOI"""
    author_str = format_author_list(cr.get('author', []))
    if not author_str:
        return None

    year       = _get_year(cr)
    title      = _get_title(cr)
    proc_title = _strip_html(_get_title(cr, 'container-title'))
    editors    = cr.get('editor', [])
    pages      = _format_page_range(cr.get('page', '') or '', prefix=True)
    publisher  = _strip_html(cr.get('publisher', '') or '')
    doi_url    = _format_doi_url(cr.get('DOI', ''))

    if not title:
        return None

    sep    = '' if author_str.endswith('.') else '.'
    result = f'{author_str}{sep} ({year}). {title}.'

    if proc_title:
        if editors:
            ed_str  = format_editor_list(editors)
            in_part = f' In {ed_str}, {proc_title}'
        else:
            in_part = f' In {proc_title}'
        if pages:
            in_part += f' ({pages})'
        result += in_part + '.'

    if publisher:
        result += f' {publisher}.'
    if doi_url:
        result += f' {doi_url}'
    return result


def _build_report(cr: dict) -> str | None:
    """Author(s). (Year). *Title*. Publisher. DOI"""
    author_str = format_author_list(cr.get('author', []))
    if not author_str:
        return None

    year      = _get_year(cr)
    title     = _get_title(cr)
    publisher = _strip_html(cr.get('publisher', '') or '')
    doi_url   = _format_doi_url(cr.get('DOI', ''))

    if not title:
        return None

    sep    = '' if author_str.endswith('.') else '.'
    result = f'{author_str}{sep} ({year}). {title}.'
    if publisher:
        result += f' {publisher}.'
    if doi_url:
        result += f' {doi_url}'
    return result


def _build_dataset(cr: dict) -> str | None:
    """Author(s). (Year). *Title* [Data set]. Publisher. DOI"""
    author_str = format_author_list(cr.get('author', []))
    if not author_str:
        return None

    year      = _get_year(cr)
    title     = _get_title(cr)
    publisher = _strip_html(cr.get('publisher', '') or '')
    doi_url   = _format_doi_url(cr.get('DOI', ''))

    if not title:
        return None

    sep    = '' if author_str.endswith('.') else '.'
    result = f'{author_str}{sep} ({year}). {title} [Data set].'
    if publisher:
        result += f' {publisher}.'
    if doi_url:
        result += f' {doi_url}'
    return result


def _build_dissertation(cr: dict) -> str | None:
    """Author. (Year). *Title* [Doctoral dissertation, Institution]. DOI"""
    author_str = format_author_list(cr.get('author', []))
    if not author_str:
        return None

    year    = _get_year(cr)
    title   = _get_title(cr)
    doi_url = _format_doi_url(cr.get('DOI', ''))

    if not title:
        return None

    institution = cr.get('institution', []) or []
    inst_name   = institution[0].get('name', '') if institution else ''

    bracket = (
        f'[Doctoral dissertation, {inst_name}]'
        if inst_name
        else '[Doctoral dissertation]'
    )

    sep    = '' if author_str.endswith('.') else '.'
    result = f'{author_str}{sep} ({year}). {title} {bracket}.'
    if doi_url:
        result += f' {doi_url}'
    return result


def _build_preprint(cr: dict) -> str | None:
    """Author(s). (Year). Title. Repository. DOI  (posted-content)"""
    author_str = format_author_list(cr.get('author', []))
    if not author_str:
        return None

    year    = _get_year(cr)
    title   = _get_title(cr)
    doi_url = _format_doi_url(cr.get('DOI', ''))

    if not title:
        return None

    institution = cr.get('institution', []) or []
    source = institution[0].get('name', '') if institution else ''

    sep    = '' if author_str.endswith('.') else '.'
    result = f'{author_str}{sep} ({year}). {title}.'
    if source:
        result += f' {source}.'
    if doi_url:
        result += f' {doi_url}'
    return result


# Map CrossRef 'type' values to their builder functions
_BUILDERS: dict[str, object] = {
    'journal-article':    _build_journal_article,
    'book':               _build_book,
    'monograph':          _build_book,
    'reference-book':     _build_book,
    'book-section':       _build_book,
    'edited-book':        _build_edited_book,
    'book-chapter':       _build_book_chapter,
    'proceedings-article': _build_proceedings_article,
    'report':             _build_report,
    'report-series':      _build_report,
    'dataset':            _build_dataset,
    'dissertation':       _build_dissertation,
    'posted-content':     _build_preprint,
}


def build_apa7_from_crossref(cr_item: dict) -> str | None:
    """Build a full APA 7 reference string from a CrossRef work item.

    Returns None when the type is unknown or required fields (author, title,
    etc.) are absent — in that case no tracked change should be generated.
    """
    builder = _BUILDERS.get(cr_item.get('type', ''))
    if builder is None:
        return None
    return builder(cr_item)  # type: ignore[operator]


# ── Comparison and issue detection ────────────────────────────────────────────

def _normalise_for_compare(text: str) -> str:
    """Aggressively normalise a reference string for similarity comparison.

    - Decodes HTML entities and smart quotes
    - Converts en dash / em dash to hyphen (so we compare content, not encoding)
    - Collapses whitespace
    - Lowercases everything
    """
    text = _strip_html(text)
    text = text.translate(_SMART_QUOTE_MAP)
    text = text.replace('–', '-').replace('—', '-')  # en/em dash -> hyphen
    text = _WS.sub(' ', text).strip().lower()
    return text


def detect_format_issues(original: str, reconstructed: str, cr_item: dict) -> list[str]:
    """Return a list of format problem labels found in the submitted reference.

    Checks specific, reliably detectable APA 7 format rules using CrossRef data:
      - Missing or incorrectly formatted DOI
      - Page range separator (hyphen instead of en dash)
      - Volume/issue format (Vol. X, No. Y instead of X(Y))
      - Author full names instead of initials

    Returns an empty list when:
      - No specific issue is found, OR
      - The difference is only in a field we cannot safely auto-correct
        (e.g. title capitalisation, publisher name variations)

    An empty list means no tracked change should be generated even if the
    overall strings differ — we avoid false positives.
    """
    issues: list[str] = []
    orig_lower = original.lower()

    # ── 1. DOI checks ─────────────────────────────────────────────────────────
    doi = (cr_item.get('DOI', '') or '').strip()
    if doi:
        correct_url    = f'https://doi.org/{doi.lower()}'
        correct_url_hs = f'http://doi.org/{doi.lower()}'
        doi_lower      = doi.lower()

        if correct_url not in orig_lower:
            # Is the DOI present but in a wrong form?
            if doi_lower in orig_lower and not _DOI_HTTPS.search(original):
                issues.append('DOI format — should be https://doi.org/...')
            elif correct_url_hs in orig_lower:
                issues.append('DOI URL uses http — should be https://doi.org/...')
            elif re.search(r'\bdoi\s*:\s*' + re.escape(doi_lower), orig_lower):
                issues.append('DOI format — should be https://doi.org/...')
            else:
                # DOI absent entirely
                issues.append('missing DOI')

    # ── 2. Page separator ─────────────────────────────────────────────────────
    # Flag only when there's a digit-hyphen-digit pattern after a comma
    # (typical page range context), not for year hyphens or DOI paths.
    if re.search(r',\s*\d+\s*-\s*\d+', original):
        issues.append('page separator — use en dash (–) not hyphen (-)')

    # ── 3. Volume/issue format (journal articles only) ────────────────────────
    if cr_item.get('type') == 'journal-article':
        volume = str(cr_item.get('volume', '') or '')
        issue  = str(cr_item.get('issue',  '') or '')
        if volume and issue:
            correct_vi = f'{volume}({issue})'
            if correct_vi not in original:
                # Only flag if an obviously wrong form is present
                if (re.search(r'\bvol\.?\s*' + re.escape(volume), original, re.IGNORECASE)
                        or re.search(r'\bno\.?\s+' + re.escape(issue), original, re.IGNORECASE)):
                    issues.append(
                        f'volume/issue format — should be {correct_vi}'
                    )

    # ── 4. Author full names instead of initials ──────────────────────────────
    authors = cr_item.get('author', []) or []
    if authors:
        year_m = re.search(r'\(\d{4}', original)
        if year_m:
            author_segment = original[:year_m.start()]
            # Build the set of known surnames so we can skip them when scanning
            # for full given names. Without this, ", Ensor" (a surname) would
            # incorrectly match the pattern for a full given name.
            surnames_lower = {
                (a.get('family') or '').strip().lower()
                for a in authors
                if a.get('family')
            }
            found_full_given = False
            for m in re.finditer(r',\s+([A-Z][a-z]{2,})', author_segment):
                word = m.group(1).lower()
                if word not in surnames_lower:
                    found_full_given = True
                    break
            if found_full_given:
                issues.append(
                    'author names — use initials only (e.g. Smith, J. A., not Smith, John A.)'
                )

    return issues


def references_are_equivalent(original: str, reconstructed: str) -> bool:
    """Return True when the submitted and reconstructed references are close
    enough that no tracked change is warranted.

    Uses a high similarity threshold (0.93) on aggressively normalised strings
    so minor punctuation and spacing differences do not trigger false positives.
    A separate targeted check via detect_format_issues() is always the final
    gate — this function is a fast-path optimisation only.
    """
    orig_n  = _normalise_for_compare(original)
    recon_n = _normalise_for_compare(reconstructed)
    if orig_n == recon_n:
        return True
    return SequenceMatcher(None, orig_n, recon_n).ratio() >= 0.93
