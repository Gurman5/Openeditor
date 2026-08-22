"""Insert page breaks before tables that are unlikely to fit on one page.

Word pagination is layout-engine state, not stored directly in the DOCX XML, so
the server cannot know exact rendered page breaks without automating Word. This
pass uses a conservative structural estimate: row count plus wrapped cell text.
When a table is likely to run beyond a page, it inserts a page break before the
table's caption block so the caption and table start on the same fresh page.
"""

from __future__ import annotations

import os
import zipfile

from lxml import etree

from app.services.language_corrections import WQ, W

# A portrait manuscript page usually holds roughly 28-32 single-line table rows
# after margins/caption. Use a lower threshold so multi-line rows do not start
# at the bottom of the previous page.
_MAX_TABLE_PAGE_UNITS = 24
_CHARS_PER_TABLE_LINE = 65
_CAPTION_STYLES = frozenset({
    "Table Number", "TableNumber",
    "Table Title", "TableTitle",
})


def _cell_text(cell_el: etree._Element) -> str:
    return "".join(t.text or "" for t in cell_el.iter(f"{WQ}t") if t.text).strip()


def _row_height_units(row_el: etree._Element) -> int:
    cells = row_el.findall(f"{WQ}tc")
    if not cells:
        return 1
    max_lines = 1
    for cell in cells:
        text = _cell_text(cell)
        if not text:
            continue
        # Integer ceiling without importing math.
        max_lines = max(max_lines, max(1, (len(text) + _CHARS_PER_TABLE_LINE - 1) // _CHARS_PER_TABLE_LINE))
    return max_lines


def _table_page_units(table_el: etree._Element) -> int:
    return sum(_row_height_units(row) for row in table_el.findall(f"{WQ}tr"))


def _para_style(para_el: etree._Element) -> str:
    ppr = para_el.find(f"{WQ}pPr")
    if ppr is None:
        return ""
    pstyle = ppr.find(f"{WQ}pStyle")
    return pstyle.get(f"{WQ}val", "") if pstyle is not None else ""


def _para_text(para_el: etree._Element) -> str:
    return "".join(t.text or "" for t in para_el.iter(f"{WQ}t") if t.text).strip()


def _para_has_page_break(para_el: etree._Element) -> bool:
    ppr = para_el.find(f"{WQ}pPr")
    if ppr is not None and ppr.find(f"{WQ}pageBreakBefore") is not None:
        return True
    for br in para_el.findall(f".//{WQ}br"):
        if br.get(f"{WQ}type") == "page":
            return True
    return False


def _page_break_anchor(table_el: etree._Element) -> etree._Element:
    anchor = table_el
    prev = table_el.getprevious()
    while prev is not None and prev.tag == f"{WQ}p":
        if _para_has_page_break(prev):
            break
        style = _para_style(prev)
        text = _para_text(prev)
        if style in _CAPTION_STYLES or text == "":
            anchor = prev
            prev = prev.getprevious()
            continue
        break
    return anchor


def _preceded_by_page_break(table_el: etree._Element) -> bool:
    prev = _page_break_anchor(table_el).getprevious()
    while prev is not None:
        if prev.tag == f"{WQ}p":
            if _para_has_page_break(prev):
                return True
            return _para_text(prev) == ""
        if prev.tag == f"{WQ}tbl":
            return False
        prev = prev.getprevious()
    return False


def _make_page_break_paragraph() -> etree._Element:
    para = etree.Element(f"{WQ}p", nsmap={"w": W})
    run = etree.SubElement(para, f"{WQ}r")
    br = etree.SubElement(run, f"{WQ}br")
    br.set(f"{WQ}type", "page")
    return para


def apply_table_page_breaks(
    input_path: str,
    output_path: str,
    *,
    max_page_units: int = _MAX_TABLE_PAGE_UNITS,
) -> list[dict]:
    """Insert page breaks before likely overflowing tables.

    Returns action dictionaries for each table that received a break.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        doc_xml = z.read("word/document.xml")

    doc_root = etree.fromstring(doc_xml)
    body = doc_root.find(f"{WQ}body")
    if body is None:
        return []

    actions: list[dict] = []
    table_number = 0
    for child in list(body):
        if child.tag != f"{WQ}tbl":
            continue
        table_number += 1
        units = _table_page_units(child)
        if units <= max_page_units:
            continue
        if _preceded_by_page_break(child):
            continue
        _page_break_anchor(child).addprevious(_make_page_break_paragraph())
        actions.append(
            {
                "rule": "table_page_break",
                "table_number": table_number,
                "page_units": units,
            }
        )

    if not actions:
        if input_path != output_path:
            with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
                output_path, "w", zipfile.ZIP_DEFLATED
            ) as zout:
                for item in zin.infolist():
                    zout.writestr(item, zin.read(item.filename))
        return actions

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    tmp = output_path + ".table-page-breaks.tmp"
    try:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
            tmp, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return actions
