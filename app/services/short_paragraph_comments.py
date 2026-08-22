"""Flag short prose paragraphs (<3 sentences) with Word comments.

This pass emits comments only (no tracked-change rewrites). It scans prose
paragraphs in the front/body zones and skips headings, references, captions,
and end-matter using the shared zone/style skip logic.
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
    iter_paragraphs_with_zone,
    should_skip_prose_paragraph,
)
from app.services.language_corrections import WQ, W

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _iter_text_runs(para_el: etree._Element):
    """Yield editable visible text runs from ``para_el``.

    Runs inside tracked-change wrappers are ignored so sentence counting and
    anchors are based on currently visible text.
    """
    for r in para_el.iter(f"{WQ}r"):
        parent = r.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        t_el = r.find(f"{WQ}t")
        if t_el is None:
            continue
        yield r, t_el.text or ""


def _paragraph_text(para_el: etree._Element) -> str:
    return "".join(text for _, text in _iter_text_runs(para_el))


def _sentence_count(text: str) -> int:
    """Count sentence-like spans in ``text``.

    A sentence is any non-empty chunk after splitting on terminal punctuation
    boundaries. If punctuation is missing, one non-empty chunk counts as one
    sentence.
    """
    chunks = [chunk.strip() for chunk in _SENTENCE_SPLIT.split(text) if chunk.strip()]
    if not chunks:
        return 0
    return sum(1 for chunk in chunks if any(ch.isalnum() for ch in chunk))


def _first_token_span(text: str) -> tuple[int, int] | None:
    match = re.search(r"\S+", text)
    if match is None:
        return None
    return match.start(), match.end()


def apply_short_paragraph_comments(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Add comments to paragraphs with fewer than three sentences.

    Returns ``(next_change_id, actions)`` for parity with sibling passes.
    This pass writes only comments, so ``next_change_id`` is unchanged.
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

    for para_idx, (para_el, zone) in enumerate(iter_paragraphs_with_zone(doc_root)):
        # The 3-sentence guideline is a body-prose recommendation. Front-
        # matter (title, abstract, practitioner notes, keywords) and end-
        # matter (acknowledgements, references) follow different formatting
        # rules and should never be flagged for expansion.
        if zone != "body":
            continue
        if should_skip_prose_paragraph(para_el, zone):
            continue

        text = _paragraph_text(para_el)
        if not text.strip():
            continue

        # Guard against single-token labels, numeric cells, and other
        # non-prose fragments that slipped through style-based filtering.
        # A real body paragraph has at least one space and >= 12 alphabetic
        # characters; anything shorter is almost certainly a heading, label,
        # or numeric value where the 3-sentence guideline doesn't apply.
        stripped = text.strip()
        if " " not in stripped:
            continue
        alpha_count = sum(1 for ch in text if ch.isalpha())
        if alpha_count < 12:
            continue

        # Heading-like paragraphs styled as Normal still slip through the
        # style filter. Detect them structurally: prose paragraphs end in
        # terminal punctuation (.!?) — bare headings and table captions
        # ("Descriptive statistics: Ethics of data", "Research Approach")
        # do not. Combine with an upper bound on length so we only catch
        # short label-like paragraphs, never real body sentences that
        # forgot a final stop.
        last_char = stripped[-1]
        if last_char not in ".!?" and len(stripped) < 80:
            continue

        count = _sentence_count(text)
        if count >= 3:
            continue

        token_span = _first_token_span(text)
        if token_span is None:
            continue

        anchor_start, anchor_end = token_span
        run_offset = 0
        anchor_location = None
        for run_el, run_text in _iter_text_runs(para_el):
            run_len = len(run_text)
            if run_offset + run_len > anchor_start:
                intra_start = anchor_start - run_offset
                intra_end = min(anchor_end - run_offset, run_len)
                anchor_location = (run_el, intra_start, intra_end)
                break
            run_offset += run_len

        if anchor_location is None:
            continue

        message = (
            f"This paragraph has {count} sentence(s). Please expand it to at least "
            "three sentences where appropriate."
        )

        comments_root.append(_make_comment_element(next_comment_id, message))

        run_el, intra_start, intra_end = anchor_location
        _split_run_for_action(
            run_el,
            intra_start,
            intra_end,
            expansion=None,
            comment_id=next_comment_id,
            change_id=0,
        )

        actions.append(
            {
                "rule": "PARA_SHORT",
                "para_idx": para_idx,
                "sentence_count": count,
                "comment_id": next_comment_id,
            }
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

    tmp = output_path + ".shortpara.tmp"
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
