##JUTLP Template Structure -> move to domain when done
import re as _re

# Leading section enumeration such as "1. ", "2.1 ", "1.2.3. ", "1) ", "(1) ".
# Authors number their headings ("1. Introduction", "2. Literature Review");
# JUTLP headings are unnumbered, so the number is stripped before template
# matching and physically removed (tracked) by the heading-corrections pass.
_SECTION_NUMBER_RE = _re.compile(r"^\s*\(?\d+(?:\.\d+)*\)?\.?\s+")


def strip_leading_section_number(text: str) -> str:
    """Remove a leading heading number from ``text`` (e.g. "2. Literature" ->
    "Literature"). Returns the original text unchanged when stripping would
    leave nothing (a heading that is only a number)."""
    if not text:
        return text
    stripped = _SECTION_NUMBER_RE.sub("", text, count=1)
    return stripped if stripped.strip() else text


def _normalise_subsection(text: str) -> str:
    """Lower-case, collapse whitespace, strip a leading heading number and any
    trailing colon/period/semicolon.

    Mirrors the normalisation both consumer code paths already do
    (output_generation_samfix._normalise_heading_for_match and the
    inline rstrip in jutlp_validator) so the alias-match agrees with
    both.
    """
    if not text:
        return ""
    cleaned = _re.sub(r"\s+", " ", strip_leading_section_number(text).strip().lower())
    return cleaned.rstrip(".:;")


def subsection_alias_match(canonical_label: str, found_subs) -> bool:
    """Return True when ``canonical_label`` is satisfied by ``found_subs``.

    ``found_subs`` is an iterable of heading texts (any case, any trailing
    punctuation). The match succeeds if any of them, after normalisation,
    equals the canonical label or any of its registered aliases.

    The function reads ``CANONICAL_STRUCTURE['subsection_aliases']`` so the
    alias map remains the single source of truth.
    """
    target_norms = {_normalise_subsection(canonical_label)}
    aliases = CANONICAL_STRUCTURE.get("subsection_aliases", {}).get(canonical_label, [])
    for alias in aliases:
        target_norms.add(_normalise_subsection(alias))
    for sub in found_subs:
        if _normalise_subsection(sub) in target_norms:
            return True
    return False


CANONICAL_STRUCTURE = {
    "front_page": {
        "title_style": "Article Title",
        "authors_style": "Authors",
        "affiliations_style": "Author Affiliations",
        "abstract_heading": "Abstract",
        "abstract_style": "Front Page Text",
        # JUTLP front-page rule: the abstract must fit the lines 7–23 region of
        # the front page (so all summary content stays before the Introduction
        # on page 2) and be at most 250 words. lines 7–23 inclusive = 17 lines;
        # at the template's Front Page Text formatting ~250 words ≈ 17 lines, so
        # the words-per-line estimate keeps the two limits consistent.
        "abstract_max_words": 250,
        "abstract_line_region": [7, 23],
        "abstract_max_lines": 17,
        "abstract_words_per_line_estimate": 15,
        "practitioner_notes_heading": "Practitioner Notes",
        "practitioner_notes_style": "Practitioner Notes",
        "practitioner_notes_count": 5,
        "keywords_heading": "Keywords",
        "keywords_max_count": 5,
        "page_break_before_introduction": True,
    },
    "main_sections": [
        "Introduction",
        "Literature",
        "Method",
        "Results",
        "Discussion",
        "Conclusion",   # allow alias later
        "Acknowledgements",
        "References",
    ],
    # Recognised alternative wordings for each main (Heading 1) section. Two
    # things consume this map: the structural validator (treats a section as
    # PRESENT when a heading matches the canonical label or any alias, so the
    # bot does not falsely report it missing) and the heading-renaming passes
    # (rewrite the alias to the canonical JUTLP label). Combined headings that
    # merge two distinct canonical sections — "Results and Discussion",
    # "Findings and Discussion" — are listed so the section is detected, but
    # SECTION_RENAME_MAP excludes them from renaming so the validator's
    # "split these" flag stands. Keep entries title-cased; matching is
    # case-/number-/punctuation-insensitive.
    "section_aliases": {
        "Introduction": [
            "Introduction and Background",
            "Background and Introduction",
            "Introduction and Overview",
        ],
        "Literature": [
            "Literature Review",
            "Literature Reviews",
            "Review of Literature",
            "Review of the Literature",
            "Review of Related Literature",
            "Literature Survey",
            "Related Work",
            "Related Works",
            "Related Literature",
            "Background Literature",
            "Theoretical Background",
            "Literature Review and Background",
            "Background and Literature Review",
        ],
        "Method": [
            "Methods",
            "Methodology",
            "Methodologies",
            "Research Method",
            "Research Methods",
            "Research Methodology",
            "Research Methodologies",
            "Methodological Approach",
            "Materials and Methods",
            "Methods and Materials",
            "Method and Materials",
            "Methods and Procedures",
            "Research Design and Methods",
            "Research Design and Methodology",
        ],
        "Results": [
            "Result",
            "Findings",
            "Key Findings",
            "Main Findings",
            "Study Findings",
            "Research Findings",
            "Empirical Findings",
            "Empirical Results",
            "Study Results",
            "Results and Findings",
            "Findings and Results",
            "Results and Discussion",      # combined — detected, not renamed
            "Findings and Discussion",     # combined — detected, not renamed
        ],
        "Discussion": [
            "Discussions",
            "General Discussion",
            "Discussion and Implications",
        ],
        "Conclusion": [
            "Conclusions",
            "Concluding Remarks",
            "Concluding Comments",
            "Concluding Thoughts",
            "Concluding Summary",
            "Final Remarks",
            "Closing Remarks",
            "Summary and Conclusion",
            "Summary and Conclusions",
            "Conclusion and Recommendations",
            "Conclusions and Recommendations",
            "Conclusion and Future Work",
            "Conclusions and Future Work",
            "Conclusion and Future Research",
        ],
        "Acknowledgements": [
            "Acknowledgments",
            "Acknowledgement",
            "Acknowledgment",
        ],
        "References": [
            "Reference",
            "Reference List",
            "Bibliography",
            "Works Cited",
        ],
    },
    "missing_section_queries": {
        "Literature": (
            "JUTLP policy: The section immediately following the Introduction "
            "should be entitled Literature and use a Heading Level 1 style."
        ),
        "Method": (
            "JUTLP policy: The section immediately following the Literature "
            "should be entitled Method and use a Heading Level 1 style."
        ),
        "Results": (
            "JUTLP policy: The section immediately following the Method "
            "should be entitled Results and use a Heading Level 1 style."
        ),
    },
    "combined_results_discussion_query": (
        "JUTLP policy: Results and Discussion should be separate Heading Level "
        "1 sections. This Journal does not include combined analyses and "
        "discussion sections as it typically limits the opportunity to report "
        "findings clearly and then synthesize these findings with contemporary "
        "literature."
    ),
    "required_subsections": {
        "Method": [
            "Research Design",
            "Participants",
            "Measures",
            "Procedure",
            "Analysis",
        ],
        "Discussion": [
            "Practical Implications",
            "Theoretical Implications",
            "Limitations and Future Research",
        ],
    },
    # Accepted alternative wordings for each required subheading. The bot
    # treats a required subsection as PRESENT when the document contains
    # either the canonical label OR any alias listed here (case-insensitive,
    # trailing colon/period stripped). Two code paths consume this map:
    # jutlp_validator.check_method_subsections /
    # check_discussion_subsections (per-rule pass/fail) and
    # output_generation_samfix._collect_method/discussion_subheading_issues
    # (consolidated comment) — keeping the map here means both stay in
    # sync.
    "subsection_aliases": {
        "Research Design": [
            "setting of the research",
            "research setting",
            "study design",
            "research approach",
            "study setting",
            "research context",
        ],
        "Participants": [
            "sample",
            "respondents",
            "subjects",
            "participant profile",
        ],
        "Measures": [
            "research instrument",
            "instrument",
            "instruments",
            "research instrument development and validation",
            "instrument development",
            "materials",
        ],
        "Procedure": [
            "procedures",
            "data collection",
            "data collection procedure",
            "data collection procedures",
        ],
        "Analysis": [
            "data analysis",
            "analytical approach",
            "analytic strategy",
            "analyses",
        ],
        "Practical Implications": [
            "implications for practice",
            "implications",
        ],
        "Theoretical Implications": [
            "implications for theory",
        ],
        "Limitations and Future Research": [
            "limitations",
            "future research",
            "limitations and directions",
            "limitations and future directions",
            "limitations and recommendations",
        ],
    },
    "style_rules": {
        "main_heading": "Heading 1",
        "subheading": "Heading 2",
        "body": "Normal",
        "quote": "Quote",
        "figure_number": "Figure Number",
        "figure_title": "Figure Title",
        "table_number": "Table Number",
        "table_title": "Table Title",
        "reference_entry": "APA 7 Reference List Entry",
        "forbidden_styles": ["Guidance Notes"],
    },
    "special_rules": {
        "separate_results_and_discussion": True,
        "page_break_before_references": True,
    }
}


# Split points for a combined heading ("Results and Discussion", "Methods &
# Procedures", "Summary/Conclusion").
_COMBINED_SPLIT_RE = _re.compile(r"\s*(?:&|/|,|\band\b)\s*")


def _section_for_part(part: str) -> str | None:
    """Return the canonical main section a heading fragment names, or None.

    Matches the fragment against every canonical label and its single-section
    aliases (case-/number-/punctuation-insensitive)."""
    norm = _normalise_subsection(part)
    if not norm:
        return None
    for canonical, aliases in CANONICAL_STRUCTURE["section_aliases"].items():
        names = {_normalise_subsection(canonical)}
        names.update(_normalise_subsection(a) for a in aliases)
        if norm in names:
            return canonical
    for canonical in CANONICAL_STRUCTURE["main_sections"]:
        if norm == _normalise_subsection(canonical):
            return canonical
    return None


def _merges_two_sections(alias: str) -> bool:
    """True when ``alias`` merges two *distinct* canonical sections (e.g.
    "Results and Discussion") — these must be split, never renamed. A heading
    naming one section under two words ("Results and Findings") is not a merge.
    """
    parts = [p for p in _COMBINED_SPLIT_RE.split(alias) if p.strip()]
    if len(parts) < 2:
        return False
    sections = {s for s in (_section_for_part(p) for p in parts) if s}
    return len(sections) >= 2


def _build_section_rename_map() -> dict:
    """``normalised alias -> canonical label`` for safe heading renames.

    Built from ``section_aliases`` minus any alias that merges two distinct
    canonical sections, so "Findings" -> "Results" and "Literature Review" ->
    "Literature" rename, while "Results and Discussion" is left for the author
    to split. Single source of truth shared by every rename pass.
    """
    rename: dict[str, str] = {}
    for canonical, aliases in CANONICAL_STRUCTURE["section_aliases"].items():
        for alias in aliases:
            if _merges_two_sections(alias):
                continue
            key = _normalise_subsection(alias)
            if key and key != _normalise_subsection(canonical):
                rename[key] = canonical
    return rename


# Normalised-alias -> canonical-label map used by both heading-rename passes
# (Sam's silent Heading 1 normalisation and the tracked heading-corrections
# pass), so they stay in sync and cover the same wordings.
SECTION_RENAME_MAP = _build_section_rename_map()
