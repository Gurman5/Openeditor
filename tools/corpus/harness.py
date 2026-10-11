"""Track K conformance harness.

This file handles the command-line interface and combines the results
from the Track K corpus checks.

It is the Person A orchestration layer. Individual conformance checks
remain in tools/corpus/checks/.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tools.corpus.docx_view import (
    accepted_view,
    check_validity as check_docx_validity,
)

from tools.corpus.checks.layout import (
    CHECKS as LAYOUT_CHECKS,
    check_layout,
)
from tools.corpus.checks.fonts import check_fonts
from tools.corpus.checks.headings import check_headings
from tools.corpus.checks.abstract import check_abstract
from tools.corpus.checks.refs import check_references
from tools.corpus.checks.residue import check_residue
from tools.corpus.checks.appendices import check_appendices
from tools.corpus.checks.preservation import check_preservation


# Checks that can be selected from the command line.
AVAILABLE_CHECKS = (
    "validity",
    "margins",
    "spacing",
    "align",
    "indent",
    "pagenum",
    "fonts",
    "headings",
    "abstract",
    "refs",
    "residue",
    "appendices",
    "preservation",
)


# Checks that need the AcceptedView / style resolver.
VIEW_CHECKS = {
    "margins",
    "spacing",
    "align",
    "indent",
    "pagenum",
    "fonts",
    "headings",
    "abstract",
    "refs",
}


def result(
    check: str,
    status: str,
    evidence: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standard harness result."""

    output: dict[str, Any] = {
        "check": check,
        "status": status,
        "evidence": evidence,
    }

    if details is not None:
        output["details"] = details

    return output


def check_validity(
    docx_path: Path | str,
) -> dict[str, Any]:
    """
    Run Zac's K-H1 validity implementation and adapt its output to the
    common harness result format.

    Duplicate revision w:id values are reported but do not by themselves
    make the DOCX invalid.
    """

    raw = check_docx_validity(
        docx_path
    )

    valid = bool(
        raw.get("valid")
    )

    reasons = (
        raw.get("reasons")
        or []
    )

    duplicate_count = int(
        raw.get(
            "duplicate_id_count",
            0,
        )
        or 0
    )

    duplicate_ids = (
        raw.get(
            "duplicate_ids"
        )
        or {}
    )

    if valid:
        evidence = (
            "DOCX container and XML "
            "are valid."
        )
    else:
        evidence = (
            "; ".join(
                str(reason)
                for reason in reasons
            )
            if reasons
            else "DOCX validity check failed."
        )

    return result(
        "validity",
        "pass" if valid else "fail",
        evidence,
        {
            "path": raw.get(
                "path",
                str(docx_path),
            ),

            # Names used by the Track K scoring/reporting side.
            "duplicate_w_id_count": (
                duplicate_count
            ),
            "duplicate_w_ids": (
                duplicate_ids
            ),

            # Keep the original K-H1 names as well.
            "duplicate_id_count": (
                duplicate_count
            ),
            "duplicate_ids": (
                duplicate_ids
            ),

            "reasons": reasons,
        },
    )


def validate_selected_checks(
    selected_checks: list[str],
) -> None:
    """Raise if a programmatic caller supplied an unknown check."""

    unknown = [
        name
        for name in selected_checks
        if name not in AVAILABLE_CHECKS
    ]

    if unknown:
        raise ValueError(
            "Unknown check(s): "
            + ", ".join(
                unknown
            )
        )


def run_harness(
    docx_path: Path | str,
    selected_checks: list[str],
    *,
    input_docx: Path | str | None = None,
    check_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run selected Track K checks and combine their results.

    Parameters
    ----------
    docx_path:
        Document being graded. For a pipeline run this is the engine
        output DOCX.

    selected_checks:
        Names from AVAILABLE_CHECKS.

    input_docx:
        Original input document. Required for preservation and used by
        residue/appendix preservation checks.

    check_options:
        Per-matrix-row options supplied by corpus/injector metadata.

        Example:

            {
                "APA-08": {
                    "require_abstract": True
                }
            }

    Returns
    -------
    A JSON-safe dictionary containing all check results.
    """

    docx_path = Path(
        docx_path
    )

    if input_docx is not None:
        input_docx = Path(
            input_docx
        )

    validate_selected_checks(
        selected_checks
    )

    if check_options is None:
        check_options = {}

    if not isinstance(
        check_options,
        dict,
    ):
        raise ValueError(
            "check_options must be a dictionary"
        )

    check_results: dict[str, Any] = {}

    # --------------------------------------------------------------
    # K-H1 validity
    # --------------------------------------------------------------

    if "validity" in selected_checks:
        validity = check_validity(
            docx_path
        )

        check_results[
            "validity"
        ] = validity

        # No other output checks are reliable when the DOCX itself
        # cannot be parsed.
        if (
            validity["status"]
            == "fail"
        ):
            return {
                "schema_version": 1,
                "document": str(
                    docx_path
                ),
                "input_document": (
                    str(input_docx)
                    if input_docx
                    is not None
                    else None
                ),
                "accepted_view": {
                    "available": False,
                    "reason": (
                        "validity check failed"
                    ),
                },
                "check_options": (
                    check_options
                ),
                "checks": (
                    check_results
                ),
            }

    # --------------------------------------------------------------
    # Build the AcceptedView once for all resolver-based checks.
    # --------------------------------------------------------------

    needs_view = any(
        name in VIEW_CHECKS
        for name in selected_checks
    )

    view = None

    if needs_view:
        try:
            view = accepted_view(
                docx_path
            )

        except Exception as exc:
            return {
                "schema_version": 1,
                "document": str(
                    docx_path
                ),
                "input_document": (
                    str(input_docx)
                    if input_docx
                    is not None
                    else None
                ),
                "accepted_view": {
                    "available": False,
                    "error": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                },
                "check_options": (
                    check_options
                ),
                "checks": (
                    check_results
                ),
            }

    # --------------------------------------------------------------
    # K-H2
    # APA-00 margins
    # APA-01 spacing
    # APA-03 alignment
    # APA-04 indentation
    # APA-05 page numbers
    # --------------------------------------------------------------

    layout_names = [
        name
        for name in selected_checks
        if name in LAYOUT_CHECKS
    ]

    if layout_names:
        if view is None:
            raise RuntimeError(
                "AcceptedView was not created "
                "for layout checks."
            )

        check_results.update(
            check_layout(
                view,
                checks=layout_names,
            )
        )

    # --------------------------------------------------------------
    # K-H3
    # APA-02 fonts
    # --------------------------------------------------------------

    if "fonts" in selected_checks:
        if view is None:
            raise RuntimeError(
                "AcceptedView was not created "
                "for font checks."
            )

        font_result = check_fonts(
            view
        )

        check_results[
            font_result["matrix_id"]
        ] = font_result

    # --------------------------------------------------------------
    # K-H4
    # APA-10 / APA-11 headings
    # --------------------------------------------------------------

    if "headings" in selected_checks:
        if view is None:
            raise RuntimeError(
                "AcceptedView was not created "
                "for heading checks."
            )

        check_results.update(
            check_headings(
                view
            )
        )

    # --------------------------------------------------------------
    # K-H6
    # APA-08 abstract / APA-09 keywords
    #
    # APA-08c injector rows can set:
    #
    # {
    #     "APA-08": {
    #         "require_abstract": true
    #     }
    # }
    #
    # Professional-mode documents also use this option through score.py.
    # --------------------------------------------------------------

    if "abstract" in selected_checks:
        if view is None:
            raise RuntimeError(
                "AcceptedView was not created "
                "for abstract checks."
            )

        abstract_options = (
            check_options.get(
                "APA-08",
                {},
            )
        )

        if abstract_options is None:
            abstract_options = {}

        if not isinstance(
            abstract_options,
            dict,
        ):
            raise ValueError(
                "check_options['APA-08'] "
                "must be a dictionary"
            )

        require_abstract = bool(
            abstract_options.get(
                "require_abstract",
                False,
            )
        )

        check_results.update(
            check_abstract(
                view,
                require_abstract=(
                    require_abstract
                ),
            )
        )

    # --------------------------------------------------------------
    # K-H5
    # APA-12 references / APA-18 DOI format
    # --------------------------------------------------------------

    if "refs" in selected_checks:
        if view is None:
            raise RuntimeError(
                "AcceptedView was not created "
                "for reference checks."
            )

        check_results.update(
            check_references(
                view
            )
        )

    # --------------------------------------------------------------
    # K-H7
    # JUTLP residue.
    #
    # The check returns NA when the original input already contains
    # residue, because in that situation the engine did not necessarily
    # introduce it.
    # --------------------------------------------------------------

    if "residue" in selected_checks:
        check_results[
            "residue"
        ] = check_residue(
            docx_path,
            input_docx,
        )

    # --------------------------------------------------------------
    # K-H8
    # Appendix preservation.
    #
    # The check returns NA when the original input has no Appendix.
    # --------------------------------------------------------------

    if "appendices" in selected_checks:
        check_results[
            "appendices"
        ] = check_appendices(
            docx_path,
            input_docx,
        )

    # --------------------------------------------------------------
    # K-H9
    # Hard text-preservation flag.
    # --------------------------------------------------------------

    if "preservation" in selected_checks:
        if input_docx is None:
            raise ValueError(
                "preservation check "
                "requires input_docx"
            )

        preservation_result = (
            check_preservation(
                docx_path,
                input_docx,
            )
        )

        check_results[
            "preservation"
        ] = preservation_result

    return {
        "schema_version": 1,
        "document": str(
            docx_path
        ),
        "input_document": (
            str(input_docx)
            if input_docx is not None
            else None
        ),
        "accepted_view": {
            "available": (
                view is not None
                if needs_view
                else True
            ),
            "result_type": (
                type(view).__name__
                if view is not None
                else None
            ),
        },
        "check_options": (
            check_options
        ),
        "checks": (
            check_results
        ),
    }


def write_report(
    report: dict[str, Any],
    output: str,
) -> None:
    """Write the harness report to stdout or a JSON file."""

    rendered = json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
    )

    if output == "-":
        print(
            rendered
        )
        return

    output_path = Path(
        output
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        rendered + "\n",
        encoding="utf-8",
    )

    print(
        "Wrote harness report: "
        f"{output_path}"
    )


def parse_checks(
    value: str,
) -> list[str]:
    """Parse the comma-separated --checks argument."""

    checks = [
        item.strip().lower()
        for item in value.split(",")
        if item.strip()
    ]

    unknown = [
        item
        for item in checks
        if item not in AVAILABLE_CHECKS
    ]

    if unknown:
        raise argparse.ArgumentTypeError(
            "Unknown check(s): "
            + ", ".join(
                unknown
            )
        )

    return checks


def report_has_failure(
    report: dict[str, Any],
) -> bool:
    """Return True if any harness result failed."""

    for item in (
        report.get(
            "checks",
            {}
        ).values()
    ):
        if (
            isinstance(
                item,
                dict,
            )
            and item.get(
                "status"
            )
            == "fail"
        ):
            return True

    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run Track K conformance "
            "checks on a DOCX file."
        )
    )

    parser.add_argument(
        "--docx",
        required=True,
        help=(
            "DOCX file to check. "
            "For comparison checks this "
            "is the engine output DOCX."
        ),
    )

    parser.add_argument(
        "--input",
        help=(
            "Original input DOCX. "
            "Required for preservation; "
            "also used by residue and "
            "appendix checks."
        ),
    )

    group = (
        parser.add_mutually_exclusive_group(
            required=True
        )
    )

    group.add_argument(
        "--checks",
        type=parse_checks,
        help=(
            "Comma-separated checks. "
            "Choices: "
            + ",".join(
                AVAILABLE_CHECKS
            )
        ),
    )

    group.add_argument(
        "--all",
        action="store_true",
        help=(
            "Run all available checks. "
            "Preservation is included "
            "when --input is supplied."
        ),
    )

    parser.add_argument(
        "--require-abstract",
        action="store_true",
        help=(
            "A missing abstract fails "
            "APA-08 instead of returning na."
        ),
    )

    parser.add_argument(
        "--out",
        default="-",
        help=(
            "JSON output file, or '-' "
            "to print to the terminal."
        ),
    )

    args = parser.parse_args()

    docx_path = Path(
        args.docx
    )

    input_docx = (
        Path(
            args.input
        )
        if args.input
        else None
    )

    if args.all:
        selected_checks = [
            name
            for name in AVAILABLE_CHECKS
            if name != "preservation"
        ]

        if input_docx is not None:
            selected_checks.append(
                "preservation"
            )

    else:
        selected_checks = (
            args.checks
        )

    if (
        "preservation"
        in selected_checks
        and input_docx is None
    ):
        parser.error(
            "--input is required when "
            "running the preservation check"
        )

    check_options: dict[
        str,
        Any,
    ] = {}

    if args.require_abstract:
        check_options[
            "APA-08"
        ] = {
            "require_abstract": True,
        }

    report = run_harness(
        docx_path,
        selected_checks,
        input_docx=input_docx,
        check_options=check_options,
    )

    write_report(
        report,
        args.out,
    )

    if report_has_failure(
        report
    ):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )