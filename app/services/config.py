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