"""Structure defect recipes (K-I3a: headings + abstract).

Same apply(roots, rng, where, base_view) contract as format_defects.py. Each
recipe has one mode, so `where` is just recorded.

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
"""

from __future__ import annotations

import math

from tools.corpus.checks.abstract import check_abstract, find_abstract
from tools.corpus.checks.headings import check_headings, find_headings
from tools.corpus.defects.common import (
    DOC, Recipe, p_ppr, raw_body_paragraphs, set_first_line, set_jc, text_elements,
)
from tools.corpus.docx_view import w

FILLER = "Further details are reported in the full paper."
TARGET_ABSTRACT_WORDS = 261


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
)}
