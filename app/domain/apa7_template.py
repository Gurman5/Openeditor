"""
APA-7 Template Definitions and Formatting Constants.
Locked Decisions: Calibri 11pt, AU spelling variant, carousel retained.

APA7 Template Definition & Logical Layer (C-10 / C-11)

This module serves as the APA7 successor to `canonical_jultp_template.py`.
It defines the logical layer and rule structures required by downstream modules,
while the physical style definitions remain in the `.docx` template read live 
via `extract_template_styles()`.

Architecture Comparison:
------------------------
| Layer          | canonical_jultp_template.py (Legacy)    | apa7_template.py (Intended)                                     |
|----------------|---------------------------------------------|-----------------------------------------------------------------|
| Helpers        | strip_leading_section_number,               | Same 3 helpers ported verbatim                                  |
|                | _normalise_subsection, subsection_alias_match|                                                                 |
| Structure dict | CANONICAL_STRUCTURE                         | CANONICAL_STRUCTURE_APA7                                        |
|                | (front page, sections, style_rules,         | (student/prof front page, abstract <= 250 words,                |
|                | special_rules)                              | Method/Results/Discussion, appendices allowed)                  |
| Consumers      | 9 modules import from it                    | C-11 ticket repoints those 9 modules here                       |

Development Status:
-------------------
The file is currently a placeholder. The remaining C-10 work includes:
1. Porting the subsection and section-number matching helpers verbatim.
2. Writing `CANONICAL_STRUCTURE_APA7` (including its corresponding `style_rules` 
   and `special_rules`) aligned with the `.docx` base template spec.
3. Executing the C-11 sweep to repoint the consumer modules.
"""
# > File is part of C-10-C-11

# Font & Typography Standards
DEFAULT_FONT_FAMILY = "Calibri"
DEFAULT_FONT_SIZE_PT = 11

# Spelling and Locale Rules
DEFAULT_LOCALE = "en-AU"

# Template structure markers
CAROUSEL_ENABLED = True

# Temporary robust bridge for C-10/C-11 WIP placeholder state
try:
    from app.domain.canonical_jultp_template import (
        CANONICAL_STRUCTURE as _LEGACY_STRUCTURE,
        strip_leading_section_number,
        _normalise_subsection,
        subsection_alias_match,
        SECTION_RENAME_MAP as _LEGACY_SECTION_RENAME_MAP,
    )
    CANONICAL_STRUCTURE = _LEGACY_STRUCTURE
    CANONICAL_STRUCTURE_APA7 = _LEGACY_STRUCTURE
    APA7_STRUCTURE = _LEGACY_STRUCTURE
    SECTION_RENAME_MAP = _LEGACY_SECTION_RENAME_MAP
except ImportError:
    CANONICAL_STRUCTURE = {}
    CANONICAL_STRUCTURE_APA7 = {}
    APA7_STRUCTURE = {}
    SECTION_RENAME_MAP = {}
    def strip_leading_section_number(text: str) -> str: return text
    def _normalise_subsection(text: str) -> str: return text
    def subsection_alias_match(s1: str, s2: str) -> bool: return s1 == s2