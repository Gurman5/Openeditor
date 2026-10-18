"""Headless batch runner: full APA 7 pipeline over a corpus folder.
Usage:
    python -m app.cli_apa7 tests/corpus/seed --out results.json
    python -m app.cli_apa7 tests/corpus/seed --out results.json --no-llm
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from app.domain.apa7_matrix import MATRIX_ID_MAP
from app.pipelines.feedback_gen_pipeline import doc_analysis_pipeline

log = logging.getLogger(__name__)


def _matrix_ids_fired(result: dict) -> list[str]:
    """Extract the APA matrix IDs fired by the deterministic validator.

    Each validator result already carries ``matrix_id`` (C-20a); fall back to
    the legacy-id map (C-21) for anything that only has a ``rule_id``.
    """
    det = result.get("deterministic_check_results") or {}
    ids = []
    for r in det.get("results", []):
        mid = r.get("matrix_id") or MATRIX_ID_MAP.get(r.get("rule_id", ""), "")
        if mid:
            ids.append(mid)
    return ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the full APA 7 pipeline over a corpus of .docx files."
    )
    parser.add_argument("corpus", help="Folder of .docx files to process")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip the LLM editorial stage (deterministic-only baseline)",
    )
    args = parser.parse_args(argv)

    if args.no_llm:
        from app.services.ai import llm_client

        llm_client.OPENAI_API_KEY = ""

    corpus = Path(args.corpus)
    docs = sorted(p for p in corpus.glob("*.docx") if not p.name.startswith("reviewed_"))
    if not docs:
        log.error("No .docx files found in %s", corpus)
        return 1

    out = []
    for doc in docs:
        log.info("Processing %s", doc.name)
        result = doc_analysis_pipeline(doc)
        ids = _matrix_ids_fired(result)
        counts = {mid: ids.count(mid) for mid in sorted(set(ids))}
        out.append(
            {
                "file": doc.name,
                "matrix_ids": ids,
                "counts": counts,
                "stage_errors": result.get("stage_errors", []),
            }
        )

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    log.info("Wrote %d docs to %s", len(out), args.out)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
