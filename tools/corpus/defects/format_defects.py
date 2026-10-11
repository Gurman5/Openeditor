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

from lxml import etree

from tools.corpus.checks.abstract import find_abstract
from tools.corpus.checks.fonts import check_fonts
from tools.corpus.checks.layout import check_alignment, check_indent, check_margins, check_spacing
from tools.corpus.checks.page_numbers import (
    check_page_numbers, is_page_instruction, sections_in_use,
)
from tools.corpus.checks.refs import find_references
from tools.corpus.defects.common import (
    DOC, STYLES, Recipe, choose_body, normal_style, own_runs, p_ppr, r_rpr,
    raw_body_paragraphs, run_in_heading_paragraphs, set_first_line, set_font, set_jc,
    set_spacing_line, style_ppr, style_rpr, two_modes,
)
from tools.corpus.docx_view import w
from tools.corpus.style_resolver import StyleResolver, resolve_paragraph

BAD_LEFT_MARGIN_TWIPS = "1080"            # 0.75"
SPACING_1_15 = "276"
DISALLOWED_FONT = "Comic Sans MS"
WRONG_SIZE_FONT, WRONG_SIZE_HALF_POINTS = "Arial", "24"     # Arial 12 pt


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
    target, resolver = normal_style(roots, base_view)
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
            set_jc(style_ppr(style), value)
            pinned[sid] = value

    set_jc(style_ppr(target), "both")
    return {"where": "style", "style": normal, "was": normal_align, "pinned_styles": pinned}


def _justify_paragraphs(roots, rng, base_view) -> dict:
    chosen = choose_body(base_view, rng)
    raw = raw_body_paragraphs(roots[DOC])
    for index in chosen:
        set_jc(p_ppr(raw[index]), "both")
    return {"where": "paragraph", "paragraphs": chosen}


def apply_justified(roots, rng, where, base_view) -> dict:
    return two_modes(where, lambda: _justify_paragraphs(roots, rng, base_view),
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
        chosen = choose_body(base_view, rng)
        raw = raw_body_paragraphs(roots[DOC])
        for index in chosen:
            set_spacing_line(p_ppr(raw[index]), SPACING_1_15)
        return {"where": "paragraph", "paragraphs": chosen, "line": SPACING_1_15}

    def style():
        target, _ = normal_style(roots, base_view)
        raw = raw_body_paragraphs(roots[DOC])
        pinned = []
        for p in find_references(base_view)[1]:          # APA-12 reads entry spacing
            current = resolve_paragraph(p, base_view)["spacing"]
            set_spacing_line(p_ppr(raw[p.index]), current["line"], current["lineRule"])
            pinned.append(p.index)
        set_spacing_line(style_ppr(target), SPACING_1_15)
        return {"where": "style", "style": target.get(w("styleId")), "line": SPACING_1_15,
                "pinned_paragraphs": pinned}

    return two_modes(where, paragraphs, style, "APA-01")


# --------------------------------------------------------------------------
# APA-04: first-line indent removed
# --------------------------------------------------------------------------

def apply_no_first_line_indent(roots, rng, where, base_view) -> dict:
    def paragraphs():
        chosen = choose_body(base_view, rng)
        raw = raw_body_paragraphs(roots[DOC])
        for index in chosen:
            set_first_line(p_ppr(raw[index]), "0")
        return {"where": "paragraph", "paragraphs": chosen}

    def style():
        target, _ = normal_style(roots, base_view)
        raw = raw_body_paragraphs(roots[DOC])
        _, _, keywords = find_abstract(base_view)
        protect = sorted(run_in_heading_paragraphs(base_view)
                         | ({keywords.index} if keywords is not None else set()))
        pinned = []
        for index in protect:                # APA-09 / APA-11 read these indents
            para = resolve_paragraph(base_view.paragraphs[index], base_view)
            if para["sources"].get("indent.firstLine") != "direct":
                set_first_line(p_ppr(raw[index]), para["indent"]["firstLine"])
                pinned.append(index)
        set_first_line(style_ppr(target), "0")
        return {"where": "style", "style": target.get(w("styleId")),
                "pinned_paragraphs": pinned}

    return two_modes(where, paragraphs, style, "APA-04")


# --------------------------------------------------------------------------
# APA-02: fonts
# --------------------------------------------------------------------------

def _font_recipe(family: str, half_points: str | None, name: str):
    def apply(roots, rng, where, base_view) -> dict:
        def paragraphs():
            chosen = choose_body(base_view, rng)
            raw = raw_body_paragraphs(roots[DOC])
            runs = 0
            for index in chosen:
                for r in own_runs(raw[index]):
                    set_font(r_rpr(r), family, half_points)
                    runs += 1
            return {"where": "paragraph", "paragraphs": chosen, "runs": runs,
                    "font": family, "size_half_points": half_points}

        def style():
            target, _ = normal_style(roots, base_view)
            set_font(style_rpr(target), family, half_points)
            return {"where": "style", "style": target.get(w("styleId")),
                    "font": family, "size_half_points": half_points}

        return two_modes(where, paragraphs, style, name)
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
        for r in own_runs(p):
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
