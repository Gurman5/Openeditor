"""APA-12 References block: new page, bold centred heading (C-25).

Three fixes, applied in order of preference:

1. **Heading promotion.** A References heading authored as bold ``Normal``
   text (or left on a numeric style id) is promoted to ``Heading 1``. The APA
   base template already defines ``Heading1`` as centred + bold + Calibri, so
   promotion satisfies APA-12 through the style. This is deliberately the
   *primary* path: ``_strip_heading_direct_jc`` removes a direct ``w:jc``
   from every Heading 1-5, so writing direct alignment as the main fix would
   be silently undone.
2. **Tracked direct formatting fallback.** When ``Heading 1`` cannot be
   resolved (the style is missing from the output), bold + centre are written
   directly and recorded with a tracked ``w:pPrChange`` so the editor sees the
   change in All Markup.
3. **Page break before the heading.** ``<w:pageBreakBefore/>``, silent —
   layout plumbing, matching the existing ``_apply_intro_page_break``
   precedent. Idempotent, and recognises a trailing ``<w:br w:type="page"/>``
   so it never double-breaks.

Hanging indent stays owned by ``reference_indent_corrections``; this module
deliberately does not touch it, so the two passes cannot fight over
``w:pPrChange`` on the same paragraph.
"""

from __future__ import annotations

import os
import shutil
import zipfile

from lxml import etree

from app.services.docx_format_helpers import (
    find_canonical_heading,
    get_or_add_ppr,
    has_tracked_page_break_before,
    paragraph_text,
    para_style_id,
    set_para_style,
    set_tracked_ppr,
)
from app.services.language_corrections import WQ

_HEADING1_IDS = ("Heading1", "Heading 1")
_HANGING = "720"  # 0.5in in twips — shared with reference_indent_corrections


def _styles_index(styles_xml: bytes | None) -> dict[str, str]:
    """Return ``styleId -> lowercased style name`` (numeric ids resolve)."""
    if not styles_xml:
        return {}
    try:
        root = etree.fromstring(styles_xml)
    except etree.XMLSyntaxError:
        return {}
    out: dict[str, str] = {}
    for style_el in root.findall(f"{WQ}style"):
        sid = style_el.get(f"{WQ}styleId")
        if not sid:
            continue
        name_el = style_el.find(f"{WQ}name")
        out[sid] = (
            name_el.get(f"{WQ}val", "") if name_el is not None else ""
        ).strip().lower()
    return out


def _heading1_available(styles_index: dict[str, str]) -> str | None:
    """Return the styleId to promote to, or None when Heading 1 is absent.

    A style only counts if it is a paragraph style *named* "heading 1" —
    matching how a checker reads it, so a document with no usable Heading 1
    takes the tracked fallback instead of being tagged with an id that will
    not resolve.
    """
    for sid, name in styles_index.items():
        if name == "heading 1":
            return sid
    return None


def _all_runs_bold(para_el: etree._Element) -> bool:
    """True when the paragraph has visible runs and every one is bold.

    Mirrors ``ParagraphRecord.is_all_bold`` in document_analysis_services, so
    the promotion test and the "is this already a pseudo-heading" test in the
    validator agree.
    """
    runs = [
        r for r in para_el.iter(f"{WQ}r")
        if (r.find(f"{WQ}t") is not None and (r.find(f"{WQ}t").text or "").strip())
    ]
    if not runs:
        return False
    for r in runs:
        r_pr = r.find(f"{WQ}rPr")
        if r_pr is None:
            return False
        b = r_pr.find(f"{WQ}b")
        if b is None:
            return False
        if (b.get(f"{WQ}val", "true") or "true").lower() in ("false", "0", "off"):
            return False
    return True


def _has_direct_jc(para_el: etree._Element) -> str | None:
    p_pr = para_el.find(f"{WQ}pPr")
    if p_pr is None:
        return None
    jc = p_pr.find(f"{WQ}jc")
    return jc.get(f"{WQ}val") if jc is not None else None


def apply_references_block_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Give the References block its APA-12 form.

    Returns ``(next_change_id, actions)``. Actions carry a ``kind`` of
    ``heading_style``, ``heading_format`` or ``page_break``.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        styles_xml = z.read("word/styles.xml") if "word/styles.xml" in names else None

    styles_index = _styles_index(styles_xml)
    heading1_id = _heading1_available(styles_index)
    doc_root = etree.fromstring(doc_xml)
    body = doc_root.find(f"{WQ}body")
    actions: list[dict] = []
    if body is None:
        return next_change_id, actions

    body_paras = [el for el in body if el.tag == f"{WQ}p"]
    heading_el = find_canonical_heading(body_paras, "References")
    if heading_el is None:
        # No References heading: nothing to reformat. The structural rule
        # (SEC-family presence) reports the omission; this pass stays quiet
        # rather than inventing a section. Copy through so callers can always
        # treat output_path as written.
        if input_path != output_path:
            shutil.copyfile(input_path, output_path)
        return next_change_id, actions

    style_id = para_style_id(heading_el)
    style_name = styles_index.get(style_id, style_id.lower())
    is_heading1 = style_name == "heading 1"
    already_bold = _all_runs_bold(heading_el)

    # 1) Promote to Heading 1 so the style supplies centring + bold.
    if heading1_id and not is_heading1:
        set_para_style(heading_el, heading1_id)
        actions.append({"kind": "heading_style", "description": "References heading set to Heading 1"})
        is_heading1 = True

    # 2) Fallback: no usable Heading 1, so write the formatting directly and
    #    record it as a tracked change.
    if not is_heading1:
        if not already_bold:
            for r in heading_el.iter(f"{WQ}r"):
                t = r.find(f"{WQ}t")
                if t is None or not (t.text or "").strip():
                    continue
                r_pr = r.find(f"{WQ}rPr")
                if r_pr is None:
                    r_pr = etree.Element(f"{WQ}rPr")
                    r.insert(0, r_pr)
                if r_pr.find(f"{WQ}b") is None:
                    etree.SubElement(r_pr, f"{WQ}b")
            actions.append({"kind": "heading_format", "description": "References heading set bold"})
        if _has_direct_jc(heading_el) != "center":
            next_change_id = set_tracked_ppr(
                heading_el, "jc", {"val": "center"}, next_change_id
            )
            actions.append({"kind": "heading_format", "description": "References heading centred"})

    # 3) Start the References block on a new page (silent, idempotent).
    if not has_tracked_page_break_before(heading_el):
        p_pr = get_or_add_ppr(heading_el)
        # Drop any DISABLED pageBreakBefore first: a paragraph may carry only
        # one, and leaving the stale val="false" ahead of the new element
        # would make the break read as absent.
        for pb in p_pr.findall(f"{WQ}pageBreakBefore"):
            p_pr.remove(pb)
        pb = etree.Element(f"{WQ}pageBreakBefore")
        # Schema order: w:pPrChange must stay the LAST child of w:pPr, so a
        # silent property written after step 2 has to slot in front of it —
        # appending would leave Word to reject the part.
        existing_change = p_pr.find(f"{WQ}pPrChange")
        if existing_change is not None:
            existing_change.addprevious(pb)
        else:
            p_pr.append(pb)
        actions.append({"kind": "page_break", "description": "Page break inserted before References"})

    if not actions:
        # Nothing to change: copy through so callers can always treat
        # output_path as written (a no-op pass must not leave it missing).
        if input_path != output_path:
            shutil.copyfile(input_path, output_path)
        return next_change_id, actions

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    tmp = output_path + ".refsblock.tmp"
    try:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
            tmp, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return next_change_id, actions


def check_reference_entries_hanging(docx_path: str) -> list[str]:
    """Return human-readable notes on reference entries missing the indent.

    Used by APA012. Resolves the effective hanging indent through the
    paragraph style's ``basedOn`` chain, so an entry that inherits the
    template's ``APA 7 Reference List Entry`` style is not flagged.
    """
    from app.services.reference_indent_corrections import (
        _already_correct,
        _build_style_hanging_map,
        _build_style_name_map,
    )

    with zipfile.ZipFile(docx_path, "r") as z:
        names = z.namelist()
        doc_root = etree.fromstring(z.read("word/document.xml"))
        style_hanging = _build_style_hanging_map(z) if "word/styles.xml" in names else {}
        style_names = _build_style_name_map(z) if "word/styles.xml" in names else {}

    body = doc_root.find(f"{WQ}body")
    if body is None:
        return []
    body_paras = [el for el in body if el.tag == f"{WQ}p"]

    from app.services.docx_format_helpers import heading_names, normalise_heading_text

    refs_names = heading_names("References")
    in_refs = False
    problems: list[str] = []
    for para_el in body_paras:
        style_id = para_style_id(para_el)
        style_name = style_names.get(style_id, style_id.lower())
        text = paragraph_text(para_el)

        if normalise_heading_text(text) in refs_names:
            in_refs = True
            continue
        # Paragraph styles can carry only ONE pPrChange, so an entry the
        # indent pass already touched cannot also record one here. Skip
        # whatever already carries tracked formatting rather than corrupt it.
        existing_p_pr = para_el.find(f"{WQ}pPr")
        if existing_p_pr is not None and \
                existing_p_pr.find(f"{WQ}pPrChange") is not None:
            continue
        if in_refs and style_name.startswith("heading"):
            in_refs = False
        is_ref_style = "reference list entry" in style_name
        if not (is_ref_style or in_refs):
            continue
        if not text:
            continue
        p_pr = get_or_add_ppr(para_el)
        if not _already_correct(p_pr, style_hanging.get(style_id, "")):
            problems.append(text[:60])
    return problems