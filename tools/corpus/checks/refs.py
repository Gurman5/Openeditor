"""References check (K-H5, matrix rows APA-12 and APA-18).

APA-12: "References" starts a new page and is bold + centered; every entry
        has a 0.5" hanging indent and is double spaced; entries are in
        alphabetical order (v1: first word of each entry, ignoring case,
        accents and punctuation). Ties and other close calls are info only.
APA-18: DOIs use https://doi.org/... . Old forms fail: "doi:10...",
        "DOI: 10...", http://doi.org/, http(s)://dx.doi.org/, and a bare
        "10.xxxx/..." with no https://doi.org/ in front. An entry without a
        DOI is fine; a list with no DOIs at all is "na" (nothing to grade).
        "Don't add URLs to database homepages" is not graded.

The reference list runs from the first "References" paragraph to the next
section label (Appendix..., Tables, Figures, Footnotes, ... see
headings.SECTION_LABELS) or the end of the document. Tables are skipped.
No "References" label -> both rows "na".

"Starts a new page" counts any of:
  - pageBreakBefore on the label (direct or through its style)
  - a page break in a run between the last text before the label and the
    label's own text (end of the previous paragraph, an empty paragraph,
    or the start of the label paragraph); pageBreakBefore on an empty
    paragraph in that gap also counts
  - a section break (w:pPr/w:sectPr) in that gap, unless it is continuous
    (w:type="continuous" or "nextColumn" does not start a new page)

Usage:
  python -m tools.corpus.checks.refs --docx file.docx
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

from tools.corpus.checks.abstract import has_pr_flag
from tools.corpus.checks.headings import is_section_label
from tools.corpus.docx_view import AcceptedView, ParagraphView, accepted_view, w
from tools.corpus.style_resolver import resolve_emphasis, resolve_paragraph

HANGING_IN = 0.5
ARTICLES = {"a", "an", "the"}
PARTICLES = {"de", "del", "della", "der", "di", "da", "du", "la", "le", "van", "von",
             "ten", "ter", "st", "dos", "das"}
_NO_NEW_PAGE_SECTIONS = {"continuous", "nextColumn"}

_DOI_RE = re.compile(r"10\.\d{4,9}/\S+")
_BAD_DOI_FORMS = [
    (re.compile(r"\bdoi:\s*$", re.IGNORECASE), "doi: prefix"),
    (re.compile(r"https?://dx\.doi\.org/$", re.IGNORECASE), "dx.doi.org"),
    (re.compile(r"http://doi\.org/$", re.IGNORECASE), "http:// instead of https://"),
]
_GOOD_PREFIX = re.compile(r"https://doi\.org/$", re.IGNORECASE)


def _norm(text: str) -> str:
    return " ".join(text.split()).lower().rstrip(".:")


def _snippet(p: ParagraphView) -> str:
    return p.text.strip()[:50]


def find_references(view: AcceptedView) -> tuple[ParagraphView | None, list[ParagraphView]]:
    """(the "References" label or None, [entry paragraphs])."""
    paras = view.paragraphs
    label = next((p for p in paras if not p.in_table and _norm(p.text) == "references"), None)
    if label is None:
        return None, []
    entries = []
    for p in paras[label.index + 1:]:
        if p.in_table or not p.text.strip():
            continue
        if is_section_label(p.text):
            break
        entries.append(p)
    return label, entries


# --------------------------------------------------------------------------
# New page
# --------------------------------------------------------------------------

def _events(p: ParagraphView) -> list[str]:
    """Run content in order: "T" for visible text, "B" for a page break."""
    out = []
    for run in p.runs:
        for child in run.element:
            if child.tag == w("br") and child.get(w("type")) == "page":
                out.append("B")
            elif child.tag == w("t") and (child.text or "").strip():
                out.append("T")
    return out


def _new_page_section_break(p: ParagraphView) -> bool:
    sect = None if p.pPr is None else p.pPr.find(w("sectPr"))
    if sect is None:
        return False
    kind = sect.find(w("type"))
    return (kind.get(w("val")) if kind is not None else "nextPage") not in _NO_NEW_PAGE_SECTIONS


def starts_new_page(view: AcceptedView, label: ParagraphView) -> str | None:
    """How the label gets onto a new page, or None if it doesn't."""
    if has_pr_flag(label, view, "pageBreakBefore"):
        return "pageBreakBefore on the label"
    events = _events(label)
    first_text = events.index("T") if "T" in events else len(events)
    if "B" in events[:first_text]:
        return "page break at the start of the label paragraph"

    for p in reversed(view.paragraphs[:label.index]):
        if _new_page_section_break(p):
            return f"section break after paragraph {p.index}"
        events = _events(p)
        if "T" in events:
            last_text = len(events) - 1 - events[::-1].index("T")
            if "B" in events[last_text:]:
                return f"page break after the text of paragraph {p.index}"
            return None                      # reached the previous text: no break
        if "B" in events or has_pr_flag(p, view, "pageBreakBefore"):
            return f"page break in empty paragraph {p.index}"
    return None


# --------------------------------------------------------------------------
# Alphabetical order
# --------------------------------------------------------------------------

def sort_key(text: str) -> str:
    """First word, accents and punctuation removed, lowercase ("O'Brien," -> "obrien")."""
    words = text.split()
    if not words:
        return ""
    plain = unicodedata.normalize("NFKD", words[0])
    return "".join(c for c in plain if c.isalnum()).lower()


def _alphabetical(entries: list[ParagraphView]):
    keys = [sort_key(p.text) for p in entries]
    wrong, close = [], []
    for i in range(len(entries) - 1):
        if keys[i] > keys[i + 1]:
            wrong.append({"entry": _snippet(entries[i]), "then": _snippet(entries[i + 1]),
                          "keys": [keys[i], keys[i + 1]]})
        elif keys[i] == keys[i + 1]:
            close.append({"reason": "same first word: check by next author / year",
                          "entries": [_snippet(entries[i]), _snippet(entries[i + 1])]})
    for p, key in zip(entries, keys):
        first = p.text.split()[0]
        if key in ARTICLES:
            close.append({"reason": f'starts with "{first}": APA ignores A/An/The for order',
                          "entries": [_snippet(p)]})
        elif not first[0].isalpha():
            close.append({"reason": "starts with a non-letter", "entries": [_snippet(p)]})
        elif key in PARTICLES:
            close.append({"reason": f'name particle "{first}"', "entries": [_snippet(p)]})
    return wrong, close


# --------------------------------------------------------------------------
# DOIs
# --------------------------------------------------------------------------

def _doi_problems(entries: list[ParagraphView]) -> tuple[int, list[dict]]:
    """(number of DOIs found, [problems])."""
    found, problems = 0, []
    for p in entries:
        for m in _DOI_RE.finditer(p.text):
            found += 1
            before = p.text[:m.start()]
            if _GOOD_PREFIX.search(before):
                continue
            reason = next((r for rx, r in _BAD_DOI_FORMS if rx.search(before)),
                          "bare DOI without https://doi.org/")
            problems.append({"paragraph": p.index, "entry": _snippet(p),
                             "doi": m.group(0), "reason": reason})
    return found, problems


# --------------------------------------------------------------------------
# Public entry point + CLI
# --------------------------------------------------------------------------

def _sub(problems, **evidence) -> dict:
    return {"status": "fail" if problems else "pass", "problems": problems, **evidence}


def _row(check, matrix_id, subchecks, **extra) -> dict:
    if subchecks is None:
        return {"check": check, "matrix_id": matrix_id, "status": "na", "subchecks": {},
                **extra}
    failed = any(s["status"] == "fail" for s in subchecks.values())
    return {"check": check, "matrix_id": matrix_id, "status": "fail" if failed else "pass",
            "subchecks": subchecks, **extra}


def check_references(doc: AcceptedView | str | Path) -> dict:
    """Run APA-12 and APA-18. Returns {"APA-12": {...}, "APA-18": {...}}."""
    view = doc if isinstance(doc, AcceptedView) else accepted_view(doc)
    label, entries = find_references(view)
    if label is None:
        reason = "no References label"
        return {"APA-12": _row("references", "APA-12", None, reason=reason),
                "APA-18": _row("doi", "APA-18", None, reason=reason)}

    how = starts_new_page(view, label)
    label_units = resolve_paragraph(label, view)["units"]
    not_bold = [r.text for r in label.runs if r.text.strip()
                and not resolve_emphasis(r, view)["bold"]]
    not_hanging, not_double = [], []
    for p in entries:
        u = resolve_paragraph(p, view)["units"]
        if u["left_in"] != HANGING_IN or u["first_line_in"] != -HANGING_IN:
            not_hanging.append({"paragraph": p.index, "entry": _snippet(p),
                                "left_in": u["left_in"], "first_line_in": u["first_line_in"]})
        if u["line_rule"] != "auto" or u["line_multiple"] != 2.0:
            not_double.append({"paragraph": p.index, "entry": _snippet(p),
                               "line_rule": u["line_rule"], "line_multiple": u["line_multiple"]})
    wrong_order, close_calls = _alphabetical(entries)

    apa12 = _row("references", "APA-12", {
        "new_page": _sub([] if how else ["References does not start on a new page"], how=how),
        "label_bold": _sub(not_bold),
        "label_centered": _sub([] if label_units["align"] == "center"
                               else [f"alignment is {label_units['align']}"]),
        "entries_present": _sub([] if entries else ["References label but no entries"],
                                entries=len(entries)),
        "hanging_indent": _sub(not_hanging),
        "double_spacing": _sub(not_double),
        "alphabetical": _sub(wrong_order),
        "close_calls": {"status": "info", "items": close_calls,
                        "note": "first-word order only: review manually"},
    }, paragraph=label.index)

    found, bad = _doi_problems(entries)
    if found == 0:
        apa18 = _row("doi", "APA-18", None, reason="no DOIs in the reference list")
    else:
        apa18 = _row("doi", "APA-18", {"https_doi_org": _sub(bad, dois_found=found)})
    return {"APA-12": apa12, "APA-18": apa18}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="APA-12/APA-18 references check")
    ap.add_argument("--docx", required=True, help="path to a .docx file")
    args = ap.parse_args(argv)
    print(json.dumps(check_references(args.docx), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
