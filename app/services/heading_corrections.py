"""Correct section headings as tracked changes.

Two heading problems this pass fixes on the output document:

1. **Numbered headings.** Authors often number their sections
   ("1. Introduction", "2. Literature Review"). JUTLP headings are unnumbered,
   so the leading number is removed.

2. **Non-canonical section names.** A main section may carry a recognised
   alternative wording — e.g. "Findings" (should be "Results"), "Literature
   Review" (should be "Literature"), "Methods" (should be "Method"). These are
   renamed to the canonical JUTLP label.

Both are applied as a single tracked change per heading (``<w:del>`` of the old
text, ``<w:ins>`` of the corrected text), preserving the paragraph's heading
style, so the author sees and can accept/reject the edit.

Combined sections such as "Results and Discussion" are deliberately *not*
renamed — the structural validator flags those separately so the author splits
them, and silently renaming would hide that problem.
"""

from __future__ import annotations

import os
import re
import zipfile
from copy import deepcopy

from lxml import etree

from app.domain.canonical_jultp_template import (
    SECTION_RENAME_MAP,
    strip_leading_section_number,
)
from app.services.document_zones import get_style_name
from app.services.language_corrections import AUTHOR, DATE, WQ, W

_XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

# Curated ``normalised alias -> canonical label`` map (combined "split-me"
# headings already excluded). Shared with Sam's Heading 1 normalisation.
_RENAME_MAP = SECTION_RENAME_MAP


def _norm(text: str) -> str:
    """Lower-case, collapse whitespace, drop trailing colon/period/semicolon.

    Matches the normalisation used to build SECTION_RENAME_MAP's keys (the
    heading text is already number-stripped before lookup)."""
    return re.sub(r"\s+", " ", text.strip().lower()).rstrip(".:;")


def _level_from_name(name: str) -> int | None:
    """Heading level from a style NAME/ID ("Heading 1", "heading1", "Heading")."""
    s = re.sub(r"\s+", "", (name or "").lower())
    if s == "heading":  # some manuscripts use a bare "Heading" for H1
        return 1
    m = re.fullmatch(r"heading(\d+)", s)
    return int(m.group(1)) if m else None


def _build_style_level_map(styles_xml: bytes | None) -> dict[str, int]:
    """Map ``styleId -> heading level`` from ``styles.xml``.

    Documents converted from Google Docs / other tools give heading styles
    numeric ids ("3", "4") with the real name in ``<w:name>`` ("heading 1") —
    so the paragraph's ``w:pStyle/@w:val`` alone ("3") can't tell us the level.
    Resolve it from the style's name, falling back to ``<w:outlineLvl>``
    (0-based: outlineLvl 0 == Heading 1)."""
    levels: dict[str, int] = {}
    if not styles_xml:
        return levels
    try:
        root = etree.fromstring(styles_xml)
    except etree.XMLSyntaxError:
        return levels
    for style in root.findall(f"{WQ}style"):
        if style.get(f"{WQ}type") not in (None, "paragraph"):
            continue
        sid = style.get(f"{WQ}styleId")
        if not sid:
            continue
        name_el = style.find(f"{WQ}name")
        level = _level_from_name(name_el.get(f"{WQ}val") if name_el is not None else "")
        if level is None:
            ppr = style.find(f"{WQ}pPr")
            ol = ppr.find(f"{WQ}outlineLvl") if ppr is not None else None
            if ol is not None:
                try:
                    level = int(ol.get(f"{WQ}val")) + 1
                except (TypeError, ValueError):
                    level = None
        if level is not None:
            levels[sid] = level
    return levels


def _heading_level(style_val: str, level_map: dict[str, int] | None = None) -> int | None:
    """Return 1/2/… for a Heading style, or None for non-heading styles.

    Resolves both the friendly form ("Heading 1") and a numeric style id ("3")
    via ``level_map`` (built from styles.xml). Front-page heading styles
    ("Heading Front Page") return None — they are never numbered."""
    if level_map and style_val in level_map:
        return level_map[style_val]
    return _level_from_name(style_val)


def _direct_text_runs(para_el: etree._Element) -> list[etree._Element]:
    """Direct-child ``<w:r>`` of the paragraph that carry a ``<w:t>``.

    Runs already inside a tracked ``<w:del>``/``<w:ins>`` are skipped so we
    never double-edit our own change.
    """
    return [
        r for r in para_el
        if r.tag == f"{WQ}r" and r.find(f"{WQ}t") is not None
    ]


def _corrected_heading(text: str, level: int) -> str | None:
    """Return the corrected heading text, or None if no change is needed."""
    stripped = strip_leading_section_number(text)
    corrected = stripped
    if level == 1:  # rename recognised aliases only for main (H1) sections
        canonical = _RENAME_MAP.get(_norm(stripped))
        if canonical is not None and _norm(stripped) != _norm(canonical):
            corrected = canonical
    return corrected if corrected != text else None


def _apply_tracked_edit(
    para_el: etree._Element, new_text: str, del_id: int, ins_id: int
) -> bool:
    """Replace the paragraph's direct text runs with a del(old)/ins(new) pair."""
    runs = _direct_text_runs(para_el)
    if not runs:
        return False
    old_text = "".join((r.find(f"{WQ}t").text or "") for r in runs)
    rpr = runs[0].find(f"{WQ}rPr")
    insert_pos = list(para_el).index(runs[0])
    for r in runs:
        para_el.remove(r)

    def _wrap(tag: str, change_id: int, text_tag: str, text: str) -> etree._Element:
        el = etree.Element(f"{WQ}{tag}", nsmap={"w": W})
        el.set(f"{WQ}id", str(change_id))
        el.set(f"{WQ}author", AUTHOR)
        el.set(f"{WQ}date", DATE)
        run = etree.SubElement(el, f"{WQ}r")
        if rpr is not None:
            run.append(deepcopy(rpr))
        t = etree.SubElement(run, f"{WQ}{text_tag}")
        t.text = text
        t.set(_XML_SPACE, "preserve")
        return el

    del_el = _wrap("del", del_id, "delText", old_text)
    ins_el = _wrap("ins", ins_id, "t", new_text)
    para_el.insert(insert_pos, del_el)
    para_el.insert(insert_pos + 1, ins_el)
    return True


def apply_heading_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Strip heading numbers and rename non-canonical section names (tracked).

    Returns ``(next_change_id, actions)``. Each correction consumes two change
    ids (one del, one ins).
    """
    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        styles_xml = z.read("word/styles.xml") if "word/styles.xml" in names else None

    level_map = _build_style_level_map(styles_xml)
    doc_root = etree.fromstring(doc_xml)
    body = doc_root.find(f"{WQ}body")
    actions: list[dict] = []
    if body is not None:
        for para_el in body.iter(f"{WQ}p"):
            level = _heading_level(get_style_name(para_el), level_map)
            if level not in (1, 2):
                continue
            runs = _direct_text_runs(para_el)
            if not runs:
                continue
            text = "".join((r.find(f"{WQ}t").text or "") for r in runs)
            corrected = _corrected_heading(text, level)
            if corrected is None:
                continue
            if _apply_tracked_edit(
                para_el, corrected, next_change_id, next_change_id + 1
            ):
                actions.append({
                    "rule": "heading_correction",
                    "from": text,
                    "to": corrected,
                })
                next_change_id += 2

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

    tmp = output_path + ".headfix.tmp"
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

    return next_change_id, actions
