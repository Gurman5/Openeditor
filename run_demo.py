"""Demo script for JUTLP Copy-Editor AI — LLM Editorial Review.

Usage:
    python run_demo.py <path_to_docx>
    python run_demo.py                  (uses a default sample document)

"""

import sys
import time

from app.services.ai.editorial_review_service import run_editorial_review
from app.services.jutlp_validator import validate

SEVERITY_COLORS = {
    "requires_attention": "\033[91m",  # red
    "advisory": "\033[93m",            # yellow
    "minor": "\033[94m",               # blue
}
RESET = "\033[0m"
BOLD = "\033[1m"

DEFAULT_DOCX = "docs/Sample Documents/Compassionate+Pedagogy_Hatfield+et+al.docx"


def main():
    docx_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DOCX

    print(f"\n{BOLD}JUTLP Copy-Editor AI — Editorial Review{RESET}")
    print(f"{'=' * 50}")
    print(f"Document: {docx_path}\n")

    deterministic_result = validate(docx_path)

    start = time.time()
    result = run_editorial_review(docx_path, deterministic_check_result=deterministic_result)
    elapsed = time.time() - start

    print(f"Model: {result.model_used}")
    print(f"Tokens: {result.token_usage.get('total_tokens', 'N/A')}")
    print(f"Time: {elapsed:.1f}s")
    print(f"Notes: {len(result.notes)}")
    print(f"{'=' * 50}\n")

    for i, note in enumerate(result.notes, 1):
        color = SEVERITY_COLORS.get(note.severity, "")
        print(f"{BOLD}Note {i}{RESET} [{color}{note.severity.upper()}{RESET}] "
              f"{note.category} — {note.section}")
        print(f"  {note.message}")
        print(f"  -> {note.suggestion}\n")

    requires_attention = sum(1 for n in result.notes if n.severity == "requires_attention")
    advisory = sum(1 for n in result.notes if n.severity == "advisory")
    minor = sum(1 for n in result.notes if n.severity == "minor")
    print(f"{'=' * 50}")
    print(f"Summary: {SEVERITY_COLORS['requires_attention']}{requires_attention} requires attention{RESET}, "
          f"{SEVERITY_COLORS['advisory']}{advisory} advisory{RESET}, "
          f"{SEVERITY_COLORS['minor']}{minor} minor{RESET}")


if __name__ == "__main__":
    main()
