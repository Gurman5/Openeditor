"""Replace 3+ author in-text citations with et al. as tracked changes.

APA 7 requires et al. from the first citation when a work has three or more
authors.  This correction handles:

  Bracketed (parenthetical) citations
    (Smith, Jones, & Brown, 2020)          →  (Smith et al., 2020)
    (Smith, Jones, & Brown, 2020, p. 45)   →  (Smith et al., 2020, p. 45)
    (Smith, Jones, & Brown, 2020, pp. 4-6) →  (Smith et al., 2020, pp. 4-6)

  Narrative (author-prominent) citations
    Smith, Jones, and Brown (2020)          →  Smith et al. (2020)
    Smith, Jones, and Brown (2020, p. 45)   →  Smith et al. (2020, p. 45)

Detection rule: 3+ authors are present when there is at least one
comma-separated author name BEFORE the final "& / and Author" segment.
Two-author forms — "(Smith & Jones, 2020)" or "Smith and Jones (2020)" —
do not have that comma, so they are left untouched.
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

# One author last name: starts with a capital, followed by one or more
# letters (including accented), hyphens, or apostrophes.
# Deliberately excludes initials like "J." because the dot is not in the set.
_NAME = r"[A-Z][a-zA-ZÀ-ÿ\-\']+"

# Optional page suffix inside a citation: ", p. 23" or ", pp. 23-45".
# Handles en-dash (–) and hyphen page ranges.
_PAGE = r"(?:,\s*pp?\.\s*\d[\d–\-]*)?"

# ---------------------------------------------------------------------------
# Bracketed citation pattern
# Matches the entire "(First, Middle, & Last, Year[, page])" group.
# Requires >=1 comma-separated middle author -> enforces 3+ total.
# ---------------------------------------------------------------------------
_BRACKET = re.compile(
    r"\("
    + r"(" + _NAME + r")"
    + r"(?:,\s*" + _NAME + r")+"
    + r",\s*(?:&|and)\s*" + _NAME
    + r",\s*(\d{4})"
    + r"(" + _PAGE + r")"
    + r"\)",
    re.UNICODE,
)

# ---------------------------------------------------------------------------
# Narrative citation pattern
# Matches "First, Middle, and Last (Year[, page])".
# Requires >=1 middle author before the "and/& Last" part -> 3+ total.
# ---------------------------------------------------------------------------
_NARRATIVE = re.compile(
    r"(" + _NAME + r")"
    + r"(?:,\s*" + _NAME + r")+"
    + r",\s*(?:&|and)\s*" + _NAME
    + r"\s*\("
    + r"(\d{4})"
    + r"(" + _PAGE + r")"
    + r"\)",
    re.UNICODE,
)


def _corrected_bracket(m: re.Match) -> str:
    first, year, page = m.group(1), m.group(2), m.group(3) or ""
    return f"({first} et al., {year}{page})"


def _corrected_narrative(m: re.Match) -> str:
    first, year, page = m.group(1), m.group(2), m.group(3) or ""
    return f"{first} et al. ({year}{page})"


def _apply_corrections_to_para(
    para_el: etree._Element,
    change_id: int,
    made: list[dict],
) -> int:
    _merge_adjacent_runs(para_el)

    for pattern, make_corrected in (
        (_BRACKET, _corrected_bracket),
        (_NARRATIVE, _corrected_narrative),
    ):
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
                m = pattern.search(run_text)
                if m is None:
                    continue
                corrected = make_corrected(m)
                if corrected == m.group(0):
                    continue
                change_id = _split_run_at_match(r, m, corrected, change_id)
                made.append({"original": m.group(0), "replacement": corrected})
                changed = True
                break

    return change_id


def apply_et_al_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Replace 3+ author in-text citations with et al. as tracked changes.

    Returns (next_change_id, corrections_made).
    """
    with zipfile.ZipFile(input_path, "r") as z:
        doc_xml = z.read("word/document.xml")

    doc_root = etree.fromstring(doc_xml)
    made: list[dict] = []

    WQ = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

    in_references = False
    for para_el in doc_root.iter(f"{WQ}p"):
        if _is_references_heading(para_el):
            in_references = True
        if in_references:
            continue
        if _get_style_name(para_el) in _SKIP_STYLES:
            continue
        # Pre-filter: skip paragraphs that can't possibly contain 3+ authors.
        plain = "".join(
            (t.text or "")
            for r in para_el.iter(f"{WQ}r")
            for t in r.findall(f"{WQ}t")
            if r.getparent() is not None
            and r.getparent().tag not in (f"{WQ}del", f"{WQ}ins")
        )
        if "&" not in plain and " and " not in plain:
            continue
        next_change_id = _apply_corrections_to_para(para_el, next_change_id, made)

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    tmp = output_path + ".etal.tmp"
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
