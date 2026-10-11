import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")
OPENAI_TEMPERATURE: float = float(os.environ.get("OPENAI_TEMPERATURE", "0.2"))
OPENAI_MAX_TOKENS: int = int(os.environ.get("OPENAI_MAX_TOKENS", "16384"))

# APA-7 Standard Document Configuration
APA7_DEFAULT_FONT: str = "Calibri"
APA7_DEFAULT_FONT_SIZE_PT: int = 11
APA7_LOCALE: str = "en-AU"
APA7_CAROUSEL_RETENTION_ENABLED: bool = True


# APA-7 Configuration Constants (C-15)
DEFAULT_FONT: str = "Calibri"
DEFAULT_FONT_SIZE: int = 11
HEADING_FONT: str = "Calibri"
ALLOWED_FONTS: list[str] = ["Calibri", "Arial", "Times New Roman", "Georgia", "Computer Modern"]
DEFAULT_MODE: str = "apa7"
SPELLING_VARIANT: str = "American"
MARGIN_IN: float = 1.0
DOUBLE_SPACING_TWIPS: int = 480
FIRST_LINE_INDENT_IN: float = 0.5

# Backward Compatibility Aliases
APA7_DEFAULT_FONT = DEFAULT_FONT
APA7_DEFAULT_FONT_SIZE_PT = DEFAULT_FONT_SIZE