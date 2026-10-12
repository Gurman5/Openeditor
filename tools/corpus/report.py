"""Track K K-0.5b Markdown report generator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(
    path: Path,
) -> dict[str, Any]:

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            f"{path}: JSON root "
            "must be an object"
        )

    return data


def percent(
    value: float | None,
) -> str:

    if value is None:
        return "n/a"

    return (
        f"{value * 100:.1f}%"
    )


def table(
    headers: list[str],
    rows: list[list[Any]],
) -> list[str]:

    lines = [
        "| "
        + " | ".join(headers)
        + " |",

        "| "
        + " | ".join(
            "---"
            for _ in headers
        )
        + " |",
    ]

    for row in rows:

        values = [
            str(value).replace(
                "|",
                r"\|",
            )
            for value in row
        ]

        lines.append(
            "| "
            + " | ".join(values)
            + " |"
        )

    return lines


def render(
    scores: dict[str, Any],
) -> str:

    aggregate = (
        scores.get(
            "aggregate"
        )
        or {}
    )

    overall = (
        aggregate.get(
            "overall"
        )
        or {}
    )

    injected = (
        aggregate.get(
            "injected_defects"
        )
        or {}
    )

    lines = [
        "# Track K Conformance Report",
        "",
        (
            f"- Corpus: "
            f"`{scores.get('corpus', '')}`"
        ),
        (
            f"- Outputs: "
            f"`{scores.get('outputs', '')}`"
        ),
        (
            f"- Manifest: "
            f"`{scores.get('manifest', '')}`"
        ),
        (
            f"- Created: "
            f"`{scores.get('created_at', '')}`"
        ),
        "",
        "## Overall",
        "",
        (
            "- Documents scored: "
            f"**{aggregate.get('documents_scored', 0)}"
            "/"
            f"{aggregate.get('documents_total', 0)}**"
        ),
        (
            "- Scoring errors: "
            f"**{aggregate.get('documents_error', 0)}**"
        ),
        (
            "- APA passes: "
            f"**{overall.get('pass', 0)}**"
        ),
        (
            "- APA failures: "
            f"**{overall.get('fail', 0)}**"
        ),
        (
            "- APA NA: "
            f"**{overall.get('na', 0)}**"
        ),
        (
            "- Conformance: "
            f"**{percent(overall.get('conformance'))}**"
        ),
        (
            "- Hard preservation failures: "
            f"**{aggregate.get('hard_preservation_failures', 0)}**"
        ),
        (
            "- Validity failures: "
            f"**{aggregate.get('validity_failures', 0)}**"
        ),
        (
            "- Duplicate w:id count: "
            f"**{aggregate.get('duplicate_w_id_count', 0)}**"
        ),
        (
            "- Residue failures: "
            f"**{aggregate.get('residue_failures', 0)}**"
        ),
        (
            "- Appendix preservation failures: "
            f"**{aggregate.get('appendix_failures', 0)}**"
        ),
        "",
        "## Injected Defects",
        "",
        (
            "- Defects scored: "
            f"**{injected.get('total', 0)}**"
        ),
        (
            "- Defects fixed: "
            f"**{injected.get('fixed', 0)}**"
        ),
        (
            "- Defect-fix rate: "
            f"**{percent(injected.get('fix_rate'))}**"
        ),
        "",
        "## Matrix Summary",
        "",
    ]

    matrix_rows = []

    matrix = (
        aggregate.get(
            "matrix"
        )
        or {}
    )

    for (
        matrix_id,
        row,
    ) in sorted(
        matrix.items()
    ):

        matrix_rows.append(
            [
                matrix_id,
                row.get(
                    "pass",
                    0,
                ),
                row.get(
                    "fail",
                    0,
                ),
                row.get(
                    "na",
                    0,
                ),
                percent(
                    row.get(
                        "conformance"
                    )
                ),
            ]
        )

    if matrix_rows:

        lines.extend(
            table(
                [
                    "Matrix row",
                    "Pass",
                    "Fail",
                    "NA",
                    "Conformance",
                ],
                matrix_rows,
            )
        )

    else:
        lines.append(
            "_No APA matrix rows "
            "were scored._"
        )

    lines.extend(
        [
            "",
            "## Per-document Results",
            "",
        ]
    )

    document_rows = []

    documents = (
        scores.get(
            "documents"
        )
        or []
    )

    for document in documents:

        counts = (
            document.get(
                "counts"
            )
            or {}
        )

        document_rows.append(
            [
                document.get(
                    "document_id",
                    "",
                ),
                document.get(
                    "mode"
                )
                or "",
                document.get(
                    "status",
                    "",
                ),
                counts.get(
                    "pass",
                    0,
                ),
                counts.get(
                    "fail",
                    0,
                ),
                counts.get(
                    "na",
                    0,
                ),
                percent(
                    document.get(
                        "conformance"
                    )
                ),
                (
                    "YES"
                    if document.get(
                        "preservation_hard_flag"
                    )
                    else "no"
                ),
                document.get(
                    "duplicate_w_id_count",
                    0,
                ),
            ]
        )

    if document_rows:

        lines.extend(
            table(
                [
                    "Document",
                    "Mode",
                    "Status",
                    "Pass",
                    "Fail",
                    "NA",
                    "Conformance",
                    "Preservation flag",
                    "Duplicate w:id",
                ],
                document_rows,
            )
        )

    else:
        lines.append(
            "_No documents were scored._"
        )

    injected_rows = []

    for document in documents:

        injected_info = (
            document.get(
                "injected"
            )
            or {}
        )

        recipe_ids = ", ".join(
            injected_info.get(
                "recipe_ids"
            )
            or []
        )

        for target in (
            injected_info.get(
                "targets"
            )
            or []
        ):

            injected_rows.append(
                [
                    document.get(
                        "document_id",
                        "",
                    ),
                    recipe_ids,
                    target.get(
                        "matrix_id",
                        "",
                    ),
                    target.get(
                        "output_status",
                        "",
                    ),
                    (
                        "YES"
                        if target.get(
                            "fixed"
                        )
                        else "no"
                    ),
                ]
            )

    if injected_rows:

        lines.extend(
            [
                "",
                "## Injected Defect Detail",
                "",
            ]
        )

        lines.extend(
            table(
                [
                    "Document",
                    "Recipe",
                    "Matrix row",
                    "Output status",
                    "Fixed",
                ],
                injected_rows,
            )
        )

    lines.extend(
        [
            "",
            "## Failures Requiring Review",
            "",
        ]
    )

    failures_found = False

    for document in documents:

        failures = []

        if (
            document.get(
                "status"
            )
            == "error"
        ):
            failures.append(
                "scoring error: "
                + str(
                    document.get(
                        "error"
                    )
                )
            )

        checks = (
            document.get(
                "checks"
            )
            or {}
        )

        for (
            name,
            check,
        ) in checks.items():

            if (
                isinstance(
                    check,
                    dict,
                )
                and check.get(
                    "status"
                )
                == "fail"
            ):
                failures.append(
                    name
                )

        if failures:

            failures_found = True

            lines.append(
                "- **"
                + str(
                    document.get(
                        "document_id",
                        ""
                    )
                )
                + "**: "
                + ", ".join(
                    failures
                )
            )

    if not failures_found:

        lines.append(
            "_No failed checks "
            "were recorded._"
        )

    run_meta = scores.get(
        "run_meta"
    )

    if isinstance(
        run_meta,
        dict,
    ):

        git = (
            run_meta.get(
                "git"
            )
            or {}
        )

        llm = (
            run_meta.get(
                "llm"
            )
            or {}
        )

        lines.extend(
            [
                "",
                "## Run Metadata",
                "",
                (
                    "- Git commit: "
                    f"`{git.get('commit', '')}`"
                ),
                (
                    "- Git branch: "
                    f"`{git.get('branch', '')}`"
                ),
                (
                    "- LLM mode: "
                    f"`{llm.get('mode', '')}`"
                ),
                (
                    "- Environment API key active: "
                    f"`{llm.get('env_api_key_set')}`"
                ),
                (
                    "- llm_client API key active: "
                    f"`{llm.get('client_api_key_set')}`"
                ),
            ]
        )

    return (
        "\n".join(lines)
        + "\n"
    )


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Generate the Track K "
            "Markdown score report."
        )
    )

    parser.add_argument(
        "--scores",
        required=True,
        help=(
            "Path to scores.json."
        ),
    )

    parser.add_argument(
        "--out",
        required=True,
        help=(
            "Output Markdown file."
        ),
    )

    args = parser.parse_args()

    try:

        scores = load_json(
            Path(
                args.scores
            )
        )

        rendered = render(
            scores
        )

    except Exception as exc:

        print(
            "ERROR: "
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        return 1

    output = Path(
        args.out
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        rendered,
        encoding="utf-8",
    )

    print(
        "Wrote Track K report: "
        f"{output}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )