"""Headless entry point for the LLM editorial-review stage.

Runs ONLY ``run_editorial_review`` and writes the result to a JSON file,
for test harnesses and CI without spinning up the full pipeline.

Usage:
    python -m app.services.ai.cli \
        --docx path/to/manuscript.docx \
        --deterministic results.json \
        --ref refs.json \
        --out notes.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from app.services.ai.editorial_review_service import run_editorial_review


def _load_json(path: str | None) -> dict | None:
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the LLM editorial-review stage headlessly."
    )
    parser.add_argument("--docx", required=True, help="Path to the manuscript .docx")
    parser.add_argument(
        "--deterministic",
        default=None,
        help="Path to deterministic check results JSON",
    )
    parser.add_argument(
        "--ref",
        default=None,
        help="Path to reference check results JSON",
    )
    parser.add_argument("--out", required=True, help="Path to write the notes JSON")
    args = parser.parse_args(argv)

    result = run_editorial_review(
        args.docx,
        _load_json(args.deterministic),
        _load_json(args.ref),
        raise_on_error=False,
    )

    payload = {
        "notes": [asdict(n) for n in result.notes],
        "structural_validations": [asdict(v) for v in result.structural_validations],
        "model_used": result.model_used,
        "token_usage": result.token_usage,
        "error": result.error,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
