"""Accepted-changes view of a .docx (K-0.3 view half) plus OOXML validity check (K-H1).

Accepted view rules:
  - keep everything inside <w:ins> and <w:moveTo> (the wrapper is removed)
  - drop <w:del> and <w:moveFrom> with everything inside (incl. w:delText)
  - drop formatting-history snapshots (pPrChange, rPrChange, sectPrChange, ...)
    so only the CURRENT pPr/rPr remain
  - a deleted paragraph mark (w:pPr/w:rPr/w:del) merges that paragraph
    into the next one, like Word does when you accept the deletion

Usage:
  python -m tools.corpus.docx_view --docx file.docx            (prints accepted text)
  python -m tools.corpus.docx_view --docx file.docx --json     (paragraphs as JSON)
  python -m tools.corpus.docx_view --docx file.docx --validity (K-H1 check as JSON)
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W_NS, "r": R_NS}


def w(tag: str) -> str:
    """Return the full namespaced name for a w: tag, e.g. w('p')."""
    return f"{{{W_NS}}}{tag}"


# Wrappers whose CONTENT is kept (the wrapper itself is removed).
_UNWRAP = {w("ins"), w("moveTo")}
# Elements removed together with everything inside them.
_DROP = {w("del"), w("moveFrom"), w("delText"), w("delInstrText")}
# Formatting-history snapshots: removed so the current properties win.
_CHANGE_SNAPSHOTS = {
    w("pPrChange"), w("rPrChange"), w("sectPrChange"), w("tblPrChange"),
    w("tblGridChange"), w("trPrChange"), w("tcPrChange"), w("numberingChange"),
    w("tblPrExChange"),
}
# Range markers for moves (no content of their own).
_MARKERS = {
    w("moveFromRangeStart"), w("moveFromRangeEnd"),
    w("moveToRangeStart"), w("moveToRangeEnd"),
}
# Every element that carries a revision w:id (used by the validity check).
_REVISION_TAGS = (
    {w("ins"), w("del"), w("moveTo"), w("moveFrom")}
    | _CHANGE_SNAPSHOTS
)


# --------------------------------------------------------------------------
# Data returned to callers (agreed interface: accepted_view(docx) -> text/runs)
# --------------------------------------------------------------------------

@dataclass
class RunView:
    text: str
    rPr: etree._Element | None  # current run properties (None if the run has none)
    element: etree._Element     # the <w:r> in the accepted tree


@dataclass
class ParagraphView:
    index: int                   # position in document order (0-based)
    text: str
    style_id: str | None         # w:pStyle value, e.g. "Heading1"; None = default style
    pPr: etree._Element | None   # current paragraph properties
    runs: list[RunView]
    in_table: bool
    element: etree._Element      # the <w:p> in the accepted tree


@dataclass
class AcceptedView:
    path: str
    paragraphs: list[ParagraphView]
    sections: list[etree._Element]   # every w:sectPr, in order (last = body-level)
    tree: etree._Element             # accepted w:document root (a modified COPY)
    parts: dict[str, bytes] = field(repr=False, default_factory=dict)

    @property
    def text(self) -> str:
        """Whole document text, one paragraph per line."""
        return "\n".join(p.text for p in self.paragraphs)


# --------------------------------------------------------------------------
# Reading parts
# --------------------------------------------------------------------------

def read_parts(docx_path: str | Path) -> dict[str, bytes]:
    """Return every file inside the .docx zip as {name: bytes}."""
    with zipfile.ZipFile(docx_path) as z:
        return {name: z.read(name) for name in z.namelist()}


def parse_xml(data: bytes) -> etree._Element:
    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
    return etree.fromstring(data, parser)


# --------------------------------------------------------------------------
# Accepting revisions
# --------------------------------------------------------------------------

def accept_revisions(root: etree._Element) -> etree._Element:
    """Return a COPY of `root` with all tracked changes accepted."""
    root = copy.deepcopy(root)

    # 1. Drop deletions and formatting snapshots. Paragraph-mark deletions
    #    (w:pPr/w:rPr/w:del) are recorded first so paragraphs can be merged.
    merge_into_next = []
    for el in list(root.iter()):
        if not isinstance(el.tag, str):
            continue
        if el.tag == w("del") and _is_paragraph_mark_del(el):
            p = el.getparent().getparent().getparent()  # del -> rPr -> pPr -> p
            merge_into_next.append(p)
            el.getparent().remove(el)
        elif el.tag == w("ins") and _is_paragraph_mark_ins(el):
            el.getparent().remove(el)  # inserted paragraph mark: just accept it
        elif el.tag in _DROP or el.tag in _CHANGE_SNAPSHOTS or el.tag in _MARKERS:
            parent = el.getparent()
            if parent is not None:
                _remove_keep_tail(el)

    # 2. Unwrap insertions: move their children up into the parent.
    for el in list(root.iter(*_UNWRAP)):
        _unwrap(el)

    # 3. Merge paragraphs whose paragraph mark was deleted.
    for p in merge_into_next:
        _merge_with_next(p)

    return root


def _is_paragraph_mark_del(el: etree._Element) -> bool:
    parent = el.getparent()
    return (
        parent is not None and parent.tag == w("rPr")
        and parent.getparent() is not None and parent.getparent().tag == w("pPr")
    )


def _is_paragraph_mark_ins(el: etree._Element) -> bool:
    return _is_paragraph_mark_del(el)  # same position check


def _remove_keep_tail(el: etree._Element) -> None:
    parent = el.getparent()
    if el.tail:
        prev = el.getprevious()
        if prev is not None:
            prev.tail = (prev.tail or "") + el.tail
        else:
            parent.text = (parent.text or "") + el.tail
    parent.remove(el)


def _unwrap(el: etree._Element) -> None:
    parent = el.getparent()
    if parent is None:
        return
    idx = parent.index(el)
    for child in list(el):
        parent.insert(idx, child)
        idx += 1
    _remove_keep_tail(el)


def _merge_with_next(p: etree._Element) -> None:
    """Move content of the next sibling paragraph into p, keeping the NEXT
    paragraph's properties (Word keeps the following paragraph mark)."""
    if p.getparent() is None:
        return
    nxt = p.getnext()
    while nxt is not None and nxt.tag != w("p"):
        nxt = nxt.getnext()
    if nxt is None:
        return
    # Content of the merged paragraph = p's content + nxt's content, nxt's pPr.
    p_content = [c for c in p if c.tag != w("pPr")]
    insert_at = 0
    nxt_ppr = nxt.find("w:pPr", NS)
    if nxt_ppr is not None:
        insert_at = 1
    for c in p_content:
        nxt.insert(insert_at, c)
        insert_at += 1
    p.getparent().remove(p)


# --------------------------------------------------------------------------
# Text extraction
# --------------------------------------------------------------------------

def run_text(r: etree._Element) -> str:
    """Visible text of one <w:r> (field instructions are not visible text)."""
    out = []
    for el in r:
        tag = el.tag
        if tag == w("t"):
            out.append(el.text or "")
        elif tag == w("tab") or tag == w("ptab"):
            out.append("\t")
        elif tag in (w("br"), w("cr")):
            out.append("\n")
        elif tag == w("noBreakHyphen"):
            out.append("-")
        elif tag == w("sym"):
            out.append("?")
    return "".join(out)


def _paragraph_runs(p: etree._Element) -> list[etree._Element]:
    """Runs belonging to this paragraph, in order. Includes runs inside
    hyperlinks, smart tags, content controls and fldSimple, but NOT runs of
    nested paragraphs (e.g. text boxes)."""
    runs = []
    for r in p.iter(w("r")):
        owner = r.getparent()
        while owner is not None and owner.tag != w("p"):
            owner = owner.getparent()
        if owner is p:
            runs.append(r)
    return runs


def paragraph_view(p: etree._Element, index: int) -> ParagraphView:
    ppr = p.find("w:pPr", NS)
    style = None
    if ppr is not None:
        ps = ppr.find("w:pStyle", NS)
        if ps is not None:
            style = ps.get(w("val"))
    runs = [RunView(run_text(r), r.find("w:rPr", NS), r) for r in _paragraph_runs(p)]
    in_table = any(a.tag == w("tc") for a in p.iterancestors())
    return ParagraphView(
        index=index,
        text="".join(rv.text for rv in runs),
        style_id=style,
        pPr=ppr,
        runs=runs,
        in_table=in_table,
        element=p,
    )


# --------------------------------------------------------------------------
# Public entry points
# --------------------------------------------------------------------------

def accepted_view(docx_path: str | Path) -> AcceptedView:
    """Agreed interface: accepted view of word/document.xml as text + runs."""
    parts = read_parts(docx_path)
    root = accept_revisions(parse_xml(parts["word/document.xml"]))
    body = root.find("w:body", NS)
    paragraphs = []
    if body is not None:
        for i, p in enumerate(
            el for el in body.iter(w("p"))
            if not any(a.tag == w("txbxContent") for a in el.iterancestors())
        ):
            paragraphs.append(paragraph_view(p, i))
    sections = list(root.iter(w("sectPr")))
    return AcceptedView(str(docx_path), paragraphs, sections, root, parts)


def accepted_part(docx_path: str | Path, part_name: str) -> etree._Element:
    """Accepted view of any other XML part, e.g. 'word/header1.xml'."""
    parts = read_parts(docx_path)
    return accept_revisions(parse_xml(parts[part_name]))


def check_validity(docx_path: str | Path) -> dict:
    """K-H1: zip valid, [Content_Types].xml present, all XML well-formed,
    w:document root, and a COUNT of duplicate revision w:id values
    (reported, not failed, since ids are only guaranteed unique, not ordered)."""
    reasons: list[str] = []
    duplicate_ids = 0
    duplicates: dict[str, int] = {}

    try:
        parts = read_parts(docx_path)
    except (zipfile.BadZipFile, OSError) as exc:
        return {"path": str(docx_path), "valid": False,
                "reasons": [f"not a valid zip: {exc}"],
                "duplicate_id_count": 0, "duplicate_ids": {}}

    if "[Content_Types].xml" not in parts:
        reasons.append("missing [Content_Types].xml")
    if "word/document.xml" not in parts:
        reasons.append("missing word/document.xml")

    ids: Counter[str] = Counter()
    for name, data in parts.items():
        if not (name.endswith(".xml") or name.endswith(".rels")):
            continue
        try:
            root = parse_xml(data)
        except etree.XMLSyntaxError as exc:
            reasons.append(f"malformed XML in {name}: {exc}")
            continue
        if name == "word/document.xml" and root.tag != w("document"):
            reasons.append(f"word/document.xml root is {root.tag}, expected w:document")
        if name.startswith("word/"):
            for el in root.iter(*_REVISION_TAGS):
                rid = el.get(w("id"))
                if rid is not None:
                    ids[rid] += 1

    duplicates = {k: v for k, v in ids.items() if v > 1}
    duplicate_ids = sum(v - 1 for v in duplicates.values())
    return {
        "path": str(docx_path),
        "valid": not reasons,
        "reasons": reasons,
        "duplicate_id_count": duplicate_ids,
        "duplicate_ids": duplicates,
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Accepted-changes view of a .docx")
    ap.add_argument("--docx", required=True, help="path to a .docx file")
    ap.add_argument("--json", action="store_true", help="print paragraphs as JSON")
    ap.add_argument("--validity", action="store_true", help="run the K-H1 validity check")
    args = ap.parse_args(argv)

    if args.validity:
        print(json.dumps(check_validity(args.docx), indent=2))
        return 0

    view = accepted_view(args.docx)
    if args.json:
        data = [
            {"index": p.index, "style_id": p.style_id, "in_table": p.in_table, "text": p.text}
            for p in view.paragraphs
        ]
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(view.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
