"""Keep tables (and their headers) from splitting awkwardly across pages.

A common defect: a table's caption and header row land at the bottom of a
page while the data rows flow onto the next, leaving the header stranded.
Word pagination is layout-engine state the DOCX XML never stores, so rather
than guess page positions (the brittle hard-page-break approach), this pass
sets the row/paragraph properties that let Word's own layout engine do the
right thing:

  * ``w:cantSplit`` on every row      — a row never breaks across a page.
  * ``w:tblHeader`` on the first row  — if the table genuinely spans pages,
                                        the header repeats on each one (so it
                                        is never orphaned, even for long tables).
  * ``w:keepNext`` on the caption     — the "Table N" label and italic title
    paragraphs immediately above        stay glued to the table and float to a
    the table                           fresh page with it when it can't fit.

These are applied directly (not as tracked changes), matching the existing
``_apply_heading_keep_next`` pass — layout-hint properties are not the kind of
edit an author reviews and rejects, and tracked changes on table-row
properties are awkward in Word.
"""

from __future__ import annotations

import os
import zipfile

from lxml import etree

from app.services.language_corrections import WQ

# Caption styles that sit directly above a table; they should keep with it.
_CAPTION_STYLES = frozenset({
    "Table Number", "TableNumber",
    "Table Title", "TableTitle",
})

# Schema order of CT_TrPr children — new children must be inserted in this
# order or Word may reject the row properties.
_TRPR_ORDER = [
    "cnfStyle", "divId", "gridBefore", "gridAfter", "wBefore", "wAfter",
    "cantSplit", "trHeight", "tblHeader", "tblCellSpacing", "jc", "hidden",
]


def _para_style(para_el: etree._Element) -> str:
    p_pr = para_el.find(f"{WQ}pPr")
    if p_pr is None:
        return ""
    p_style = p_pr.find(f"{WQ}pStyle")
    return p_style.get(f"{WQ}val", "") if p_style is not None else ""


def _para_text(para_el: etree._Element) -> str:
    return "".join(t.text or "" for t in para_el.iter(f"{WQ}t") if t.text).strip()


def _ensure_trpr(row_el: etree._Element) -> etree._Element:
    """Return the row's ``w:trPr``, creating it as the first child if absent."""
    tr_pr = row_el.find(f"{WQ}trPr")
    if tr_pr is None:
        tr_pr = etree.Element(f"{WQ}trPr")
        row_el.insert(0, tr_pr)
    return tr_pr


def _ensure_trpr_child(tr_pr: etree._Element, tag: str) -> bool:
    """Insert ``w:<tag>`` into ``trPr`` in schema order. Returns True if added."""
    if tr_pr.find(f"{WQ}{tag}") is not None:
        return False
    order = _TRPR_ORDER.index(tag)
    insert_at = len(tr_pr)
    for i, child in enumerate(tr_pr):
        name = etree.QName(child).localname
        if name in _TRPR_ORDER and _TRPR_ORDER.index(name) > order:
            insert_at = i
            break
    tr_pr.insert(insert_at, etree.Element(f"{WQ}{tag}"))
    return True


def _ensure_keep_next(para_el: etree._Element) -> bool:
    """Add ``w:keepNext`` to a paragraph (after ``w:pStyle``). Returns True if
    a change was made — including clearing an explicit keepNext="0"."""
    p_pr = para_el.find(f"{WQ}pPr")
    if p_pr is None:
        p_pr = etree.Element(f"{WQ}pPr")
        para_el.insert(0, p_pr)
    existing = p_pr.find(f"{WQ}keepNext")
    if existing is not None:
        val = existing.get(f"{WQ}val", "")
        if val.lower() in ("0", "false", "off"):
            existing.attrib.pop(f"{WQ}val", None)
            return True
        return False
    keep = etree.Element(f"{WQ}keepNext")
    p_style = p_pr.find(f"{WQ}pStyle")
    if p_style is not None:
        p_style.addnext(keep)
    else:
        p_pr.insert(0, keep)
    return True


def _apply_caption_keep_next(table_el: etree._Element) -> int:
    """Add keepNext to caption paragraphs immediately preceding the table.

    Walks backward over preceding siblings while they are caption-styled (or
    blank spacer paragraphs), so both "Table N" and the italic title keep with
    the table. Stops at the first non-caption, non-blank paragraph.
    """
    changes = 0
    prev = table_el.getprevious()
    while prev is not None and prev.tag == f"{WQ}p":
        style = _para_style(prev)
        text = _para_text(prev)
        if style in _CAPTION_STYLES:
            if _ensure_keep_next(prev):
                changes += 1
        elif text == "":
            # Blank spacer between caption and table — keep it with the table
            # too, but don't treat it as the caption boundary.
            if _ensure_keep_next(prev):
                changes += 1
        else:
            break
        prev = prev.getprevious()
    return changes


def apply_table_keep_together(input_path: str, output_path: str) -> list[dict]:
    """Set cantSplit / tblHeader / caption keepNext on every table.

    Returns one action dict per table that received any change.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        doc_xml = z.read("word/document.xml")

    doc_root = etree.fromstring(doc_xml)
    body = doc_root.find(f"{WQ}body")
    if body is None:
        return []

    actions: list[dict] = []
    table_number = 0
    # Iterate every table in the document (including nested) for row props,
    # but caption keepNext only makes sense for top-level tables with sibling
    # captions; getprevious() naturally returns None inside a cell wrapper.
    for table_el in doc_root.iter(f"{WQ}tbl"):
        table_number += 1
        rows = table_el.findall(f"{WQ}tr")
        if not rows:
            continue

        changed = False
        for i, row in enumerate(rows):
            tr_pr = _ensure_trpr(row)
            if _ensure_trpr_child(tr_pr, "cantSplit"):
                changed = True
            if i == 0 and _ensure_trpr_child(tr_pr, "tblHeader"):
                changed = True

        if _apply_caption_keep_next(table_el) > 0:
            changed = True

        if changed:
            actions.append({"rule": "table_keep_together", "table_number": table_number})

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

    tmp = output_path + ".table-keep-together.tmp"
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
