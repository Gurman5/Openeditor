import argparse
import logging
import os
import re
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pprint import pprint
from typing import Callable

from lxml import etree

from app.services.abbreviation_corrections import apply_abbreviation_corrections
from app.services.acronym_corrections import apply_acronym_corrections
from app.services.ai.editorial_review_service import run_editorial_review
from app.services.appendix_removal import apply_appendix_removal
from app.services.blinded_citation_comments import apply_blinded_citation_comments
from app.services.caption_apa7_check import apply_caption_apa7_comments
from app.services.decimal_corrections import apply_decimal_corrections
from app.services.document_normalisation_services import normalise_docx
from app.services.grammar_corrections import apply_contingent_grammar_comments
from app.services.heading_corrections import apply_heading_corrections
from app.services.jutlp_validator import validate
from app.services.language_corrections import AUTHOR, DATE, apply_au_spelling_corrections
from app.services.number_word_corrections import apply_number_word_corrections
from app.services.output_generation import (
    REFERENCE_ISSUE_SUMMARY_PREFIX,
    _reference_issue_summary_comment,
    add_document_summary_comment,
    add_paragraph_comment,
    generate_commented_docx,
)
from app.services.output_generation_samfix import (
    _renumber_author_queries_by_anchor_order,
    build_edited_document,
)
from app.services.reference_checker import check_and_report
from app.services.reference_format_corrections import apply_reference_format_corrections
from app.services.reference_indent_corrections import apply_reference_indent_corrections
from app.services.reference_order_comments import apply_reference_order_comments
from app.services.run_font_corrections import apply_run_font_corrections
from app.services.sentence_coherence_corrections import apply_sentence_coherence_corrections
from app.services.short_paragraph_comments import apply_short_paragraph_comments
from app.services.spell_checker import apply_spell_corrections
from app.services.table_keep_together import apply_table_keep_together
from app.services.table_n_notation_comments import apply_table_n_notation_comments
from app.services.table_page_breaks import apply_table_page_breaks
from app.services.table_section_boundary_comments import apply_table_section_boundary_comments

log = logging.getLogger(__name__)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower())


def _safe_unlink(path: str) -> None:
    """Best-effort temp-file cleanup — never raises."""
    try:
        os.unlink(path)
    except OSError:
        pass


def _renumber_final_author_queries(docx_path: str) -> bool:
    """Renumber visible Author Query labels after every comment pass has run."""
    return _renumber_author_queries_by_anchor_order(docx_path)


def _max_revision_id(docx_path: str) -> int:
    """Return the largest ``w:id`` on any tracked-change element in the doc.

    Tracked-change elements (``w:ins`` and ``w:del``) live in the same id
    namespace. The correction passes that run after ``generate_commented_docx``
    and Sam's ``build_edited_document`` need to start their ``w:id`` counter
    above whatever has already been written — otherwise IDs collide with
    Sam's hardcoded ranges (10, 20, 1000, 1200, 7000+, 8000+) and Word can
    silently drop one of the colliding revisions during accept/reject.
    """
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            if "word/document.xml" not in z.namelist():
                return 0
            doc_xml = z.read("word/document.xml")
    except (zipfile.BadZipFile, OSError):
        return 0

    root = etree.fromstring(doc_xml)
    max_id = 0
    for tag in (f"{WQ}ins", f"{WQ}del"):
        for el in root.iter(tag):
            raw = el.get(f"{WQ}id")
            if raw is None:
                continue
            try:
                value = int(raw)
            except (TypeError, ValueError):
                continue
            if value > max_id:
                max_id = value
    return max_id


def _remove_duplicate_sam_comments(docx_path: str, our_max_id: int) -> None:
    """Remove Sam's comments (id > our_max_id) that duplicate our validator output.

    Uses a simple word-overlap check: if a Sam comment shares ≥5 words with any
    of our comments it's considered a duplicate and stripped from the docx.
    """
    with zipfile.ZipFile(docx_path, "r") as z:
        if "word/comments.xml" not in z.namelist():
            return
        comments_xml = z.read("word/comments.xml")
        doc_xml = z.read("word/document.xml")

    comments_root = etree.fromstring(comments_xml)
    our_texts: list[str] = []
    sam_ids_to_remove: set[int] = set()

    for el in comments_root.findall(f"{WQ}comment"):
        cid = int(el.get(f"{WQ}id", 0))
        texts = [t.text or "" for t in el.iter(f"{WQ}t") if t.text]
        msg = _normalise(" ".join(texts))
        if cid <= our_max_id:
            our_texts.append(msg)

    for el in comments_root.findall(f"{WQ}comment"):
        cid = int(el.get(f"{WQ}id", 0))
        if cid <= our_max_id:
            continue
        texts = [t.text or "" for t in el.iter(f"{WQ}t") if t.text]
        sam_msg = _normalise(" ".join(texts))
        sam_words = set(w for w in sam_msg.split() if len(w) > 3)
        for our_msg in our_texts:
            our_words = set(w for w in our_msg.split() if len(w) > 3)
            overlap = sam_words & our_words
            if len(overlap) >= 3:
                sam_ids_to_remove.add(cid)
                break

    if not sam_ids_to_remove:
        return

    # Remove comment elements from comments.xml
    for el in list(comments_root.findall(f"{WQ}comment")):
        if int(el.get(f"{WQ}id", 0)) in sam_ids_to_remove:
            comments_root.remove(el)

    # Remove comment markers from document.xml
    doc_root = etree.fromstring(doc_xml)
    tags_to_strip = {f"{WQ}commentRangeStart", f"{WQ}commentRangeEnd"}
    to_remove = []
    for node in doc_root.iter():
        if node.tag in tags_to_strip:
            if int(node.get(f"{WQ}id", 0)) in sam_ids_to_remove:
                to_remove.append(node)
        elif node.tag == f"{WQ}r":
            ref = node.find(f"{WQ}commentReference")
            if ref is not None and int(ref.get(f"{WQ}id", 0)) in sam_ids_to_remove:
                to_remove.append(node)
    for node in to_remove:
        parent = node.getparent()
        if parent is not None:
            parent.remove(node)

    new_comments_xml = etree.tostring(comments_root, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_doc_xml = etree.tostring(doc_root, xml_declaration=True, encoding="UTF-8", standalone=True)

    tmp = docx_path + ".dedup.tmp"
    try:
        with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/comments.xml":
                    zout.writestr(item, new_comments_xml)
                elif item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
        os.replace(tmp, docx_path)
    except Exception:
        _safe_unlink(tmp)
        raise


_URL_RE = re.compile(r'https?://\S+')
_REF_STYLES = {
    "APA7ReferenceListEntry",
    "APA 7 Reference List Entry",
    "APA7 Reference List Entry",
    "APAReferenceListEntry",
    "Reference List Entry",
    "References",
}
_PKG_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_R_NS   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_HL_TYPE = f"{_R_NS}/hyperlink"


_YEAR_RE = re.compile(r'\(\d{4}[a-z]?\)')
_APPENDIX_HEADING_RE = re.compile(r'^\s*appendi(?:x|ces)\b', re.IGNORECASE)


def _has_reference_issue_summary_comment(docx_path: str) -> bool:
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            if "word/comments.xml" not in z.namelist():
                return False
            comments_xml = z.read("word/comments.xml")
    except (zipfile.BadZipFile, OSError):
        return False

    comments_root = etree.fromstring(comments_xml)
    for comment in comments_root.findall(f"{WQ}comment"):
        text = "".join(t.text or "" for t in comment.iter(f"{WQ}t"))
        if REFERENCE_ISSUE_SUMMARY_PREFIX in text:
            return True
    return False


def _insert_suspicious_ref_comments(docx_path: str, ref_results: list[dict]) -> None:
    """Add Word comments for reference issues:
    - CONS001/CONS002 citation-consistency warnings → anchored to the References heading
    - CREF/HREF/DOIT fail results → anchored to the individual reference entry paragraph
    """
    # Collect CONS messages to attach to the References heading
    cons_messages: list[str] = [
        r["message"] for r in ref_results
        if r.get("rule_id", "").startswith("CONS") and r.get("status") == "warn"
    ]

    # Collect entry numbers and messages for CREF fail/warn results.
    # fail  → DOI not found or reference unverifiable
    # warn  → DOI resolves to a different paper (mismatch)
    cref_issues: dict[int, str] = {}
    cref_pass_count = 0
    cref_total = 0
    for r in ref_results:
        rule_id = r.get("rule_id", "")
        if not rule_id.startswith("CREF"):
            continue
        num_str = rule_id[4:].split("_")[0]
        if not num_str.isdigit():
            continue
        entry_num = int(num_str)
        cref_total += 1
        status = r.get("status", "")
        if status == "pass":
            cref_pass_count += 1
        elif status in ("fail", "warn"):
            cref_issues[entry_num] = r.get("message", "")

    # Build a CrossRef summary for the References heading.
    summary_parts: list[str] = []
    if cref_total:
        summary_parts.append(
            f"CrossRef verification: {cref_pass_count}/{cref_total} references verified."
        )
        if cref_issues:
            nums = ", ".join(f"Entry {n}" for n in sorted(cref_issues))
            summary_parts.append(f"Issues found: {nums}.")
    crossref_summary = " ".join(summary_parts)

    if not cons_messages and not cref_issues and not crossref_summary:
        return

    # Walk body paragraphs to find:
    #   refs_heading_idx  — the References heading para index (for CONS comments)
    #   entry_para_map    — entry_num -> para_idx (for CREF/HREF/DOIT comments)
    with zipfile.ZipFile(docx_path, "r") as z:
        doc_xml = z.read("word/document.xml")
    doc_root   = etree.fromstring(doc_xml)
    body       = doc_root.find(f"{WQ}body")
    if body is None:
        return
    body_paras = [el for el in body if el.tag == f"{WQ}p"]

    refs_heading_idx: int | None = None
    entry_para_map: dict[int, int] = {}
    entry_num = 0
    in_refs   = False

    # First pass: collect (para_idx, style, text) for every paragraph that
    # lives INSIDE the References section — after the References heading and
    # before the next Heading-1. This mirrors reference_checker's
    # `_references_window`, so appendix paragraphs that follow References are
    # never counted as reference entries (JUTLP allows nothing after
    # References; some papers include appendices anyway).
    window: list[tuple[int, str, str]] = []
    for para_idx, para in enumerate(body_paras):
        pPr   = para.find(f"{WQ}pPr")
        style = ""
        if pPr is not None:
            ps = pPr.find(f"{WQ}pStyle")
            if ps is not None:
                style = ps.get(f"{WQ}val", "")
        text = "".join(t.text or "" for t in para.iter(f"{WQ}t")).strip()

        if style in ("Heading1", "Heading 1") and text.lower() in ("references", "reference list"):
            refs_heading_idx = para_idx
            in_refs = True
            continue
        # Close at the next Heading-1 OR an appendix heading (by text, style-
        # independent) so appendix entry numbering matches reference_checker.
        if in_refs and (style in ("Heading1", "Heading 1") or _APPENDIX_HEADING_RE.match(text)):
            break
        if in_refs and text:
            window.append((para_idx, style, text))

    # Two-tier selection identical to reference_checker._select_reference_entries:
    # prefer style-marked entries; fall back to the year+length heuristic only
    # when no styled entry exists in the window. Keeps "Entry N" numbering in
    # sync with what CrossRef actually verified.
    styled_window = [(i, t) for (i, s, t) in window if s in _REF_STYLES]
    if styled_window:
        entries = styled_window
    else:
        entries = [
            (i, t) for (i, s, t) in window
            if len(t) > 20 and bool(_YEAR_RE.search(t))
        ]
    for entry_num, (para_idx, _text) in enumerate(entries, start=1):
        if entry_num in cref_issues:
            entry_para_map[entry_num] = para_idx

    if refs_heading_idx is not None and not _has_reference_issue_summary_comment(docx_path):
        summary_message = _reference_issue_summary_comment(ref_results)
        if summary_message is not None:
            add_paragraph_comment(docx_path, refs_heading_idx, summary_message)

    # CONS comments → References heading
    if cons_messages and refs_heading_idx is not None:
        for msg in cons_messages:
            add_paragraph_comment(docx_path, refs_heading_idx, msg)

    # CREF fail/warn comments → individual entry paragraphs
    for num in sorted(cref_issues):
        para_idx = entry_para_map.get(num)
        if para_idx is None:
            continue
        issue_msg = cref_issues[num]
        if not issue_msg:
            issue_msg = (
                "AUTHOR QUERY — This reference could not be automatically "
                "verified in CrossRef. Please confirm it is accurate."
            )
        add_paragraph_comment(docx_path, para_idx, issue_msg)


def _inject_crossref_doi_links(docx_path: str, ref_results: list[dict]) -> None:
    """Append CrossRef-verified DOI hyperlinks as tracked insertions to reference
    paragraphs that have no URL.

    The DOI is wrapped in w:hyperlink → w:ins → w:r so the editor sees it as a
    proposed addition they can accept or reject.  The link is styled black so it
    does not print in hyperlink blue.
    """
    XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

    # Build entry_number → doi_url map from verified CREF results
    doi_map: dict[int, str] = {}
    for r in ref_results:
        doi_url = r.get("doi_url", "")
        if r.get("status") == "pass" and doi_url:
            m = re.match(r"CREF(\d+)", r.get("rule_id", ""))
            if m:
                doi_map[int(m.group(1))] = doi_url

    if not doi_map:
        return

    with zipfile.ZipFile(docx_path, "r") as z:
        doc_xml  = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")

    doc_root  = etree.fromstring(doc_xml)
    rels_root = etree.fromstring(rels_xml)

    # Start change IDs above the highest existing one to avoid collisions.
    next_change_id = max(
        (int(el.get(f"{WQ}id", 0))
         for tag in (f"{WQ}ins", f"{WQ}del")
         for el in doc_root.iter(tag)
         if el.get(f"{WQ}id", "").lstrip("-").isdigit()),
        default=0,
    ) + 1

    next_rid = max(
        (int(r.get("Id", "rId0")[3:]) for r in rels_root
         if r.get("Id", "").startswith("rId") and r.get("Id", "rId0")[3:].isdigit()),
        default=0,
    ) + 1
    url_to_rid: dict[str, str] = {}

    def _get_or_add_rel(url: str) -> str:
        nonlocal next_rid
        if url in url_to_rid:
            return url_to_rid[url]
        rid = f"rId{next_rid}"
        next_rid += 1
        url_to_rid[url] = rid
        rel = etree.SubElement(rels_root, f"{{{_PKG_NS}}}Relationship")
        rel.set("Id", rid)
        rel.set("Type", _HL_TYPE)
        rel.set("Target", url)
        rel.set("TargetMode", "External")
        return rid

    # Collect reference paragraphs in document order
    ref_paras = []
    for para in doc_root.iter(f"{WQ}p"):
        pPr = para.find(f"{WQ}pPr")
        if pPr is None:
            continue
        pStyle = pPr.find(f"{WQ}pStyle")
        if pStyle is not None and pStyle.get(f"{WQ}val") in _REF_STYLES:
            ref_paras.append(para)

    for idx, para in enumerate(ref_paras, start=1):
        doi_url = doi_map.get(idx)
        if not doi_url:
            continue

        # Skip if paragraph already has a URL anywhere (including in del/ins text)
        para_text = "".join(t.text or "" for t in para.iter(f"{WQ}t"))
        if _URL_RE.search(para_text):
            continue
        # Also skip if already has a hyperlink element
        if para.find(f"{WQ}hyperlink") is not None:
            continue

        rid = _get_or_add_rel(doi_url)

        # w:hyperlink → w:ins → w:r  (tracked insertion, black colour)
        hl = etree.SubElement(para, f"{WQ}hyperlink")
        hl.set(f"{{{_R_NS}}}id", rid)
        hl.set(f"{WQ}history", "1")

        ins = etree.SubElement(hl, f"{WQ}ins")
        ins.set(f"{WQ}id",     str(next_change_id))
        ins.set(f"{WQ}author", AUTHOR)
        ins.set(f"{WQ}date",   DATE)
        next_change_id += 1

        hl_run = etree.SubElement(ins, f"{WQ}r")
        hl_rPr = etree.SubElement(hl_run, f"{WQ}rPr")
        rs = etree.SubElement(hl_rPr, f"{WQ}rStyle")
        rs.set(f"{WQ}val", "Hyperlink")
        hl_color = etree.SubElement(hl_rPr, f"{WQ}color")
        hl_color.set(f"{WQ}val", "000000")
        hl_t = etree.SubElement(hl_run, f"{WQ}t")
        hl_t.text = " " + doi_url
        hl_t.set(XML_SPACE, "preserve")

    new_doc_xml  = etree.tostring(doc_root,  xml_declaration=True, encoding="UTF-8", standalone=True)
    new_rels_xml = etree.tostring(rels_root, xml_declaration=True, encoding="UTF-8", standalone=True)

    tmp = docx_path + ".doi2.tmp"
    try:
        with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item.filename == "word/_rels/document.xml.rels":
                    zout.writestr(item, new_rels_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
        os.replace(tmp, docx_path)
    except Exception:
        _safe_unlink(tmp)
        raise


def _hyperlink_plain_urls_in_refs(docx_path: str) -> None:
    """Convert plain-text http(s) URLs in reference-list paragraphs to Word hyperlinks."""
    from copy import deepcopy
    XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

    with zipfile.ZipFile(docx_path, "r") as z:
        doc_xml  = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")

    doc_root  = etree.fromstring(doc_xml)
    rels_root = etree.fromstring(rels_xml)

    # Find next free rId number
    next_rid = max(
        (int(r.get("Id", "rId0")[3:]) for r in rels_root
         if r.get("Id", "").startswith("rId") and r.get("Id", "rId0")[3:].isdigit()),
        default=0
    ) + 1
    url_to_rid: dict[str, str] = {}

    def _get_or_add_rel(url: str) -> str:
        nonlocal next_rid
        if url in url_to_rid:
            return url_to_rid[url]
        rid = f"rId{next_rid}"
        next_rid += 1
        url_to_rid[url] = rid
        rel = etree.SubElement(rels_root, f"{{{_PKG_NS}}}Relationship")
        rel.set("Id", rid)
        rel.set("Type", _HL_TYPE)
        rel.set("Target", url)
        rel.set("TargetMode", "External")
        return rid

    for para in doc_root.iter(f"{WQ}p"):
        pPr = para.find(f"{WQ}pPr")
        if pPr is None:
            continue
        pStyle = pPr.find(f"{WQ}pStyle")
        if pStyle is None or pStyle.get(f"{WQ}val") not in _REF_STYLES:
            continue

        changed = True
        while changed:
            changed = False
            for run in list(para):
                if run.tag != f"{WQ}r":
                    continue
                if run.getparent() is not None and run.getparent().tag == f"{WQ}hyperlink":
                    continue
                t_el = run.find(f"{WQ}t")
                if t_el is None:
                    continue
                text = t_el.text or ""
                m = _URL_RE.search(text)
                if not m:
                    continue

                url = m.group(0).rstrip(".,;:)>\"'")
                rid = _get_or_add_rel(url)
                rPr = run.find(f"{WQ}rPr")
                idx = list(para).index(run)
                para.remove(run)

                ins = idx
                before, url_text, after = text[:m.start()], text[m.start():m.start()+len(url)], text[m.start()+len(url):]

                def _plain_run(txt):
                    r = etree.Element(f"{WQ}r")
                    if rPr is not None:
                        r.append(deepcopy(rPr))
                    t = etree.SubElement(r, f"{WQ}t")
                    t.text = txt
                    t.set(XML_SPACE, "preserve")
                    return r

                if before:
                    para.insert(ins, _plain_run(before))
                    ins += 1

                hl = etree.Element(f"{WQ}hyperlink")
                hl.set(f"{{{_R_NS}}}id", rid)
                hl.set(f"{WQ}history", "1")
                hl_run = etree.SubElement(hl, f"{WQ}r")
                hl_rPr = etree.SubElement(hl_run, f"{WQ}rPr")
                rs = etree.SubElement(hl_rPr, f"{WQ}rStyle")
                rs.set(f"{WQ}val", "Hyperlink")
                hl_t = etree.SubElement(hl_run, f"{WQ}t")
                hl_t.text = url_text
                hl_t.set(XML_SPACE, "preserve")
                para.insert(ins, hl)
                ins += 1

                if after:
                    para.insert(ins, _plain_run(after))

                changed = True
                break

    new_doc_xml  = etree.tostring(doc_root,  xml_declaration=True, encoding="UTF-8", standalone=True)
    new_rels_xml = etree.tostring(rels_root, xml_declaration=True, encoding="UTF-8", standalone=True)

    tmp = docx_path + ".doi.tmp"
    try:
        with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item.filename == "word/_rels/document.xml.rels":
                    zout.writestr(item, new_rels_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
        os.replace(tmp, docx_path)
    except Exception:
        _safe_unlink(tmp)
        raise


def _patch_settings_show_markup(docx_path: str) -> None:
    """Patch word/settings.xml so the document opens in All Markup (balloon) view.

    Inserts <w:showDel/>, <w:showInsMarkup/>, and <w:revisionView> before
    <w:rsids> — the correct schema position — so Word doesn't ignore them.
    """
    W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    WQ_S = f"{{{W_NS}}}"

    with zipfile.ZipFile(docx_path, "r") as z:
        if "word/settings.xml" not in z.namelist():
            return
        settings_xml = z.read("word/settings.xml")

    root = etree.fromstring(settings_xml)

    # Remove any pre-existing copies of the elements we're about to add
    for tag in ("revisionView", "showDel", "showInsMarkup", "trackChanges"):
        for el in root.findall(f"{WQ_S}{tag}"):
            root.remove(el)

    # Insert before <w:rsids> (schema-correct position); fall back to end
    children = list(root)
    rsids = root.find(f"{WQ_S}rsids")
    pos = children.index(rsids) if rsids is not None else len(children)

    # <w:showDel/>  — standalone element: show deleted text
    root.insert(pos, etree.Element(f"{WQ_S}showDel"))
    pos += 1

    # <w:showInsMarkup/> — standalone element: show inserted text as markup
    root.insert(pos, etree.Element(f"{WQ_S}showInsMarkup"))
    pos += 1

    # <w:revisionView> — All Markup mode with balloons for deletions
    rev = etree.Element(f"{WQ_S}revisionView")
    rev.set(f"{WQ_S}markup",         "1")
    rev.set(f"{WQ_S}comments",        "1")
    rev.set(f"{WQ_S}displayXMLNames", "0")
    rev.set(f"{WQ_S}showDel",         "1")
    rev.set(f"{WQ_S}showInsMarkup",   "1")
    rev.set(f"{WQ_S}formatting",      "1")
    rev.set(f"{WQ_S}inkAnnotations",  "1")
    root.insert(pos, rev)

    new_settings_xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    tmp = docx_path + ".settings.tmp"
    try:
        with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/settings.xml":
                    zout.writestr(item, new_settings_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
        os.replace(tmp, docx_path)
    except Exception:
        _safe_unlink(tmp)
        raise


def doc_analysis_pipeline(
    path_to_doc: str | Path,
    output_path: str | Path | None = None,
    progress_callback: Callable[[int, str], None] | None = None,
) -> dict:
    last_progress = 0

    def _progress(pct: int, stage: str) -> None:
        nonlocal last_progress
        pct = max(last_progress, min(99, int(pct)))
        last_progress = pct
        if progress_callback:
            progress_callback(pct, stage)

    original_docx_path = str(path_to_doc)
    input_path = Path(original_docx_path)
    resolved_output_path = (
        str(output_path)
        if output_path is not None
        else str(input_path.with_name(f"reviewed_{input_path.name}"))
    )

    # Accumulator for stages that failed silently. Each entry is
    # {"stage": "<label>", "error": "<exception str>"}. The pipeline returns
    # this list so the caller (and the UI) can show a warning when a stage
    # didn't run to completion — previously these were log.warning-only and
    # invisible to the editor.
    stage_errors: list[dict] = []

    def _record_stage_error(stage_label: str, exc: Exception) -> None:
        log.warning("%s failed: %s", stage_label, exc)
        stage_errors.append({"stage": stage_label, "error": str(exc)})

    # ── Phase 0: Normalise author formatting noise on a working copy ─────────
    # Strips author-supplied tracked changes, run-level colour and highlighting,
    # and deletes any leftover "Guidance Notes" template paragraphs. All
    # downstream stages read from the normalised copy so the LLM and validators
    # see a clean baseline.
    working_fd, working_path = tempfile.mkstemp(suffix=".docx", prefix="normalised_")
    os.close(working_fd)
    try:
        try:
            _progress(8, "structure")
            normalisation_report = normalise_docx(original_docx_path, working_path)
            docx_path = working_path
        except Exception as exc:
            _record_stage_error("Document normalisation", exc)
            normalisation_report = None
            docx_path = original_docx_path

        # ── Phase 1: Run all independent analysis tasks in parallel ─────────────────
        _progress(15, "structure")
        with ThreadPoolExecutor(max_workers=2) as executor:
            f_validate  = executor.submit(validate, docx_path)
            f_ref       = executor.submit(check_and_report, docx_path)

            deterministic_check_results = f_validate.result()
            _progress(30, "refs")
            ref_check_result            = f_ref.result()
            _progress(42, "refs")

        # ── Phase 2: LLM editorial review (needs validate + ref results) ─────────
        _progress(48, "llm")
        llm_result = run_editorial_review(
            docx_path,
            deterministic_check_result=deterministic_check_results,
            ref_check_result=ref_check_result,
        )
        _progress(68, "building")

        # ── Phase 3: Sequential document assembly ────────────────────────────────
        # Sam handles all front-page items (FP*) via tracked changes — skip them here
        # so the same issue doesn't appear as both a comment and a tracked change.
        _SAM_COVERED = {"FP"}
        filtered_report = {
            **deterministic_check_results,
            "results": [
                r for r in deterministic_check_results["results"]
                if not any(r["rule_id"].startswith(p) for p in _SAM_COVERED)
            ],
        }

        generate_commented_docx(
            input_path=docx_path,
            output_path=resolved_output_path,
            report=filtered_report,
            ref_results=ref_check_result["results"],
            llm_results=llm_result,
        )
        _progress(78, "building")

        # If normalisation actually changed anything, leave a single summary
        # comment on the output so reviewers can see what was stripped.
        if normalisation_report is not None and normalisation_report.changed:
            try:
                add_document_summary_comment(
                    resolved_output_path, normalisation_report.summary_text()
                )
            except Exception as exc:
                _record_stage_error("Normalisation summary comment", exc)

            # Also write a per-strip audit sidecar so reviewers can search
            # "what was highlighted in §3 paragraph 4?" without diffing the
            # binary. Best-effort: never block the pipeline if disk I/O fails.
            try:
                normalisation_report.write_sidecar(resolved_output_path)
            except Exception as exc:
                _record_stage_error("Normalisation sidecar write", exc)
    finally:
        try:
            os.unlink(working_path)
        except OSError:
            pass

    sam_result = None
    try:
        _progress(82, "finalizing")
        with zipfile.ZipFile(resolved_output_path, "r") as z:
            if "word/comments.xml" in z.namelist():
                xml = z.read("word/comments.xml")
                root = etree.fromstring(xml)
                ids = [int(el.get(f"{WQ}id", 0)) for el in root.findall(f"{WQ}comment")]
                our_max_id = max(ids, default=0)
            else:
                our_max_id = 0
        sam_result = build_edited_document(resolved_output_path, resolved_output_path)
        _remove_duplicate_sam_comments(resolved_output_path, our_max_id)
        _progress(88, "finalizing")
    except Exception as exc:
        _record_stage_error("Tracked-changes pass", exc)

    # Seed the tracked-change id counter above any w:id Sam (or
    # generate_commented_docx) already wrote — see _max_revision_id docstring
    # for the collision rationale. Shared by every tracked-change pass below.
    next_lang_id = _max_revision_id(resolved_output_path) + 1

    # Correct section headings as tracked changes: strip leading numbers
    # ("2. Literature Review" -> "Literature Review") and rename non-canonical
    # section names to the JUTLP label ("Findings" -> "Results", "Literature
    # Review" -> "Literature"). Runs early so later text passes see clean
    # heading text.
    heading_corrections: list[dict] = []
    try:
        next_lang_id, heading_corrections = apply_heading_corrections(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(89, "finalizing")
    except Exception as exc:
        _record_stage_error("Heading corrections", exc)

    # AU English spelling corrections as tracked changes.
    spelling_corrections: list[dict] = []
    try:
        next_lang_id, spelling_corrections = apply_au_spelling_corrections(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(90, "finalizing")
    except Exception as exc:
        _record_stage_error("AU spelling corrections", exc)

    # Spell out whole numbers 0-9 in running prose as tracked changes.
    number_word_corrections: list[dict] = []
    try:
        next_lang_id, number_word_corrections = apply_number_word_corrections(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(92, "finalizing")
    except Exception as exc:
        _record_stage_error("Number-to-word corrections", exc)

    # Abbreviation / journal-style fixes: ``e.g.`` and ``i.e.`` missing the
    # trailing comma (including after brackets, dashes, and other
    # non-letter left-context the prior LLM-only treatment missed), and
    # ``Fig. N`` → ``Figure N`` per JUTLP house style.
    abbreviation_actions: list[dict] = []
    try:
        next_lang_id, abbreviation_actions = apply_abbreviation_corrections(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(92, "finalizing")
    except Exception as exc:
        _record_stage_error("Abbreviation corrections", exc)

    # General spell-check (pyspellchecker). High-confidence single-candidate
    # typos like ``studentss → students`` become tracked changes; ambiguous
    # suspects become comments. AU/US variants are handled separately by
    # apply_au_spelling_corrections, so this pass only catches genuine
    # misspellings.
    spell_check_corrections: list[dict] = []
    try:
        next_lang_id, spell_check_corrections = apply_spell_corrections(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(93, "finalizing")
    except Exception as exc:
        _record_stage_error("Spell-check corrections", exc)

    # Acronym checks: emit a single consolidated comment listing every
    # acronym whose first use in its zone (abstract or body) isn't a proper
    # "full term (ACRO)" introduction. The first body occurrence of each
    # such acronym also gets a tracked-change rewrite when the expansion is
    # known. See app.services.acronym_corrections for the full rules.
    acronym_actions: list[dict] = []
    try:
        next_lang_id, acronym_actions = apply_acronym_corrections(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(94, "finalizing")
    except Exception as exc:
        _record_stage_error("Acronym corrections", exc)

    # Decimal-precision (>2 decimal places, fired once) and comma-as-decimal
    # checks. Both emit comments only — no tracked changes.
    decimal_actions: list[dict] = []
    try:
        next_lang_id, decimal_actions = apply_decimal_corrections(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(96, "finalizing")
    except Exception as exc:
        _record_stage_error("Decimal corrections", exc)

    # Sentence-coherence pass: flag sentences that fail to parse as
    # Word comments. Complements grammar_corrections (which catches
    # specific structural error types) by handling the open-ended
    # "this sentence doesn't make sense" category Joey asked for.
    coherence_actions: list[dict] = []
    try:
        next_lang_id, coherence_actions = apply_sentence_coherence_corrections(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(96, "finalizing")
    except Exception as exc:
        _record_stage_error("Sentence-coherence corrections", exc)

    # Late grammar comments catch agreement issues that can be exposed only
    # after earlier tracked-change passes have partially rewritten nearby
    # text (for example, "their work are"). Comment-only so the editor can
    # judge the surrounding sentence before changing the verb.
    contingent_grammar_actions: list[dict] = []
    try:
        next_lang_id, contingent_grammar_actions = apply_contingent_grammar_comments(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(96, "finalizing")
    except Exception as exc:
        _record_stage_error("Contingent grammar comments", exc)

    # Flag single-paragraph Figure/Table captions that should be split
    # into the three APA 7 paragraphs (label / italic title / Note).
    # Comment-only — mis-splitting a caption is more harmful than
    # leaving it joined, so the editor handles the restructure.
    caption_apa7_actions: list[dict] = []
    try:
        next_lang_id, caption_apa7_actions = apply_caption_apa7_comments(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(96, "finalizing")
    except Exception as exc:
        _record_stage_error("Caption APA7 check", exc)

    # Flag table column headers that are a bare capital "N" — a capital N
    # means the whole population/sample while a lowercase italic n means a
    # subsample, so the author should confirm which they intend. Comment-only.
    table_n_actions: list[dict] = []
    try:
        next_lang_id, table_n_actions = apply_table_n_notation_comments(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(96, "finalizing")
    except Exception as exc:
        _record_stage_error("Table N notation check", exc)

    # Flag sections that open or close directly with a table (no prose lead-in
    # or interpretation). Caption / Note paragraphs are treated as part of the
    # table block when deciding adjacency. Comment-only.
    table_section_boundary_actions: list[dict] = []
    try:
        next_lang_id, table_section_boundary_actions = apply_table_section_boundary_comments(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(96, "finalizing")
    except Exception as exc:
        _record_stage_error("Table section boundary check", exc)

    # Stop tables (and their header rows) from splitting awkwardly across a
    # page boundary: cantSplit on rows, tblHeader on the first row so a long
    # table repeats its header, and keepNext on the caption so it floats to a
    # fresh page with the table. Lets Word's layout engine keep the table
    # intact instead of guessing page positions. Runs before the page-break
    # fallback below.
    table_keep_together_actions: list[dict] = []
    try:
        table_keep_together_actions = apply_table_keep_together(
            resolved_output_path, resolved_output_path
        )
        _progress(96, "finalizing")
    except Exception as exc:
        _record_stage_error("Table keep-together", exc)

    # If a table is structurally too tall to fit comfortably on one page,
    # start it on a fresh page. DOCX does not expose exact rendered pagination
    # server-side, so the table pass uses a conservative row/text estimate.
    table_page_break_actions: list[dict] = []
    try:
        table_page_break_actions = apply_table_page_breaks(
            resolved_output_path, resolved_output_path
        )
        _progress(96, "finalizing")
    except Exception as exc:
        _record_stage_error("Table page breaks", exc)

    # Comment on any content after the reference list — JUTLP does not accept
    # appendices. A single comment at the first appendix paragraph advises the
    # author to integrate the material into the body and remove it. Comment-
    # only: the content is left in place for the author to relocate.
    appendix_actions: list[dict] = []
    try:
        next_lang_id, appendix_actions = apply_appendix_removal(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(97, "finalizing")
    except Exception as exc:
        _record_stage_error("Appendix comment", exc)

    # Flag blinded / placeholder citations and self-references left over from
    # peer review (e.g. "[Author] et al., under review", "[University]"). JUTLP
    # publishes identified manuscripts, so these must be de-anonymised. Comment-
    # only: only the author knows the real citation/affiliation.
    blinded_citation_actions: list[dict] = []
    try:
        next_lang_id, blinded_citation_actions = apply_blinded_citation_comments(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(97, "finalizing")
    except Exception as exc:
        _record_stage_error("Blinded citation check", exc)

    # ── Reference cluster ────────────────────────────────────────────────────
    # Ordered so the indent + font passes operate on the FINAL reference text.
    # The APA-7 format pass rewrites whole entries (tracked del/ins) and DOI
    # injection adds hyperlink runs; both must run BEFORE the indent/font passes
    # so those passes style the reconstructed text rather than runs that the
    # rewrite would discard (which previously left reconstructed entries at the
    # wrong font/size).

    # 1) APA 7 reference format corrections as tracked changes. Runs before DOI
    # injection so the reconstructed text (with the DOI URL already in a w:ins)
    # is present and DOI injection skips those entries.
    ref_format_corrections: list[dict] = []
    try:
        next_lang_id, ref_format_corrections = apply_reference_format_corrections(
            resolved_output_path,
            resolved_output_path,
            next_lang_id,
            ref_check_result["results"],
        )
        _progress(97, "finalizing")
    except Exception as exc:
        _record_stage_error("Reference format corrections", exc)

    # 2) Inject CrossRef-verified DOI hyperlinks for references that have no URL.
    try:
        _inject_crossref_doi_links(resolved_output_path, ref_check_result["results"])
        _progress(97, "finalizing")
    except Exception as exc:
        _record_stage_error("CrossRef DOI injection", exc)

    # The rewrite + DOI injection added tracked changes with their own w:ids
    # (DOI injection self-seeds), so re-seed the shared counter above them
    # before the next tracked-change passes to avoid id collisions.
    next_lang_id = _max_revision_id(resolved_output_path) + 1

    # 3) APA hanging indent on every reference entry (tracked pPr change).
    reference_indent_actions: list[dict] = []
    try:
        next_lang_id, reference_indent_actions = apply_reference_indent_corrections(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(98, "finalizing")
    except Exception as exc:
        _record_stage_error("Reference indent corrections", exc)

    # 4) Normalise run-level fonts to Arial 11pt — now applied to the
    # reconstructed reference text and injected DOI link runs (both inside a
    # w:ins, so styled directly), plus any leftover direct non-Arial run.
    run_font_actions: list[dict] = []
    try:
        next_lang_id, run_font_actions = apply_run_font_corrections(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(98, "finalizing")
    except Exception as exc:
        _record_stage_error("Run font corrections", exc)

    # 5) Flag a reference list that is not in alphabetical order by first-author
    # surname (APA 7 / JUTLP). Comment-only — reordering is an editorial
    # judgement, so the bot flags it on the References heading.
    reference_order_actions: list[dict] = []
    try:
        next_lang_id, reference_order_actions = apply_reference_order_comments(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(98, "finalizing")
    except Exception as exc:
        _record_stage_error("Reference order check", exc)

    # Flag paragraphs that contain fewer than three sentences and attach
    # comment-only author queries at each paragraph.
    short_paragraph_actions: list[dict] = []
    try:
        next_lang_id, short_paragraph_actions = apply_short_paragraph_comments(
            resolved_output_path, resolved_output_path, next_lang_id
        )
        _progress(98, "finalizing")
    except Exception as exc:
        _record_stage_error("Short paragraph comments", exc)

    # Add Word comments on reference entries that could not be verified.
    try:
        _insert_suspicious_ref_comments(resolved_output_path, ref_check_result["results"])
    except Exception as exc:
        _record_stage_error("Suspicious reference comments", exc)

    # Convert any remaining plain-text http(s) URLs to clickable hyperlinks.
    try:
        _hyperlink_plain_urls_in_refs(resolved_output_path)
        _progress(99, "finalizing")
    except Exception as exc:
        _record_stage_error("URL hyperlinking", exc)

    # Ensure the document opens with All Markup (balloon) view by default.
    try:
        _patch_settings_show_markup(resolved_output_path)
        _progress(99, "finalizing")
    except Exception as exc:
        _record_stage_error("Markup view settings", exc)

    # Late deterministic passes append comments after Sam's builder has already
    # renumbered its own comments. Do one final pass so visible Author Query
    # labels follow the document anchors instead of raw creation order.
    try:
        _renumber_final_author_queries(resolved_output_path)
        _progress(99, "finalizing")
    except Exception as exc:
        _record_stage_error("Final author-query renumbering", exc)

    return {
        "message": "Document feedback generated.",
        "output_path": resolved_output_path,
        "deterministic_check_results": deterministic_check_results,
        "ref_check_result": ref_check_result,
        "llm_result": llm_result,
        "sam_result": sam_result,
        "spelling_corrections": spelling_corrections,
        "number_word_corrections": number_word_corrections,
        "abbreviation_actions": abbreviation_actions,
        "acronym_actions": acronym_actions,
        "decimal_actions": decimal_actions,
        "coherence_actions": coherence_actions,
        "contingent_grammar_actions": contingent_grammar_actions,
        "caption_apa7_actions": caption_apa7_actions,
        "table_n_actions": table_n_actions,
        "table_section_boundary_actions": table_section_boundary_actions,
        "table_keep_together_actions": table_keep_together_actions,
        "table_page_break_actions": table_page_break_actions,
        "appendix_actions": appendix_actions,
        "reference_indent_actions": reference_indent_actions,
        "run_font_actions": run_font_actions,
        "reference_order_actions": reference_order_actions,
        "short_paragraph_actions": short_paragraph_actions,
        "spell_check_corrections": spell_check_corrections,
        "ref_format_corrections": ref_format_corrections,
        "stage_errors": stage_errors,
    }




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full document analysis pipeline.")
    parser.add_argument(
        "docx_path",
        nargs="?",
        default="tests/jutlp_sample_docx_test_pack/02_missing_method_subsection.docx",
        help="Path to the input .docx file",
    )
    args = parser.parse_args()

    result = doc_analysis_pipeline(Path(args.docx_path))
    pprint(result)
