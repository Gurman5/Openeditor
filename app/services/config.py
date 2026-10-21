import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")
OPENAI_TEMPERATURE: float = float(os.environ.get("OPENAI_TEMPERATURE", "0.2"))
OPENAI_MAX_TOKENS: int = int(os.environ.get("OPENAI_MAX_TOKENS", "16384"))

# --- APA 7 deterministic output defaults (C-15, Track C)
# >  output_generation_samfix.py now imports these instead of hardcoding
# > see output_generation_samfix.py line 3793
ALLOWED_FONTS = {"Calibri", "Arial", "Times New Roman", "Georgia", "Lucida Sans Unicode"}
# Reporting reference for APA002: the fixer normalises everything to
# DEFAULT_FONT, but the check message names this set so the author sees which
# typefaces APA actually permits. Consulted by apa7_formatting_checks only —
# no fixer reads it.
DEFAULT_FONT = "Calibri"          # C-27: default, Calibri for body + headings (D2 locked)
DEFAULT_FONT_SIZE = 11
HEADING_FONT = "Calibri"
# Typefaces the font sweep must never rewrite (equations, symbols). Compared
# case-insensitively; shared by run_font_corrections and docx_format_helpers.
SYMBOL_FONTS = frozenset({"symbol", "wingdings", "wingdings 2", "wingdings 3", "webdings"})
DEFAULT_MODE = os.environ.get(
    "APA7_TITLE_PAGE_MODE",
    os.environ.get("DEFAULT_MODE", "auto"),
).strip().lower() or "auto"       # auto-detect student/pro + manual override (D1 locked)
SPELLING_VARIANT = "AU"           # spelling direction, confirmed AU (D3 locked)

MARGIN_IN = 1.0                   # APA-00: 1" margins all sides
APA_MARGIN_TWIPS = "1440"         # 1 inch = 1440 twips (used by output passes)
APA_SPACE_AFTER_TWIPS = "0"       # APA-01: no blank line before/after headings
DOUBLE_SPACING_TWIPS = "480"      # double spacing = 2.0 * 240
APA_FIRST_LINE_INDENT_TWIPS = "720"  # APA-04: 0.5" first-line indent = 720 twips

# Backward compatibility aliases (C-15)
DEFAULT_FONT = globals().get("DEFAULT_FONT", "Calibri")
DEFAULT_FONT_SIZE = globals().get("DEFAULT_FONT_SIZE", 11)
APA7_DEFAULT_FONT = DEFAULT_FONT
APA7_DEFAULT_FONT_SIZE_PT = DEFAULT_FONT_SIZE
APA7_LOCALE = globals().get("DEFAULT_LOCALE", "en-AU")
APA7_CAROUSEL_RETENTION_ENABLED = globals().get("CAROUSEL_ENABLED", True)

# JB-03: Acronym feature flag
ENABLE_ACRONYM_PROCESSING = os.environ.get("ENABLE_ACRONYM_PROCESSING", "true").lower() in ("true", "1", "yes")

def is_rq_hypothesis_exempt(document_metadata: dict, assignment_type: str = None) -> bool:
    """
    JB-05: Determines whether the document or assignment type is exempt 
    from Research Question (RQ) or hypothesis validation checks.
    """
    exempt_types = {"literature_review", "reflective_essay", "annotated_bibliography"}
    
    if assignment_type and assignment_type.lower() in exempt_types:
        return True
        
    if document_metadata.get("exempt_from_rq_hypothesis", False):
        return True
        
    return False