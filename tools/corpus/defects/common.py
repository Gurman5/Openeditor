"""Shared pieces for defect recipes (format_defects.py, struct_defects.py).

  Recipe          what a recipe is (see format_defects.py for the apply() contract)
  child(), ...    insert XML children in OOXML schema order so Word opens the result
  choose_body()   pick body paragraphs with the injector's seeded RNG
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from lxml import etree

from tools.corpus.checks.headings import find_headings
from tools.corpus.checks.layout import body_paragraphs
from tools.corpus.docx_view import AcceptedView, w
from tools.corpus.style_resolver import StyleResolver

DOC = "word/document.xml"
STYLES = "word/styles.xml"
TARGET_PARAGRAPHS = 3


@dataclass(frozen=True)
class Recipe:
    id: str                          # registry key, e.g. "APA-02a"
    matrix_id: str                   # the row it breaks, e.g. "APA-02"
    name: str
    apply: Callable[[dict, random.Random, str, AcceptedView], dict]
    check: Callable[[AcceptedView], dict]
    default_where: str
    wheres: tuple[str, ...]          # values this recipe accepts
    # Other rows this recipe changes on purpose, with their expected status
    # (e.g. removing the abstract also removes the keywords: {"APA-09": "na"}).
    side_effects: dict = field(default_factory=dict)
    # Options the harness must pass to grade the injected row the same way
    # this recipe's check does, e.g. {"APA-08": {"require_abstract": True}}.
    check_options: dict = field(default_factory=dict)


# --------------------------------------------------------------------------
# XML helpers
# --------------------------------------------------------------------------

PPR_ORDER = [w(t) for t in (
    "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl",
    "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens",
    "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN",
    "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing",
    "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment",
    "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange")]
RPR_ORDER = [w(t) for t in (
    "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike",
    "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish",
    "webHidden", "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight",
    "u", "effect", "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang",
    "eastAsianLayout", "specVanish", "oMath", "rPrChange")]
STYLE_ORDER = [w(t) for t in (
    "name", "aliases", "basedOn", "next", "link", "autoRedefine", "hidden", "uiPriority",
    "semiHidden", "unhideWhenUsed", "qFormat", "locked", "personal", "personalCompose",
    "personalReply", "rsid", "pPr", "rPr", "tblPr", "trPr", "tcPr", "tblStylePr")]


def child(parent, tag: str, order: list[str]) -> etree._Element:
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


def p_ppr(p) -> etree._Element:
    ppr = p.find(w("pPr"))
    if ppr is None:
        ppr = etree.Element(w("pPr"))
        p.insert(0, ppr)                     # w:pPr is always first in w:p
    return ppr


def r_rpr(r) -> etree._Element:
    rpr = r.find(w("rPr"))
    if rpr is None:
        rpr = etree.Element(w("rPr"))
        r.insert(0, rpr)                     # w:rPr is always first in w:r
    return rpr


def style_ppr(style) -> etree._Element:
    return child(style, "pPr", STYLE_ORDER)


def style_rpr(style) -> etree._Element:
    return child(style, "rPr", STYLE_ORDER)


def set_jc(ppr, value: str) -> None:
    child(ppr, "jc", PPR_ORDER).set(w("val"), value)


def set_spacing_line(ppr, line: str, rule: str = "auto") -> None:
    spacing = child(ppr, "spacing", PPR_ORDER)
    spacing.set(w("line"), line)
    spacing.set(w("lineRule"), rule)


def set_first_line(ppr, value: str) -> None:
    ind = child(ppr, "ind", PPR_ORDER)
    ind.attrib.pop(w("hanging"), None)
    ind.set(w("firstLine"), value)


def set_font(rpr, family: str, half_points: str | None = None) -> None:
    """Explicit font (theme font attributes removed so they can't win)."""
    old = rpr.find(w("rFonts"))
    if old is not None:
        rpr.remove(old)
    fonts = child(rpr, "rFonts", RPR_ORDER)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(w(attr), family)
    if half_points is not None:
        for tag in ("sz", "szCs"):
            child(rpr, tag, RPR_ORDER).set(w("val"), half_points)


# --------------------------------------------------------------------------
# Finding and choosing targets
# --------------------------------------------------------------------------

def raw_body_paragraphs(document_root) -> list[etree._Element]:
    """Body w:p in the same order as accepted_view (base has no tracked changes)."""
    body = document_root.find(w("body"))
    return [p for p in body.iter(w("p"))
            if not any(a.tag == w("txbxContent") for a in p.iterancestors())]


def own_runs(p) -> list[etree._Element]:
    """Runs belonging to p (not to paragraphs nested inside it, e.g. text boxes)."""
    runs = []
    for r in p.iter(w("r")):
        owner = r.getparent()
        while owner is not None and owner.tag != w("p"):
            owner = owner.getparent()
        if owner is p:
            runs.append(r)
    return runs


def text_elements(p) -> list[etree._Element]:
    """The w:t elements with visible text in p's own runs, in order."""
    return [t for r in own_runs(p) for t in r.findall(w("t")) if (t.text or "").strip()]


def run_in_heading_paragraphs(base_view) -> set[int]:
    _, _, headings = find_headings(base_view)
    return {h["paragraph"] for h in headings if h["found_by"] == "run-in"}


def choose_body(base_view, rng) -> list[int]:
    run_in = run_in_heading_paragraphs(base_view)
    candidates = [p.index for p in body_paragraphs(base_view) if p.index not in run_in]
    if not candidates:
        raise ValueError("base has no body paragraphs to change")
    return sorted(rng.sample(candidates, min(TARGET_PARAGRAPHS, len(candidates))))


def normal_style(roots, base_view) -> tuple[etree._Element, StyleResolver]:
    resolver = StyleResolver(base_view.parts)
    normal = resolver.default_paragraph_style
    if normal is None:
        raise ValueError("base has no default paragraph style")
    style = next(s for s in roots[STYLES].iter(w("style")) if s.get(w("styleId")) == normal)
    return style, resolver


def two_modes(where, paragraph_fn, style_fn, name):
    if where == "paragraph":
        return paragraph_fn()
    if where == "style":
        return style_fn()
    raise ValueError(f"{name} recipe: where must be 'paragraph' or 'style', got {where!r}")
