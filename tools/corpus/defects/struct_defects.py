"""Structure defect recipes (K-I3a: headings + abstract; K-I3b: references).

Same apply(roots, rng, where, base_view) contract as format_defects.py. Each
recipe has one mode, so `where` is just recorded.

DEFERRED (no automatic check yet, so the injector couldn't verify them):
  - APA-13 "et al." / "&" in narrative citations and APA-14 block quotes:
    wait for K-H11 (citation check, deferred this sprint)
  - APA-17 comma decimals ("3,5"): graded manually until C decides the
    decimal policy

  APA-11a  numbered headings: Level 1 headings become "1. Method", "2. ...".
  APA-11b  heading level wrong: every Level 2 heading is formatted like a
           Level 1 heading (centered) while keeping its Heading 2 style.
           (Restyling Heading 2 -> Heading 1 is NOT used: it gives a correctly
           formatted Level 1 heading, which no check can tell is wrong.)
  APA-08a  abstract over 250 words: a neutral sentence is appended to the
           abstract's last text until it has more than 260 words (same run,
           so formatting doesn't change).
  APA-08b  abstract indented: 0.5" first-line indent on the abstract paragraph(s).
  APA-08c  abstract missing: the "Abstract" label, the abstract and the
           Keywords line are removed. Graded with require_abstract=True
           (check_options) and APA-09 becomes "na" on purpose (side_effects).
  APA-12a  References not on a new page: EVERY page break between the last
           text before "References" and the label's own text is removed -
           pageBreakBefore on the label (direct removed; from a style it is
           switched off with a direct w:val="0"), page breaks in runs and
           empty paragraphs, and section breaks (made continuous).
  APA-12b  missing hanging indent: up to 2 entries (chosen by the seed) get
           left = 0 and first line = 0.
  APA-12c  not alphabetical: the first entry is moved to the end of the list.
  APA-18a  old DOI form: one https://doi.org/ DOI (chosen by the seed)
           becomes http://dx.doi.org/.
"""

from __future__ import annotations

import math

from tools.corpus.checks.abstract import check_abstract, find_abstract
from tools.corpus.checks.headings import check_headings, find_headings
from tools.corpus.checks.refs import check_references, find_references
from tools.corpus.defects.common import (
    DOC, PPR_ORDER, Recipe, child, own_runs, p_ppr, raw_body_paragraphs, set_first_line,
    set_jc, text_elements,
)
from tools.corpus.docx_view import w
from tools.corpus.style_resolver import get_resolver

FILLER = "Further details are reported in the full paper."
TARGET_ABSTRACT_WORDS = 261
UNHUNG_ENTRIES = 2
GOOD_DOI, OLD_DOI = "https://doi.org/", "http://dx.doi.org/"
_OFF = ("0", "false", "off")
SECT_ORDER = [w(t) for t in (
    "headerReference", "footerReference", "footnotePr", "endnotePr", "type", "pgSz",
    "pgMar", "paperSrc", "pgBorders", "lnNumType", "pgNumType", "cols", "formProt",
    "vAlign", "noEndnote", "titlePg", "textDirection", "bidi", "rtlGutter", "docGrid",
    "printerSettings", "sectPrChange")]


def _outline_headings(base_view, level: int) -> list[dict]:
    _, _, headings = find_headings(base_view)
    found = [h for h in headings if h["found_by"] == "outline" and h["level"] == level]
    if not found:
        raise ValueError(f"base has no Level {level} headings")
    return found


# --------------------------------------------------------------------------
# APA-11
# --------------------------------------------------------------------------

def apply_numbered_headings(roots, rng, where, base_view) -> dict:
    raw = raw_body_paragraphs(roots[DOC])
    numbered = []
    for n, h in enumerate(_outline_headings(base_view, 1), start=1):
        texts = text_elements(raw[h["paragraph"]])
        texts[0].text = f"{n}. {texts[0].text}"
        numbered.append({"paragraph": h["paragraph"], "text": f"{n}. {h['text']}"})
    return {"where": where, "headings": numbered}


def apply_level2_formatted_as_level1(roots, rng, where, base_view) -> dict:
    raw = raw_body_paragraphs(roots[DOC])
    changed = []
    for h in _outline_headings(base_view, 2):
        set_jc(p_ppr(raw[h["paragraph"]]), "center")
        changed.append(h["paragraph"])
    return {"where": where, "paragraphs": changed, "align": "center"}


# --------------------------------------------------------------------------
# APA-08
# --------------------------------------------------------------------------

def _abstract(base_view):
    label, body, keywords = find_abstract(base_view)
    if label is None or not body:
        raise ValueError("base has no abstract")
    return label, body, keywords


def apply_long_abstract(roots, rng, where, base_view) -> dict:
    _, body, _ = _abstract(base_view)
    before = sum(len(p.text.split()) for p in body)
    repeats = max(1, math.ceil((TARGET_ABSTRACT_WORDS - before) / len(FILLER.split())))
    last = text_elements(raw_body_paragraphs(roots[DOC])[body[-1].index])[-1]
    last.text = last.text.rstrip() + (" " + FILLER) * repeats
    after = before + repeats * len(FILLER.split())
    return {"where": where, "paragraph": body[-1].index, "words_before": before,
            "words_after": after}


def apply_indented_abstract(roots, rng, where, base_view) -> dict:
    _, body, _ = _abstract(base_view)
    raw = raw_body_paragraphs(roots[DOC])
    for p in body:
        set_first_line(p_ppr(raw[p.index]), "720")
    return {"where": where, "paragraphs": [p.index for p in body], "first_line_twips": "720"}


def apply_missing_abstract(roots, rng, where, base_view) -> dict:
    label, body, keywords = _abstract(base_view)
    raw = raw_body_paragraphs(roots[DOC])
    doomed = [label, *body] + ([keywords] if keywords is not None else [])
    for p in doomed:
        ppr = raw[p.index].find(w("pPr"))
        if ppr is not None and ppr.find(w("sectPr")) is not None:
            raise ValueError(f"paragraph {p.index} ends a section; removing it would "
                             f"change the page layout")
    for p in doomed:
        el = raw[p.index]
        el.getparent().remove(el)
    return {"where": where, "removed_paragraphs": [p.index for p in doomed]}


# --------------------------------------------------------------------------
# APA-12 / APA-18: references
# --------------------------------------------------------------------------

def _references(base_view, minimum: int = 1):
    label, entries = find_references(base_view)
    if label is None or len(entries) < minimum:
        raise ValueError(f"base needs a References list with at least {minimum} entries")
    return label, entries


def _page_breaks(p) -> list:
    """[(kind, element)] in p's own runs: kind "T" = visible text, "B" = page break."""
    out = []
    for r in own_runs(p):
        for el in r:
            if el.tag == w("br") and el.get(w("type")) == "page":
                out.append(("B", el))
            elif el.tag == w("t") and (el.text or "").strip():
                out.append(("T", el))
    return out


def _drop(br) -> None:
    run = br.getparent()
    run.remove(br)
    if not [c for c in run if c.tag != w("rPr")]:
        run.getparent().remove(run)               # run is now empty


def _switch_off_page_break_before(raw_p, view_p, base_view) -> str | None:
    """Remove a direct pageBreakBefore; if a style still turns it on, override it."""
    ppr = raw_p.find(w("pPr"))
    direct = None if ppr is None else ppr.find(w("pageBreakBefore"))
    if direct is not None and direct.get(w("val")) in _OFF:
        return None                               # already off directly: style can't win
    removed = None
    if direct is not None:
        ppr.remove(direct)
        removed = "direct pageBreakBefore removed"
    for src, level in get_resolver(base_view).paragraph_levels(view_p.element):
        if src == "direct":
            continue
        el = level.find(w("pageBreakBefore"))
        if el is not None:
            if el.get(w("val")) not in _OFF:
                child(p_ppr(raw_p), "pageBreakBefore", PPR_ORDER).set(w("val"), "0")
                return f"pageBreakBefore from {src} switched off"
            break
    return removed


def apply_references_same_page(roots, rng, where, base_view) -> dict:
    label, _ = _references(base_view)
    raw = raw_body_paragraphs(roots[DOC])
    removed = []

    how = _switch_off_page_break_before(raw[label.index], label, base_view)
    if how:
        removed.append({"paragraph": label.index, "what": how})
    events = _page_breaks(raw[label.index])
    first_text = next((i for i, (k, _) in enumerate(events) if k == "T"), len(events))
    for _, br in [e for e in events[:first_text] if e[0] == "B"]:
        _drop(br)
        removed.append({"paragraph": label.index, "what": "page break before label text"})

    for p in reversed(base_view.paragraphs[:label.index]):
        raw_p = raw[p.index]
        sect = None if raw_p.find(w("pPr")) is None else raw_p.find(w("pPr")).find(w("sectPr"))
        if sect is not None:
            kind = child(sect, "type", SECT_ORDER)
            if kind.get(w("val")) not in ("continuous", "nextColumn"):
                kind.set(w("val"), "continuous")
                removed.append({"paragraph": p.index, "what": "section break made continuous"})
        events = _page_breaks(raw_p)
        texts = [i for i, (k, _) in enumerate(events) if k == "T"]
        tail = events[texts[-1]:] if texts else events
        for _, br in [e for e in tail if e[0] == "B"]:
            _drop(br)
            removed.append({"paragraph": p.index, "what": "page break in run"})
        if texts:
            break                               # reached the last text before the label
        how = _switch_off_page_break_before(raw_p, p, base_view)
        if how:
            removed.append({"paragraph": p.index, "what": how})

    if not removed:
        raise ValueError("References does not start on a new page in the base")
    return {"where": where, "removed": removed}


def apply_entries_without_hanging(roots, rng, where, base_view) -> dict:
    _, entries = _references(base_view)
    chosen = sorted(rng.sample([p.index for p in entries], min(UNHUNG_ENTRIES, len(entries))))
    raw = raw_body_paragraphs(roots[DOC])
    for index in chosen:
        ind = child(p_ppr(raw[index]), "ind", PPR_ORDER)
        for attr in ("hanging", "start"):
            ind.attrib.pop(w(attr), None)
        ind.set(w("left"), "0")
        ind.set(w("firstLine"), "0")
    return {"where": where, "paragraphs": chosen}


def apply_entries_out_of_order(roots, rng, where, base_view) -> dict:
    _, entries = _references(base_view, minimum=2)
    raw = raw_body_paragraphs(roots[DOC])
    first, last = raw[entries[0].index], raw[entries[-1].index]
    last.addnext(first)
    return {"where": where, "moved_paragraph": entries[0].index,
            "moved_entry": entries[0].text.strip()[:50], "now_after": entries[-1].index}


def apply_old_doi_form(roots, rng, where, base_view) -> dict:
    _, entries = _references(base_view)
    raw = raw_body_paragraphs(roots[DOC])
    candidates = [(p.index, t) for p in entries for t in text_elements(raw[p.index])
                  if GOOD_DOI in (t.text or "")]
    if not candidates:
        raise ValueError(f"base references have no {GOOD_DOI} DOI to change")
    index, t = candidates[rng.randrange(len(candidates))]
    t.text = t.text.replace(GOOD_DOI, OLD_DOI, 1)
    return {"where": where, "paragraph": index, "from": GOOD_DOI, "to": OLD_DOI}


def _refs(row):
    return lambda view: check_references(view)[row]


def _apa08(require: bool = False):
    return lambda view: check_abstract(view, require_abstract=require)["APA-08"]


def _apa11(view):
    return check_headings(view)["APA-11"]


STRUCT_RECIPES = {r.id: r for r in (
    Recipe("APA-11a", "APA-11", "numbered_headings", apply_numbered_headings, _apa11,
           default_where="heading", wheres=("heading",)),
    Recipe("APA-11b", "APA-11", "level2_formatted_as_level1",
           apply_level2_formatted_as_level1, _apa11,
           default_where="heading", wheres=("heading",)),
    Recipe("APA-08a", "APA-08", "abstract_over_250_words", apply_long_abstract, _apa08(),
           default_where="abstract", wheres=("abstract",)),
    Recipe("APA-08b", "APA-08", "abstract_indented", apply_indented_abstract, _apa08(),
           default_where="abstract", wheres=("abstract",)),
    Recipe("APA-08c", "APA-08", "abstract_missing", apply_missing_abstract, _apa08(True),
           default_where="abstract", wheres=("abstract",),
           side_effects={"APA-09": "na"},
           check_options={"APA-08": {"require_abstract": True}}),
    Recipe("APA-12a", "APA-12", "references_not_on_new_page", apply_references_same_page,
           _refs("APA-12"), default_where="references", wheres=("references",)),
    Recipe("APA-12b", "APA-12", "entries_without_hanging_indent",
           apply_entries_without_hanging, _refs("APA-12"),
           default_where="references", wheres=("references",)),
    Recipe("APA-12c", "APA-12", "entries_not_alphabetical", apply_entries_out_of_order,
           _refs("APA-12"), default_where="references", wheres=("references",)),
    Recipe("APA-18a", "APA-18", "old_dx_doi_form", apply_old_doi_form, _refs("APA-18"),
           default_where="references", wheres=("references",)),
)}
