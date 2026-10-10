"""
APA-7 Template Definitions and Formatting Constants.
Locked Decisions: Calibri 11pt, AU spelling variant, carousel retained.
"""
import re

# Font & Typography Standards
DEFAULT_FONT_FAMILY = "Calibri"
DEFAULT_FONT_SIZE_PT = 11

# Spelling and Locale Rules
DEFAULT_LOCALE = "en-AU"

# Template structure markers
CAROUSEL_ENABLED = True

# Standard APA-7 Document Structure & Aliases
APA7_STRUCTURE = {
    "main_sections": [
        "Introduction",
        "Literature",
        "Method",
        "Results",
        "Discussion",
        "Conclusion",
        "References",
    ],
    "section_aliases": {
        "Introduction": ["Introduction", "Background"],
        "Literature": ["Literature Review", "Related Work", "Background"],
        "Method": ["Methodology", "Research Design", "Methods"],
        "Results": ["Findings", "Results and Analysis"],
        "Discussion": ["Discussion and Implications", "General Discussion"],
        "Conclusion": ["Conclusions", "Concluding Remarks"],
        "References": ["References", "Reference List", "Bibliography"],
        "Acknowledgements": ["Acknowledgements", "Acknowledgments"],
    },
    "required_subsections": {
        "Method": ["Participants", "Materials", "Procedure"],
        "Discussion": ["Implications", "Limitations", "Future Research"],
    },
    "front_page": {
        "abstract_max_words": 250,
        "abstract_max_lines": 23,
        "abstract_line_region": (7, 23),
        "abstract_words_per_line_estimate": 12,
        "practitioner_notes_count": 3,
        "keywords_max_count": 5,
    },
    "style_rules": {
        "forbidden_styles": ["Heading 3", "JUTLP Special Style"],
        "reference_entry": "APA 7 Reference List Entry",
        "figure_number": "Figure Number",
        "figure_title": "Figure Title",
        "table_number": "Table Number",
        "table_title": "Table Title",
        "table_text": "Table Text",
        "quote": "Quote",
    },
    "combined_results_discussion_query": "Ensure Results and Discussion appear as separate top-level sections.",
}

# Aliases and maps expected by heading_corrections and other modules
CANONICAL_STRUCTURE = APA7_STRUCTURE
SECTION_RENAME_MAP = {
    "Literature Review": "Literature",
    "Related Work": "Literature",
    "Methodology": "Method",
    "Methods": "Method",
    "Findings": "Results",
    "Conclusions": "Conclusion",
}
SUBSECTION_ALIASES = APA7_STRUCTURE["required_subsections"]

def strip_leading_section_number(text: str) -> str:
    return re.sub(r"^\d+(\.\d+)*\.?\s+", "", text).strip()

def subsection_alias_match(canonical: str, found_list: list[str]) -> bool:
    c_lower = canonical.strip().lower()
    for f in found_list:
        f_clean = strip_leading_section_number(f).strip().lower()
        if f_clean == c_lower:
            return True
    return False
