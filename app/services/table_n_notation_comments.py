"""Flag capital "N" used as a table column header.

In statistical reporting the case of the letter carries meaning: a capital
*N* denotes the total population / full-sample size, while a lowercase,
italicised *n* denotes a subsample. Authors routinely type a plain capital
"N" as a count column header without confirming which they mean, so this
pass leaves a single editorial comment asking them to check.

It is intentionally comment-only — no tracked change — because the bot
cannot know the author's intent (the correct symbol depends on whether the
column counts the whole sample or a subgroup). The editor decides.

Detection is deliberately narrow to avoid false positives: the comment fires
only on a table-cell paragraph whose entire text is exactly ``N``. Data cells
hold numbers, and prose never consists of a lone capital N, so a standalone
"N" inside a table is almost always a count header.
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
from app.services.document_zones import (
    is_in_table,
    iter_paragraphs_with_zone,
    para_plain_text,
)
from app.services.language_corrections import WQ, W

_COMMENT_TEXT = (
    "This column header uses a capital “N”. In statistical reporting "
    "a capital N denotes the total population or full-sample size, whereas a "
    "lowercase, italicised n denotes a subsample drawn from that population. "
    "Please confirm the correct notation is used here."
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


def _is_capital_n_header(para_el: etree._Element) -> bool:
    """True when the paragraph is a table cell whose only content is "N"."""
    if not is_in_table(para_el):
        return False
    return para_plain_text(para_el).strip() == "N"


def apply_table_n_notation_comments(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Emit one comment per table column header that is a bare capital "N".

    Returns ``(next_change_id, actions)`` to match sibling pass shape.
    ``next_change_id`` is threaded unchanged — comment-only, no tracked changes.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")
        ct_xml = z.read("[Content_Types].xml")
        has_comments = "word/comments.xml" in names
        comments_xml = z.read("word/comments.xml") if has_comments else None

    doc_root = etree.fromstring(doc_xml)

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

    actions: list[dict] = []

    for para_el, zone in iter_paragraphs_with_zone(doc_root):
        if zone == "outside":
            continue
        if not _is_capital_n_header(para_el):
            continue

        # Anchor the comment on the "N" character in its run.
        for run_el, run_text in _iter_text_runs(para_el):
            idx = run_text.find("N")
            if idx == -1:
                continue
            comments_root.append(
                _make_comment_element(next_comment_id, _COMMENT_TEXT)
            )
            _split_run_for_action(
                run_el,
                idx,
                idx + 1,
                expansion=None,
                comment_id=next_comment_id,
                change_id=0,
            )
            actions.append(
                {"rule": "table_n_notation", "comment_id": next_comment_id}
            )
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

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_comments_xml = etree.tostring(
        comments_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_rels_xml = _patch_rels(rels_xml)
    new_ct_xml = _patch_content_types(ct_xml)

    tmp = output_path + ".tabn.tmp"
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
