"""K-H7 - JUTLP residue check.

Checks that a clean APA input document does not gain JUTLP-specific
content after being processed by OpenEditor.

If the input already contains JUTLP residue, the result is NA.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
V_NS = "urn:schemas-microsoft-com:vml"
O_NS = "urn:schemas-microsoft-com:office:office"

NS = {
    "w": W_NS,
    "v": V_NS,
    "o": O_NS,
}


RESIDUE_PATTERNS = {
    "jutlp": re.compile(
        r"\bJUTLP\b",
        re.IGNORECASE,
    ),
    "practitioner_notes": re.compile(
        r"\bPractitioner\s+Notes\b",
        re.IGNORECASE,
    ),
    "credit": re.compile(
        r"\bCRediT\b",
        re.IGNORECASE,
    ),
    "this_journal": re.compile(
        r"\bThis\s+Journal\b",
        re.IGNORECASE,
    ),
    "blinded_placeholder": re.compile(
        r"\b("
        r"blinded\s+for\s+review"
        r"|author\s+details\s+removed"
        r"|removed\s+for\s+blind\s+review"
        r"|anonymous\s+for\s+review"
        r")\b",
        re.IGNORECASE,
    ),
}


STYLE_MARKERS = (
    "jutlp",
    "practitioner",
    "credit",
)


SHAPE_MARKERS = (
    "jutlp",
    "banner",
    "practitioner",
)


def _w_attr(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def _result(
    status: str,
    evidence: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "check": "residue",
        "status": status,
        "evidence": evidence,
    }

    if details is not None:
        result["details"] = details

    return result


def _scan_docx(
    docx_path: Path,
) -> list[dict[str, str]]:
    """Find JUTLP-specific text, styles and shapes."""

    if not docx_path.exists():
        raise ValueError(
            f"File does not exist: {docx_path}"
        )

    if not zipfile.is_zipfile(docx_path):
        raise ValueError(
            f"Not a valid DOCX file: {docx_path}"
        )

    matches: list[dict[str, str]] = []

    with zipfile.ZipFile(
        docx_path,
        "r",
    ) as archive:

        xml_parts = [
            name
            for name in archive.namelist()
            if name.startswith("word/")
            and name.endswith(".xml")
        ]

        for part_name in xml_parts:
            try:
                root = etree.fromstring(
                    archive.read(part_name)
                )
            except etree.XMLSyntaxError:
                continue

            # Visible text
            text_values = root.xpath(
                ".//w:t/text() | .//w:instrText/text()",
                namespaces=NS,
            )

            visible_text = " ".join(
                str(value)
                for value in text_values
            )

            for label, pattern in RESIDUE_PATTERNS.items():
                if pattern.search(visible_text):
                    matches.append(
                        {
                            "type": "text",
                            "rule": label,
                            "part": part_name,
                        }
                    )

            # Text boxes
            textboxes = root.xpath(
                ".//w:txbxContent",
                namespaces=NS,
            )

            for number, textbox in enumerate(
                textboxes,
                start=1,
            ):
                textbox_text = " ".join(
                    textbox.xpath(
                        ".//w:t/text()",
                        namespaces=NS,
                    )
                )

                for label, pattern in RESIDUE_PATTERNS.items():
                    if pattern.search(textbox_text):
                        matches.append(
                            {
                                "type": "textbox",
                                "rule": label,
                                "part": part_name,
                                "location": (
                                    f"textbox-{number}"
                                ),
                            }
                        )

            # JUTLP-related styles
            if part_name == "word/styles.xml":
                styles = root.xpath(
                    ".//w:style",
                    namespaces=NS,
                )

                for style in styles:
                    style_id = (
                        style.get(
                            _w_attr("styleId"),
                            "",
                        )
                        or ""
                    )

                    name_node = style.find(
                        "w:name",
                        namespaces=NS,
                    )

                    style_name = ""

                    if name_node is not None:
                        style_name = (
                            name_node.get(
                                _w_attr("val"),
                                "",
                            )
                            or ""
                        )

                    combined = (
                        f"{style_id} {style_name}"
                    ).lower()

                    if any(
                        marker in combined
                        for marker in STYLE_MARKERS
                    ):
                        matches.append(
                            {
                                "type": "style",
                                "rule": "jutlp_style",
                                "part": part_name,
                                "location": (
                                    style_id
                                    or style_name
                                ),
                            }
                        )

            # JUTLP/banner named VML shapes
            shapes = root.xpath(
                ".//v:shape",
                namespaces=NS,
            )

            for shape in shapes:
                shape_id = (
                    shape.get("id", "")
                    or ""
                )

                office_id = (
                    shape.get(
                        f"{{{O_NS}}}spid",
                        "",
                    )
                    or ""
                )

                combined = (
                    f"{shape_id} {office_id}"
                ).lower()

                if any(
                    marker in combined
                    for marker in SHAPE_MARKERS
                ):
                    matches.append(
                        {
                            "type": "shape",
                            "rule": "jutlp_banner_shape",
                            "part": part_name,
                            "location": (
                                shape_id
                                or office_id
                            ),
                        }
                    )

    # Remove duplicate evidence.
    unique_matches = []
    seen = set()

    for match in matches:
        key = tuple(
            sorted(match.items())
        )

        if key not in seen:
            seen.add(key)
            unique_matches.append(match)

    return unique_matches


def check_residue(
    output_docx: Path | str,
    input_docx: Path | str | None = None,
) -> dict[str, Any]:
    """Check that JUTLP residue was not introduced."""

    output_path = Path(output_docx)

    if input_docx is None:
        return _result(
            "na",
            (
                "Input document was not supplied. "
                "Residue checking requires the original input."
            ),
        )

    input_path = Path(input_docx)

    try:
        input_matches = _scan_docx(
            input_path
        )
    except ValueError as exc:
        return _result(
            "fail",
            str(exc),
        )

    # K-H7 only runs on clean inputs.
    if input_matches:
        return _result(
            "na",
            (
                "Input document already contains "
                "JUTLP-specific residue."
            ),
            {
                "input_matches": input_matches,
            },
        )

    try:
        output_matches = _scan_docx(
            output_path
        )
    except ValueError as exc:
        return _result(
            "fail",
            str(exc),
        )

    if output_matches:
        return _result(
            "fail",
            (
                "JUTLP-specific residue was found "
                "in the output document."
            ),
            {
                "matches": output_matches,
            },
        )

    return _result(
        "pass",
        (
            "No JUTLP-specific residue was found "
            "in the output document."
        ),
        {
            "matches": [],
        },
    )