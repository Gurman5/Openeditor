"""Abstract + keywords check (K-H6, matrix rows APA-08 and APA-09).

APA-08: "Abstract" label bold + centered; abstract is ONE unindented
        paragraph of at most 250 words.
APA-09: italic "Keywords:" label; keywords line indented 0.5"; at most one
        line (approximated as a character count, default 100); keywords
        lowercase unless proper nouns. Capitalised keywords are reported as
        info only, never a fail: the check cannot tell a proper noun from a
        mistake.

Finding the parts:
  label    = first paragraph whose text is "Abstract" (any capitals)
  body     = following paragraphs up to the first "Keywords:" line, heading,
             paragraph with pageBreakBefore (direct or via its style), page
             break inside a run (<w:br w:type="page"/>) or section break
             (w:pPr/w:sectPr; that paragraph is still part of the abstract)
  keywords = a paragraph starting "Keywords:" inside that zone

No abstract -> both rows "na" (student papers often have none).
Abstract but no keywords -> APA-09 "na".

The one-line limit can be changed:
  - in code:   check_abstract(doc, max_keyword_chars=120)
  - in a shell: $env:CORPUS_KEYWORDS_MAX_CHARS = "120"

Usage:
  python -m tools.corpus.checks.abstract --docx file.docx [--max-keyword-chars 120]
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
from pathlib import Path

from tools.corpus.docx_view import AcceptedView, ParagraphView, accepted_view, run_text, w
from tools.corpus.style_resolver import get_resolver, resolve_emphasis, resolve_paragraph

MAX_ABSTRACT_WORDS = 250
MAX_KEYWORD_CHARS = 100
ENV_VAR = "CORPUS_KEYWORDS_MAX_CHARS"
KEYWORD_INDENT_IN = 0.5

_KEYWORDS_RE = re.compile(r"\s*keywords\s*:", re.IGNORECASE)
_OFF = ("0", "false", "off")


def keyword_char_limit(value: int | None = None) -> int:
    """Argument, else $CORPUS_KEYWORDS_MAX_CHARS, else MAX_KEYWORD_CHARS."""
    if value is not None:
        return int(value)
    if os.environ.get(ENV_VAR):
        try:
            return int(os.environ[ENV_VAR])
        except ValueError:
            raise ValueError(f"{ENV_VAR} must be a whole number, got "
                             f"{os.environ[ENV_VAR]!r}") from None
    return MAX_KEYWORD_CHARS


# --------------------------------------------------------------------------
# Finding the abstract zone
# --------------------------------------------------------------------------

def has_pr_flag(p: ParagraphView, view: AcceptedView, tag: str) -> bool:
    """True if pPr (direct or via the style chain) turns on <tag>."""
    for _, ppr in get_resolver(view).paragraph_levels(p.element):
        el = ppr.find(w(tag))
        if el is not None:
            return el.get(w("val")) not in _OFF
    return False


def _is_heading(p: ParagraphView, view: AcceptedView) -> bool:
    for _, ppr in get_resolver(view).paragraph_levels(p.element):
        el = ppr.find(w("outlineLvl"))
        if el is not None:
            return el.get(w("val")) != "9"     # 9 = body text
    return False


def text_before_page_break(p: ParagraphView) -> tuple[str, bool]:
    """(visible text before the first <w:br w:type="page"/>, found a break?)."""
    parts = []
    for run in p.runs:
        children = list(run.element)
        breaks = [i for i, c in enumerate(children)
                  if c.tag == w("br") and c.get(w("type")) == "page"]
        if not breaks:
            parts.append(run.text)
            continue
        head = copy.deepcopy(run.element)          # run cut off at the break
        for child in list(head)[breaks[0]:]:
            head.remove(child)
        parts.append(run_text(head))
        return "".join(parts), True
    return "".join(parts), False


def find_abstract(view: AcceptedView):
    """(label, [body paragraphs], keywords paragraph or None); label None if absent."""
    paras = view.paragraphs
    label_idx = next((i for i, p in enumerate(paras)
                      if p.text.strip().lower() == "abstract"), None)
    if label_idx is None:
        return None, [], None

    body, keywords = [], None
    for p in paras[label_idx + 1:]:
        if _KEYWORDS_RE.match(p.text):
            keywords = p
            break
        if has_pr_flag(p, view, "pageBreakBefore") or _is_heading(p, view):
            break
        before, broke = text_before_page_break(p)
        if before.strip():
            body.append(p)
        if broke or _ends_section(p):
            break
    return paras[label_idx], body, keywords


def _ends_section(p: ParagraphView) -> bool:
    """A w:pPr/w:sectPr makes p the LAST paragraph of its section."""
    return p.pPr is not None and p.pPr.find(w("sectPr")) is not None


# --------------------------------------------------------------------------
# Sub-checks
# --------------------------------------------------------------------------

def _sub(ok: bool, **evidence) -> dict:
    return {"status": "pass" if ok else "fail", **evidence}


def _row(matrix_id: str, check: str, subchecks: dict | None, paragraph=None) -> dict:
    if subchecks is None:
        return {"check": check, "matrix_id": matrix_id, "status": "na", "subchecks": {}}
    failed = any(s["status"] == "fail" for s in subchecks.values())
    return {"check": check, "matrix_id": matrix_id, "status": "fail" if failed else "pass",
            "paragraph": paragraph, "subchecks": subchecks}


def _visible_runs(p: ParagraphView):
    return [r for r in p.runs if r.text.strip()]


def _check_abstract(view, label, body, max_words) -> dict:
    label_units = resolve_paragraph(label, view)["units"]
    label_runs = _visible_runs(label)
    not_bold = [r.text for r in label_runs if not resolve_emphasis(r, view)["bold"]]

    words = sum(len(p.text.split()) for p in body)
    indented = []
    for p in body:
        u = resolve_paragraph(p, view)["units"]
        if u["first_line_in"] != 0 or u["left_in"] != 0:
            indented.append({"paragraph": p.index, "first_line_in": u["first_line_in"],
                             "left_in": u["left_in"]})
    return {
        "label_bold": _sub(not not_bold, not_bold_runs=not_bold),
        "label_centered": _sub(label_units["align"] == "center", align=label_units["align"]),
        "one_paragraph": _sub(len(body) == 1, paragraphs=[p.index for p in body]),
        "word_count": _sub(words <= max_words, words=words, max=max_words),
        "unindented": _sub(not indented, indented=indented),
    }


def _check_keywords(view, kw: ParagraphView, max_chars: int) -> dict:
    text = kw.text
    label_start = len(text) - len(text.lstrip())
    label_end = _KEYWORDS_RE.match(text).end()

    not_italic, pos = [], 0
    for run in kw.runs:
        start, end = pos, pos + len(run.text)
        pos = end
        overlap = text[max(start, label_start):min(end, label_end)]
        if overlap.strip() and not resolve_emphasis(run, view)["italic"]:
            not_italic.append(run.text)

    first_line = resolve_paragraph(kw, view)["units"]["first_line_in"]
    length = len(text.strip())
    keywords = [k.strip() for k in text[label_end:].split(",") if k.strip()]
    capitalised = [k for k in keywords if k[:1].isupper()]
    return {
        "label_italic": _sub(not not_italic, not_italic_runs=not_italic),
        "indented": _sub(first_line == KEYWORD_INDENT_IN, first_line_in=first_line,
                         expected_in=KEYWORD_INDENT_IN),
        "one_line": _sub(length <= max_chars, chars=length, max=max_chars),
        "capitalised_words": {"status": "info", "words": capitalised,
                              "note": "lowercase unless proper nouns; review manually"},
    }


# --------------------------------------------------------------------------
# Public entry point + CLI
# --------------------------------------------------------------------------

def check_abstract(doc: AcceptedView | str | Path, max_words: int = MAX_ABSTRACT_WORDS,
                   max_keyword_chars: int | None = None) -> dict:
    """Run APA-08 and APA-09. Returns {"APA-08": {...}, "APA-09": {...}}."""
    view = doc if isinstance(doc, AcceptedView) else accepted_view(doc)
    max_chars = keyword_char_limit(max_keyword_chars)
    label, body, kw = find_abstract(view)

    if label is None:
        return {"APA-08": _row("APA-08", "abstract", None),
                "APA-09": _row("APA-09", "keywords", None)}
    return {
        "APA-08": _row("APA-08", "abstract", _check_abstract(view, label, body, max_words),
                       label.index),
        "APA-09": _row("APA-09", "keywords",
                       None if kw is None else _check_keywords(view, kw, max_chars),
                       None if kw is None else kw.index),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="APA-08/APA-09 abstract + keywords check")
    ap.add_argument("--docx", required=True, help="path to a .docx file")
    ap.add_argument("--max-keyword-chars", type=int, help="one-line limit (default 100)")
    args = ap.parse_args(argv)
    result = check_abstract(args.docx, max_keyword_chars=args.max_keyword_chars)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
