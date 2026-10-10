"""Track K conformance harness.

This file handles the command-line interface and combines the results
from the corpus checks.

Some checks currently use direct OOXML values as a temporary fallback.
Zac's accepted-view and style resolver will be connected later.
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


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

AVAILABLE_CHECKS = (
    "validity",
    "margins",
    "spacing",
    "align",
    "indent",
    "pagenum",
)


def w_attr(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def result(
    check: str,
    status: str,
    evidence: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output = {
        "check": check,
        "status": status,
        "evidence": evidence,
    }

    if details is not None:
        output["details"] = details

    return output


def parse_xml(data: bytes, part_name: str):
    try:
        return etree.fromstring(data)
    except etree.XMLSyntaxError as exc:
        raise ValueError(
            f"Invalid XML in {part_name}: {exc}"
        ) from exc


def read_document_xml(docx_path: Path):
    with zipfile.ZipFile(docx_path, "r") as archive:
        if "word/document.xml" not in archive.namelist():
            raise ValueError("word/document.xml is missing")

        return parse_xml(
            archive.read("word/document.xml"),
            "word/document.xml",
        )


def get_body_paragraphs(root):
    paragraphs = []

    for paragraph in root.xpath(
        "//w:body//w:p",
        namespaces=NS,
    ):
        text = "".join(
            paragraph.xpath(
                ".//w:t/text()",
                namespaces=NS,
            )
        ).strip()

        if text:
            paragraphs.append(paragraph)

    return paragraphs


def check_validity(docx_path: Path):
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


def check_margins(docx_path: Path):
    """Check that section margins are 1 inch / 1440 twips."""

    try:
        root = read_document_xml(docx_path)
    except Exception as exc:
        return result(
            "margins",
            "fail",
            str(exc),
        )

    sections = root.xpath(
        "//w:sectPr",
        namespaces=NS,
    )

    if not sections:
        return result(
            "margins",
            "fail",
            "No section properties were found.",
        )

    problems = []

    for number, section in enumerate(
        sections,
        start=1,
    ):
        margins = section.find(
            "w:pgMar",
            namespaces=NS,
        )

        if margins is None:
            problems.append(
                {
                    "section": number,
                    "problem": "w:pgMar missing",
                }
            )
            continue

        for side in (
            "top",
            "bottom",
            "left",
            "right",
        ):
            actual = margins.get(
                w_attr(side)
            )

            if actual != "1440":
                problems.append(
                    {
                        "section": number,
                        "side": side,
                        "expected": "1440",
                        "actual": actual,
                    }
                )

    if problems:
        return result(
            "margins",
            "fail",
            "One or more margins are not 1440 twips.",
            {
                "mode": "direct-ooxml",
                "problems": problems,
            },
        )

    return result(
        "margins",
        "pass",
        f"All {len(sections)} section(s) use 1440 twip margins.",
        {
            "mode": "direct-ooxml",
        },
    )


def check_spacing(docx_path: Path):
    """Temporary direct-only double-spacing check."""

    try:
        root = read_document_xml(docx_path)
    except Exception as exc:
        return result(
            "spacing",
            "fail",
            str(exc),
        )

    paragraphs = get_body_paragraphs(root)

    checked = 0
    problems = []

    for number, paragraph in enumerate(
        paragraphs,
        start=1,
    ):
        spacing = paragraph.find(
            "./w:pPr/w:spacing",
            namespaces=NS,
        )

        if spacing is None:
            continue

        line = spacing.get(
            w_attr("line")
        )

        line_rule = spacing.get(
            w_attr("lineRule")
        )

        if line is None:
            continue

        checked += 1

        if (
            line != "480"
            or line_rule not in (None, "auto")
        ):
            problems.append(
                {
                    "paragraph": number,
                    "expected_line": "480",
                    "actual_line": line,
                    "line_rule": line_rule,
                }
            )

    if problems:
        return result(
            "spacing",
            "fail",
            "Incorrect direct paragraph spacing was found.",
            {
                "mode": "direct-only",
                "problems": problems,
            },
        )

    if checked == 0:
        return result(
            "spacing",
            "na",
            (
                "No direct spacing values were found. "
                "The style resolver is needed for inherited spacing."
            ),
            {
                "mode": "direct-only",
            },
        )

    return result(
        "spacing",
        "pass",
        f"{checked} direct spacing value(s) use line=480.",
        {
            "mode": "direct-only",
        },
    )


def check_alignment(docx_path: Path):
    """Check for directly justified body paragraphs."""

    try:
        root = read_document_xml(docx_path)
    except Exception as exc:
        return result(
            "align",
            "fail",
            str(exc),
        )

    paragraphs = get_body_paragraphs(root)

    problems = []

    for number, paragraph in enumerate(
        paragraphs,
        start=1,
    ):
        alignment = paragraph.find(
            "./w:pPr/w:jc",
            namespaces=NS,
        )

        if alignment is None:
            continue

        value = alignment.get(
            w_attr("val")
        )

        if value == "both":
            problems.append(
                {
                    "paragraph": number,
                    "actual": value,
                }
            )

    if problems:
        return result(
            "align",
            "fail",
            "Justified body paragraph(s) were found.",
            {
                "mode": "direct-only",
                "problems": problems,
            },
        )

    return result(
        "align",
        "pass",
        "No directly justified body paragraphs were found.",
        {
            "mode": "direct-only",
            "note": (
                "Inherited alignment will be checked "
                "with the style resolver later."
            ),
        },
    )


def check_indent(docx_path: Path):
    """Temporary direct-only first-line indent check."""

    try:
        root = read_document_xml(docx_path)
    except Exception as exc:
        return result(
            "indent",
            "fail",
            str(exc),
        )

    paragraphs = get_body_paragraphs(root)

    checked = 0
    problems = []

    for number, paragraph in enumerate(
        paragraphs,
        start=1,
    ):
        indent = paragraph.find(
            "./w:pPr/w:ind",
            namespaces=NS,
        )

        if indent is None:
            continue

        first_line = indent.get(
            w_attr("firstLine")
        )

        if first_line is None:
            continue

        checked += 1

        if first_line != "720":
            problems.append(
                {
                    "paragraph": number,
                    "expected": "720",
                    "actual": first_line,
                }
            )

    if problems:
        return result(
            "indent",
            "fail",
            "Incorrect direct first-line indentation was found.",
            {
                "mode": "direct-only",
                "problems": problems,
            },
        )

    if checked == 0:
        return result(
            "indent",
            "na",
            (
                "No direct first-line indent values were found. "
                "The style resolver is needed for inherited indentation."
            ),
            {
                "mode": "direct-only",
            },
        )

    return result(
        "indent",
        "pass",
        f"{checked} first-line indent value(s) use 720 twips.",
        {
            "mode": "direct-only",
        },
    )


def check_page_number(docx_path: Path):
    """Look for a PAGE field in DOCX header XML."""

    if not zipfile.is_zipfile(docx_path):
        return result(
            "pagenum",
            "fail",
            "File is not a valid DOCX/ZIP file.",
        )

    try:
        with zipfile.ZipFile(
            docx_path,
            "r",
        ) as archive:

            headers = sorted(
                name
                for name in archive.namelist()
                if name.startswith("word/header")
                and name.endswith(".xml")
            )

            if not headers:
                return result(
                    "pagenum",
                    "fail",
                    "No header XML files were found.",
                )

            matches = []

            for header_name in headers:
                root = parse_xml(
                    archive.read(header_name),
                    header_name,
                )

                # Simple PAGE fields
                fields = root.xpath(
                    ".//w:fldSimple",
                    namespaces=NS,
                )

                for field in fields:
                    instruction = field.get(
                        w_attr("instr"),
                        "",
                    )

                    if "PAGE" in instruction.upper():
                        matches.append(
                            f"{header_name}: fldSimple PAGE"
                        )

                # PAGE fields made from fldChar/instrText runs
                instructions = " ".join(
                    root.xpath(
                        ".//w:instrText/text()",
                        namespaces=NS,
                    )
                )

                if "PAGE" in instructions.upper():
                    matches.append(
                        f"{header_name}: instrText PAGE"
                    )

            if not matches:
                return result(
                    "pagenum",
                    "fail",
                    "No PAGE field was found in the headers.",
                    {
                        "headers_checked": headers,
                    },
                )

            return result(
                "pagenum",
                "pass",
                "A PAGE field was found in a header.",
                {
                    "matches": matches,
                },
            )

    except Exception as exc:
        return result(
            "pagenum",
            "fail",
            str(exc),
        )


CHECK_FUNCTIONS = {
    "validity": check_validity,
    "margins": check_margins,
    "spacing": check_spacing,
    "align": check_alignment,
    "indent": check_indent,
    "pagenum": check_page_number,
}


def accepted_view_status(docx_path: Path):
    """
    Connect to Zac's docx_view module when it is available.

    This does not implement Zac's accepted-view logic here.
    """

    try:
        from tools.corpus.docx_view import accepted_view
    except ImportError:
        return {
            "available": False,
            "note": (
                "tools.corpus.docx_view is not available yet."
            ),
        }

    try:
        view = accepted_view(docx_path)

        return {
            "available": True,
            "result_type": type(view).__name__,
        }

    except Exception as exc:
        return {
            "available": True,
            "error": str(exc),
        }


def run_harness(
    docx_path: Path,
    selected_checks: list[str],
):
    check_results = {}

    for name in selected_checks:
        check_results[name] = CHECK_FUNCTIONS[name](
            docx_path
        )

    return {
        "schema_version": 1,
        "document": str(docx_path),
        "accepted_view": accepted_view_status(
            docx_path
        ),
        "checks": check_results,
    }


def write_report(
    report: dict[str, Any],
    output: str,
):
    rendered = json.dumps(
        report,
        indent=2,
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


def parse_checks(value: str):
    checks = [
        item.strip().lower()
        for item in value.split(",")
        if item.strip()
    ]

    unknown = [
        item
        for item in checks
        if item not in CHECK_FUNCTIONS
    ]

    if unknown:
        raise argparse.ArgumentTypeError(
            "Unknown check(s): "
            + ", ".join(unknown)
        )

    return checks


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run Track K conformance checks "
            "on a DOCX file."
        )
    )

    parser.add_argument(
        "--docx",
        required=True,
        help="DOCX file to check.",
    )

    group = parser.add_mutually_exclusive_group(
        required=True
    )

    group.add_argument(
        "--checks",
        type=parse_checks,
        help=(
            "Comma-separated checks, for example "
            "margins,spacing,align,indent,pagenum"
        ),
    )

    group.add_argument(
        "--all",
        action="store_true",
        help="Run all currently available checks.",
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

    if args.all:
        selected_checks = list(
            AVAILABLE_CHECKS
        )
    else:
        selected_checks = args.checks

    report = run_harness(
        docx_path,
        selected_checks,
    )

    write_report(
        report,
        args.out,
    )

    statuses = {
        item["status"]
        for item
        in report["checks"].values()
    }

    if "fail" in statuses:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())