"""Normalise run-level font (and reference size) to the JUTLP template font.

The Normal style is pinned to Arial 11pt elsewhere, so body text that *inherits*
Normal is already correct. But manuscripts converted from other tools carry
**direct** run-level font overrides (commonly Times New Roman) and direct sizes
that survive on reference entries, the abstract, and headings — the paragraph
style can't override a direct run property, so those runs still render in the
wrong font/size.

This pass applies tracked run-property changes:

* **Reference entries** must be Arial 11pt (the APA 7 style inherits the 11pt
  base): every reference run is set to Arial + sz/szCs=22.
* **Every other run** that carries a *direct* non-Arial Latin font is switched
  to Arial (font family only — its size is left alone, e.g. headings keep their
  heading size). Runs with no direct font are untouched: they correctly inherit
  Arial from their (template) paragraph style.
"""

from __future__ import annotations

import os
import zipfile
from copy import deepcopy

from lxml import etree

from app.services.language_corrections import AUTHOR, DATE, WQ

_TARGET_FONT = "Arial"
_TARGET_SZ = "22"  # 11pt in half-points

# Reference entry style ids/names (same set the indent + format passes use).
_REF_STYLE_IDS_KNOWN = frozenset({
    "APA7ReferenceListEntry", "APA 7 Reference List Entry",
    "APA7 Reference List Entry", "APAReferenceListEntry", "Reference List Entry",
})
_REF_STYLE_NAMES = frozenset({
    "apa 7 reference list entry", "apa7 reference list entry",
    "reference list entry",
})


def _ref_style_ids(styles_xml: bytes | None) -> set[str]:
    ids = set(_REF_STYLE_IDS_KNOWN)
    if not styles_xml:
        return ids
    try:
        root = etree.fromstring(styles_xml)
    except etree.XMLSyntaxError:
        return ids
    for style_el in root.findall(f"{WQ}style"):
        name_el = style_el.find(f"{WQ}name")
        name = (name_el.get(f"{WQ}val", "") if name_el is not None else "").strip().lower()
        if name in _REF_STYLE_NAMES:
            sid = style_el.get(f"{WQ}styleId")
            if sid:
                ids.add(sid)
    return ids


def _para_style_val(para_el: etree._Element) -> str:
    pPr = para_el.find(f"{WQ}pPr")
    if pPr is None:
        return ""
    pStyle = pPr.find(f"{WQ}pStyle")
    return pStyle.get(f"{WQ}val", "") if pStyle is not None else ""


def _direct_text_runs(para_el: etree._Element):
    """Yield runs carrying visible text that belong to this paragraph.

    Includes runs nested in a ``w:hyperlink`` (e.g. a reference DOI link, which
    often keeps the original Times font) but excludes runs inside a tracked
    ``w:del`` (being deleted) and runs inside a nested ``w:p`` (a text box)."""
    for r in para_el.iter(f"{WQ}r"):
        anc = r.getparent()
        owner_p = None
        skip = False
        while anc is not None:
            if anc.tag == f"{WQ}del":
                skip = True
                break
            if anc.tag == f"{WQ}p":
                owner_p = anc
                break
            anc = anc.getparent()
        if skip or owner_p is not para_el:
            continue
        t = r.find(f"{WQ}t")
        if t is None or not (t.text or "").strip():
            continue
        yield r


def _current_font(r_pr) -> str | None:
    if r_pr is None:
        return None
    rf = r_pr.find(f"{WQ}rFonts")
    return rf.get(f"{WQ}ascii") if rf is not None else None


def _current_sz(r_pr) -> str | None:
    if r_pr is None:
        return None
    sz = r_pr.find(f"{WQ}sz")
    return sz.get(f"{WQ}val") if sz is not None else None


def _is_inside_insertion(run_el) -> bool:
    """True if ``run_el`` sits inside a tracked ``<w:ins>`` (up to its paragraph).

    Such a run is itself newly-inserted text (e.g. a reconstructed reference
    rebuilt by the APA-7 format pass, or an injected DOI hyperlink), so its
    font is part of the insertion — we set it directly rather than wrapping it
    in an ``<w:rPrChange>`` (a tracked property-change nested inside a tracked
    insertion renders oddly in Word)."""
    anc = run_el.getparent()
    while anc is not None and anc.tag != f"{WQ}p":
        if anc.tag == f"{WQ}ins":
            return True
        anc = anc.getparent()
    return False


def _apply_tracked_run_font(run_el, set_font: bool, set_size: bool, change_id: int) -> bool:
    r_pr = run_el.find(f"{WQ}rPr")
    if r_pr is None:
        r_pr = etree.Element(f"{WQ}rPr")
        run_el.insert(0, r_pr)
    old_r_pr = deepcopy(r_pr)
    # Don't nest a prior rPrChange inside the new snapshot.
    for prev in old_r_pr.findall(f"{WQ}rPrChange"):
        old_r_pr.remove(prev)

    if set_font:
        rf = r_pr.find(f"{WQ}rFonts")
        if rf is None:
            rf = etree.SubElement(r_pr, f"{WQ}rFonts")
        for attr in ("ascii", "hAnsi", "cs"):
            rf.set(f"{WQ}{attr}", _TARGET_FONT)
    if set_size:
        for tag in ("sz", "szCs"):
            el = r_pr.find(f"{WQ}{tag}")
            if el is None:
                el = etree.SubElement(r_pr, f"{WQ}{tag}")
            el.set(f"{WQ}val", _TARGET_SZ)

    # Inserted runs carry their font as part of the insertion — no rPrChange.
    if _is_inside_insertion(run_el):
        return True

    change = etree.SubElement(r_pr, f"{WQ}rPrChange")
    change.set(f"{WQ}id", str(change_id))
    change.set(f"{WQ}author", AUTHOR)
    change.set(f"{WQ}date", DATE)
    change.append(old_r_pr)
    return True


def apply_run_font_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Set references to Arial 11pt and convert leftover direct non-Arial runs
    to Arial, as tracked changes. Returns ``(next_change_id, actions)``."""
    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        styles_xml = z.read("word/styles.xml") if "word/styles.xml" in names else None

    ref_ids = _ref_style_ids(styles_xml)
    doc_root = etree.fromstring(doc_xml)
    body = doc_root.find(f"{WQ}body")
    actions: list[dict] = []
    if body is not None:
        for para_el in body.iter(f"{WQ}p"):
            is_ref = _para_style_val(para_el) in ref_ids
            for run_el in _direct_text_runs(para_el):
                r_pr = run_el.find(f"{WQ}rPr")
                # Skip runs we've already changed.
                if r_pr is not None and r_pr.find(f"{WQ}rPrChange") is not None:
                    continue
                font = _current_font(r_pr)
                if is_ref:
                    set_font = font != _TARGET_FONT
                    set_size = _current_sz(r_pr) != _TARGET_SZ
                else:
                    # Only fix a wrong DIRECT font; leave inheriting runs and
                    # sizes alone (headings keep their own size).
                    set_font = font is not None and font != _TARGET_FONT
                    set_size = False
                if not (set_font or set_size):
                    continue
                _apply_tracked_run_font(run_el, set_font, set_size, next_change_id)
                actions.append({
                    "rule": "run_font",
                    "ref": is_ref,
                    "font_fixed": set_font,
                    "size_fixed": set_size,
                })
                next_change_id += 1

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
    tmp = output_path + ".runfont.tmp"
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
