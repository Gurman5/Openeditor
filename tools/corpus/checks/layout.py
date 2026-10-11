"""Page layout checks (K-H2 step A: APA-00, APA-01, APA-03, APA-04).

APA-00 margins:   every section has 1" (1440 twips) top/bottom/left/right.
APA-01 spacing:   every paragraph with text is double spaced (2.0 lines,
                  lineRule auto), has 0 space before/after, and there are no
                  blank paragraphs right before or after a heading.
                  Tables are skipped (APA allows other spacing there).
APA-03 alignment: no paragraph is justified (tables included).
APA-04 indent:    body paragraphs have a 0.5" first-line indent. Not body:
                  headings on their own line, centered/right-aligned
                  paragraphs, section labels and the title, the abstract and
                  keywords, the reference list, block quotes, "Table N" /
                  "Figure N" / "Note." lines, tables and empty paragraphs.
                  Run-in (Level 4/5) headings start body paragraphs, so they
                  are checked.

For the harness (Person A wires these in; harness.py is not edited here):
  CHECKS = {"margins": ..., "spacing": ..., "align": ..., "indent": ...,
            "pagenum": ...}   (pagenum = APA-05, in checks/page_numbers.py)
  check_layout(doc, checks=None) runs all of them, or the names given.

Margin tolerance (default 0 = exactly 1"):
  - in code:   check_margins(doc, tolerance_twips=20)
  - in a shell: $env:CORPUS_MARGIN_TOLERANCE_TWIPS = "20"

Usage:
  python -m tools.corpus.checks.layout --docx file.docx [--checks margins,spacing]
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from tools.corpus.checks.abstract import find_abstract
from tools.corpus.checks.headings import find_headings, is_section_label
from tools.corpus.checks.page_numbers import check_page_numbers
from tools.corpus.checks.refs import find_references
from tools.corpus.docx_view import AcceptedView, ParagraphView, accepted_view, w
from tools.corpus.style_resolver import resolve_paragraph

MARGIN_TWIPS = 1440
MARGIN_TOLERANCE_TWIPS = 0
MARGIN_ENV_VAR = "CORPUS_MARGIN_TOLERANCE_TWIPS"
BODY_INDENT_IN = 0.5
BLOCK_QUOTE_LEFT_IN = 0.5

JUSTIFIED = {"both", "distribute", "highKashida", "mediumKashida", "lowKashida",
             "thaiDistribute"}
_CAPTION_RE = re.compile(r"\s*((table|figure)\s+\d+|note\.)", re.IGNORECASE)
# Paragraph content that is not "blank" even without text.
_NON_TEXT_CONTENT = ("drawing", "pict", "object")


def _snippet(p: ParagraphView) -> str:
    return p.text.strip()[:40]


def _row(check: str, matrix_id: str, subchecks: dict | None) -> dict:
    """Combine sub-checks into one row: fail if any fails, na if there are none."""
    if subchecks is None:
        return {"check": check, "matrix_id": matrix_id, "status": "na", "subchecks": {}}
    failed = any(s["status"] == "fail" for s in subchecks.values())
    return {"check": check, "matrix_id": matrix_id,
            "status": "fail" if failed else "pass", "subchecks": subchecks}


def _sub(problems: list, **evidence) -> dict:
    return {"status": "fail" if problems else "pass", "problems": problems, **evidence}


def _view(doc) -> AcceptedView:
    return doc if isinstance(doc, AcceptedView) else accepted_view(doc)


def _text_paragraphs(view: AcceptedView, include_tables: bool) -> list[ParagraphView]:
    return [p for p in view.paragraphs
            if p.text.strip() and (include_tables or not p.in_table)]


# --------------------------------------------------------------------------
# APA-00 margins
# --------------------------------------------------------------------------

def margin_tolerance(value: int | None = None) -> int:
    """Argument, else $CORPUS_MARGIN_TOLERANCE_TWIPS, else MARGIN_TOLERANCE_TWIPS."""
    if value is not None:
        return int(value)
    if os.environ.get(MARGIN_ENV_VAR):
        try:
            return int(os.environ[MARGIN_ENV_VAR])
        except ValueError:
            raise ValueError(f"{MARGIN_ENV_VAR} must be a whole number of twips, got "
                             f"{os.environ[MARGIN_ENV_VAR]!r}") from None
    return MARGIN_TOLERANCE_TWIPS


def check_margins(doc, tolerance_twips: int | None = None) -> dict:
    view = _view(doc)
    tolerance = margin_tolerance(tolerance_twips)
    if not view.sections:
        return _row("margins", "APA-00", None)

    problems, sections = [], []
    for i, sect in enumerate(view.sections):
        mar = sect.find(w("pgMar"))
        found = {}
        for side in ("top", "bottom", "left", "right"):
            raw = None if mar is None else mar.get(w(side))
            try:
                twips = abs(float(raw))      # negative top/bottom = "don't overlap header"
            except (TypeError, ValueError):
                twips = None
            found[side] = None if twips is None else round(twips / 1440, 4)
            if twips is None or abs(twips - MARGIN_TWIPS) > tolerance:
                problems.append({"section": i, "side": side, "twips": raw,
                                 "inches": found[side]})
        sections.append({"section": i, "inches": found})
    return _row("margins", "APA-00", {
        "one_inch": _sub(problems, sections=sections, tolerance_twips=tolerance)})


# --------------------------------------------------------------------------
# APA-01 spacing
# --------------------------------------------------------------------------

def _is_blank(p: ParagraphView) -> bool:
    """No visible text and nothing else on the line (image, section break, page break)."""
    if p.text.strip():
        return False
    if any(p.element.iter(*(w(t) for t in _NON_TEXT_CONTENT))):
        return False
    if p.pPr is not None and p.pPr.find(w("sectPr")) is not None:
        return False
    return not any(br.get(w("type")) == "page" for br in p.element.iter(w("br")))


def check_spacing(doc) -> dict:
    view = _view(doc)
    paras = _text_paragraphs(view, include_tables=False)
    if not paras:
        return _row("spacing", "APA-01", None)

    not_double, extra_space = [], []
    for p in paras:
        u = resolve_paragraph(p, view)["units"]
        if u["line_rule"] != "auto" or u["line_multiple"] != 2.0:
            not_double.append({"paragraph": p.index, "text": _snippet(p),
                               "line_rule": u["line_rule"],
                               "line_multiple": u["line_multiple"], "line_pt": u["line_pt"]})
        if u["before_pt"] != 0 or u["after_pt"] != 0:
            extra_space.append({"paragraph": p.index, "text": _snippet(p),
                                "before_pt": u["before_pt"], "after_pt": u["after_pt"]})

    _, _, headings = find_headings(view)
    all_paras = view.paragraphs
    blank_lines = []
    for h in headings:
        if h["found_by"] != "outline":
            continue                       # run-in headings sit inside body text
        for where, i in (("before", h["paragraph"] - 1), ("after", h["paragraph"] + 1)):
            if 0 <= i < len(all_paras) and _is_blank(all_paras[i]):
                blank_lines.append({"heading": h["text"], "paragraph": i, "where": where})

    return _row("spacing", "APA-01", {
        "double_spacing": _sub(not_double, paragraphs_checked=len(paras)),
        "no_space_before_after": _sub(extra_space),
        "no_blank_lines_around_headings": _sub(blank_lines),
    })


# --------------------------------------------------------------------------
# APA-03 alignment
# --------------------------------------------------------------------------

def check_alignment(doc) -> dict:
    view = _view(doc)
    paras = _text_paragraphs(view, include_tables=True)
    if not paras:
        return _row("align", "APA-03", None)
    justified = []
    for p in paras:
        align = resolve_paragraph(p, view)["align"]
        if align in JUSTIFIED:
            justified.append({"paragraph": p.index, "text": _snippet(p), "align": align,
                              "in_table": p.in_table})
    return _row("align", "APA-03", {
        "no_justification": _sub(justified, paragraphs_checked=len(paras))})


# --------------------------------------------------------------------------
# APA-04 indent
# --------------------------------------------------------------------------

def body_paragraphs(view: AcceptedView) -> list[ParagraphView]:
    """Paragraphs that APA expects to carry a 0.5" first-line indent."""
    title, copies, headings = find_headings(view)
    skip = {h["paragraph"] for h in headings if h["found_by"] == "outline"}
    skip |= {p.index for p in copies} | ({title.index} if title else set())
    label, abstract_body, keywords = find_abstract(view)
    skip |= {p.index for p in [label, keywords, *abstract_body] if p is not None}
    skip |= {p.index for p in find_references(view)[1]}     # same list as APA-12

    body = []
    for p in _text_paragraphs(view, include_tables=False):
        if p.index in skip or is_section_label(p.text) or _CAPTION_RE.match(p.text):
            continue
        u = resolve_paragraph(p, view)["units"]
        if u["align"] in ("center", "right"):
            continue
        if u["left_in"] == BLOCK_QUOTE_LEFT_IN and u["first_line_in"] == 0:
            continue                       # block quote
        body.append(p)
    return body


def check_indent(doc) -> dict:
    view = _view(doc)
    body = body_paragraphs(view)
    if not body:
        return _row("indent", "APA-04", None)
    wrong = []
    for p in body:
        first_line = resolve_paragraph(p, view)["units"]["first_line_in"]
        if first_line != BODY_INDENT_IN:
            wrong.append({"paragraph": p.index, "text": _snippet(p),
                          "first_line_in": first_line})
    return _row("indent", "APA-04", {
        "first_line_half_inch": _sub(wrong, paragraphs_checked=len(body))})


# --------------------------------------------------------------------------
# Registry + CLI
# --------------------------------------------------------------------------

CHECKS = {
    "margins": check_margins,
    "spacing": check_spacing,
    "align": check_alignment,
    "indent": check_indent,
    "pagenum": check_page_numbers,
}


def check_layout(doc, checks: list[str] | None = None) -> dict:
    """Run the named checks (default: all). Returns {matrix_id: row, ...}."""
    view = _view(doc)
    names = list(CHECKS) if checks is None else checks
    unknown = [n for n in names if n not in CHECKS]
    if unknown:
        raise ValueError(f"unknown check(s) {unknown}; choose from {list(CHECKS)}")
    rows = [CHECKS[n](view) for n in names]
    return {row["matrix_id"]: row for row in rows}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="APA-00/01/03/04/05 layout checks")
    ap.add_argument("--docx", required=True, help="path to a .docx file")
    ap.add_argument("--checks", help=f"comma list from {','.join(CHECKS)} (default: all)")
    args = ap.parse_args(argv)
    names = [c.strip() for c in args.checks.split(",")] if args.checks else None
    print(json.dumps(check_layout(args.docx, names), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
