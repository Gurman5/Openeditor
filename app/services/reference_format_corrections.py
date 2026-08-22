"""Apply APA 7 reference format corrections as Word tracked changes.

For each reference entry where CrossRef verification found format problems,
the paragraph's existing content is replaced with a w:del / w:ins pair:

  w:del  — original text (editor sees what was there before, struck through)
  w:ins  — correctly formatted APA 7 reconstruction (editor sees the fix)

The editor can accept or reject each correction individually in Word's
All Markup view.  Paragraph properties (style, indentation) are preserved.
Comment anchors, bookmarks, and other non-run elements are also preserved
so existing comments on reference paragraphs remain attached.

Public API
----------
apply_reference_format_corrections(
    input_path, output_path, next_change_id, ref_results
) -> (next_change_id, corrections_made)
"""

import os
import re
import zipfile

from lxml import etree

from app.services.document_zones import normalise_heading
from app.services.language_corrections import AUTHOR, DATE, WQ

_REFERENCE_HEADING_TEXTS = frozenset({"references", "reference list", "bibliography"})


def _build_style_name_map(styles_xml: bytes | None) -> dict[str, str]:
    """Return ``styleId -> lowercased style name`` from styles.xml.

    Converted documents give heading styles numeric ids ("3" with name
    "heading 1"), so the paragraph's pStyle val alone can't reveal that it is a
    heading — resolve it through the style name."""
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
        if name_el is not None:
            out[sid] = (name_el.get(f"{WQ}val", "") or "").strip().lower()
    return out

# Preserve XML space attribute from the XML namespace
_XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

# Relationship namespaces for hyperlink insertion
_PKG_NS  = "http://schemas.openxmlformats.org/package/2006/relationships"
_R_NS    = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_HL_TYPE = f"{_R_NS}/hyperlink"
_R_NS_Q  = f"{{{_R_NS}}}"

# Matches a URL in the reconstructed APA string (the DOI URL at the end)
_URL_RE = re.compile(r'https?://\S+')

# Paragraph styles that mark APA 7 reference list entries
_REF_STYLES = {
    "APA7ReferenceListEntry",
    "APA 7 Reference List Entry",
    "APA7 Reference List Entry",
    "APAReferenceListEntry",
    "Reference List Entry",
}

# Used in the fallback (non-styled) entry detection
_YEAR_RE = re.compile(r'\(\d{4}[a-z]?\)')

# Elements that must survive a paragraph content replacement because they
# hold comment anchors or named bookmarks.
_PRESERVE_TAGS = frozenset({
    f'{WQ}bookmarkStart',
    f'{WQ}bookmarkEnd',
    f'{WQ}commentRangeStart',
    f'{WQ}commentRangeEnd',
})


# ── Internal helpers ──────────────────────────────────────────────────────────

def _para_style(para: etree._Element) -> str:
    pPr = para.find(f'{WQ}pPr')
    if pPr is None:
        return ''
    ps = pPr.find(f'{WQ}pStyle')
    return ps.get(f'{WQ}val', '') if ps is not None else ''


def _para_plain_text(para: etree._Element) -> str:
    """Extract all visible plain text from the paragraph.

    Iterates every w:t element — including those inside hyperlinks,
    tracked insertions, etc. — and concatenates them.
    """
    return ''.join(t.text or '' for t in para.iter(f'{WQ}t')).strip()


def _is_comment_ref_run(el: etree._Element) -> bool:
    """True if this w:r element is a comment-reference run (contains w:commentReference)."""
    return el.tag == f'{WQ}r' and el.find(f'{WQ}commentReference') is not None


def _collect_ref_paragraphs(
    body_paras: list[etree._Element],
    style_names: dict[str, str] | None = None,
) -> list[etree._Element]:
    """Return the ordered list of reference entry paragraph elements.

    Uses the same two-tier selection logic as reference_checker.extract_references
    and the pipeline's _insert_suspicious_ref_comments so entry numbering stays
    in sync with what CrossRef verified.

    Tier 1 (preferred): paragraphs styled with any APA 7 reference style.
    Tier 2 (fallback):  paragraphs inside the References section that contain a
                        year and are longer than 20 characters.

    The References heading is detected by NORMALISED text (number-tolerant) and
    the section-end by a resolved heading style, so a converted document whose
    headings carry numeric style ids ("3") — where ``style`` is "3" rather than
    "Heading 1" — is still handled (otherwise no entries were found and the
    APA-7 reformatting silently did nothing).
    """
    style_names = style_names or {}

    def _is_heading(style_val: str) -> bool:
        return (
            style_val.startswith("Heading")
            or style_names.get(style_val, "").startswith("heading")
        )

    in_refs = False
    window: list[tuple[str, etree._Element]] = []  # (style, para)

    for para in body_paras:
        style = _para_style(para)
        text  = _para_plain_text(para)

        if _is_heading(style) and normalise_heading(text) in _REFERENCE_HEADING_TEXTS:
            in_refs = True
            continue
        if in_refs and _is_heading(style):
            break  # next top-level heading ends the refs window
        if in_refs and text:
            window.append((style, para))

    # Prefer style-marked entries
    styled = [p for s, p in window if s in _REF_STYLES]
    if styled:
        return styled

    # Fallback: year + length heuristic
    return [
        p for _s, p in window
        if len(_para_plain_text(p)) > 20 and bool(_YEAR_RE.search(_para_plain_text(p)))
    ]


def _apply_del_ins(
    para: etree._Element,
    old_text: str,
    new_text: str,
    del_id: int,
    ins_id: int,
    url: str = "",
    url_rid: str = "",
    hl_ins_id: int = 0,
) -> None:
    """Replace all run-level content in the paragraph with a tracked del/ins pair.

    When *url* and *url_rid* are provided the reconstructed text is split at the
    URL: the text before it goes into a plain w:ins run and the URL itself is
    wrapped in a w:hyperlink → w:ins → w:r element styled black so it is
    clickable but does not print in blue.

    Preserves:
      - w:pPr  (paragraph style, indentation, etc.)
      - w:bookmarkStart / w:bookmarkEnd
      - w:commentRangeStart / w:commentRangeEnd
      - Any w:r that is a comment-reference run

    Everything else (text runs, hyperlinks, existing tracked changes) is
    removed so the old text appears as a single w:delText and the new
    APA 7 text appears as a single w:ins run.
    """
    pPr = para.find(f'{WQ}pPr')

    # Separate children into those we keep and those we replace
    to_keep:   list[etree._Element] = []
    to_remove: list[etree._Element] = []

    for child in para:
        if child is pPr:
            continue  # handled separately — always stays first
        if child.tag in _PRESERVE_TAGS or _is_comment_ref_run(child):
            to_keep.append(child)
        else:
            to_remove.append(child)

    # Remove everything except pPr and the preserved elements
    for child in to_remove:
        para.remove(child)
    for child in to_keep:
        para.remove(child)   # temporarily remove; re-added after del/ins

    # ── w:del ─────────────────────────────────────────────────────────────────
    del_el = etree.SubElement(para, f'{WQ}del')
    del_el.set(f'{WQ}id',     str(del_id))
    del_el.set(f'{WQ}author', AUTHOR)
    del_el.set(f'{WQ}date',   DATE)

    del_run  = etree.SubElement(del_el, f'{WQ}r')
    del_text = etree.SubElement(del_run, f'{WQ}delText')
    del_text.text = old_text
    del_text.set(_XML_SPACE, 'preserve')

    # ── w:ins (text body, up to the URL if present) ───────────────────────────
    text_before = new_text[:new_text.find(url)].rstrip() if url else new_text

    ins_el = etree.SubElement(para, f'{WQ}ins')
    ins_el.set(f'{WQ}id',     str(ins_id))
    ins_el.set(f'{WQ}author', AUTHOR)
    ins_el.set(f'{WQ}date',   DATE)

    ins_run  = etree.SubElement(ins_el, f'{WQ}r')
    ins_text = etree.SubElement(ins_run, f'{WQ}t')
    ins_text.text = text_before
    ins_text.set(_XML_SPACE, 'preserve')

    # ── w:hyperlink (URL as black clickable link inside a tracked insertion) ──
    if url and url_rid:
        hl = etree.SubElement(para, f'{WQ}hyperlink')
        hl.set(f'{_R_NS_Q}id', url_rid)
        hl.set(f'{WQ}history', '1')

        hl_ins = etree.SubElement(hl, f'{WQ}ins')
        hl_ins.set(f'{WQ}id',     str(hl_ins_id))
        hl_ins.set(f'{WQ}author', AUTHOR)
        hl_ins.set(f'{WQ}date',   DATE)

        hl_run = etree.SubElement(hl_ins, f'{WQ}r')
        hl_rPr = etree.SubElement(hl_run, f'{WQ}rPr')
        hl_style = etree.SubElement(hl_rPr, f'{WQ}rStyle')
        hl_style.set(f'{WQ}val', 'Hyperlink')
        hl_color = etree.SubElement(hl_rPr, f'{WQ}color')
        hl_color.set(f'{WQ}val', '000000')

        hl_t = etree.SubElement(hl_run, f'{WQ}t')
        hl_t.text = url
        hl_t.set(_XML_SPACE, 'preserve')

    # Re-attach preserved elements after the del/ins pair
    for child in to_keep:
        para.append(child)


# ── Public API ────────────────────────────────────────────────────────────────

def apply_reference_format_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int,
    ref_results: list[dict],
) -> tuple[int, list[dict]]:
    """Apply APA 7 format corrections to reference paragraphs as tracked changes.

    Parameters
    ----------
    input_path:
        Path to the input .docx file.
    output_path:
        Path to write the corrected .docx (may be the same as input_path;
        the function uses a temp file to avoid partial writes).
    next_change_id:
        The next available w:id integer for tracked-change elements.
        Must be higher than every existing id in the document to avoid
        collisions with Sam's builder and other correction passes.
    ref_results:
        The full list of result dicts from check_and_report().
        Only CREF### entries that carry both 'reconstructed' and
        'format_issues' keys will trigger a tracked change.

    Returns
    -------
    (next_change_id, corrections_made)
        next_change_id — updated counter for subsequent correction passes
        corrections_made — list of dicts describing each change applied
    """
    # ── Build entry_num → (reconstructed, format_issues) map ──────────────────
    correction_map: dict[int, tuple[str, list[str]]] = {}
    for r in ref_results:
        rule_id       = r.get('rule_id', '')
        reconstructed = r.get('reconstructed', '')
        format_issues = r.get('format_issues', [])

        if not reconstructed or not format_issues:
            continue
        if not rule_id.startswith('CREF'):
            continue

        # Extract the numeric part after "CREF" (e.g. "CREF003" -> 3)
        num_str = rule_id[4:].split('_')[0]
        if not num_str.isdigit():
            continue

        correction_map[int(num_str)] = (reconstructed, format_issues)

    if not correction_map:
        return next_change_id, []

    # ── Load document.xml and the relationship file ───────────────────────────
    _RELS_PATH = 'word/_rels/document.xml.rels'
    with zipfile.ZipFile(input_path, 'r') as z:
        doc_xml  = z.read('word/document.xml')
        rels_xml = z.read(_RELS_PATH) if _RELS_PATH in z.namelist() else None
        styles_xml = z.read('word/styles.xml') if 'word/styles.xml' in z.namelist() else None

    style_names = _build_style_name_map(styles_xml)

    doc_root = etree.fromstring(doc_xml)
    body     = doc_root.find(f'{WQ}body')
    if body is None:
        return next_change_id, []

    # Parse rels; build next rId counter
    if rels_xml is not None:
        rels_root = etree.fromstring(rels_xml)
    else:
        rels_root = etree.fromstring(
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
        )

    existing_ids = [
        int(rel.get('Id', 'rId0')[3:])
        for rel in rels_root
        if rel.get('Id', '').startswith('rId') and rel.get('Id', '')[3:].isdigit()
    ]
    next_rid = max(existing_ids, default=0) + 1

    def _add_hyperlink_rel(url: str) -> str:
        nonlocal next_rid
        rid = f'rId{next_rid}'
        next_rid += 1
        rel = etree.SubElement(rels_root, 'Relationship')
        rel.set('Id',         rid)
        rel.set('Type',       _HL_TYPE)
        rel.set('Target',     url)
        rel.set('TargetMode', 'External')
        return rid

    body_paras = [el for el in body if el.tag == f'{WQ}p']
    ref_paras  = _collect_ref_paragraphs(body_paras, style_names)

    corrections: list[dict] = []
    rels_modified = False

    for entry_num, para in enumerate(ref_paras, start=1):
        if entry_num not in correction_map:
            continue

        reconstructed, format_issues = correction_map[entry_num]
        original_text = _para_plain_text(para)

        if not original_text.strip():
            continue

        # Skip paragraphs that already have a tracked change from a previous
        # pass — this avoids double-wrapping if the pipeline ever runs twice.
        if para.find(f'{WQ}del') is not None or para.find(f'{WQ}ins') is not None:
            continue

        # Detect a URL in the reconstructed text
        url_match = _URL_RE.search(reconstructed)
        if url_match:
            url     = url_match.group(0).rstrip('.')
            url_rid = _add_hyperlink_rel(url)
            rels_modified = True
            _apply_del_ins(
                para,
                old_text=original_text,
                new_text=reconstructed,
                del_id=next_change_id,
                ins_id=next_change_id + 1,
                url=url,
                url_rid=url_rid,
                hl_ins_id=next_change_id + 2,
            )
            next_change_id += 3
        else:
            _apply_del_ins(
                para,
                old_text=original_text,
                new_text=reconstructed,
                del_id=next_change_id,
                ins_id=next_change_id + 1,
            )
            next_change_id += 2

        corrections.append({
            'type':          'ref_format',
            'entry_num':     entry_num,
            'format_issues': format_issues,
            'description':   (
                f'Entry {entry_num}: APA 7 format corrected '
                f'({"; ".join(format_issues)})'
            ),
        })

    if not corrections:
        return next_change_id, []

    # ── Serialise modified XML ─────────────────────────────────────────────────
    new_doc_xml  = etree.tostring(
        doc_root, xml_declaration=True, encoding='UTF-8', standalone=True
    )
    new_rels_xml = etree.tostring(
        rels_root, xml_declaration=True, encoding='UTF-8', standalone=True
    ) if rels_modified else None

    # ── Write corrected files back into a new zip ─────────────────────────────
    tmp = output_path + '.refmt.tmp'
    try:
        with (
            zipfile.ZipFile(input_path, 'r') as zin,
            zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout,
        ):
            for item in zin.infolist():
                if item.filename == 'word/document.xml':
                    zout.writestr(item, new_doc_xml)
                elif item.filename == _RELS_PATH and new_rels_xml is not None:
                    zout.writestr(item, new_rels_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
            # If rels file didn't exist originally but we created relationships,
            # add it as a new entry.
            if rels_modified and _RELS_PATH not in zin.namelist():
                zout.writestr(_RELS_PATH, new_rels_xml)
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return next_change_id, corrections
