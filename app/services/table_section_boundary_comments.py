"""Flag sections that open or close directly with a table.

JUTLP/APA style expects a table to be introduced and interpreted in prose: a
section should not *open* straight into a table (no lead-in sentence telling the
reader what the table shows) nor *close* on a table (no sentence interpreting it
before the next section begins).

A table is almost always wrapped by its caption paragraphs — "Table N" (Table
Number style) and an italic title above it, and an optional "Note." (Table Note
style) below it. Those belong to the *table block*, so they are skipped when
deciding whether real prose surrounds the table. Blank spacer paragraphs are
skipped too.

Comment-only — restructuring the section is an editorial judgement, so the bot
explains the issue and the editor decides what prose to add.
"""

from __future__ import annotations

import os
import zipfile

from lxml import etree

from app.services.acronym_corrections import (
    _make_comment_element,
    _patch_content_types,
    _patch_rels,
    _split_run_for_action,
)
from app.services.document_zones import get_style_name, para_plain_text
from app.services.language_corrections import WQ, W

_HEADING_STYLES = frozenset({
    "Heading 1", "Heading 2", "Heading 3",
    "Heading1", "Heading2", "Heading3",
})
_CAPTION_STYLES = frozenset({
    "Table Number", "TableNumber",
    "Table Title", "TableTitle",
})
_NOTE_STYLES = frozenset({
    "Table Note", "TableNote",
    "Table Notes", "TableNotes",
})

# Headings whose sections we don't police for table prose (back matter).
_SKIP_SECTION_HEADINGS = frozenset({
    "references", "reference list", "acknowledgements", "acknowledgments",
})

_OPEN_COMMENT = (
    "This section opens directly with a table. A table should be introduced by "
    "at least one sentence of lead-in text that tells the reader what it shows. "
    "Please add an introductory sentence before the table."
)
_CLOSE_COMMENT = (
    "This section ends with a table. A table should not be the final element of "
    "a section; please add a sentence after it interpreting the table before the "
    "next section begins."
)
_ONLY_COMMENT = (
    "This section consists of a table with no surrounding text. Please add an "
    "introductory sentence before the table and a concluding sentence after it."
)


def _iter_text_runs(para_el: etree._Element):
    """Yield (run_el, text) for runs we may safely anchor a comment on."""
    for r in para_el.iter(f"{WQ}r"):
        parent = r.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        prev = r.getprevious()
        if prev is not None and prev.tag == f"{WQ}commentRangeStart":
            continue
        t_el = r.find(f"{WQ}t")
        if t_el is None:
            continue
        yield r, t_el.text or ""


def _classify(child: etree._Element) -> str:
    """Classify a body-level block for section-boundary analysis."""
    if child.tag == f"{WQ}tbl":
        return "table"
    if child.tag != f"{WQ}p":
        return "other"
    style = get_style_name(child)
    text = para_plain_text(child).strip()
    if style in _HEADING_STYLES:
        return "heading"
    if style in _CAPTION_STYLES:
        return "caption"
    if style in _NOTE_STYLES:
        return "note"
    if text == "":
        return "blank"
    return "prose"


def _section_opener(content: list[tuple[str, etree._Element]]):
    """First meaningful block: a table (skipping leading caption/blank) → it,
    prose → None."""
    for kind, el in content:
        if kind in ("blank", "caption", "other"):
            continue
        return el if kind == "table" else None
    return None


def _section_closer(content: list[tuple[str, etree._Element]]):
    """Last meaningful block: a table (skipping trailing note/blank) → it,
    prose → None."""
    for kind, el in reversed(content):
        if kind in ("blank", "note", "other"):
            continue
        return el if kind == "table" else None
    return None


def _anchor_paragraph(table_el: etree._Element):
    """Return a paragraph to anchor the comment on: the nearest non-empty
    caption above the table, else the first non-empty paragraph in the table."""
    prev = table_el.getprevious()
    while prev is not None and prev.tag == f"{WQ}p":
        style = get_style_name(prev)
        text = para_plain_text(prev).strip()
        if style in _CAPTION_STYLES and text:
            return prev
        if text != "" and style not in _CAPTION_STYLES:
            break
        prev = prev.getprevious()
    for p in table_el.iter(f"{WQ}p"):
        if para_plain_text(p).strip():
            return p
    return None


def apply_table_section_boundary_comments(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Comment on sections that open and/or close directly with a table.

    Returns ``(next_change_id, actions)`` — comment-only, change id unchanged.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")
        ct_xml = z.read("[Content_Types].xml")
        has_comments = "word/comments.xml" in names
        comments_xml = z.read("word/comments.xml") if has_comments else None

    doc_root = etree.fromstring(doc_xml)
    body = doc_root.find(f"{WQ}body")
    if body is None:
        return next_change_id, []

    if comments_xml:
        comments_root = etree.fromstring(comments_xml)
        existing = [int(el.get(f"{WQ}id", 0)) for el in comments_root.findall(f"{WQ}comment")]
        next_comment_id = max(existing, default=0) + 1
    else:
        comments_root = etree.Element(f"{WQ}comments", nsmap={"w": W})
        next_comment_id = 1

    blocks = [(_classify(child), child) for child in body]
    heading_idxs = [i for i, (kind, _) in enumerate(blocks) if kind == "heading"]

    # Build the (table_el, comment_text) work list first so anchoring edits
    # don't disturb classification.
    todo: list[tuple[etree._Element, str]] = []
    for n, hi in enumerate(heading_idxs):
        heading_text = para_plain_text(blocks[hi][1]).strip().lower().rstrip(":")
        if heading_text in _SKIP_SECTION_HEADINGS:
            continue
        end = heading_idxs[n + 1] if n + 1 < len(heading_idxs) else len(blocks)
        content = blocks[hi + 1:end]
        if not content:
            continue
        opener = _section_opener(content)
        closer = _section_closer(content)
        if opener is not None and opener is closer:
            todo.append((opener, _ONLY_COMMENT))
        else:
            if opener is not None:
                todo.append((opener, _OPEN_COMMENT))
            if closer is not None:
                todo.append((closer, _CLOSE_COMMENT))

    actions: list[dict] = []
    for table_el, text in todo:
        anchor = _anchor_paragraph(table_el)
        if anchor is None:
            continue
        for run_el, run_text in _iter_text_runs(anchor):
            if not run_text:
                continue
            comments_root.append(_make_comment_element(next_comment_id, text))
            _split_run_for_action(
                run_el, 0, len(run_text),
                expansion=None, comment_id=next_comment_id, change_id=0,
            )
            actions.append({"rule": "table_section_boundary", "comment_id": next_comment_id})
            next_comment_id += 1
            break

    if not actions:
        if input_path != output_path:
            with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
                output_path, "w", zipfile.ZIP_DEFLATED
            ) as zout:
                for item in zin.infolist():
                    zout.writestr(item, zin.read(item.filename))
        return next_change_id, actions

    new_doc_xml = etree.tostring(doc_root, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_comments_xml = etree.tostring(comments_root, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_rels_xml = _patch_rels(rels_xml)
    new_ct_xml = _patch_content_types(ct_xml)

    tmp = output_path + ".tsb.tmp"
    try:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
            tmp, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item.filename == "word/_rels/document.xml.rels":
                    zout.writestr(item, new_rels_xml)
                elif item.filename == "[Content_Types].xml":
                    zout.writestr(item, new_ct_xml)
                elif item.filename == "word/comments.xml":
                    zout.writestr(item, new_comments_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
            if not has_comments:
                zout.writestr("word/comments.xml", new_comments_xml)
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return next_change_id, actions
