"""Track K baseline runner.

Runs the current OpenEditor pipeline over the evaluation corpus and stores
a reproducible baseline before the APA 7 refactor is compared against it.

K-0.5a uses the FULL in-process pipeline:
    app.pipelines.feedback_gen_pipeline.doc_analysis_pipeline

Do not replace this with the CLI --build command.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CROSSREF_CACHE = Path(
    "app/services/.crossref_cache.json"
)


def utc_now() -> str:
    """Return the current UTC time as an ISO formatted string."""

    return datetime.now(timezone.utc).isoformat()


def json_safe(value: Any) -> Any:
    """Convert pipeline return values into JSON-safe data."""

    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


def get_git_commit() -> str:
    """Return the current Git commit hash."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )

        return result.stdout.strip()

    except (subprocess.SubprocessError, OSError):
        return "unknown"


def get_git_branch() -> str:
    """Return the current Git branch."""

    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True,
        )

        return result.stdout.strip()

    except (subprocess.SubprocessError, OSError):
        return "unknown"


def get_selected_pip_freeze() -> list[str]:
    """
    Record important package versions used during the baseline.

    The Track K backlog specifically requires the environment information
    for python-docx, lxml and openai.
    """

    wanted = {
        "python-docx",
        "lxml",
        "openai",
    }

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "freeze",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    except (subprocess.SubprocessError, OSError):
        return []

    packages = []

    for line in result.stdout.splitlines():
        clean = line.strip()

        if not clean:
            continue

        package_name = clean.split("==", 1)[0].lower()

        if package_name in wanted:
            packages.append(clean)

    return sorted(packages)


def find_seed_documents(
    corpus_dir: Path,
) -> list[Path]:
    """Find DOCX files directly inside the supplied corpus directory."""

    return sorted(
        path
        for path in corpus_dir.glob("*.docx")
        if path.is_file()
    )


def copy_crossref_cache(
    run_dir: Path,
    document_id: str,
) -> None:
    """
    Copy the CrossRef cache into the baseline directory.

    A final copy is kept at:
        crossref_cache.json

    A per-document snapshot is also kept so we can see the state after
    processing each document.
    """

    if not CROSSREF_CACHE.exists():
        return

    destination = run_dir / "crossref_cache.json"

    shutil.copy2(
        CROSSREF_CACHE,
        destination,
    )

    cache_history = (
        run_dir
        / "crossref_cache_history"
    )

    cache_history.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        CROSSREF_CACHE,
        cache_history
        / f"{document_id}.json",
    )


def write_json(
    path: Path,
    data: Any,
) -> None:
    """Write formatted JSON to disk."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def run_one_document(
    input_path: Path,
    output_path: Path,
    raw_dir: Path,
    run_dir: Path,
) -> dict[str, Any]:
    """
    Run one DOCX through the full OpenEditor pipeline.

    Errors are recorded instead of stopping the entire batch.
    """

    # Import here so command-line help can still work even if
    # application dependencies have a problem.
    from app.pipelines.feedback_gen_pipeline import (
        doc_analysis_pipeline,
    )

    document_id = input_path.stem

    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    started_at = utc_now()
    started_timer = time.perf_counter()

    pipeline_return = None
    status = "success"
    error_type = None
    error_message = None

    try:
        with contextlib.redirect_stdout(
            stdout_buffer
        ), contextlib.redirect_stderr(
            stderr_buffer
        ):
            pipeline_return = doc_analysis_pipeline(
                str(input_path),
                output_path=str(output_path),
            )

    except Exception as exc:
        status = "error"
        error_type = type(exc).__name__
        error_message = str(exc)

    elapsed_seconds = (
        time.perf_counter()
        - started_timer
    )

    finished_at = utc_now()

    stdout_text = stdout_buffer.getvalue()
    stderr_text = stderr_buffer.getvalue()

    stdout_path = (
        raw_dir
        / f"{document_id}.stdout.txt"
    )

    stderr_path = (
        raw_dir
        / f"{document_id}.stderr.txt"
    )

    stdout_path.write_text(
        stdout_text,
        encoding="utf-8",
    )

    stderr_path.write_text(
        stderr_text,
        encoding="utf-8",
    )

    record = {
        "document_id": document_id,
        "input": str(input_path),
        "output": str(output_path),
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "wall_time_seconds": round(
            elapsed_seconds,
            4,
        ),
        "output_exists": (
            output_path.exists()
        ),
        "pipeline_return": json_safe(
            pipeline_return
        ),
        "error": None,
    }

    if status == "error":
        record["error"] = {
            "type": error_type,
            "message": error_message,
        }

    write_json(
        raw_dir
        / f"{document_id}.json",
        record,
    )

    copy_crossref_cache(
        run_dir,
        document_id,
    )

    return record


def configure_llm_mode(
    mode: str,
) -> bool:
    """
    Configure whether the OpenAI API key is available.

    Returns whether an API key is set after configuration.
    """

    if mode == "off":
        os.environ.pop(
            "OPENAI_API_KEY",
            None,
        )

        return False

    return bool(
        os.environ.get("OPENAI_API_KEY")
    )


def build_run_metadata(
    corpus_dir: Path,
    run_dir: Path,
    llm_mode: str,
    api_key_set: bool,
    seed_documents: list[Path],
) -> dict[str, Any]:
    """Create metadata describing this baseline run."""

    return {
        "schema_version": 1,
        "run_type": "track-k-baseline",
        "created_at": utc_now(),
        "corpus": str(corpus_dir),
        "output_directory": str(run_dir),
        "document_count": len(
            seed_documents
        ),
        "documents": [
            path.name
            for path
            in seed_documents
        ],
        "git": {
            "commit": get_git_commit(),
            "branch": get_git_branch(),
        },
        "environment": {
            "python_version": (
                platform.python_version()
            ),
            "python_executable": (
                sys.executable
            ),
            "platform": platform.platform(),
            "packages": (
                get_selected_pip_freeze()
            ),
        },
        "llm": {
            "mode": llm_mode,
            "api_key_set": api_key_set,
            "model": os.environ.get(
                "OPENAI_MODEL"
            ),
            "temperature": os.environ.get(
                "OPENAI_TEMPERATURE"
            ),
            "max_tokens": os.environ.get(
                "OPENAI_MAX_TOKENS"
            ),
        },
    }


def run_baseline(
    corpus_dir: Path,
    run_dir: Path,
    llm_mode: str,
) -> int:
    """Run the complete baseline batch."""

    if not corpus_dir.exists():
        print(
            f"ERROR: corpus directory "
            f"does not exist: {corpus_dir}"
        )
        return 1

    seed_documents = (
        find_seed_documents(
            corpus_dir
        )
    )

    if not seed_documents:
        print(
            f"ERROR: no DOCX files found "
            f"in {corpus_dir}"
        )
        return 1

    if (
        corpus_dir.name == "seed"
        and len(seed_documents) != 4
    ):
        print(
            "ERROR: Track K seed corpus "
            "must contain exactly 4 DOCX files."
        )
        print(
            f"Found: {len(seed_documents)}"
        )
        return 1

    outputs_dir = (
        run_dir
        / "outputs"
    )

    raw_dir = (
        run_dir
        / "raw"
    )

    outputs_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    api_key_set = configure_llm_mode(
        llm_mode
    )

    if (
        llm_mode == "on"
        and not api_key_set
    ):
        print(
            "ERROR: --llm on was requested "
            "but OPENAI_API_KEY is not set."
        )
        return 1

    run_meta = build_run_metadata(
        corpus_dir=corpus_dir,
        run_dir=run_dir,
        llm_mode=llm_mode,
        api_key_set=api_key_set,
        seed_documents=seed_documents,
    )

    write_json(
        run_dir / "run_meta.json",
        run_meta,
    )

    print(
        f"Track K baseline run"
    )

    print(
        f"Corpus: {corpus_dir}"
    )

    print(
        f"Output: {run_dir}"
    )

    print(
        f"Documents: "
        f"{len(seed_documents)}"
    )

    print(
        f"LLM mode: {llm_mode}"
    )

    print()

    records = []

    for index, input_path in enumerate(
        seed_documents,
        start=1,
    ):
        output_path = (
            outputs_dir
            / input_path.name
        )

        print(
            f"[{index}/"
            f"{len(seed_documents)}] "
            f"{input_path.name}"
        )

        record = run_one_document(
            input_path=input_path,
            output_path=output_path,
            raw_dir=raw_dir,
            run_dir=run_dir,
        )

        records.append(record)

        if record["status"] == "success":
            print(
                "  status: success"
            )
        else:
            print(
                "  status: error"
            )

            print(
                "  error: "
                f"{record['error']}"
            )

        print(
            "  time: "
            f"{record['wall_time_seconds']}s"
        )

    success_count = sum(
        1
        for item in records
        if item["status"] == "success"
    )

    error_count = (
        len(records)
        - success_count
    )

    summary = {
        "schema_version": 1,
        "documents_total": len(
            records
        ),
        "documents_successful": (
            success_count
        ),
        "documents_error": (
            error_count
        ),
        "results": records,
    }

    write_json(
        run_dir / "results.json",
        summary,
    )

    # Update run metadata with completion information.
    run_meta["completed_at"] = (
        utc_now()
    )

    run_meta["summary"] = {
        "successful": success_count,
        "errors": error_count,
    }

    write_json(
        run_dir / "run_meta.json",
        run_meta,
    )

    print()
    print(
        "Baseline capture complete."
    )
    print(
        f"Successful: {success_count}"
    )
    print(
        f"Errors: {error_count}"
    )
    print(
        f"Results: "
        f"{run_dir / 'results.json'}"
    )

    # Do not abort the batch because one document failed,
    # but return a non-zero code after all documents were attempted.
    if error_count:
        return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Track K OpenEditor "
            "baseline corpus."
        )
    )

    parser.add_argument(
        "--corpus",
        required=True,
        help=(
            "Corpus directory containing "
            "DOCX files."
        ),
    )

    parser.add_argument(
        "--out",
        required=True,
        help=(
            "Directory where baseline "
            "results will be stored."
        ),
    )

    parser.add_argument(
        "--llm",
        choices=("off", "on"),
        default="off",
        help=(
            "Run with the OpenAI API "
            "disabled or enabled."
        ),
    )

    args = parser.parse_args()

    return run_baseline(
        corpus_dir=Path(args.corpus),
        run_dir=Path(args.out),
        llm_mode=args.llm,
    )


if __name__ == "__main__":
    sys.exit(main())