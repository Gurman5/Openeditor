"""Flag figure/table captions that aren't split into APA 7 paragraphs.

APA 7 expects three paragraphs per figure:

  * ``Figure 1`` (bold, label-only, no trailing period)
  * Title of the figure/table in italics, title case, no trailing period
  * ``Note.`` Optional descriptive paragraph in regular text

Authors frequently jam the whole caption into a single Normal-styled
paragraph: ``Figure 1. Two-stage design for the project. Stage 1
entailed…``. The bot's existing style-restyle pass recognises a
bare ``Figure 1`` label paragraph and assigns it the ``Figure Number``
style, but it doesn't touch the single-paragraph form because there's
no clean way to know where the title ends and the note begins.

This module emits a single editorial-judgement comment per offending
caption so the editor can split it by hand. It is intentionally
comment-only — no tracked changes — because mis-splitting a caption
is more harmful than leaving it joined.
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
from app.services.document_zones import (
    get_style_name,
    iter_paragraphs_with_zone,
    para_plain_text,
)
from app.services.language_corrections import WQ, W

# Match a paragraph that opens with a Figure/Table caption label
# followed by some title prose. The lookahead `\S` requires actual
# content after the period (rules out a bare ``Figure 3.`` label
# paragraph — that's already canonical APA 7 shape).
_SINGLE_PARAGRAPH_CAPTION_RE = re.compile(
    r"^\s*(?P<kind>Figure|Fig\.?|Table)\s+"
    r"(?P<num>[A-Z]|\d+(?:\.\d+)?)"
    r"\.\s+\S",
    re.IGNORECASE,
)

# Paragraph styles where the bot has either already done the split or
# is in canonical APA 7 shape. We don't comment on these.
_SKIP_STYLES = frozenset({
    "Figure Number", "FigureNumber",
    "Figure Title", "FigureTitle",
    "Figure/Table Number", "FigureTableNumber",
    "Figure/Table Title", "FigureTableTitle",
    "Figure Notes", "FigureNotes",
    "Table Number", "TableNumber",
    "Table Title", "TableTitle",
    "Table Notes", "TableNotes",
})

# Minimum extra characters beyond `Figure N. ` before we comment —
# captions shorter than ~30 chars after the label are essentially
# title-only and won't benefit from a three-paragraph split.
_MIN_BODY_CHARS = 30

_COMMENT_TEMPLATE = (
    "Per APA 7, figure and table captions should be split across "
    "three paragraphs: a bold label on its own line (e.g. "
    "\"Figure 1\" with no trailing period), an italic title in "
    "title case on the next line, and any descriptive note as "
    "a separate paragraph starting with \"Note.\" Please restructure "
    "this caption."
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


def _needs_apa7_split(para_el: etree._Element) -> bool:
    """Return True when the paragraph holds a full single-paragraph
    figure/table caption that should be split."""
    style = get_style_name(para_el)
    if style in _SKIP_STYLES:
        return False
    text = para_plain_text(para_el)
    if not text:
        return False
    m = _SINGLE_PARAGRAPH_CAPTION_RE.match(text)
    if m is None:
        return False
    # Body content after the label must be substantial; a bare
    # ``Figure 1. Two-stage design.`` is closer to a title-only line.
    label_end = m.end() - 1  # back up to the first non-space char
    remainder = text[label_end:].strip()
    if len(remainder) < _MIN_BODY_CHARS:
        return False
    return True


def apply_caption_apa7_comments(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Emit one APA 7 caption-split comment per offending paragraph.

    Returns ``(next_change_id, actions)`` to match sibling pass shape.
    ``next_change_id`` is threaded unchanged — this pass writes comments
    only, never tracked changes.
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
        if not _needs_apa7_split(para_el):
            continue
        # Anchor the comment on the leading "Figure N." label rather
        # than the whole caption — keeps the gutter marker compact.
        text = para_plain_text(para_el)
        m = _SINGLE_PARAGRAPH_CAPTION_RE.match(text)
        if m is None:
            continue
        label_start = m.start()
        label_end = m.end() - 1  # back off the trailing matched non-space
        # Find the run holding the label start.
        offset = 0
        anchored = False
        for run_el, run_text in _iter_text_runs(para_el):
            run_end = offset + len(run_text)
            if offset <= label_start < run_end:
                local_start = label_start - offset
                local_end = min(label_end - offset, len(run_text))
                if local_end <= local_start:
                    local_end = local_start + 1
                comments_root.append(
                    _make_comment_element(next_comment_id, _COMMENT_TEMPLATE)
                )
                _split_run_for_action(
                    run_el,
                    local_start,
                    local_end,
                    expansion=None,
                    comment_id=next_comment_id,
                    change_id=0,
                )
                actions.append(
                    {
                        "rule": "caption_apa7",
                        "label": text[label_start:label_end],
                        "comment_id": next_comment_id,
                    }
                )
                next_comment_id += 1
                anchored = True
                break
            offset = run_end
        # Silently skip if we couldn't anchor (defensive — should not
        # happen because we already proved the label exists in plain text).
        _ = anchored

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

    tmp = output_path + ".cap.tmp"
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
