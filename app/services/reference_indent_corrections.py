"""Apply APA-style hanging indent to reference list paragraphs as tracked changes.

Every paragraph in the References section receives w:ind w:hanging="720"
(1.27 cm) as a tracked paragraph-property change so the editor can accept
or reject it individually in Word's All Markup view.

Paragraphs that already have the correct hanging indent — whether set directly
on the paragraph or inherited through their paragraph style — are skipped.
"""

import os
import zipfile
from copy import deepcopy

from lxml import etree

from app.services.language_corrections import (
    AUTHOR,
    DATE,
    WQ,
    _get_style_name,
)

_REF_STYLES = {
    "APA7ReferenceListEntry",
    "APA 7 Reference List Entry",
    "APA7 Reference List Entry",
    "APAReferenceListEntry",
    "Reference List Entry",
}

_HANGING = "720"   # 1.27 cm in twentieths-of-a-point (twips)
_LEFT = "720"      # APA hanging indent: continuation lines indented 1.27 cm,
                   # first line pulled back to the margin (left - hanging = 0)

_REFERENCE_HEADING_TEXTS = frozenset({"references", "reference list", "bibliography"})


def _build_style_name_map(z: zipfile.ZipFile) -> dict[str, str]:
    """Return ``styleId -> lowercased style name`` from styles.xml.

    Manuscripts converted from other tools give heading styles numeric ids
    ("3" with name "heading 1"), so the paragraph's ``w:pStyle/@w:val`` alone
    can't tell us it is a heading — resolve it through the style name."""
    if "word/styles.xml" not in z.namelist():
        return {}
    try:
        root = etree.fromstring(z.read("word/styles.xml"))
    except etree.XMLSyntaxError:
        return {}
    out: dict[str, str] = {}
    for style_el in root.findall(f"{WQ}style"):
        sid = style_el.get(f"{WQ}styleId")
        if not sid:
            continue
        name_el = style_el.find(f"{WQ}name")
        if name_el is not None:
            out[sid] = (name_el.get(f"{WQ}val", "") or "").strip().lower()
    return out


def _build_style_hanging_map(z: zipfile.ZipFile) -> dict[str, str]:
    """Return styleId → effective w:hanging value, resolved through basedOn chains.

    Reads styles.xml once and walks each style's inheritance chain so we can
    detect when the hanging indent is already provided by the style rather than
    being set directly on individual paragraphs.
    """
    if "word/styles.xml" not in z.namelist():
        return {}

    styles_root = etree.fromstring(z.read("word/styles.xml"))

    # First pass: collect raw (un-resolved) ind/hanging and basedOn for every
    # paragraph style.
    raw: dict[str, dict] = {}
    for style_el in styles_root.findall(f"{WQ}style"):
        if style_el.get(f"{WQ}type") != "paragraph":
            continue
        sid = style_el.get(f"{WQ}styleId", "")
        if not sid:
            continue
        based_on_el = style_el.find(f"{WQ}basedOn")
        based_on = based_on_el.get(f"{WQ}val", "") if based_on_el is not None else ""
        pPr = style_el.find(f"{WQ}pPr")
        hanging = ""
        if pPr is not None:
            ind = pPr.find(f"{WQ}ind")
            if ind is not None:
                hanging = ind.get(f"{WQ}hanging", "")
        raw[sid] = {"hanging": hanging, "basedOn": based_on}

    # Second pass: resolve each style by walking basedOn chain (max 20 hops).
    resolved: dict[str, str] = {}

    def _resolve(sid: str, visited: set) -> str:
        if sid in resolved:
            return resolved[sid]
        if sid not in raw or sid in visited:
            return ""
        visited.add(sid)
        entry = raw[sid]
        if entry["hanging"]:
            resolved[sid] = entry["hanging"]
            return entry["hanging"]
        parent = _resolve(entry["basedOn"], visited)
        resolved[sid] = parent
        return parent

    for sid in raw:
        _resolve(sid, set())

    return resolved


def _already_correct(pPr: etree._Element, style_hanging: str) -> bool:
    """True if the paragraph already has the target hanging indent.

    Requires BOTH the left indent and the hanging value (a hanging indent with
    no left indent renders as a *negative* first-line indent, not APA hanging).
    Checks the direct paragraph property and the value inherited from the style
    so we don't emit a redundant tracked change.
    """
    ind = pPr.find(f"{WQ}ind")
    if ind is not None:
        # A DIRECT indent overrides the style, so the paragraph is correct only
        # if that direct indent is exactly our hanging indent. In particular a
        # leftover direct w:firstLine (the common "first line indented" error)
        # overrides the style's hanging indent and shifts the entry right — it
        # must be rewritten even when the style itself provides a hanging indent.
        return (
            ind.get(f"{WQ}hanging", "0") == _HANGING
            and ind.get(f"{WQ}left", ind.get(f"{WQ}start", "0")) == _LEFT
            and f"{WQ}firstLine" not in ind.attrib
        )
    # No direct indent: rely on the value inherited from the paragraph style.
    return style_hanging == _HANGING


def apply_reference_indent_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Add 1.27 cm hanging indent to reference paragraphs as tracked pPr changes.

    Returns (next_change_id, corrections_made).
    """
    with zipfile.ZipFile(input_path, "r") as z:
        doc_xml = z.read("word/document.xml")
        style_hanging_map = _build_style_hanging_map(z)
        style_name_map = _build_style_name_map(z)

    doc_root = etree.fromstring(doc_xml)
    made: list[dict] = []

    def _resolved_name(style_val: str) -> str:
        # Resolve a (possibly numeric) style id to its lowercased name; fall
        # back to the raw value so friendly ids ("Heading 1") still compare.
        return style_name_map.get(style_val, (style_val or "").lower())

    def _is_heading(style_val: str) -> bool:
        return _resolved_name(style_val).startswith("heading")

    in_references = False
    for para_el in doc_root.iter(f"{WQ}p"):
        style = _get_style_name(para_el)
        plain_full = "".join(
            t.text or ""
            for r in para_el.iter(f"{WQ}r")
            for t in r.findall(f"{WQ}t")
        ).strip()

        # Track entry into (and exit from) the References section. Detect the
        # heading by TEXT (style-agnostic) so numeric heading style ids don't
        # hide it; end the section at the next heading-styled paragraph.
        if _is_heading(style) and plain_full.lower() in _REFERENCE_HEADING_TEXTS:
            in_references = True
            continue  # don't indent the heading itself
        if in_references and _is_heading(style):
            in_references = False  # new top-level section ends refs

        is_ref_style = style in _REF_STYLES
        if not is_ref_style and not in_references:
            continue
        # NOTE: do NOT skip _SKIP_STYLES here. That set (shared with the
        # spelling pass) includes the reference entry styles themselves, so
        # using it would skip the very paragraphs we need to indent — which is
        # exactly the bug after Sam restyles references to APA7. The
        # is_ref_style / in_references gate above is the correct filter.

        # Skip blank paragraphs (spacer lines between entries).
        plain = "".join(
            t.text or ""
            for r in para_el.iter(f"{WQ}r")
            for t in r.findall(f"{WQ}t")
        ).strip()
        if not plain:
            continue

        # Get or create w:pPr.
        pPr = para_el.find(f"{WQ}pPr")
        if pPr is None:
            pPr = etree.Element(f"{WQ}pPr")
            para_el.insert(0, pPr)

        # Skip if the indent is already correct (direct or via style).
        style_hanging = style_hanging_map.get(style, "")
        if _already_correct(pPr, style_hanging):
            continue

        # A prior pass (Sam's reference restyle) may already have recorded a
        # w:pPrChange on this paragraph while leaving the wrong DIRECT w:ind
        # (e.g. firstLine) in place. We must still fix that direct indent —
        # but a paragraph may carry only one w:pPrChange, so reuse the existing
        # one (it already records the pre-change state) and only rewrite the
        # current/new indent. Otherwise snapshot and add a fresh pPrChange.
        existing_change = pPr.find(f"{WQ}pPrChange")
        old_pPr = deepcopy(pPr) if existing_change is None else None

        # Remove any existing DIRECT w:ind (drops a wrong first-line indent).
        # findall returns only direct children, so the w:ind nested inside an
        # existing pPrChange's snapshot is left untouched.
        for el in pPr.findall(f"{WQ}ind"):
            pPr.remove(el)

        # APA hanging indent needs BOTH left and hanging (and no firstLine):
        # continuation lines sit at `left`, the first line at `left - hanging`
        # (= the margin).
        new_ind = etree.Element(f"{WQ}ind")
        new_ind.set(f"{WQ}left", _LEFT)
        new_ind.set(f"{WQ}hanging", _HANGING)

        if existing_change is not None:
            # Insert before the existing pPrChange (it must remain last).
            existing_change.addprevious(new_ind)
        else:
            pPr.append(new_ind)
            pPr_change = etree.SubElement(pPr, f"{WQ}pPrChange")
            pPr_change.set(f"{WQ}id",     str(next_change_id))
            pPr_change.set(f"{WQ}author", AUTHOR)
            pPr_change.set(f"{WQ}date",   DATE)
            pPr_change.append(old_pPr)
            next_change_id += 1

        made.append({"type": "ref_indent", "description": "Applied 1.27 cm hanging indent"})

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    tmp = output_path + ".refindent.tmp"
    with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "word/document.xml":
                zout.writestr(item, new_doc_xml)
            else:
                zout.writestr(item, zin.read(item.filename))
    os.replace(tmp, output_path)

    return next_change_id, made
