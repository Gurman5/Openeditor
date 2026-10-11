"""Page-number check (K-H2 step B, matrix row APA-05).

APA-05: a page number at the top right of every page, title page included.

Which header shows on which page:
  - every section shows its "default" header
  - "first" header on the section's first page when the section has w:titlePg
  - "even" header on even pages when word/settings.xml has w:evenAndOddHeaders
  - a section with no headerReference of a type inherits the previous
    section's header of that type (as Word does); none at all = blank header

Each header in use must contain a PAGE field, in either form:
  - <w:fldSimple w:instr=" PAGE ">
  - <w:fldChar begin/> <w:instrText> PAGE </w:instrText> ... <w:fldChar end/>
    (the instruction may be split over several instrText runs)
NUMPAGES and other fields do not count.

"Top right" = the field's paragraph is right-aligned, OR the tabs before the
field land on a right-aligned tab stop (Word's Header style has center and
right stops, so two tabs reach the right one).

Usage:
  python -m tools.corpus.checks.page_numbers --docx file.docx
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.corpus.docx_view import AcceptedView, accept_revisions, accepted_view, parse_xml, w
from tools.corpus.style_resolver import get_resolver, resolve_paragraph

R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_OFF = ("0", "false", "off")
TYPE_NAMES = {"default": "default", "first": "first-page", "even": "even-page"}


def _on(el) -> bool:
    return el is not None and el.get(w("val")) not in _OFF


def _rel_targets(view: AcceptedView) -> dict[str, str]:
    """{rId: part name} for word/document.xml."""
    rels = view.parts.get("word/_rels/document.xml.rels")
    if rels is None:
        return {}
    out = {}
    for rel in parse_xml(rels).iter(f"{{{PKG_REL_NS}}}Relationship"):
        out[rel.get("Id")] = "word/" + rel.get("Target").lstrip("/").removeprefix("word/")
    return out


def _even_and_odd(view: AcceptedView) -> bool:
    settings = view.parts.get("word/settings.xml")
    return settings is not None and _on(parse_xml(settings).find(w("evenAndOddHeaders")))


def sections_in_use(view: AcceptedView, kind: str):
    """For each section: {type: part name or None} of the headers/footers in use.
    kind is "header" or "footer"."""
    targets = _rel_targets(view)
    even = _even_and_odd(view)
    current: dict[str, str] = {}
    out = []
    for sect in view.sections:
        for ref in sect.iter(w(f"{kind}Reference")):
            part = targets.get(ref.get(f"{{{R_NS}}}id"))
            if part:
                current[ref.get(w("type")) or "default"] = part
        needed = ["default"]
        if _on(sect.find(w("titlePg"))):
            needed.insert(0, "first")
        if even:
            needed.append("even")
        out.append({t: current.get(t) for t in needed})
    return out


# --------------------------------------------------------------------------
# Finding PAGE fields
# --------------------------------------------------------------------------

def _own(el, p) -> bool:
    """True if el belongs to paragraph p (not to a paragraph nested inside it)."""
    owner = el.getparent()
    while owner is not None and owner.tag != w("p"):
        owner = owner.getparent()
    return owner is p


def is_page_instruction(instr: str) -> bool:
    words = instr.split()
    return bool(words) and words[0].upper() == "PAGE"


def page_fields(root) -> list[dict]:
    """Every PAGE field in a header/footer part:
    [{"paragraph": <w:p>, "form": "fldSimple"|"fldChar", "tabs_before": n}, ...]."""
    found = []
    for p in root.iter(w("p")):
        tabs = 0
        open_fields: list[dict] = []        # nested fldChar fields, innermost last
        for el in p.iter(w("fldSimple"), w("tab"), w("fldChar"), w("instrText")):
            if not _own(el, p) or (el.tag == w("tab") and el.getparent().tag != w("r")):
                continue                    # skip tab STOPS (w:pPr/w:tabs/w:tab)
            if el.tag == w("tab"):
                tabs += 1
            elif el.tag == w("fldSimple"):
                if is_page_instruction(el.get(w("instr")) or ""):
                    found.append({"paragraph": p, "form": "fldSimple", "tabs_before": tabs})
            elif el.tag == w("instrText"):
                if open_fields:
                    open_fields[-1]["instr"] += el.text or ""
            else:
                kind = el.get(w("fldCharType"))
                if kind == "begin":
                    open_fields.append({"instr": "", "tabs": tabs, "done": False})
                elif kind in ("separate", "end") and open_fields:
                    field = open_fields[-1]
                    if not field["done"] and is_page_instruction(field["instr"]):
                        found.append({"paragraph": p, "form": "fldChar",
                                      "tabs_before": field["tabs"]})
                    field["done"] = True    # instruction ends at "separate"
                    if kind == "end":
                        open_fields.pop()
    return found


def _tab_stops(p, view: AcceptedView) -> list[tuple[int, str]]:
    """Effective tab stops [(pos, alignment)], sorted. More specific levels win
    and w:val="clear" removes a stop inherited from a style."""
    stops: dict[int, str] = {}
    for _, ppr in reversed(get_resolver(view).paragraph_levels(p)):   # least specific first
        tabs = ppr.find(w("tabs"))
        if tabs is None:
            continue
        for tab in tabs.findall(w("tab")):
            try:
                pos = int(tab.get(w("pos")))
            except (TypeError, ValueError):
                continue
            if tab.get(w("val")) == "clear":
                stops.pop(pos, None)
            else:
                stops[pos] = tab.get(w("val"))
    return sorted(stops.items())


def _position(field: dict, view: AcceptedView) -> str | None:
    """How the field sits at the right, or None if it doesn't."""
    p = field["paragraph"]
    if resolve_paragraph(p, view)["units"]["align"] == "right":
        return "right-aligned paragraph"
    stops = _tab_stops(p, view)
    n = field["tabs_before"]
    if 1 <= n <= len(stops) and stops[n - 1][1] in ("right", "end"):
        return f"right tab stop at {stops[n - 1][0]} twips"
    return None


# --------------------------------------------------------------------------
# Public entry point + CLI
# --------------------------------------------------------------------------

def check_page_numbers(doc: AcceptedView | str | Path) -> dict:
    view = doc if isinstance(doc, AcceptedView) else accepted_view(doc)
    if not view.sections:
        return {"check": "pagenum", "matrix_id": "APA-05", "status": "na", "subchecks": {}}

    cache: dict[str, list[dict]] = {}

    def fields_in(part):
        if part not in cache:
            cache[part] = ([] if part not in view.parts
                           else page_fields(accept_revisions(parse_xml(view.parts[part]))))
        return cache[part]

    headers = sections_in_use(view, "header")
    footers = sections_in_use(view, "footer")
    slots, problems = [], []
    for i, (hdrs, ftrs) in enumerate(zip(headers, footers)):
        for htype, part in hdrs.items():
            name = TYPE_NAMES.get(htype, htype)
            slot = {"section": i, "type": htype, "part": part, "page_field": None,
                    "position": None}
            slots.append(slot)
            fields = fields_in(part) if part else []
            if fields:
                slot["page_field"] = fields[0]["form"]
                placed = [pos for f in fields if (pos := _position(f, view))]
                slot["position"] = placed[0] if placed else None
                if not placed:
                    problems.append({**slot, "reason": f"{name} page number is not at the right"})
                continue
            footer = ftrs.get(htype)
            if footer and fields_in(footer):
                reason = f"{name} page number is in the footer, should be in the header"
            elif part is None:
                reason = f"no {name} header"
            else:
                reason = f"{name} header has no page number"
            problems.append({**slot, "reason": reason})

    sub = {"status": "fail" if problems else "pass", "problems": problems, "headers": slots,
           "even_and_odd_headers": _even_and_odd(view)}
    return {"check": "pagenum", "matrix_id": "APA-05", "status": sub["status"],
            "subchecks": {"top_right_every_page": sub}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="APA-05 page-number check")
    ap.add_argument("--docx", required=True, help="path to a .docx file")
    args = ap.parse_args(argv)
    print(json.dumps(check_page_numbers(args.docx), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
