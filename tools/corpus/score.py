"""Track K K-0.5b conformance scorer.

Runs the Track K harness over engine output documents.

Conformance:
    pass / (pass + fail)

NA rows are excluded from the denominator.

For injected documents:
    defects_injected -> APA matrix row, e.g. APA-02
    injections[].recipe_id -> exact recipe, e.g. APA-02a

An injected defect counts as fixed when its matrix row passes
on the engine output.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.corpus.harness import (
    AVAILABLE_CHECKS,
    run_harness,
)


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def load_json(
    path: Path,
) -> dict[str, Any]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            f"{path}: JSON root "
            "must be an object"
        )

    return data


def write_json(
    path: Path,
    data: Any,
) -> None:
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


def document_filename(
    row: dict[str, Any],
) -> str:
    """
    Work out the DOCX filename.

    Normally Track K uses:
        id = seed-01
        file = seed-01.docx

    Optional filename/file/path fields are also supported.
    """

    for field in (
        "filename",
        "file",
        "path",
    ):
        value = row.get(field)

        if (
            isinstance(value, str)
            and value.strip()
        ):
            return Path(value).name

    document_id = row.get("id")

    if (
        not isinstance(
            document_id,
            str,
        )
        or not document_id.strip()
    ):
        raise ValueError(
            "Manifest document "
            "has no usable id."
        )

    return f"{document_id}.docx"


def effective_check_options(
    row: dict[str, Any],
) -> dict[str, Any]:
    """
    Return the check options for a document.

    Injector rows may contain:
        {
            "APA-08": {
                "require_abstract": true
            }
        }

    Professional papers also require an abstract.
    """

    raw = (
        row.get(
            "check_options"
        )
        or {}
    )

    if not isinstance(
        raw,
        dict,
    ):
        raise ValueError(
            f"{row.get('id')}: "
            "check_options must "
            "be an object"
        )

    options = deepcopy(raw)

    if (
        row.get("mode")
        == "professional"
    ):
        apa08 = options.setdefault(
            "APA-08",
            {},
        )

        if not isinstance(
            apa08,
            dict,
        ):
            raise ValueError(
                f"{row.get('id')}: "
                "APA-08 check_options "
                "must be an object"
            )

        apa08.setdefault(
            "require_abstract",
            True,
        )

    return options


def status_counts(
    checks: dict[str, Any],
) -> dict[str, int]:
    counts = {
        "pass": 0,
        "fail": 0,
        "na": 0,
    }

    for matrix_id, item in checks.items():

        if not matrix_id.startswith(
            "APA-"
        ):
            continue

        if not isinstance(
            item,
            dict,
        ):
            continue

        status = item.get(
            "status"
        )

        if status in counts:
            counts[status] += 1

    return counts


def conformance(
    counts: dict[str, int],
) -> float | None:
    denominator = (
        counts["pass"]
        + counts["fail"]
    )

    if denominator == 0:
        return None

    return round(
        counts["pass"]
        / denominator,
        4,
    )


def get_duplicate_id_count(
    checks: dict[str, Any],
) -> int:
    validity = checks.get(
        "validity"
    )

    if not isinstance(
        validity,
        dict,
    ):
        return 0

    details = validity.get(
        "details"
    )

    if not isinstance(
        details,
        dict,
    ):
        return 0

    value = details.get(
        "duplicate_w_id_count",
        0,
    )

    if isinstance(
        value,
        int,
    ):
        return value

    return 0


def score_injected_defects(
    row: dict[str, Any],
    checks: dict[str, Any],
) -> dict[str, Any]:

    defects = (
        row.get(
            "defects_injected"
        )
        or []
    )

    if not isinstance(
        defects,
        list,
    ):
        defects = []

    recipe_ids = []

    injections = (
        row.get("injections")
        or []
    )

    for injection in injections:

        if not isinstance(
            injection,
            dict,
        ):
            continue

        recipe_id = injection.get(
            "recipe_id"
        )

        if isinstance(
            recipe_id,
            str,
        ):
            recipe_ids.append(
                recipe_id
            )

    targets = []

    for matrix_id in defects:

        result = checks.get(
            matrix_id
        )

        if isinstance(
            result,
            dict,
        ):
            status = result.get(
                "status"
            )
        else:
            status = None

        targets.append(
            {
                "matrix_id": (
                    matrix_id
                ),
                "output_status": (
                    status
                    or "missing"
                ),
                "fixed": (
                    status
                    == "pass"
                ),
            }
        )

    fixed = sum(
        1
        for target in targets
        if target["fixed"]
    )

    total = len(targets)

    return {
        "recipe_ids": recipe_ids,
        "targets": targets,
        "total": total,
        "fixed": fixed,
        "fix_rate": (
            round(
                fixed / total,
                4,
            )
            if total
            else None
        ),
    }


def score_document(
    row: dict[str, Any],
    corpus_dir: Path,
    outputs_dir: Path,
) -> dict[str, Any]:

    document_id = row.get(
        "id",
        "<unknown>",
    )

    filename = (
        document_filename(
            row
        )
    )

    input_path = (
        corpus_dir
        / filename
    )

    output_path = (
        outputs_dir
        / filename
    )

    options = (
        effective_check_options(
            row
        )
    )

    result: dict[str, Any] = {
        "document_id": (
            document_id
        ),
        "filename": filename,
        "mode": row.get(
            "mode"
        ),
        "input": str(
            input_path
        ),
        "output": str(
            output_path
        ),
        "defects_injected": (
            row.get(
                "defects_injected"
            )
            or []
        ),

        # These describe the input corpus document.
        "input_verdicts": (
            row.get(
                "verdicts"
            )
            or {}
        ),

        "check_options": options,
    }

    missing = []

    if not input_path.exists():
        missing.append(
            str(input_path)
        )

    if not output_path.exists():
        missing.append(
            str(output_path)
        )

    if missing:

        result.update(
            {
                "status": "error",
                "error": (
                    "Missing file(s): "
                    + ", ".join(
                        missing
                    )
                ),
                "checks": {},
                "counts": {
                    "pass": 0,
                    "fail": 0,
                    "na": 0,
                },
                "conformance": None,
                "preservation_hard_flag": False,
                "duplicate_w_id_count": 0,
                "injected": (
                    score_injected_defects(
                        row,
                        {},
                    )
                ),
            }
        )

        return result

    try:
        harness_report = (
            run_harness(
                output_path,
                list(
                    AVAILABLE_CHECKS
                ),
                input_docx=(
                    input_path
                ),
                check_options=(
                    options
                ),
            )
        )

    except Exception as exc:

        result.update(
            {
                "status": "error",
                "error": (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
                "checks": {},
                "counts": {
                    "pass": 0,
                    "fail": 0,
                    "na": 0,
                },
                "conformance": None,
                "preservation_hard_flag": False,
                "duplicate_w_id_count": 0,
                "injected": (
                    score_injected_defects(
                        row,
                        {},
                    )
                ),
            }
        )

        return result

    checks = (
        harness_report.get(
            "checks"
        )
        or {}
    )

    counts = status_counts(
        checks
    )

    preservation = (
        checks.get(
            "preservation"
        )
        or {}
    )

    hard_flag = False

    if isinstance(
        preservation,
        dict,
    ):
        hard_flag = bool(
            preservation.get(
                "hard_flag"
            )
        )

    validity = (
        checks.get(
            "validity"
        )
        or {}
    )

    validity_failed = (
        isinstance(
            validity,
            dict,
        )
        and validity.get(
            "status"
        )
        == "fail"
    )

    residue_status = None
    residue = checks.get(
        "residue"
    )

    if isinstance(
        residue,
        dict,
    ):
        residue_status = (
            residue.get(
                "status"
            )
        )

    appendices_status = None
    appendices = checks.get(
        "appendices"
    )

    if isinstance(
        appendices,
        dict,
    ):
        appendices_status = (
            appendices.get(
                "status"
            )
        )

    result.update(
        {
            "status": "scored",
            "error": None,
            "accepted_view": (
                harness_report.get(
                    "accepted_view"
                )
            ),
            "checks": checks,
            "counts": counts,
            "conformance": (
                conformance(
                    counts
                )
            ),
            "validity_failed": (
                validity_failed
            ),
            "preservation_hard_flag": (
                hard_flag
            ),
            "duplicate_w_id_count": (
                get_duplicate_id_count(
                    checks
                )
            ),
            "residue_status": (
                residue_status
            ),
            "appendices_status": (
                appendices_status
            ),
            "injected": (
                score_injected_defects(
                    row,
                    checks,
                )
            ),
        }
    )

    return result


def aggregate_scores(
    documents: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    overall = {
        "pass": 0,
        "fail": 0,
        "na": 0,
    }

    matrix: dict[
        str,
        dict[str, int],
    ] = {}

    errors = 0
    preservation_failures = 0
    validity_failures = 0
    duplicate_ids = 0
    residue_failures = 0
    appendix_failures = 0

    injected_total = 0
    injected_fixed = 0

    for document in documents:

        if (
            document.get(
                "status"
            )
            != "scored"
        ):
            errors += 1
            continue

        checks = (
            document.get(
                "checks"
            )
            or {}
        )

        for (
            matrix_id,
            result,
        ) in checks.items():

            if not matrix_id.startswith(
                "APA-"
            ):
                continue

            if not isinstance(
                result,
                dict,
            ):
                continue

            status = result.get(
                "status"
            )

            if status not in overall:
                continue

            overall[status] += 1

            matrix_counts = (
                matrix.setdefault(
                    matrix_id,
                    {
                        "pass": 0,
                        "fail": 0,
                        "na": 0,
                    },
                )
            )

            matrix_counts[
                status
            ] += 1

        if document.get(
            "preservation_hard_flag"
        ):
            preservation_failures += 1

        if document.get(
            "validity_failed"
        ):
            validity_failures += 1

        duplicate_ids += int(
            document.get(
                "duplicate_w_id_count"
            )
            or 0
        )

        if (
            document.get(
                "residue_status"
            )
            == "fail"
        ):
            residue_failures += 1

        if (
            document.get(
                "appendices_status"
            )
            == "fail"
        ):
            appendix_failures += 1

        injected = (
            document.get(
                "injected"
            )
            or {}
        )

        injected_total += int(
            injected.get(
                "total"
            )
            or 0
        )

        injected_fixed += int(
            injected.get(
                "fixed"
            )
            or 0
        )

    matrix_summary = {}

    for matrix_id in sorted(
        matrix
    ):
        counts = matrix[
            matrix_id
        ]

        matrix_summary[
            matrix_id
        ] = {
            **counts,
            "conformance": (
                conformance(
                    counts
                )
            ),
        }

    return {
        "documents_total": (
            len(documents)
        ),
        "documents_scored": (
            len(documents)
            - errors
        ),
        "documents_error": (
            errors
        ),

        "matrix": (
            matrix_summary
        ),

        "overall": {
            **overall,
            "conformance": (
                conformance(
                    overall
                )
            ),
        },

        "hard_preservation_failures": (
            preservation_failures
        ),

        "validity_failures": (
            validity_failures
        ),

        "duplicate_w_id_count": (
            duplicate_ids
        ),

        "residue_failures": (
            residue_failures
        ),

        "appendix_failures": (
            appendix_failures
        ),

        "injected_defects": {
            "total": (
                injected_total
            ),
            "fixed": (
                injected_fixed
            ),
            "fix_rate": (
                round(
                    injected_fixed
                    / injected_total,
                    4,
                )
                if injected_total
                else None
            ),
        },
    }


def score(
    corpus_dir: Path,
    outputs_dir: Path,
    manifest_path: Path,
    run_meta_path: (
        Path | None
    ) = None,
) -> dict[str, Any]:

    manifest = load_json(
        manifest_path
    )

    rows = manifest.get(
        "documents"
    )

    if not isinstance(
        rows,
        list,
    ):
        raise ValueError(
            f"{manifest_path}: "
            "missing documents array"
        )

    documents = []

    for row in rows:

        if not isinstance(
            row,
            dict,
        ):
            continue

        documents.append(
            score_document(
                row,
                corpus_dir,
                outputs_dir,
            )
        )

    result: dict[str, Any] = {
        "schema_version": 1,
        "score_type": (
            "track-k-conformance"
        ),
        "created_at": utc_now(),
        "corpus": str(
            corpus_dir
        ),
        "outputs": str(
            outputs_dir
        ),
        "manifest": str(
            manifest_path
        ),
        "documents": documents,
        "aggregate": (
            aggregate_scores(
                documents
            )
        ),
    }

    if run_meta_path is not None:
        result["run_meta"] = (
            load_json(
                run_meta_path
            )
        )

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Score Track K engine outputs "
            "using the conformance harness."
        )
    )

    parser.add_argument(
        "--corpus",
        required=True,
        help=(
            "Directory containing "
            "original DOCX files."
        ),
    )

    parser.add_argument(
        "--outputs",
        required=True,
        help=(
            "Directory containing "
            "engine output DOCX files."
        ),
    )

    parser.add_argument(
        "--manifest",
        help=(
            "Manifest file. Defaults to "
            "<corpus>/manifest.json."
        ),
    )

    parser.add_argument(
        "--run-meta",
        help=(
            "Optional run_meta.json "
            "to embed in scores.json."
        ),
    )

    parser.add_argument(
        "--out",
        required=True,
        help=(
            "Where to write scores.json."
        ),
    )

    args = parser.parse_args()

    corpus_dir = Path(
        args.corpus
    )

    outputs_dir = Path(
        args.outputs
    )

    if args.manifest:
        manifest_path = Path(
            args.manifest
        )
    else:
        manifest_path = (
            corpus_dir
            / "manifest.json"
        )

    run_meta_path = (
        Path(args.run_meta)
        if args.run_meta
        else None
    )

    try:
        result = score(
            corpus_dir=corpus_dir,
            outputs_dir=outputs_dir,
            manifest_path=(
                manifest_path
            ),
            run_meta_path=(
                run_meta_path
            ),
        )

    except Exception as exc:
        print(
            "ERROR: "
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        return 1

    write_json(
        Path(args.out),
        result,
    )

    aggregate = result[
        "aggregate"
    ]

    print(
        "Track K scoring complete."
    )

    print(
        "Documents scored: "
        f"{aggregate['documents_scored']}/"
        f"{aggregate['documents_total']}"
    )

    print(
        "Conformance: "
        f"{aggregate['overall']['conformance']}"
    )

    print(
        "Hard preservation failures: "
        f"{aggregate['hard_preservation_failures']}"
    )

    print(
        "Injected defect fix rate: "
        f"{aggregate['injected_defects']['fix_rate']}"
    )

    print(
        f"Scores: {args.out}"
    )

    if aggregate[
        "documents_error"
    ]:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )