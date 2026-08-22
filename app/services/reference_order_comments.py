"""Flag a reference list that is not in alphabetical order.

APA 7 (which JUTLP follows) requires the reference list to be ordered
alphabetically by the first author's surname (letter by letter; organisational
authors alphabetised by their first significant word). This pass checks the
order and, when it is wrong, leaves a single explanatory comment on the
References heading.

It is **comment-only**: reordering a reference list correctly (same-author
entries by year, hanging indents, in-text citation links, numbered vs unnumbered
styles) is an editorial judgement, so the bot flags the problem and the editor
reorders. Detection reuses the same entry extraction and surname parsing as the
reference verifier, so "what counts as an entry" stays consistent.
"""

from __future__ import annotations

import os
import re
import zipfile

from lxml import etree

from app.services.acronym_corrections import (
    _make_comment_element,
    _patch_content_types,
    _patch_rels,
)
from app.services.language_corrections import WQ, W
from app.services.reference_checker import (
    _extract_ref_author_part,
    _normalise_surname,
    extract_references,
)

_REFERENCE_HEADINGS = frozenset({"references", "reference list", "bibliography"})


def _sort_key_and_label(entry: str) -> tuple[str, str] | None:
    """Return ``(normalised_surname, display_surname)`` for a reference entry,
    or None when no author/surname can be parsed."""
    author_part = _extract_ref_author_part(entry)
    norm = _normalise_surname(author_part)
    if not norm:
        return None
    display = re.split(r"[,&]|\band\b|\bet\b", author_part)[0].strip()
    return norm, (display or author_part.strip())


def _first_inversion(entries: list[str]) -> tuple[str, str] | None:
    """Return ``(earlier_label, misplaced_label)`` for the first entry that
    breaks alphabetical order, or None when the list is correctly ordered."""
    keys = [k for k in (_sort_key_and_label(e) for e in entries) if k is not None]
    for i in range(1, len(keys)):
        if keys[i][0] < keys[i - 1][0]:
            return keys[i - 1][1], keys[i][1]
    return None


def _build_comment(earlier: str, misplaced: str) -> str:
    return (
        "The reference list does not appear to be in alphabetical order. APA 7 "
        "(JUTLP house style) requires entries to be ordered alphabetically by "
        f"the first author's surname. For example, “{misplaced}” appears after "
        f"“{earlier}” but should come before it. Please reorder the reference "
        "list alphabetically by first-author surname."
    )


def _find_references_heading(body: etree._Element) -> etree._Element | None:
    """Locate the References heading by text (style-agnostic — manuscripts give
    headings numeric style ids, so text is the reliable signal)."""
    for para in body.iter(f"{WQ}p"):
        text = "".join(t.text or "" for t in para.iter(f"{WQ}t")).strip().lower()
        if text in _REFERENCE_HEADINGS:
            return para
    return None


def _anchor_comment_on_paragraph(para_el: etree._Element, comment_id: int) -> None:
    nsmap = {"w": W}
    start = etree.Element(f"{WQ}commentRangeStart", nsmap=nsmap)
    start.set(f"{WQ}id", str(comment_id))
    end = etree.Element(f"{WQ}commentRangeEnd", nsmap=nsmap)
    end.set(f"{WQ}id", str(comment_id))

    ref_run = etree.Element(f"{WQ}r", nsmap=nsmap)
    r_pr = etree.SubElement(ref_run, f"{WQ}rPr")
    r_style = etree.SubElement(r_pr, f"{WQ}rStyle")
    r_style.set(f"{WQ}val", "CommentReference")
    comment_ref = etree.SubElement(ref_run, f"{WQ}commentReference")
    comment_ref.set(f"{WQ}id", str(comment_id))

    pPr = para_el.find(f"{WQ}pPr")
    insert_at = (list(para_el).index(pPr) + 1) if pPr is not None else 0
    para_el.insert(insert_at, start)
    para_el.append(end)
    para_el.append(ref_run)


def _passthrough(input_path: str, output_path: str, next_change_id: int):
    if input_path != output_path:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
            output_path, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))
    return next_change_id, []


def apply_reference_order_comments(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Comment on a reference list that is not alphabetically ordered.

    Comment-only — ``next_change_id`` is threaded unchanged. Returns
    ``(next_change_id, actions)`` to match sibling passes.
    """
    entries = extract_references(input_path)
    # Need at least a few entries before "order" is meaningful.
    if len(entries) < 3:
        return _passthrough(input_path, output_path, next_change_id)

    inversion = _first_inversion(entries)
    if inversion is None:
        return _passthrough(input_path, output_path, next_change_id)

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
        return _passthrough(input_path, output_path, next_change_id)

    heading = _find_references_heading(body)
    if heading is None:
        return _passthrough(input_path, output_path, next_change_id)

    if comments_xml:
        comments_root = etree.fromstring(comments_xml)
        existing = [
            int(el.get(f"{WQ}id", 0)) for el in comments_root.findall(f"{WQ}comment")
        ]
        next_comment_id = max(existing, default=0) + 1
    else:
        comments_root = etree.Element(f"{WQ}comments", nsmap={"w": W})
        next_comment_id = 1

    comment_id = next_comment_id
    comments_root.append(_make_comment_element(comment_id, _build_comment(*inversion)))
    _anchor_comment_on_paragraph(heading, comment_id)

    actions = [{
        "rule": "reference_order",
        "comment_id": comment_id,
        "earlier": inversion[0],
        "misplaced": inversion[1],
    }]

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_comments_xml = etree.tostring(
        comments_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_rels_xml = _patch_rels(rels_xml)
    new_ct_xml = _patch_content_types(ct_xml)

    tmp = output_path + ".reforder.tmp"
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
