"""Normalise document fonts to the APA default (Calibri 11pt, C-27).

Two layers, matching how Word resolves fonts:

* **Run level (tracked).** Every text run whose *effective* Latin typeface is
  not the default is rewritten with a tracked ``w:rPrChange``: runs carrying
  a wrong explicit font, runs bound only to the Office theme (which resolves
  to Cambria via ``theme1.xml``, not to the paragraph style), and runs
  inheriting a wrong font from a linked character style. Runs with no direct
  font information are left alone — they correctly inherit from their
  paragraph style, which the style layer owns.
* **Style level (silent).** Every ``w:rFonts`` in ``styles.xml`` and the
  ``w:docDefaults`` run default are pinned to the default. Styles carry no
  tracked-change mechanism, so — like ``_ensure_normal_style_body_rpr`` —
  this is a direct edit.

Symbol typefaces (Symbol / Wingdings / Webdings…) are never rewritten at
either layer: a ∑ set in Symbol that the sweep "fixed" to Calibri would
silently corrupt the manuscript.

Reference entries additionally get 11pt (``sz``/``szCs``); every other run
keeps its size (headings keep their heading size).

Parts swept: ``document.xml``, headers, footers, footnotes, endnotes and
comments. ``styles.xml`` is swept for style-level fonts (and read for
reference-entry style ids).
"""

from __future__ import annotations

import os
import zipfile

from copy import deepcopy
from lxml import etree

from app.services.config import DEFAULT_FONT, DEFAULT_FONT_SIZE
from app.services.docx_format_helpers import (
    is_symbol_font,
    rfonts_explicit,
    rfonts_needs_fix,
    set_explicit_font,
)
from app.services.language_corrections import AUTHOR, DATE, WQ

_TARGET_FONT = DEFAULT_FONT
_TARGET_SZ = str(int(DEFAULT_FONT_SIZE) * 2)  # 11pt in half-points

# Parts (besides document.xml) whose text runs the sweep covers. Headers and
# footers repeat on every page; footnotes/endnotes/comments carry
# author-facing text — a Times run there is as wrong as one in the body.
_TEXT_PART_SUFFIXES = (".xml",)
_TEXT_PART_NAMES = ("word/footnotes.xml", "word/endnotes.xml", "word/comments.xml")


def _is_text_part(name: str) -> bool:
    if name == "word/document.xml":
        return True
    if name in _TEXT_PART_NAMES:
        return True
    base = name.rsplit("/", 1)[-1]
    return (base.startswith("header") or base.startswith("footer")) and name.endswith(
        _TEXT_PART_SUFFIXES
    )


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


def _char_style_font_map(styles_xml: bytes | None) -> dict[str, dict[str, str]]:
    """Return character-style id -> explicit ``{attr: typeface}`` map.

    Used to detect runs that inherit a wrong font from a linked character
    style (e.g. a "Times" char style): such runs carry no direct ``w:rFonts``
    but still render in the wrong typeface, so the sweep pins them directly.
    """
    out: dict[str, dict[str, str]] = {}
    if not styles_xml:
        return out
    try:
        root = etree.fromstring(styles_xml)
    except etree.XMLSyntaxError:
        return out
    for style_el in root.findall(f"{WQ}style"):
        if style_el.get(f"{WQ}type", "paragraph") != "character":
            continue
        sid = style_el.get(f"{WQ}styleId")
        if not sid:
            continue
        rPr = style_el.find(f"{WQ}rPr")
        rfonts = rPr.find(f"{WQ}rFonts") if rPr is not None else None
        fonts = rfonts_explicit(rfonts)
        if fonts:
            out[sid] = fonts
    return out


def _run_char_style_id(run_el: etree._Element) -> str:
    rPr = run_el.find(f"{WQ}rPr")
    if rPr is None:
        return ""
    rStyle = rPr.find(f"{WQ}rStyle")
    return rStyle.get(f"{WQ}val", "") if rStyle is not None else ""


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
    ``w:del`` (being deleted) and runs inside a nested ``w:p`` (a text box).
    Field-code runs (``w:instrText``, e.g. the PAGE field) carry no ``w:t``
    and are skipped — the page-number run already declares Calibri."""
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
        set_explicit_font(rf, _TARGET_FONT)
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


def _sweep_styles_fonts(styles_root: etree._Element) -> list[str]:
    """Pin every style-level ``w:rFonts`` to the target font (silent).

    Symbol-only styles are skipped. Returns the changed style ids.
    Sizes are deliberately untouched — headings keep their own size.
    """
    changed: list[str] = []
    for style_el in styles_root.findall(f"{WQ}style"):
        rPr = style_el.find(f"{WQ}rPr")
        if rPr is None:
            continue
        rfonts = rPr.find(f"{WQ}rFonts")
        if rfonts is None:
            continue
        explicit = rfonts_explicit(rfonts)
        if explicit and all(is_symbol_font(v) for v in explicit.values()):
            continue
        if set_explicit_font(rfonts, _TARGET_FONT):
            changed.append(style_el.get(f"{WQ}styleId", ""))
    return changed


def _sweep_docdefaults(styles_root: etree._Element) -> bool:
    """Pin ``w:docDefaults`` run fonts to the target (silent).

    A theme-bound docDefault resolves through ``theme1.xml`` (minor font =
    Cambria in our template), so any run inheriting all the way down renders
    in Cambria. Pinning explicit fonts here closes that leak.
    """
    changed = False
    for rPr in styles_root.findall(f"{WQ}docDefaults/{WQ}rPrDefault/{WQ}rPr"):
        rfonts = rPr.find(f"{WQ}rFonts")
        if rfonts is None:
            rfonts = etree.SubElement(rPr, f"{WQ}rFonts")
        if set_explicit_font(rfonts, _TARGET_FONT):
            changed = True
    return changed


def apply_run_font_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Normalise fonts to Calibri 11pt across runs and styles.

    Run-level fixes are tracked changes; style-level (``styles.xml``) and
    ``docDefaults`` fixes are silent direct edits (styles carry no
    tracked-change mechanism). Returns ``(next_change_id, actions)``.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        parts = {n: z.read(n) for n in names if _is_text_part(n)}
        styles_xml = z.read("word/styles.xml") if "word/styles.xml" in names else None

    ref_ids = _ref_style_ids(styles_xml)
    char_fonts = _char_style_font_map(styles_xml)
    actions: list[dict] = []
    rewritten: dict[str, bytes] = {}

    # ── Style layer (silent) ─────────────────────────────────────────────
    if styles_xml is not None:
        styles_root = etree.fromstring(styles_xml)
        for sid in _sweep_styles_fonts(styles_root):
            actions.append({
                "rule": "style_font",
                "ref": False,
                "font_fixed": True,
                "size_fixed": False,
                "part": "word/styles.xml",
                "scope": "style",
                "style": sid,
            })
        defaults_fixed = _sweep_docdefaults(styles_root)
        if defaults_fixed:
            actions.append({
                "rule": "docdefaults_font",
                "ref": False,
                "font_fixed": True,
                "size_fixed": False,
                "part": "word/styles.xml",
                "scope": "defaults",
                "style": "",
            })
        if any(a["scope"] in ("style", "defaults") for a in actions):
            rewritten["word/styles.xml"] = etree.tostring(
                styles_root, xml_declaration=True, encoding="UTF-8", standalone=True
            )

    # ── Run layer (tracked) ──────────────────────────────────────────────
    for part_name, part_xml in parts.items():
        root = etree.fromstring(part_xml)
        part_changed = False
        for para_el in root.iter(f"{WQ}p"):
            is_ref = _para_style_val(para_el) in ref_ids
            for run_el in _direct_text_runs(para_el):
                r_pr = run_el.find(f"{WQ}rPr")
                # Skip runs we've already changed.
                if r_pr is not None and r_pr.find(f"{WQ}rPrChange") is not None:
                    continue
                rfonts = r_pr.find(f"{WQ}rFonts") if r_pr is not None else None
                char_id = _run_char_style_id(run_el)
                reason = rfonts_needs_fix(
                    rfonts, char_fonts.get(char_id), _TARGET_FONT
                )
                if is_ref:
                    set_font = reason is not None
                    set_size = _current_sz(r_pr) != _TARGET_SZ
                else:
                    set_font = reason is not None
                    set_size = False
                if not (set_font or set_size):
                    continue
                _apply_tracked_run_font(run_el, set_font, set_size, next_change_id)
                actions.append({
                    "rule": "run_font",
                    "ref": is_ref,
                    "font_fixed": set_font,
                    "size_fixed": set_size,
                    "part": part_name,
                    "scope": "run",
                    "reason": reason or ("size" if set_size else "explicit"),
                })
                next_change_id += 1
                part_changed = True
        if part_changed:
            rewritten[part_name] = etree.tostring(
                root, xml_declaration=True, encoding="UTF-8", standalone=True
            )

    if not rewritten:
        if input_path != output_path:
            with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
                output_path, "w", zipfile.ZIP_DEFLATED
            ) as zout:
                for item in zin.infolist():
                    zout.writestr(item, zin.read(item.filename))
        return next_change_id, actions

    tmp = output_path + ".runfont.tmp"
    try:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
            tmp, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                if item.filename in rewritten:
                    zout.writestr(item, rewritten[item.filename])
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
