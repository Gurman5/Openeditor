"""Formatting defect recipes (K-I1 starters + K-I2).

Each recipe breaks exactly one APA matrix row in a known-good document and
names the check that must then fail. Recipes edit parsed XML parts in place:

    apply(roots, rng, where, base_view) -> details (dict, goes in the manifest row)

  roots      part name -> parsed root, opened on first use, e.g. roots[DOC],
             roots[STYLES], roots["word/header1.xml"] (raw XML, edited)
  rng        random.Random seeded by the injector (choose paragraphs with it)
  where      the recipe's default_where unless the caller asks for another
  base_view  accepted_view of the untouched base (to find body paragraphs)

Recipes with two modes default to where="paragraph" (3 body paragraphs chosen
by the seed; paragraphs that start with a run-in heading are skipped);
where="style" changes the Normal style and is only used when asked for. In
style mode, anything another row also reads is "pinned" first (its current
value written onto it directly) so only the recipe's own row changes; pinned
items are listed in the details.

  APA-03   justified text. style: other paragraph styles that inherit their
           alignment from Normal are pinned. LIMITATION: Level 4/5 run-in
           headings sit inside Normal body paragraphs, so in style mode those
           paragraphs become justified too and APA-11 fails as well.
  APA-00   margins (where="section"): first section's left margin -> 0.75".
  APA-01   line spacing 1.15 (line="276" lineRule="auto"). style: reference
           entries are pinned to their current spacing (APA-12 reads it).
  APA-04   first-line indent removed (firstLine="0"). style: the Keywords line
           (APA-09) and run-in heading paragraphs (APA-11) are pinned to 0.5".
  APA-02a  disallowed font: Comic Sans MS.
  APA-02b  allowed font at the wrong size: Arial 12 pt (Arial must be 11).
  APA-05   page number removed (where="header"): every PAGE field is stripped
           from every header in use, result text included.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from lxml import etree

from tools.corpus.checks.abstract import find_abstract
from tools.corpus.checks.fonts import check_fonts
from tools.corpus.checks.headings import find_headings
from tools.corpus.checks.layout import (
    body_paragraphs, check_alignment, check_indent, check_margins, check_spacing,
)
from tools.corpus.checks.page_numbers import (
    check_page_numbers, is_page_instruction, sections_in_use,
)
from tools.corpus.checks.refs import find_references
from tools.corpus.docx_view import AcceptedView, w
from tools.corpus.style_resolver import StyleResolver, resolve_paragraph

DOC = "word/document.xml"
STYLES = "word/styles.xml"
TARGET_PARAGRAPHS = 3
BAD_LEFT_MARGIN_TWIPS = "1080"            # 0.75"
SPACING_1_15 = "276"
DISALLOWED_FONT = "Comic Sans MS"
WRONG_SIZE_FONT, WRONG_SIZE_HALF_POINTS = "Arial", "24"     # Arial 12 pt


@dataclass(frozen=True)
class Recipe:
    id: str                          # registry key, e.g. "APA-02a"
    matrix_id: str                   # the row it breaks, e.g. "APA-02"
    name: str
    apply: Callable[[dict, random.Random, str, AcceptedView], dict]
    check: Callable[[AcceptedView], dict]
    default_where: str
    wheres: tuple[str, ...]          # values this recipe accepts


# --------------------------------------------------------------------------
# XML helpers: insert children in OOXML schema order so Word opens the result
# --------------------------------------------------------------------------

_PPR_ORDER = [w(t) for t in (
    "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl",
    "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens",
    "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN",
    "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing",
    "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment",
    "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange")]
_RPR_ORDER = [w(t) for t in (
    "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike",
    "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish",
    "webHidden", "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight",
    "u", "effect", "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang",
    "eastAsianLayout", "specVanish", "oMath", "rPrChange")]
_STYLE_ORDER = [w(t) for t in (
    "name", "aliases", "basedOn", "next", "link", "autoRedefine", "hidden", "uiPriority",
    "semiHidden", "unhideWhenUsed", "qFormat", "locked", "personal", "personalCompose",
    "personalReply", "rsid", "pPr", "rPr", "tblPr", "trPr", "tcPr", "tblStylePr")]


def _child(parent, tag: str, order: list[str]) -> etree._Element:
    """Existing <tag> child of parent, or a new one inserted in schema order."""
    qtag = w(tag)
    found = parent.find(qtag)
    if found is not None:
        return found
    el = etree.Element(qtag)
    rank = order.index(qtag)
    for i, existing in enumerate(parent):
        if existing.tag in order and order.index(existing.tag) > rank:
            parent.insert(i, el)
            return el
    parent.append(el)
    return el


def _p_ppr(p) -> etree._Element:
    ppr = p.find(w("pPr"))
    if ppr is None:
        ppr = etree.Element(w("pPr"))
        p.insert(0, ppr)                     # w:pPr is always first in w:p
    return ppr


def _r_rpr(r) -> etree._Element:
    rpr = r.find(w("rPr"))
    if rpr is None:
        rpr = etree.Element(w("rPr"))
        r.insert(0, rpr)                     # w:rPr is always first in w:r
    return rpr


def _style_ppr(style) -> etree._Element:
    return _child(style, "pPr", _STYLE_ORDER)


def _style_rpr(style) -> etree._Element:
    return _child(style, "rPr", _STYLE_ORDER)


def set_jc(ppr, value: str) -> None:
    _child(ppr, "jc", _PPR_ORDER).set(w("val"), value)


def _set_spacing_line(ppr, line: str, rule: str = "auto") -> None:
    spacing = _child(ppr, "spacing", _PPR_ORDER)
    spacing.set(w("line"), line)
    spacing.set(w("lineRule"), rule)


def _set_first_line(ppr, value: str) -> None:
    ind = _child(ppr, "ind", _PPR_ORDER)
    ind.attrib.pop(w("hanging"), None)
    ind.set(w("firstLine"), value)


def _set_font(rpr, family: str, half_points: str | None = None) -> None:
    """Explicit font (theme font attributes removed so they can't win)."""
    old = rpr.find(w("rFonts"))
    if old is not None:
        rpr.remove(old)
    fonts = _child(rpr, "rFonts", _RPR_ORDER)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(w(attr), family)
    if half_points is not None:
        for tag in ("sz", "szCs"):
            _child(rpr, tag, _RPR_ORDER).set(w("val"), half_points)


# --------------------------------------------------------------------------
# Choosing targets
# --------------------------------------------------------------------------

def _raw_body_paragraphs(document_root) -> list[etree._Element]:
    """Body w:p in the same order as accepted_view (base has no tracked changes)."""
    body = document_root.find(w("body"))
    return [p for p in body.iter(w("p"))
            if not any(a.tag == w("txbxContent") for a in p.iterancestors())]


def _run_in_heading_paragraphs(base_view) -> set[int]:
    _, _, headings = find_headings(base_view)
    return {h["paragraph"] for h in headings if h["found_by"] == "run-in"}


def _choose_body(base_view, rng) -> list[int]:
    run_in = _run_in_heading_paragraphs(base_view)
    candidates = [p.index for p in body_paragraphs(base_view) if p.index not in run_in]
    if not candidates:
        raise ValueError("base has no body paragraphs to change")
    return sorted(rng.sample(candidates, min(TARGET_PARAGRAPHS, len(candidates))))


def _own_runs(p) -> list[etree._Element]:
    """Runs belonging to p (not to paragraphs nested inside it, e.g. text boxes)."""
    runs = []
    for r in p.iter(w("r")):
        owner = r.getparent()
        while owner is not None and owner.tag != w("p"):
            owner = owner.getparent()
        if owner is p:
            runs.append(r)
    return runs


def _normal_style(roots, base_view) -> tuple[etree._Element, StyleResolver]:
    resolver = StyleResolver(base_view.parts)
    normal = resolver.default_paragraph_style
    if normal is None:
        raise ValueError("base has no default paragraph style")
    style = next(s for s in roots[STYLES].iter(w("style")) if s.get(w("styleId")) == normal)
    return style, resolver


def _two_modes(where, paragraph_fn, style_fn, name):
    if where == "paragraph":
        return paragraph_fn()
    if where == "style":
        return style_fn()
    raise ValueError(f"{name} recipe: where must be 'paragraph' or 'style', got {where!r}")


# --------------------------------------------------------------------------
# APA-03: justified text
# --------------------------------------------------------------------------

def _style_alignment(resolver: StyleResolver, style_id: str) -> tuple[str, str]:
    """(effective alignment of a paragraph style, where it comes from)."""
    for sid, style in resolver.chain(style_id):
        ppr = style.find(w("pPr"))
        jc = None if ppr is None else ppr.find(w("jc"))
        if jc is not None:
            return jc.get(w("val")), sid
    defaults = resolver.default_ppr
    jc = None if defaults is None else defaults.find(w("jc"))
    if jc is not None:
        return jc.get(w("val")), "docDefaults"
    return "left", "word-default"


def _justify_style(roots, base_view) -> dict:
    target, resolver = _normal_style(roots, base_view)
    normal = target.get(w("styleId"))
    normal_align, _ = _style_alignment(resolver, normal)

    pinned = {}
    for style in roots[STYLES].iter(w("style")):
        sid = style.get(w("styleId"))
        if sid == normal or style.get(w("type")) != "paragraph":
            continue
        if normal not in [s for s, _ in resolver.chain(sid)]:
            continue
        value, source = _style_alignment(resolver, sid)
        if source in (normal, "docDefaults", "word-default"):
            set_jc(_style_ppr(style), value)
            pinned[sid] = value

    set_jc(_style_ppr(target), "both")
    return {"where": "style", "style": normal, "was": normal_align, "pinned_styles": pinned}


def _justify_paragraphs(roots, rng, base_view) -> dict:
    chosen = _choose_body(base_view, rng)
    raw = _raw_body_paragraphs(roots[DOC])
    for index in chosen:
        set_jc(_p_ppr(raw[index]), "both")
    return {"where": "paragraph", "paragraphs": chosen}


def apply_justified(roots, rng, where, base_view) -> dict:
    return _two_modes(where, lambda: _justify_paragraphs(roots, rng, base_view),
                      lambda: _justify_style(roots, base_view), "APA-03")


# --------------------------------------------------------------------------
# APA-00: margins
# --------------------------------------------------------------------------

def apply_bad_margin(roots, rng, where, base_view) -> dict:
    sect = next(roots[DOC].iter(w("sectPr")), None)
    if sect is None:
        raise ValueError("base has no section properties")
    mar = sect.find(w("pgMar"))
    if mar is None:
        raise ValueError("base section has no w:pgMar")
    old = mar.get(w("left"))
    mar.set(w("left"), BAD_LEFT_MARGIN_TWIPS)
    return {"where": "section", "section": 0, "side": "left", "was": old,
            "twips": BAD_LEFT_MARGIN_TWIPS}


# --------------------------------------------------------------------------
# APA-01: line spacing 1.15
# --------------------------------------------------------------------------

def apply_spacing_1_15(roots, rng, where, base_view) -> dict:
    def paragraphs():
        chosen = _choose_body(base_view, rng)
        raw = _raw_body_paragraphs(roots[DOC])
        for index in chosen:
            _set_spacing_line(_p_ppr(raw[index]), SPACING_1_15)
        return {"where": "paragraph", "paragraphs": chosen, "line": SPACING_1_15}

    def style():
        target, _ = _normal_style(roots, base_view)
        raw = _raw_body_paragraphs(roots[DOC])
        pinned = []
        for p in find_references(base_view)[1]:          # APA-12 reads entry spacing
            current = resolve_paragraph(p, base_view)["spacing"]
            _set_spacing_line(_p_ppr(raw[p.index]), current["line"], current["lineRule"])
            pinned.append(p.index)
        _set_spacing_line(_style_ppr(target), SPACING_1_15)
        return {"where": "style", "style": target.get(w("styleId")), "line": SPACING_1_15,
                "pinned_paragraphs": pinned}

    return _two_modes(where, paragraphs, style, "APA-01")


# --------------------------------------------------------------------------
# APA-04: first-line indent removed
# --------------------------------------------------------------------------

def apply_no_first_line_indent(roots, rng, where, base_view) -> dict:
    def paragraphs():
        chosen = _choose_body(base_view, rng)
        raw = _raw_body_paragraphs(roots[DOC])
        for index in chosen:
            _set_first_line(_p_ppr(raw[index]), "0")
        return {"where": "paragraph", "paragraphs": chosen}

    def style():
        target, _ = _normal_style(roots, base_view)
        raw = _raw_body_paragraphs(roots[DOC])
        _, _, keywords = find_abstract(base_view)
        protect = sorted(_run_in_heading_paragraphs(base_view)
                         | ({keywords.index} if keywords is not None else set()))
        pinned = []
        for index in protect:                # APA-09 / APA-11 read these indents
            para = resolve_paragraph(base_view.paragraphs[index], base_view)
            if para["sources"].get("indent.firstLine") != "direct":
                _set_first_line(_p_ppr(raw[index]), para["indent"]["firstLine"])
                pinned.append(index)
        _set_first_line(_style_ppr(target), "0")
        return {"where": "style", "style": target.get(w("styleId")),
                "pinned_paragraphs": pinned}

    return _two_modes(where, paragraphs, style, "APA-04")


# --------------------------------------------------------------------------
# APA-02: fonts
# --------------------------------------------------------------------------

def _font_recipe(family: str, half_points: str | None, name: str):
    def apply(roots, rng, where, base_view) -> dict:
        def paragraphs():
            chosen = _choose_body(base_view, rng)
            raw = _raw_body_paragraphs(roots[DOC])
            runs = 0
            for index in chosen:
                for r in _own_runs(raw[index]):
                    _set_font(_r_rpr(r), family, half_points)
                    runs += 1
            return {"where": "paragraph", "paragraphs": chosen, "runs": runs,
                    "font": family, "size_half_points": half_points}

        def style():
            target, _ = _normal_style(roots, base_view)
            _set_font(_style_rpr(target), family, half_points)
            return {"where": "style", "style": target.get(w("styleId")),
                    "font": family, "size_half_points": half_points}

        return _two_modes(where, paragraphs, style, name)
    return apply


# --------------------------------------------------------------------------
# APA-05: page number removed
# --------------------------------------------------------------------------

def _strip_page_fields(root) -> int:
    """Remove every PAGE field (both forms, result text included). Returns the count."""
    removed = 0
    for fld in list(root.iter(w("fldSimple"))):
        if is_page_instruction(fld.get(w("instr")) or ""):
            fld.getparent().remove(fld)
            removed += 1
    for p in list(root.iter(w("p"))):
        open_fields: list[dict] = []
        doomed: list[etree._Element] = []
        for r in _own_runs(p):
            fc = r.find(w("fldChar"))
            kind = None if fc is None else fc.get(w("fldCharType"))
            if kind == "begin":
                open_fields.append({"runs": [], "instr": ""})
            for field in open_fields:
                field["runs"].append(r)
            if open_fields:
                for instr in r.iter(w("instrText")):
                    open_fields[-1]["instr"] += instr.text or ""
            if kind == "end" and open_fields:
                field = open_fields.pop()
                if is_page_instruction(field["instr"]):
                    doomed.extend(field["runs"])
                    removed += 1
        for r in doomed:
            if r.getparent() is not None:
                r.getparent().remove(r)
    return removed


def apply_no_page_number(roots, rng, where, base_view) -> dict:
    parts = sorted({part for section in sections_in_use(base_view, "header")
                    for part in section.values() if part})
    removed = sum(_strip_page_fields(roots[part]) for part in parts)
    if removed == 0:
        raise ValueError("base headers have no PAGE field to remove")
    return {"where": "header", "parts": parts, "fields_removed": removed}


FORMAT_RECIPES = {r.id: r for r in (
    Recipe("APA-03", "APA-03", "justified", apply_justified, check_alignment,
           default_where="paragraph", wheres=("paragraph", "style")),
    Recipe("APA-00", "APA-00", "left_margin_0.75in", apply_bad_margin, check_margins,
           default_where="section", wheres=("section",)),
    Recipe("APA-01", "APA-01", "spacing_1.15", apply_spacing_1_15, check_spacing,
           default_where="paragraph", wheres=("paragraph", "style")),
    Recipe("APA-04", "APA-04", "no_first_line_indent", apply_no_first_line_indent,
           check_indent, default_where="paragraph", wheres=("paragraph", "style")),
    Recipe("APA-02a", "APA-02", "disallowed_font_comic_sans",
           _font_recipe(DISALLOWED_FONT, None, "APA-02a"), check_fonts,
           default_where="paragraph", wheres=("paragraph", "style")),
    Recipe("APA-02b", "APA-02", "arial_12pt_wrong_size",
           _font_recipe(WRONG_SIZE_FONT, WRONG_SIZE_HALF_POINTS, "APA-02b"), check_fonts,
           default_where="paragraph", wheres=("paragraph", "style")),
    Recipe("APA-05", "APA-05", "no_page_number", apply_no_page_number, check_page_numbers,
           default_where="header", wheres=("header",)),
)}
