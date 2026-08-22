"""Reset the Normal paragraph style to JUTLP template requirements.

If an author's Normal style has been customised or corrupted, this pass
restores the three canonical properties directly in word/styles.xml so that
body paragraphs that inherit from Normal get the correct formatting:

  • w:jc val="both"                                       justified alignment
  • w:spacing after="120" line="276" lineRule="auto"      6 pt after, 1.15 lines
  • w:rFonts ascii/hAnsi/cs="Arial"                       Arial font

This is a direct style edit rather than a tracked change because Word's
revision-tracking system does not cover style definitions.
"""

import os
import zipfile

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"

_TARGET_JC = "both"
_TARGET_AFTER = "120"
_TARGET_LINE = "276"
_TARGET_LINE_RULE = "auto"
_TARGET_FONT = "Arial"


def apply_normal_style_corrections(input_path: str, output_path: str) -> list[dict]:
    """Patch the Normal style in styles.xml to match JUTLP template requirements.

    Returns a list of dicts describing each property that was corrected.
    Returns an empty list (and leaves output_path unchanged) when no fix
    was needed or when styles.xml is absent.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        if "word/styles.xml" not in z.namelist():
            return []
        styles_xml = z.read("word/styles.xml")

    root = etree.fromstring(styles_xml)
    changed: list[dict] = []

    normal_style = None
    for style_el in root.findall(f"{WQ}style"):
        if style_el.get(f"{WQ}styleId") == "Normal":
            normal_style = style_el
            break

    if normal_style is None:
        return []

    # ── Paragraph properties ─────────────────────────────────────────────────
    pPr = normal_style.find(f"{WQ}pPr")
    if pPr is None:
        pPr = etree.SubElement(normal_style, f"{WQ}pPr")

    # Justification
    jc = pPr.find(f"{WQ}jc")
    if jc is None:
        jc = etree.SubElement(pPr, f"{WQ}jc")
        jc.set(f"{WQ}val", _TARGET_JC)
        changed.append({"property": "alignment", "old": "(missing)", "new": _TARGET_JC})
    elif jc.get(f"{WQ}val", "") != _TARGET_JC:
        old = jc.get(f"{WQ}val", "")
        jc.set(f"{WQ}val", _TARGET_JC)
        changed.append({"property": "alignment", "old": old, "new": _TARGET_JC})

    # Paragraph spacing
    spacing = pPr.find(f"{WQ}spacing")
    spacing_ok = (
        spacing is not None
        and spacing.get(f"{WQ}after", "") == _TARGET_AFTER
        and spacing.get(f"{WQ}line", "") == _TARGET_LINE
    )
    if not spacing_ok:
        old_after = spacing.get(f"{WQ}after", "(missing)") if spacing is not None else "(missing)"
        old_line = spacing.get(f"{WQ}line", "(missing)") if spacing is not None else "(missing)"
        if spacing is None:
            spacing = etree.SubElement(pPr, f"{WQ}spacing")
        spacing.set(f"{WQ}after", _TARGET_AFTER)
        spacing.set(f"{WQ}line", _TARGET_LINE)
        spacing.set(f"{WQ}lineRule", _TARGET_LINE_RULE)
        changed.append({
            "property": "spacing",
            "old": f"after={old_after} line={old_line}",
            "new": f"after={_TARGET_AFTER} line={_TARGET_LINE}",
        })

    # ── Run properties ────────────────────────────────────────────────────────
    rPr = normal_style.find(f"{WQ}rPr")
    if rPr is None:
        rPr = etree.SubElement(normal_style, f"{WQ}rPr")

    rFonts = rPr.find(f"{WQ}rFonts")
    font_ok = (
        rFonts is not None
        and rFonts.get(f"{WQ}ascii", "") == _TARGET_FONT
        and rFonts.get(f"{WQ}hAnsi", "") == _TARGET_FONT
    )
    if not font_ok:
        old_font = rFonts.get(f"{WQ}ascii", "(missing)") if rFonts is not None else "(missing)"
        if rFonts is None:
            rFonts = etree.SubElement(rPr, f"{WQ}rFonts")
        rFonts.set(f"{WQ}ascii", _TARGET_FONT)
        rFonts.set(f"{WQ}hAnsi", _TARGET_FONT)
        rFonts.set(f"{WQ}cs", _TARGET_FONT)
        changed.append({"property": "font", "old": old_font, "new": _TARGET_FONT})

    if not changed:
        return []

    new_styles_xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    tmp = output_path + ".normalstyle.tmp"
    with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "word/styles.xml":
                zout.writestr(item, new_styles_xml)
            else:
                zout.writestr(item, zin.read(item.filename))
    os.replace(tmp, output_path)

    return changed
