"""Flag APA 7 figure-block violations (JB-09).

APA 7 figures are: a bold ``Figure N`` label on its own line, an italicised
title in title case, a descriptive note, and the figure must be referenced
in the body text before it appears.

This pass is comment-only. For each figure it checks four properties and
emits one comment per missing property:

  * the label is bold,
  * the title is italicised,
  * a descriptive ``Note.`` paragraph is present,
  * the figure number is referenced in an earlier paragraph.

Correctly-formed figures are left untouched. Tables are out of scope here
(handled by ``table_n_notation_comments`` and ``caption_apa7_check``).
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
    _split_run_for_action,
)
from app.services.document_zones import get_style_name, para_plain_text
from app.services.language_corrections import WQ, W

# A label-only figure paragraph: "Figure 1", "Figure A.", "Fig. 3" (trailing
# period tolerated — the period is itself a common APA-7 mistake, but the label
# is still recognised so the other checks can run).
_FIGURE_LABEL_RE = re.compile(
    r"^\s*(?:Figure|Fig\.?)\s+(?P<num>[A-Z]|\d+(?:\.\d+)?)\s*\.?\s*$",
    re.IGNORECASE,
)

# An in-text reference to a figure: "Figure 1", "see Figure 1", "(Figure A)",
# "Fig. 3 shows…". Captures the number so callouts can be matched to labels.
_FIGURE_REF_RE = re.compile(
    r"(?:Figure|Fig\.?)\s+(?P<num>[A-Z]|\d+(?:\.\d+)?)",
    re.IGNORECASE,
)

_FIGURE_NUMBER_STYLES = frozenset({
    "Figure Number", "FigureNumber", "Figure/Table Number", "FigureTableNumber",
})
_FIGURE_TITLE_STYLES = frozenset({
    "Figure Title", "FigureTitle", "Figure/Table Title", "FigureTableTitle",
})


def _iter_text_runs(para_el: etree._Element):
    """Yield (run_el, text) for runs we may safely anchor a comment on."""
    for r in para_el.iter(f"{WQ}r"):
        parent = r.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        t_el = r.find(f"{WQ}t")
        if t_el is None:
            continue
        yield r, t_el.text or ""


def _run_is_bold(run_el: etree._Element) -> bool:
    r_pr = run_el.find(f"{WQ}rPr")
    if r_pr is None:
        return False
    b = r_pr.find(f"{WQ}b")
    if b is None:
        return False
    return (b.get(f"{WQ}val", "true") or "true").lower() not in ("false", "0", "off")


def _run_is_italic(run_el: etree._Element) -> bool:
    r_pr = run_el.find(f"{WQ}rPr")
    if r_pr is None:
        return False
    i = r_pr.find(f"{WQ}i")
    if i is None:
        return False
    return (i.get(f"{WQ}val", "true") or "true").lower() not in ("false", "0", "off")


def _paragraph_is_bold(para_el: etree._Element) -> bool:
    runs = [r for r, _ in _iter_text_runs(para_el)]
    if not runs:
        return False
    return all(_run_is_bold(r) for r in runs)


def _paragraph_is_italic(para_el: etree._Element) -> bool:
    runs = [r for r, _ in _iter_text_runs(para_el)]
    if not runs:
        return False
    return all(_run_is_italic(r) for r in runs)


def _anchor_comment(comments_root, para_el, comment_id, text, actions, rule):
    """Append a comment anchored on the paragraph's first text run."""
    for run_el, run_text in _iter_text_runs(para_el):
        local_end = min(len(run_text), 1)
        comments_root.append(_make_comment_element(comment_id, text))
        _split_run_for_action(
            run_el,
            0,
            local_end,
            expansion=None,
            comment_id=comment_id,
            change_id=0,
        )
        actions.append({"rule": rule, "comment_id": comment_id})
        return True
    return False


def _is_note_paragraph(para_el: etree._Element) -> bool:
    return para_plain_text(para_el).lstrip().lower().startswith("note.")


def apply_figure_apa7_comments(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Emit one comment per missing APA 7 figure-block property.

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

    body = doc_root.find(f"{WQ}body")
    if body is None:
        return next_change_id, []

    # Direct body children in document order (paragraphs + tables + sectPr).
    children = list(body)
    paras = [el for el in children if el.tag == f"{WQ}p"]

    actions: list[dict] = []

    for pos, label_el in enumerate(paras):
        text = para_plain_text(label_el)
        m = _FIGURE_LABEL_RE.match(text)
        if m is None:
            continue
        num = m.group("num")
        style = get_style_name(label_el)

        # --- bold label -----------------------------------------------------
        if style not in _FIGURE_NUMBER_STYLES and not _paragraph_is_bold(label_el):
            _anchor_comment(
                comments_root, label_el, next_comment_id,
                f"Figure {num}: the label should be bold per APA 7.",
                actions, "figure_apa7_bold",
            )
            next_comment_id += 1

        # --- italic title (next non-empty paragraph) ------------------------
        title_el = None
        for j in range(pos + 1, len(paras)):
            cand_el = paras[j]
            cand_text = para_plain_text(cand_el).strip()
            if not cand_text:
                continue
            if _FIGURE_LABEL_RE.match(cand_text):
                continue
            if cand_text.lower().startswith("note."):
                continue
            title_el = cand_el
            break

        if title_el is None:
            _anchor_comment(
                comments_root, label_el, next_comment_id,
                f"Figure {num}: an italicised title line is missing per APA 7.",
                actions, "figure_apa7_title",
            )
            next_comment_id += 1
        else:
            title_style = get_style_name(title_el)
            if title_style not in _FIGURE_TITLE_STYLES and not _paragraph_is_italic(title_el):
                _anchor_comment(
                    comments_root, title_el, next_comment_id,
                    f"Figure {num}: the title should be italicised per APA 7.",
                    actions, "figure_apa7_title",
                )
                next_comment_id += 1

        # --- description ("Note.") present ----------------------------------
        has_note = False
        for k in range(pos + 1, len(paras)):
            if _is_note_paragraph(paras[k]):
                has_note = True
                break
        if not has_note:
            _anchor_comment(
                comments_root, label_el, next_comment_id,
                f"Figure {num}: add a descriptive note (starting with 'Note.') per APA 7.",
                actions, "figure_apa7_description",
            )
            next_comment_id += 1

        # --- in-text reference before it appears ----------------------------
        referenced = False
        for k in range(pos):
            for ref in _FIGURE_REF_RE.finditer(para_plain_text(paras[k])):
                if ref.group("num").upper() == num.upper():
                    referenced = True
                    break
            if referenced:
                break
        if not referenced:
            _anchor_comment(
                comments_root, label_el, next_comment_id,
                f"Figure {num} is not referenced in the text before it appears "
                "(APA 7: refer to every figure, e.g. 'see Figure 1').",
                actions, "figure_apa7_callout",
            )
            next_comment_id += 1

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

    tmp = output_path + ".fig.tmp"
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
