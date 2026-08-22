"""Insert missing space after p. / pp. in in-text page references.

APA style requires a space between the abbreviation and the page number:
  p. 23  (not p.23)
  pp. 45-47  (not pp.45-47)

Corrections are emitted as <w:del>/<w:ins> tracked-change pairs so the
editor can accept or reject each one individually in Word.
"""

from __future__ import annotations

import os
import re
import zipfile

from lxml import etree

from app.services.language_corrections import (
    _SKIP_STYLES,
    WQ,
    _get_style_name,
    _is_references_heading,
    _merge_adjacent_runs,
    _split_run_at_match,
)

# Match "p." or "pp." immediately followed by a digit (no space between).
# Captures: group(1) = "p" or "pp", group(2) = the first digit.
# The full match ("p.3" / "pp.45") is what appears in del; replacement adds the space.
_PAGE_PATTERN = re.compile(r"(pp?)\.(\d)")


def _apply_corrections_to_para(
    para_el: etree._Element,
    change_id: int,
    made: list[dict],
) -> int:
    _merge_adjacent_runs(para_el)

    changed = True
    while changed:
        changed = False
        for r in para_el.iter(f"{WQ}r"):
            parent = r.getparent()
            if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
                continue
            t_el = r.find(f"{WQ}t")
            if t_el is None:
                continue
            run_text = t_el.text or ""
            m = _PAGE_PATTERN.search(run_text)
            if m is None:
                continue
            prefix, digit = m.group(1), m.group(2)
            corrected = f"{prefix}. {digit}"
            change_id = _split_run_at_match(r, m, corrected, change_id)
            made.append({"original": m.group(0), "replacement": corrected})
            changed = True
            break

    return change_id


def apply_citation_formatting_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Add a space after p./pp. before page numbers as tracked changes.

    Returns (next_change_id, corrections_made).
    """
    with zipfile.ZipFile(input_path, "r") as z:
        doc_xml = z.read("word/document.xml")

    doc_root = etree.fromstring(doc_xml)
    made: list[dict] = []

    in_references = False
    for para_el in doc_root.iter(f"{WQ}p"):
        if _is_references_heading(para_el):
            in_references = True
        if in_references:
            continue
        if _get_style_name(para_el) in _SKIP_STYLES:
            continue
        # Quick pre-filter — skip paragraphs that can't match.
        plain = "".join(
            (t.text or "")
            for r in para_el.iter(f"{WQ}r")
            for t in r.findall(f"{WQ}t")
            if r.getparent() is not None
            and r.getparent().tag not in (f"{WQ}del", f"{WQ}ins")
        )
        if not _PAGE_PATTERN.search(plain):
            continue
        next_change_id = _apply_corrections_to_para(para_el, next_change_id, made)

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    tmp = output_path + ".citfmt.tmp"
    with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
        tmp, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            if item.filename == "word/document.xml":
                zout.writestr(item, new_doc_xml)
            else:
                zout.writestr(item, zin.read(item.filename))
    os.replace(tmp, output_path)

    return next_change_id, made
