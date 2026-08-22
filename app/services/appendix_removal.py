"""Flag content that appears AFTER the reference list (appendices).

JUTLP house rule: a manuscript must end with the References section.
Appendices are not accepted — anything beyond the reference list (an
``Appendix`` section, a stray supplementary figure, supporting tables,
etc.) does not belong in the submitted paper.

This pass is **comment-only**: it leaves a single explanatory comment on the
first appendix paragraph advising the author to integrate the material into
the body and remove it. It does NOT delete the content — relocating appendix
material is an editorial judgement, so the author decides what to keep.

Detection:

1. Locate the References heading (``References`` / ``Reference List`` /
   ``Bibliography``).
2. Find where the reference *list* ends and appendix content begins — the
   first paragraph after the References heading that is a heading, an appendix
   heading detected by TEXT (``Appendix A`` …, even when it isn't styled as a
   Heading — authors frequently leave it unstyled or carrying the reference
   style), or carries an image / drawing. Reference entries carry none of
   these, so the boundary is unambiguous.
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
from app.services.document_zones import (
    get_style_name,
    normalise_heading,
    para_plain_text,
)
from app.services.language_corrections import WQ, W

# Reference-section headings that mark the start of the reference list.
_REFERENCE_HEADINGS = frozenset({
    "references",
    "reference list",
    "bibliography",
})

# An appendix heading such as "Appendix", "Appendix A", "Appendix 1.",
# "Appendices" — detected by text so the boundary is found regardless of the
# paragraph's style.
_APPENDIX_HEADING_RE = re.compile(r'^\s*appendi(?:x|ces)\b', re.IGNORECASE)

_COMMENT_TEXT = (
    "JUTLP does not accept appendices — the manuscript must end with the "
    "References section. This content appears after the reference list. "
    "Please integrate any essential material into the body of the paper and "
    "remove it from here."
)


def _is_appendix_heading(text: str) -> bool:
    return bool(_APPENDIX_HEADING_RE.match(text or ""))


def _is_heading_paragraph(para_el: etree._Element) -> bool:
    return get_style_name(para_el).startswith("Heading")


def _paragraph_has_image(para_el: etree._Element) -> bool:
    """Return True if the paragraph contains a drawing / picture / embedded
    object (figure, diagram, chart, screenshot)."""
    for el in para_el.iter():
        tag = etree.QName(el).localname
        if tag in {"drawing", "pict", "object", "OLEObject"}:
            return True
    return False


def _find_appendix_start(body: etree._Element) -> int | None:
    """Return the index (within ``body``'s ``<w:p>`` children list) of the
    first appendix paragraph, or ``None`` when the document has no content
    after the reference list.

    The appendix begins at the first paragraph AFTER the References heading
    that is a heading, an appendix heading (by text), or carries an image.
    Reference entries (plain body paragraphs with none of these) are skipped,
    so the reference list itself is never flagged.
    """
    paras = [el for el in body if el.tag == f"{WQ}p"]

    # Locate the References heading.
    refs_idx = None
    for i, p in enumerate(paras):
        if not _is_heading_paragraph(p):
            continue
        if normalise_heading(para_plain_text(p)) in _REFERENCE_HEADINGS:
            refs_idx = i
            break
    if refs_idx is None:
        return None

    # Scan forward for the first heading / appendix-heading / image paragraph —
    # the appendix boundary. Empty paragraphs and reference entries are skipped.
    for i in range(refs_idx + 1, len(paras)):
        p = paras[i]
        if (
            _is_heading_paragraph(p)
            or _is_appendix_heading(para_plain_text(p))
            or _paragraph_has_image(p)
        ):
            return i
    return None


def _anchor_comment_on_paragraph(
    para_el: etree._Element, comment_id: int
) -> None:
    """Wrap the whole paragraph in a comment range so the explanatory
    comment is anchored to the first appendix paragraph."""
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

    # Insert range start after pPr (if any) so it stays valid; append the
    # range end + reference run at the paragraph's end.
    pPr = para_el.find(f"{WQ}pPr")
    insert_at = (list(para_el).index(pPr) + 1) if pPr is not None else 0
    para_el.insert(insert_at, start)
    para_el.append(end)
    para_el.append(ref_run)


def apply_appendix_removal(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Comment on appendix content (everything after the reference list).

    Comment-only — no tracked changes — so ``next_change_id`` is threaded
    unchanged. Mirrors sibling pass shape: returns ``(next_change_id, actions)``.
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
        return _passthrough(input_path, output_path, next_change_id)

    start_idx = _find_appendix_start(body)
    if start_idx is None:
        return _passthrough(input_path, output_path, next_change_id)

    paras = [el for el in body if el.tag == f"{WQ}p"]
    appendix_paras = paras[start_idx:]
    if not appendix_paras:
        return _passthrough(input_path, output_path, next_change_id)

    # Comment bookkeeping.
    if comments_xml:
        comments_root = etree.fromstring(comments_xml)
        existing = [
            int(el.get(f"{WQ}id", 0))
            for el in comments_root.findall(f"{WQ}comment")
        ]
        next_comment_id = max(existing, default=0) + 1
    else:
        comments_root = etree.Element(f"{WQ}comments", nsmap={"w": W})
        next_comment_id = 1

    # Anchor a single explanatory comment on the first appendix paragraph.
    comment_id = next_comment_id
    comments_root.append(_make_comment_element(comment_id, _COMMENT_TEXT))
    _anchor_comment_on_paragraph(appendix_paras[0], comment_id)

    actions = [{
        "rule": "appendix_comment",
        "commented_paragraphs": len(appendix_paras),
        "comment_id": comment_id,
        "snippet": para_plain_text(appendix_paras[0])[:80],
    }]

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_comments_xml = etree.tostring(
        comments_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_rels_xml = _patch_rels(rels_xml)
    new_ct_xml = _patch_content_types(ct_xml)

    tmp = output_path + ".appx.tmp"
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


def _passthrough(
    input_path: str, output_path: str, next_change_id: int
) -> tuple[int, list[dict]]:
    """Copy input → output unchanged and report no actions."""
    if input_path != output_path:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
            output_path, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))
    return next_change_id, []
