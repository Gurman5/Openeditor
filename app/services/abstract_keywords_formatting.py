"""APA-08 / APA-09 abstract and keywords formatting (C-26).

Abstract: heading bold + centred, body a single unindented paragraph.
Keywords: italic ``Keywords:`` label, keywords paragraph indented 0.5in.

Style-first, direct-formatting fallback. The APA base template now defines
``Heading Front Page`` / ``Front Page Text`` / ``Keywords`` / ``Keywords
Label``, so the retag normally supplies all of APA-08/09 through the style and
nothing is written directly. The fallback exists because those style names
are absent from plenty of real manuscripts: without it the pass would silently
do nothing, which is exactly the defect that made the original Abstract
heading render as plain left-aligned Normal text.

Heading formatting is recorded as a tracked ``w:pPrChange`` (a visible
editorial decision); the italic label is written on the label run directly.
"""

from __future__ import annotations

import os
import shutil
import zipfile

from lxml import etree

from app.services.docx_format_helpers import (
    find_canonical_heading,
    get_or_add_ppr,
    heading_names,
    normalise_heading_text,
    paragraph_text,
    para_style_id,
    set_para_style,
    set_tracked_ppr,
)
from app.services.language_corrections import WQ

_HEADING_STYLE_NAMES = ("Heading Front Page", "Front Page Text", "Keywords")
_LABEL_STYLE_NAME = "Keywords Label"

_KEYWORDS_INLINE_RE = r"^\s*keywords?\s*[:\-–]\s*"
_KEYWORDS_TERMINATORS = frozenset({
    "introduction", "method", "results", "discussion", "citation", "abstract",
})


def _styles_index(styles_xml: bytes | None) -> dict[str, str]:
    """Return ``styleId -> lowercased style name``."""
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


def _style_id_for(styles_index: dict[str, str], wanted: str) -> str | None:
    """Return the styleId whose declared name is ``wanted`` (case-insensitive)."""
    target = wanted.strip().lower()
    for sid, name in styles_index.items():
        if name == target:
            return sid
    return None


def _available_style_ids(styles_index: dict[str, str]) -> dict[str, str]:
    return {
        name: sid
        for name in (
            "Heading Front Page", "Front Page Text", "Keywords", "Keywords Label",
        )
        if (sid := _style_id_for(styles_index, name)) is not None
    }


def _runs(para_el: etree._Element):
    """Direct-or-hyperlink text runs belonging to this paragraph."""
    for r in para_el.iter(f"{WQ}r"):
        t = r.find(f"{WQ}t")
        if t is None or not (t.text or "").strip():
            continue
        yield r


def _is_bold(r_pr) -> bool:
    if r_pr is None:
        return False
    b = r_pr.find(f"{WQ}b")
    if b is None:
        return False
    return (b.get(f"{WQ}val", "true") or "true").lower() not in ("false", "0", "off")


def _is_italic(r_pr) -> bool:
    if r_pr is None:
        return False
    i = r_pr.find(f"{WQ}i")
    if i is None:
        return False
    return (i.get(f"{WQ}val", "true") or "true").lower() not in ("false", "0", "off")


def _ensure_run_flag(run_el, tag: str) -> bool:
    """Add a run property (``w:b`` / ``w:i``) if absent. True when written."""
    r_pr = run_el.find(f"{WQ}rPr")
    if r_pr is None:
        r_pr = etree.Element(f"{WQ}rPr")
        run_el.insert(0, r_pr)
    if r_pr.find(f"{WQ}{tag}") is not None:
        return False
    el = etree.Element(f"{WQ}{tag}")
    # rFonts/rStyle/b/i… schema order: keep the flag after rStyle/rFonts.
    anchor = r_pr.find(f"{WQ}rStyle") or r_pr.find(f"{WQ}rFonts")
    if anchor is not None:
        anchor.addnext(el)
    else:
        r_pr.insert(0, el)
    return True


def _find_keywords_paragraph(body_paras: list[etree._Element]) -> etree._Element | None:
    """Return the Keywords paragraph — either a heading or the inline label."""
    for para_el in body_paras:
        text = paragraph_text(para_el)
        if normalise_heading_text(text) == "keywords":
            return para_el
    for para_el in body_paras:
        low = paragraph_text(para_el).strip().lower()
        if low.startswith("keywords:") or low.startswith("keywords -"):
            return para_el
    return None


def _keywords_text_paragraph(
    body_paras: list[etree._Element],
    heading_el: etree._Element,
) -> etree._Element | None:
    """The paragraph carrying the keyword terms (after a Keywords heading)."""
    seen = False
    for para_el in body_paras:
        if para_el is heading_el:
            seen = True
            continue
        if not seen:
            continue
        text = paragraph_text(para_el)
        if not text:
            continue
        if normalise_heading_text(text) in _KEYWORDS_TERMINATORS:
            return None
        if para_style_id(para_el).lower().startswith("heading"):
            return None
        return para_el
    return None


def apply_abstract_keywords_formatting(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Apply APA-08 (abstract) and APA-09 (keywords) formatting.

    Returns ``(next_change_id, actions)``. No-ops (and copies through) when
    neither block is present, so the pass is safe on any manuscript.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        styles_xml = z.read("word/styles.xml") if "word/styles.xml" in names else None

    styles_index = _styles_index(styles_xml)
    available = _available_style_ids(styles_index)
    doc_root = etree.fromstring(doc_xml)
    body = doc_root.find(f"{WQ}body")
    actions: list[dict] = []
    if body is None:
        return next_change_id, actions

    body_paras = [el for el in body if el.tag == f"{WQ}p"]

    # ── APA-08: Abstract heading bold + centred ───────────────────────────
    abstract_el = find_canonical_heading(body_paras, "Abstract")
    if abstract_el is not None:
        if "Heading Front Page" in available and \
                normalise_heading_text(paragraph_text(abstract_el)) == "abstract":
            if para_style_id(abstract_el) != available["Heading Front Page"]:
                set_para_style(abstract_el, available["Heading Front Page"])
                actions.append({"kind": "abstract_heading_style",
                                "description": "Abstract heading set to Heading Front Page"})

        # Fallback only when the style can't carry the formatting.
        heading_style_name = styles_index.get(para_style_id(abstract_el), "")
        if heading_style_name != "heading front page":
            bold_written = False
            for r in abstract_el.iter(f"{WQ}r"):
                t = r.find(f"{WQ}t")
                if t is None or not (t.text or "").strip():
                    continue
                r_pr = r.find(f"{WQ}rPr")
                if not _is_bold(r_pr):
                    bold_written = _ensure_run_flag(r, "b") or bold_written
            if bold_written:
                actions.append({"kind": "abstract_heading_bold",
                                "description": "Abstract heading set bold"})
            p_pr = get_or_add_ppr(abstract_el)
            jc = p_pr.find(f"{WQ}jc")
            if jc is None or jc.get(f"{WQ}val") != "center":
                next_change_id = set_tracked_ppr(
                    abstract_el, "jc", {"val": "center"}, next_change_id
                )
                actions.append({"kind": "abstract_heading_centre",
                                "description": "Abstract heading centred"})

        # ── APA-08: abstract body a single unindented paragraph ───────────
        body_paras = [el for el in body if el.tag == f"{WQ}p"]
        abstract_body = _abstract_body_paragraphs(body_paras, abstract_el)
        if abstract_body:
            first = abstract_body[0]
            if "Front Page Text" in available and \
                    para_style_id(first) != available["Front Page Text"]:
                set_para_style(first, available["Front Page Text"])
                actions.append({"kind": "abstract_body_style",
                                "description": "Abstract body set to Front Page Text"})
            p_pr = get_or_add_ppr(first)
            ind = p_pr.find(f"{WQ}ind")
            # firstLine="0" is already correct — only a *non-zero* first line
            # or a non-zero left indent needs rewriting (otherwise the pass
            # re-reports the same fix on every run and never converges).
            first_line = ind.get(f"{WQ}firstLine") if ind is not None else None
            left = (ind.get(f"{WQ}left") if ind is not None else None) or "0"
            if (first_line not in (None, "0")) or left != "0":
                next_change_id = set_tracked_ppr(
                    first, "ind", {"left": "0", "firstLine": "0"}, next_change_id
                )
                actions.append({"kind": "abstract_body_indent",
                                "description": "Abstract body indent removed"})

    # ── APA-09: Keywords label italic, paragraph indented ─────────────────
    body_paras = [el for el in body if el.tag == f"{WQ}p"]
    keywords_el = _find_keywords_paragraph(body_paras)
    if keywords_el is not None:
        is_inline = bool(
            normalise_heading_text(paragraph_text(keywords_el)) != "keywords"
        )
        terms_el = keywords_el if is_inline else _keywords_text_paragraph(
            body_paras, keywords_el
        )

        if not is_inline and "Keywords" in available and \
                para_style_id(keywords_el) != available["Keywords"]:
            set_para_style(keywords_el, available["Keywords"])
            actions.append({"kind": "keywords_style",
                            "description": "Keywords line set to Keywords style"})

        # Italicise the LABEL only — never the keyword terms. With the inline
        # form the label is the "Keywords:" run of the terms paragraph; with a
        # standalone Keywords heading the heading IS the label, so it is the
        # heading that carries the italic.
        label_el = keywords_el if not is_inline else terms_el
        if label_el is not None and _italicise_keyword_label(label_el, available):
            actions.append({"kind": "keywords_label_italic",
                            "description": "Keywords: label set italic"})

        target = terms_el if terms_el is not None else keywords_el
        style_name = styles_index.get(para_style_id(target), "")
        if style_name != "keywords":
            p_pr = get_or_add_ppr(target)
            ind = p_pr.find(f"{WQ}ind")
            left = (ind.get(f"{WQ}left") if ind is not None else None) or "0"
            if left != "720":
                next_change_id = set_tracked_ppr(
                    target, "ind", {"left": "720", "firstLine": "0"}, next_change_id
                )
                actions.append({"kind": "keywords_indent",
                                "description": "Keywords line indented 0.5in"})

    if not actions:
        if input_path != output_path:
            shutil.copyfile(input_path, output_path)
        return next_change_id, actions

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    tmp = output_path + ".abstractkw.tmp"
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


def _abstract_body_paragraphs(
    body_paras: list[etree._Element],
    heading_el: etree._Element,
) -> list[etree._Element]:
    """Non-empty paragraphs between the Abstract heading and the next boundary.

    Mirrors ``document_analysis_services._is_abstract_boundary`` (minus the
    paragraph model) so the fixer and the APA008 check agree on where the
    abstract body ends. Practitioner Notes is a legacy terminator only.
    """
    terminators = (
        {"keywords", "keyword", "citation"}
        | {"practitioner notes", "practioner notes"}
        | heading_names("Introduction") | heading_names("Method")
    )
    out: list[etree._Element] = []
    seen = False
    for para_el in body_paras:
        if para_el is heading_el:
            seen = True
            continue
        if not seen:
            continue
        text = paragraph_text(para_el)
        if not text:
            continue
        low = normalise_heading_text(text)
        if low in terminators or low.startswith(("keywords:", "citation:")):
            break
        if para_style_id(para_el).lower().startswith("heading") and \
                low not in ("abstract",):
            break
        out.append(para_el)
    return out


def _italicise_keyword_label(
    terms_el: etree._Element,
    available: dict[str, str],
) -> bool:
    """Italicise the keywords LABEL (never the terms).

    Prefers the ``Keywords Label`` character style when the document has it;
    otherwise writes a direct ``w:i``. Returns False when the label is
    already italic — a redundant second style (or direct flag on top of the
    character style) would make this pass report a fix on every run.
    """
    label_style = available.get(_LABEL_STYLE_NAME)
    for run_el in terms_el.iter(f"{WQ}r"):
        t = run_el.find(f"{WQ}t")
        if t is None:
            continue
        if not (t.text or "").strip():
            continue
        # The first non-empty run of the label paragraph is the label itself.
        if not (t.text or "").strip().lower().startswith("keywords"):
            return False  # reached the terms — stop

        r_pr = run_el.find(f"{WQ}rPr")
        if r_pr is None:
            r_pr = etree.Element(f"{WQ}rPr")
            run_el.insert(0, r_pr)
        r_style = r_pr.find(f"{WQ}rStyle")

        if label_style is not None:
            if r_style is not None and r_style.get(f"{WQ}val") == label_style:
                return False  # already italic via the character style
            if r_style is None:
                r_style = etree.Element(f"{WQ}rStyle")
                r_pr.insert(0, r_style)
            r_style.set(f"{WQ}val", label_style)
            return True

        if _is_italic(r_pr):
            return False
        return _ensure_run_flag(run_el, "i")
    return False