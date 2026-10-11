"""K-H8 - Appendix preservation check.

If an Appendix exists in the input document, it must still exist in
the output document.

If the input has no Appendix, the check returns NA.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

NS = {
    "w": W_NS,
}


APPENDIX_PATTERN = re.compile(
    r"^\s*"
    r"(appendix|appendices)"
    r"(?:\s+[A-Z0-9]+)?"
    r"(?:\s*[:\-].*)?"
    r"\s*$",
    re.IGNORECASE,
)


def _result(
    status: str,
    evidence: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "check": "appendices",
        "status": status,
        "evidence": evidence,
    }

    if details is not None:
        result["details"] = details

    return result


def _paragraph_texts(
    docx_path: Path,
) -> list[str]:
    """Read current visible paragraph text from document.xml."""

    if not docx_path.exists():
        raise ValueError(
            f"File does not exist: {docx_path}"
        )

    if not zipfile.is_zipfile(docx_path):
        raise ValueError(
            f"Not a valid DOCX file: {docx_path}"
        )

    with zipfile.ZipFile(
        docx_path,
        "r",
    ) as archive:

        if (
            "word/document.xml"
            not in archive.namelist()
        ):
            raise ValueError(
                "word/document.xml is missing"
            )

        try:
            root = etree.fromstring(
                archive.read(
                    "word/document.xml"
                )
            )
        except etree.XMLSyntaxError as exc:
            raise ValueError(
                f"Invalid document XML: {exc}"
            ) from exc

    paragraphs = []

    for paragraph in root.xpath(
        "//w:body//w:p",
        namespaces=NS,
    ):
        # Keep normal and inserted text.
        # Ignore deleted tracked-change text.
        text_parts = paragraph.xpath(
            ".//w:t[not(ancestor::w:del)]/text()",
            namespaces=NS,
        )

        text = "".join(
            str(part)
            for part in text_parts
        ).strip()

        if text:
            paragraphs.append(text)

    return paragraphs


def _find_appendix_headings(
    docx_path: Path,
) -> list[str]:
    """Return paragraphs that look like Appendix headings."""

    paragraphs = _paragraph_texts(
        docx_path
    )

    return [
        paragraph
        for paragraph in paragraphs
        if APPENDIX_PATTERN.match(
            paragraph
        )
    ]


def check_appendices(
    output_docx: Path | str,
    input_docx: Path | str | None = None,
) -> dict[str, Any]:
    """Check that appendices from input are preserved in output."""

    if input_docx is None:
        return _result(
            "na",
            (
                "Input document was not supplied. "
                "Appendix preservation requires "
                "both input and output documents."
            ),
        )

    input_path = Path(input_docx)
    output_path = Path(output_docx)

    try:
        input_appendices = (
            _find_appendix_headings(
                input_path
            )
        )
    except ValueError as exc:
        return _result(
            "fail",
            str(exc),
        )

    if not input_appendices:
        return _result(
            "na",
            (
                "The input document does not "
                "contain an Appendix."
            ),
            {
                "input_appendices": [],
            },
        )

    try:
        output_appendices = (
            _find_appendix_headings(
                output_path
            )
        )
    except ValueError as exc:
        return _result(
            "fail",
            str(exc),
        )

    if not output_appendices:
        return _result(
            "fail",
            (
                "The input contained an Appendix "
                "but no Appendix was found in the output."
            ),
            {
                "input_appendices": input_appendices,
                "output_appendices": [],
            },
        )

    output_lookup = {
        heading.casefold()
        for heading in output_appendices
    }

    missing = [
        heading
        for heading in input_appendices
        if heading.casefold()
        not in output_lookup
    ]

    if missing:
        return _result(
            "fail",
            (
                "One or more Appendix headings "
                "were not preserved."
            ),
            {
                "input_appendices": input_appendices,
                "output_appendices": output_appendices,
                "missing": missing,
            },
        )

    return _result(
        "pass",
        "Appendix headings were preserved.",
        {
            "input_appendices": input_appendices,
            "output_appendices": output_appendices,
        },
    )