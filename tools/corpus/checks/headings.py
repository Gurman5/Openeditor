"""Headings check (K-H4, matrix rows APA-10 and APA-11).

APA-10: the paper title is repeated (bold, centered) on the first body page,
        and there is NO "Introduction" heading.
APA-11: heading formatting by level:
          L1 centered, bold                  (own paragraph)
          L2 flush left, bold                (own paragraph)
          L3 flush left, bold italic         (own paragraph)
          L4 indented 0.5", bold, ends "."   (run-in: starts a body paragraph)
          L5 indented 0.5", bold italic, "." (run-in)
        Headings must not be numbered: typed ("1. Method", "2.1 Participants",
        "IV. Results") or automatic list numbering (w:numPr) both fail.
        Title case is reported as info only (small words and proper nouns
        can't be judged reliably), never a fail.

Finding headings:
  - L1-L3: paragraphs with outlineLvl 0-2 (direct or through the style chain,
    e.g. Heading1 -> outlineLvl 0)
  - a paragraph with outlineLvl 3-4 (e.g. a Heading4 style) is a L4/L5 heading
    on its own line, which fails: L4/L5 must run in with the paragraph text
  - L4/L5 run-in: a body paragraph that starts with bold text ending in a
    period, followed by more text (bold -> L4, bold italic -> L5)
  - NOT headings, even with a Heading style: the paper title (first paragraph
    with text) and its copies, and the labels in SECTION_LABELS
  - paragraphs inside tables are skipped

Usage:
  python -m tools.corpus.checks.headings --docx file.docx
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from tools.corpus.docx_view import AcceptedView, ParagraphView, accepted_view, w
from tools.corpus.style_resolver import get_resolver, resolve_emphasis, resolve_paragraph

# Standard APA section labels: never section headings. "appendix" also
# covers "Appendix A", "Appendix B", ...
SECTION_LABELS = {"abstract", "references", "author note", "footnotes", "tables",
                  "figures", "appendix"}
_APPENDIX_RE = re.compile(r"appendix(\s+[a-z0-9]+)?")

# "1." "1.2" "1.2.3" "IV." "A." followed by a space. A plain year ("2020 Survey")
# has no period or second number, so it does not match.
_NUMBERED_RE = re.compile(r"\s*(\d+\.(?:\d+\.?)*|\d+(?:\.\d+)+|[IVXLCDM]+\.|[A-Z]\.)\s")

RUN_IN_INDENT_IN = 0.5
# Expected formatting per level: (align, bold, italic, first_line_in, run_in)
LEVEL_RULES = {
    1: ("center", True, False, 0.0, False),
    2: ("left", True, False, 0.0, False),
    3: ("left", True, True, 0.0, False),
    4: ("left", True, False, RUN_IN_INDENT_IN, True),
    5: ("left", True, True, RUN_IN_INDENT_IN, True),
}


def _norm(text: str) -> str:
    return " ".join(text.split()).lower()


def is_section_label(text: str) -> bool:
    t = _norm(text).rstrip(".:")
    return t in SECTION_LABELS or bool(_APPENDIX_RE.fullmatch(t))


def _outline_level(p: ParagraphView, view: AcceptedView) -> int | None:
    """1-based heading level from outlineLvl (direct or style chain), or None."""
    for _, ppr in get_resolver(view).paragraph_levels(p.element):
        el = ppr.find(w("outlineLvl"))
        if el is not None:
            try:
                level = int(el.get(w("val"))) + 1
            except (TypeError, ValueError):
                return None
            return level if 1 <= level <= 5 else None   # 9 (+1 = 10) = body text
    return None


def _run_in_heading(p: ParagraphView, view: AcceptedView):
    """(heading runs, heading text, period_in_bold) if p starts with a run-in
    heading, else None."""
    heading_runs, pos = [], 0
    for run in p.runs:
        if run.text.strip() and not resolve_emphasis(run, view)["bold"]:
            break
        heading_runs.append(run)
        pos += len(run.text)
    heading = "".join(r.text for r in heading_runs)
    rest = p.text[pos:]
    if not heading.strip():
        return None
    if heading.rstrip().endswith("."):
        period_in_bold, after = True, rest
    elif rest.lstrip().startswith("."):
        period_in_bold, after = False, rest.lstrip()[1:]
    else:
        return None                     # bold start without a period: emphasis, not a heading
    if not after.strip():
        return None                     # nothing follows: not run-in
    return [r for r in heading_runs if r.text.strip()], heading.strip(), period_in_bold


def _numbering(p: ParagraphView, view: AcceptedView, text: str) -> str | None:
    """How a heading is numbered, or None. Typed numbers ("1. Method",
    "2.1 Participants", "IV. Results", "A. Method") and Word's automatic list
    numbering (w:numPr, direct or through the style chain) both count."""
    match = _NUMBERED_RE.match(text)
    if match:
        return f'typed "{match.group(1)}"'
    for src, ppr in get_resolver(view).paragraph_levels(p.element):
        num = ppr.find(w("numPr"))
        if num is not None:
            num_id = num.find(w("numId"))
            if num_id is not None and num_id.get(w("val")) != "0":   # numId 0 = none
                return f"automatic list numbering from {src}"
            return None
    return None


def _title_case_issues(text: str) -> list[str]:
    """Words APA would capitalise but that start lowercase: the first word and
    any word of 4+ letters."""
    words = re.findall(r"[A-Za-z][A-Za-z'\-]*", text)
    return [wd for i, wd in enumerate(words)
            if wd[0].islower() and (i == 0 or len(wd) >= 4)]


def _check_heading(view, p, level, found_by, runs, text, period_in_bold=True) -> dict:
    align, bold, italic, first_line, run_in = LEVEL_RULES[level]
    units = resolve_paragraph(p, view)["units"]
    emph = [resolve_emphasis(r, view) for r in runs]
    problems = []

    if run_in and found_by != "run-in":
        problems.append(f"Level {level} headings should run in with the paragraph text")
    if units["align"] != align:
        problems.append(f"alignment should be {align}, got {units['align']}")
    if units["first_line_in"] != first_line:
        problems.append(f"first-line indent should be {first_line:g}in, got {units['first_line_in']}")
    if not run_in and units["left_in"] != 0:
        problems.append(f"left indent should be 0in, got {units['left_in']}")
    if bold and not all(e["bold"] for e in emph):
        problems.append("should be bold")
    if italic and not all(e["italic"] for e in emph):
        problems.append("should be bold italic")
    if not italic and any(e["italic"] for e in emph):
        problems.append("should not be italic")
    if run_in and found_by == "run-in" and not period_in_bold:
        problems.append("the ending period should be part of the bold heading")
    numbering = _numbering(p, view, text)
    if numbering:
        problems.append(f"heading should not be numbered ({numbering})")

    return {"paragraph": p.index, "level": level, "text": text, "found_by": found_by,
            "status": "fail" if problems else "pass", "problems": problems,
            "title_case_words": _title_case_issues(text)}


def find_headings(view: AcceptedView):
    """(title paragraph or None, [title copies], [heading results])."""
    paras = [p for p in view.paragraphs if not p.in_table]
    title = next((p for p in paras if p.text.strip()), None)
    title_norm = _norm(title.text) if title else None
    copies, headings = [], []

    for p in paras:
        if p is title or not p.text.strip():
            continue
        if _norm(p.text) == title_norm:
            copies.append(p)
            continue
        if is_section_label(p.text):
            continue
        visible = [r for r in p.runs if r.text.strip()]
        level = _outline_level(p, view)
        if level is not None:
            headings.append(_check_heading(view, p, level, "outline", visible, p.text.strip()))
            continue
        run_in = _run_in_heading(p, view)
        if run_in is not None:
            runs, text, period_in_bold = run_in
            italic = resolve_emphasis(runs[0], view)["italic"]
            headings.append(_check_heading(view, p, 5 if italic else 4, "run-in",
                                           runs, text, period_in_bold))
    return title, copies, headings


def _sub(ok: bool, **evidence) -> dict:
    return {"status": "pass" if ok else "fail", **evidence}


def check_headings(doc: AcceptedView | str | Path) -> dict:
    """Run APA-10 and APA-11. Returns {"APA-10": {...}, "APA-11": {...}}."""
    view = doc if isinstance(doc, AcceptedView) else accepted_view(doc)
    title, copies, headings = find_headings(view)

    # APA-10
    intro = [h for h in headings if _norm(h["text"]).rstrip(".") == "introduction"]
    if title is None:
        repeated = {"status": "na", "reason": "no title found"}
    else:
        good = [c.index for c in copies
                if resolve_paragraph(c, view)["units"]["align"] == "center"
                and all(resolve_emphasis(r, view)["bold"] for r in c.runs if r.text.strip())]
        repeated = _sub(bool(good), title=title.text.strip(),
                        copies=[c.index for c in copies], bold_centered_copies=good)
    apa10_subs = {
        "no_introduction_heading": _sub(not intro, found=[h["paragraph"] for h in intro]),
        "title_repeated": repeated,
    }
    apa10 = {"check": "introduction", "matrix_id": "APA-10",
             "status": "fail" if any(s["status"] == "fail" for s in apa10_subs.values())
             else "pass", "subchecks": apa10_subs}

    # APA-11
    if not headings:
        status = "na"
    else:
        status = "fail" if any(h["status"] == "fail" for h in headings) else "pass"
    apa11 = {"check": "headings", "matrix_id": "APA-11", "status": status,
             "headings": headings,
             "title_case": {"status": "info",
                            "headings": [{"paragraph": h["paragraph"], "text": h["text"],
                                          "words": h["title_case_words"]}
                                         for h in headings if h["title_case_words"]],
                            "note": "title case: review manually (small words, proper nouns)"}}
    return {"APA-10": apa10, "APA-11": apa11}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="APA-10/APA-11 headings check")
    ap.add_argument("--docx", required=True, help="path to a .docx file")
    args = ap.parse_args(argv)
    print(json.dumps(check_headings(args.docx), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
