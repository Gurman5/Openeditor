"""Recolour existing blue hyperlinks in the References section to black.

If the user submits a document where reference URLs/DOIs are already Word
hyperlinks but styled blue (via the built-in Hyperlink character style or
an explicit colour), this pass adds a tracked run-property change
(w:rPrChange) to set the colour to black so the editor can accept or
reject it individually in Word's All Markup view.

Runs that already carry an explicit black colour are left untouched.
"""

import os
import zipfile
from copy import deepcopy

from lxml import etree

from app.services.language_corrections import (
    _SKIP_STYLES,
    AUTHOR,
    DATE,
    WQ,
    _get_style_name,
    _is_references_heading,
)

_REF_STYLES = {
    "APA7ReferenceListEntry",
    "APA 7 Reference List Entry",
    "APA7 Reference List Entry",
    "APAReferenceListEntry",
    "Reference List Entry",
}


def _run_already_black(rPr: etree._Element | None) -> bool:
    """True if the run already has an explicit black colour."""
    if rPr is None:
        return False
    color_el = rPr.find(f"{WQ}color")
    if color_el is None:
        return False
    return color_el.get(f"{WQ}val", "").lower() in ("000000", "auto")


def apply_ref_hyperlink_colour_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Apply tracked colour-to-black on existing blue reference hyperlinks.

    Returns (next_change_id, corrections_made).
    """
    with zipfile.ZipFile(input_path, "r") as z:
        doc_xml = z.read("word/document.xml")

    doc_root = etree.fromstring(doc_xml)
    made: list[dict] = []

    in_references = False
    for para_el in doc_root.iter(f"{WQ}p"):
        style = _get_style_name(para_el)

        if _is_references_heading(para_el):
            in_references = True
            continue
        if in_references and style.startswith("Heading"):
            in_references = False

        if style not in _REF_STYLES and not in_references:
            continue
        if style in _SKIP_STYLES:
            continue

        for hl_el in para_el.iter(f"{WQ}hyperlink"):
            for run_el in hl_el.findall(f"{WQ}r"):
                rPr = run_el.find(f"{WQ}rPr")

                if _run_already_black(rPr):
                    continue

                # Skip runs that already carry a tracked rPr change.
                if rPr is not None and rPr.find(f"{WQ}rPrChange") is not None:
                    continue

                if rPr is None:
                    rPr = etree.Element(f"{WQ}rPr")
                    run_el.insert(0, rPr)

                old_rPr = deepcopy(rPr)

                # Add or update w:color to black.
                color_el = rPr.find(f"{WQ}color")
                if color_el is not None:
                    color_el.set(f"{WQ}val", "000000")
                else:
                    color_el = etree.Element(f"{WQ}color")
                    color_el.set(f"{WQ}val", "000000")
                    # Insert after w:rStyle if present, otherwise prepend.
                    rStyle = rPr.find(f"{WQ}rStyle")
                    if rStyle is not None:
                        rPr.insert(list(rPr).index(rStyle) + 1, color_el)
                    else:
                        rPr.insert(0, color_el)

                # w:rPrChange must be last child of w:rPr.
                rPr_change = etree.SubElement(rPr, f"{WQ}rPrChange")
                rPr_change.set(f"{WQ}id",     str(next_change_id))
                rPr_change.set(f"{WQ}author", AUTHOR)
                rPr_change.set(f"{WQ}date",   DATE)
                rPr_change.append(old_rPr)
                next_change_id += 1

                made.append({
                    "type": "hyperlink_colour",
                    "description": "Changed hyperlink colour to black",
                })

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    tmp = output_path + ".refhlclr.tmp"
    with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "word/document.xml":
                zout.writestr(item, new_doc_xml)
            else:
                zout.writestr(item, zin.read(item.filename))
    os.replace(tmp, output_path)

    return next_change_id, made
