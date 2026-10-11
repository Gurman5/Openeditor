"""Formatting defect recipes (K-I1 starter set; K-I2 adds the rest).

Each recipe breaks exactly one APA matrix row in a known-good document and
names the check that must then fail. Recipes edit parsed XML parts in place:

    apply(roots, rng, where, base_view) -> details (dict, goes in the manifest row)

  roots      {"word/document.xml": <root>, "word/styles.xml": <root>} (raw XML, edited)
  rng        random.Random seeded by the injector (choose paragraphs with it)
  where      the recipe's default_where unless the caller asks for another
  base_view  accepted_view of the untouched base (to find body paragraphs)

Starter recipes:
  APA-03  justified text (default where="paragraph")
          where="paragraph": 3 body paragraphs (chosen by the seed) are justified;
                             paragraphs that start with a run-in heading are skipped.
          where="style":     only when asked for. Normal becomes justified. Any
                             paragraph style that would inherit that through
                             basedOn first gets its current alignment written
                             onto it, so headings and other styles keep theirs.
                             LIMITATION: Level 4/5 run-in headings sit inside
                             Normal body paragraphs, so on a document that has
                             them, those paragraphs become justified too and
                             APA-11 fails as well as APA-03.
  APA-00  margins (where="section"): the first section's left margin becomes
          0.75" (1080 twips).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from lxml import etree

from tools.corpus.checks.headings import find_headings
from tools.corpus.checks.layout import body_paragraphs, check_alignment, check_margins
from tools.corpus.docx_view import AcceptedView, w
from tools.corpus.style_resolver import StyleResolver

DOC = "word/document.xml"
STYLES = "word/styles.xml"
JUSTIFY_PARAGRAPHS = 3
BAD_LEFT_MARGIN_TWIPS = "1080"            # 0.75"

# Children that must come AFTER w:jc inside w:pPr (OOXML schema order).
_AFTER_JC = {w(t) for t in ("textDirection", "textAlignment", "textboxTightWrap",
                            "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange")}
# Children that must come AFTER w:pPr inside w:style.
_AFTER_PPR = {w(t) for t in ("rPr", "tblPr", "trPr", "tcPr", "tblStylePr")}


@dataclass(frozen=True)
class Recipe:
    matrix_id: str
    name: str
    apply: Callable[[dict, random.Random, str, AcceptedView], dict]
    check: Callable[[AcceptedView], dict]
    default_where: str
    wheres: tuple[str, ...]          # values this recipe accepts


# --------------------------------------------------------------------------
# XML helpers (keep schema order so Word opens the result)
# --------------------------------------------------------------------------

def _insert_before_first(parent, child, successors) -> None:
    for i, existing in enumerate(parent):
        if existing.tag in successors:
            parent.insert(i, child)
            return
    parent.append(child)


def _get_or_add_ppr(owner, successors=None) -> etree._Element:
    ppr = owner.find(w("pPr"))
    if ppr is None:
        ppr = etree.Element(w("pPr"))
        if successors is None:
            owner.insert(0, ppr)                 # w:p: pPr is always first
        else:
            _insert_before_first(owner, ppr, successors)
    return ppr


def set_jc(ppr: etree._Element, value: str) -> None:
    jc = ppr.find(w("jc"))
    if jc is None:
        jc = etree.Element(w("jc"))
        _insert_before_first(ppr, jc, _AFTER_JC)
    jc.set(w("val"), value)


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


def _justify_style(roots: dict, base_view: AcceptedView) -> dict:
    styles = roots[STYLES]
    resolver = StyleResolver(base_view.parts)
    normal = resolver.default_paragraph_style
    if normal is None:
        raise ValueError("base has no default paragraph style to justify")
    normal_align, _ = _style_alignment(resolver, normal)

    # Pin every other paragraph style whose alignment currently comes from
    # Normal (or below it), so justifying Normal doesn't reach it via basedOn.
    pinned = {}
    for style in styles.iter(w("style")):
        sid = style.get(w("styleId"))
        if sid == normal or style.get(w("type")) != "paragraph":
            continue
        chain_ids = [s for s, _ in resolver.chain(sid)]
        if normal not in chain_ids:
            continue
        value, source = _style_alignment(resolver, sid)
        if source in (normal, "docDefaults", "word-default"):
            set_jc(_get_or_add_ppr(style, _AFTER_PPR), value)
            pinned[sid] = value

    target = next(s for s in styles.iter(w("style")) if s.get(w("styleId")) == normal)
    set_jc(_get_or_add_ppr(target, _AFTER_PPR), "both")
    return {"where": "style", "style": normal, "was": normal_align,
            "pinned_styles": pinned}


def _raw_body_paragraphs(document_root) -> list[etree._Element]:
    """Body w:p in the same order as accepted_view (base has no tracked changes)."""
    body = document_root.find(w("body"))
    return [p for p in body.iter(w("p"))
            if not any(a.tag == w("txbxContent") for a in p.iterancestors())]


def _justify_paragraphs(roots: dict, rng: random.Random, base_view: AcceptedView) -> dict:
    _, _, headings = find_headings(base_view)
    run_in = {h["paragraph"] for h in headings if h["found_by"] == "run-in"}
    candidates = [p.index for p in body_paragraphs(base_view) if p.index not in run_in]
    if not candidates:
        raise ValueError("base has no body paragraphs to justify")
    chosen = sorted(rng.sample(candidates, min(JUSTIFY_PARAGRAPHS, len(candidates))))
    raw = _raw_body_paragraphs(roots[DOC])
    for index in chosen:
        set_jc(_get_or_add_ppr(raw[index]), "both")
    return {"where": "paragraph", "paragraphs": chosen}


def apply_justified(roots, rng, where, base_view) -> dict:
    if where == "style":
        return _justify_style(roots, base_view)
    if where == "paragraph":
        return _justify_paragraphs(roots, rng, base_view)
    raise ValueError(f"APA-03 recipe: where must be 'style' or 'paragraph', got {where!r}")


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


FORMAT_RECIPES = {
    "APA-03": Recipe("APA-03", "justified", apply_justified, check_alignment,
                     default_where="paragraph", wheres=("paragraph", "style")),
    "APA-00": Recipe("APA-00", "left_margin_0.75in", apply_bad_margin, check_margins,
                     default_where="section", wheres=("section",)),
}
