"""Track K conformance harness.

This file handles the command-line interface and combines the results
from the corpus checks.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from lxml import etree

from tools.corpus.docx_view import accepted_view

from tools.corpus.checks.layout import (
    CHECKS as LAYOUT_CHECKS,
    check_layout,
)
from tools.corpus.checks.fonts import check_fonts
from tools.corpus.checks.headings import check_headings
from tools.corpus.checks.abstract import check_abstract
from tools.corpus.checks.refs import check_references
from tools.corpus.checks.preservation import check_preservation


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


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
    "preservation",
)


def result(
    check: str,
    status: str,
    evidence: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a result for checks owned by the harness."""

    output = {
        "check": check,
        "status": status,
        "evidence": evidence,
    }

    if details is not None:
        output["details"] = details

    return output


def parse_xml(data: bytes, part_name: str):
    """Parse XML and give a useful error if it is invalid."""

    try:
        return etree.fromstring(data)

    except etree.XMLSyntaxError as exc:
        raise ValueError(
            f"Invalid XML in {part_name}: {exc}"
        ) from exc


def check_validity(docx_path: Path) -> dict[str, Any]:
    """Basic DOCX and XML validity check."""

    if not docx_path.exists():
        return result(
            "validity",
            "fail",
            f"File does not exist: {docx_path}",
        )

    if not zipfile.is_zipfile(docx_path):
        return result(
            "validity",
            "fail",
            "File is not a valid DOCX/ZIP file.",
        )

    try:
        with zipfile.ZipFile(docx_path, "r") as archive:
            members = archive.namelist()

            required = {
                "[Content_Types].xml",
                "word/document.xml",
            }

            missing = sorted(
                required - set(members)
            )

            if missing:
                return result(
                    "validity",
                    "fail",
                    f"Missing required files: {missing}",
                )

            bad_member = archive.testzip()

            if bad_member is not None:
                return result(
                    "validity",
                    "fail",
                    f"Corrupt ZIP member: {bad_member}",
                )

            xml_parts = [
                name
                for name in members
                if name.endswith(".xml")
                or name.endswith(".rels")
            ]

            for part_name in xml_parts:
                parse_xml(
                    archive.read(part_name),
                    part_name,
                )

            root = parse_xml(
                archive.read("word/document.xml"),
                "word/document.xml",
            )

            expected_root = f"{{{W_NS}}}document"

            if root.tag != expected_root:
                return result(
                    "validity",
                    "fail",
                    "word/document.xml does not use a w:document root.",
                )

            ids = root.xpath(
                "//@w:id",
                namespaces=NS,
            )

            counts = Counter(ids)

            duplicate_ids = {
                value: count
                for value, count in counts.items()
                if count > 1
            }

            duplicate_count = sum(
                count - 1
                for count in duplicate_ids.values()
            )

            return result(
                "validity",
                "pass",
                "DOCX container and XML are valid.",
                {
                    "xml_parts_checked": len(xml_parts),
                    "duplicate_w_id_count": duplicate_count,
                    "duplicate_w_ids": duplicate_ids,
                },
            )

    except Exception as exc:
        return result(
            "validity",
            "fail",
            str(exc),
        )


def run_harness(
    docx_path: Path,
    selected_checks: list[str],
    *,
    input_docx: Path | None = None,
    check_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the selected corpus checks and combine their results."""

    check_results: dict[str, Any] = {}

    if check_options is None:
        check_options = {}

    # Validity is owned by harness.py and can run before AcceptedView.
    if "validity" in selected_checks:
        validity = check_validity(docx_path)
        check_results["validity"] = validity

        # Stop here if the file itself is invalid.
        if validity["status"] == "fail":
            return {
                "schema_version": 1,
                "document": str(docx_path),
                "accepted_view": {
                    "available": False,
                    "reason": "validity check failed",
                },
                "checks": check_results,
            }

    # All resolver-based checks use the same accepted view.
    try:
        view = accepted_view(docx_path)

    except Exception as exc:
        return {
            "schema_version": 1,
            "document": str(docx_path),
            "accepted_view": {
                "available": False,
                "error": str(exc),
            },
            "checks": check_results,
        }

    # APA-00, APA-01, APA-03, APA-04 and APA-05.
    layout_names = [
        name
        for name in selected_checks
        if name in LAYOUT_CHECKS
    ]

    if layout_names:
        check_results.update(
            check_layout(
                view,
                checks=layout_names,
            )
        )

    # APA-02.
    if "fonts" in selected_checks:
        font_result = check_fonts(view)

        check_results[
            font_result["matrix_id"]
        ] = font_result

    # APA-10 and APA-11.
    if "headings" in selected_checks:
        check_results.update(
            check_headings(view)
        )

    # APA-08 and APA-09.
    if "abstract" in selected_checks:
        abstract_options = check_options.get(
            "APA-08",
            {},
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
                require_abstract=require_abstract,
            )
        )

    # APA-12 and APA-18.
    if "refs" in selected_checks:
        check_results.update(
            check_references(view)
        )

    # K-H9 preservation hard flag.
    if "preservation" in selected_checks:
        if input_docx is None:
            raise ValueError(
                "preservation check requires input_docx"
            )

        preservation_result = check_preservation(
            docx_path,
            input_docx,
        )

        check_results[
            "preservation"
        ] = preservation_result

    return {
        "schema_version": 1,
        "document": str(docx_path),
        "accepted_view": {
            "available": True,
            "result_type": type(view).__name__,
        },
        "checks": check_results,
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
        print(rendered)
        return

    output_path = Path(output)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        rendered + "\n",
        encoding="utf-8",
    )

    print(
        f"Wrote harness report: {output_path}"
    )


def parse_checks(value: str) -> list[str]:
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
            + ", ".join(unknown)
        )

    return checks


def report_has_failure(report: dict[str, Any]) -> bool:
    """Return True if any harness result failed."""

    for item in report["checks"].values():
        if (
            isinstance(item, dict)
            and item.get("status") == "fail"
        ):
            return True

    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run Track K conformance checks "
            "on a DOCX file."
        )
    )

    parser.add_argument(
        "--docx",
        required=True,
        help=(
            "DOCX file to check. For preservation this is "
            "the engine output DOCX."
        ),
    )

    parser.add_argument(
        "--input",
        help=(
            "Original input DOCX. Required when "
            "running the preservation check."
        ),
    )

    group = parser.add_mutually_exclusive_group(
        required=True
    )

    group.add_argument(
        "--checks",
        type=parse_checks,
        help=(
            "Comma-separated checks, for example "
            "margins,spacing,align,indent,pagenum,"
            "fonts,headings,abstract,refs"
        ),
    )

    group.add_argument(
        "--all",
        action="store_true",
        help=(
            "Run all available document checks. "
            "Preservation is also run when --input is supplied."
        ),
    )

    parser.add_argument(
        "--require-abstract",
        action="store_true",
        help=(
            "A missing abstract fails APA-08 "
            "instead of returning na."
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

    docx_path = Path(args.docx)

    input_docx = (
        Path(args.input)
        if args.input
        else None
    )

    if args.all:
        # --all can still be used on a single document.
        # Preservation needs both an input and output file.
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
        selected_checks = args.checks

    if (
        "preservation" in selected_checks
        and input_docx is None
    ):
        parser.error(
            "--input is required when running "
            "the preservation check"
        )

    check_options: dict[str, Any] = {}

    if args.require_abstract:
        check_options["APA-08"] = {
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

    if report_has_failure(report):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())