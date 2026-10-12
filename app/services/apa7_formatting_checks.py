"""APA-7 formatting checks (APA0xx family), run against the source document.

C-27 ships APA002 (font sweep). C-25 adds APA010/APA011/APA012 (references
block) and C-26 adds APA008/APA009 (abstract/keywords) here.

Every check mirrors its fixer's predicate exactly — the fixer owns the
definition of "wrong" (see ``docx_format_helpers``), so a check can never
flag what the fixer would leave alone or miss what it would rewrite.
"""

from __future__ import annotations

import zipfile

from copy import deepcopy
from lxml import etree

from app.services.config import ALLOWED_FONTS, DEFAULT_FONT
from app.services.docx_format_helpers import (
    find_canonical_heading,
    has_tracked_page_break_before,
    is_symbol_font,
    normalise_heading_text,
    paragraph_text,
    para_style_id,
    rfonts_explicit,
    rfonts_needs_fix,
    set_explicit_font,
)
from app.services.language_corrections import WQ
from app.services.references_block_corrections import (
    _all_runs_bold,
    check_reference_entries_hanging,
)
from app.services.run_font_corrections import (
    _char_style_font_map,
    _direct_text_runs,
    _is_text_part,
    _run_char_style_id,
)


def _result(rule_id: str, status: str, message: str) -> dict:
    return {"rule_id": rule_id, "status": status, "message": message}


def _style_rfonts_would_change(rfonts_el: etree._Element) -> list[str]:
    """Return the wrong typefaces a style/defaults ``w:rFonts`` declares.

    Dry-run of the C-27 style sweep: probe a copy with ``set_explicit_font``
    and report what it would rewrite. Symbol-only declarations return [].
    """
    explicit = rfonts_explicit(rfonts_el)
    if explicit and all(is_symbol_font(v) for v in explicit.values()):
        return []
    probe = deepcopy(rfonts_el)
    if not set_explicit_font(probe, DEFAULT_FONT):
        return []
    return sorted({v for v in explicit.values() if v}) or ["theme-bound"]


def check_fonts(docx_path: str) -> list[dict]:
    """APA002: every typeface resolves to the APA default (Calibri).

    Inspects text runs (document, headers, footers, footnotes, endnotes,
    comments), style-level fonts and ``docDefaults``. Symbol typefaces are
    exempt. ``ALLOWED_FONTS`` names the APA-permitted set in the message;
    the fixer still normalises everything to the default.
    """
    with zipfile.ZipFile(docx_path, "r") as z:
        names = z.namelist()
        text_parts = {n: z.read(n) for n in names if _is_text_part(n)}
        styles_xml = z.read("word/styles.xml") if "word/styles.xml" in names else None

    char_fonts = _char_style_font_map(styles_xml)
    offenders: dict[str, int] = {}

    def _note(font: str, count: int = 1) -> None:
        offenders[font] = offenders.get(font, 0) + count

    for part_xml in text_parts.values():
        root = etree.fromstring(part_xml)
        for para_el in root.iter(f"{WQ}p"):
            for run_el in _direct_text_runs(para_el):
                r_pr = run_el.find(f"{WQ}rPr")
                if r_pr is not None and r_pr.find(f"{WQ}rPrChange") is not None:
                    continue
                rfonts = r_pr.find(f"{WQ}rFonts") if r_pr is not None else None
                reason = rfonts_needs_fix(
                    rfonts, char_fonts.get(_run_char_style_id(run_el)), DEFAULT_FONT
                )
                if reason is None:
                    continue
                if reason == "theme":
                    _note("theme-bound (resolves via the Office theme)")
                elif reason == "char-style":
                    for v in char_fonts.get(_run_char_style_id(run_el), {}).values():
                        if v and not is_symbol_font(v):
                            _note(f"{v} (via character style)")
                else:
                    for v in rfonts_explicit(rfonts).values():
                        if v and v.strip().lower() != DEFAULT_FONT.lower() \
                                and not is_symbol_font(v):
                            _note(v)

    if styles_xml is not None:
        styles_root = etree.fromstring(styles_xml)
        for style_el in styles_root.findall(f"{WQ}style"):
            rPr = style_el.find(f"{WQ}rPr")
            rfonts = rPr.find(f"{WQ}rFonts") if rPr is not None else None
            if rfonts is None:
                continue
            wrong = _style_rfonts_would_change(rfonts)
            if wrong:
                sid = style_el.get(f"{WQ}styleId", "")
                _note(f"{', '.join(wrong)} ({sid or 'unnamed'} style)")
        for _ in styles_root.findall(f"{WQ}docDefaults/{WQ}rPrDefault/{WQ}rPr"):
            rfonts = _.find(f"{WQ}rFonts")
            if rfonts is not None and _style_rfonts_would_change(rfonts):
                _note("docDefaults (inherited document default)")

    if not offenders:
        return [_result(
            "APA002", "pass",
            "All text, styles and defaults use Calibri (symbol fonts excepted).",
        )]
    parts = sorted(offenders, key=lambda k: -offenders[k])[:8]
    detail = "; ".join(
        f"{name} ×{offenders[name]}" if offenders[name] > 1 else name
        for name in parts
    )
    if len(offenders) > 8:
        detail += f"; +{len(offenders) - 8} more"
    allowed = ", ".join(sorted(ALLOWED_FONTS))
    return [_result(
        "APA002", "fail",
        f"Non-default fonts in use: {detail}. APA permits {allowed}; "
        f"output is normalised to {DEFAULT_FONT} 11pt.",
    )]


# ── APA-12 References block (C-25) ───────────────────────────────────────


def _references_heading_and_body(docx_path: str):
    """Return (heading_el, body_paras) or (None, []) when absent.

    Reuses the fixer's text-based heading lookup so a bold-Normal References
    heading is seen by both.
    """
    with zipfile.ZipFile(docx_path, "r") as z:
        doc_root = etree.fromstring(z.read("word/document.xml"))
    body = doc_root.find(f"{WQ}body")
    if body is None:
        return None, []
    body_paras = [el for el in body if el.tag == f"{WQ}p"]
    return find_canonical_heading(body_paras, "References"), body_paras


def _styles_index(docx_path: str) -> dict[str, str]:
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            if "word/styles.xml" not in z.namelist():
                return {}
            root = etree.fromstring(z.read("word/styles.xml"))
    except (zipfile.BadZipFile, OSError):
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


def check_references_page_break(docx_path: str) -> list[dict]:
    """APA010: the References block starts on a new page."""
    heading_el, _ = _references_heading_and_body(docx_path)
    if heading_el is None:
        return []  # absence is reported by the structural section rule
    if has_tracked_page_break_before(heading_el):
        return [_result("APA010", "pass", "References starts on a new page")]
    return [_result(
        "APA010", "fail",
        "References does not start on a new page — APA requires the "
        "reference list to begin on a fresh page",
    )]


def check_references_heading_format(docx_path: str) -> list[dict]:
    """APA011: the References heading is bold and centred.

    Accepts either path the fixer takes: a ``Heading 1``-styled heading (the
    template style is centred + bold), or direct formatting. Resolves the
    style rather than trusting the style id, so a numeric id still counts.
    """
    heading_el, _ = _references_heading_and_body(docx_path)
    if heading_el is None:
        return []
    styles_index = _styles_index(docx_path)
    style_name = styles_index.get(para_style_id(heading_el), "")

    if style_name == "heading 1":
        return [_result(
            "APA011", "pass",
            "References heading is Heading 1 (centred, bold)",
        )]

    problems = []
    if not _all_runs_bold(heading_el):
        problems.append("not bold")
    p_pr = heading_el.find(f"{WQ}pPr")
    jc = p_pr.find(f"{WQ}jc") if p_pr is not None else None
    if jc is None or jc.get(f"{WQ}val") != "center":
        problems.append("not centred")
    if not problems:
        return [_result("APA011", "pass", "References heading is bold and centred")]
    return [_result(
        "APA011", "fail",
        f"References heading is {' and '.join(problems)} — APA requires it "
        f"bold and centred",
    )]


def check_references_hanging_indent(docx_path: str) -> list[dict]:
    """APA012: every reference entry carries a 0.5in hanging indent."""
    problems = check_reference_entries_hanging(docx_path)
    if not problems:
        return [_result(
            "APA012", "pass",
            "Reference entries use a 0.5in hanging indent",
        )]
    return [_result(
        "APA012", "fail",
        f"{len(problems)} reference entr{'y' if len(problems) == 1 else 'ies'} "
        f"missing the 0.5in hanging indent (e.g. \"{problems[0]}...\")",
    )]


# ── APA-08 / APA-09 abstract + keywords (C-26) ────────────────────────────


def _front_matter_paras(docx_path: str):
    with zipfile.ZipFile(docx_path, "r") as z:
        doc_root = etree.fromstring(z.read("word/document.xml"))
    body = doc_root.find(f"{WQ}body")
    if body is None:
        return [], {}
    paras = [el for el in body if el.tag == f"{WQ}p"]
    return paras, _styles_index(docx_path)


def _first_effective_ind(para_el: etree._Element) -> dict[str, str]:
    p_pr = para_el.find(f"{WQ}pPr")
    ind = p_pr.find(f"{WQ}ind") if p_pr is not None else None
    if ind is None:
        return {}
    return {k.split("}")[-1]: v for k, v in ind.attrib.items()}


def check_abstract_format(docx_path: str) -> list[dict]:
    """APA008: "Abstract" heading is bold + centred; body unindented."""
    from app.services.abstract_keywords_formatting import (
        _abstract_body_paragraphs,
    )

    paras, styles_index = _front_matter_paras(docx_path)
    abstract_el = find_canonical_heading(paras, "Abstract")
    if abstract_el is None:
        return []  # absence is reported by FP004

    problems = []
    style_name = styles_index.get(para_style_id(abstract_el), "")
    if style_name == "heading front page":
        pass  # the template style carries centring + bold
    else:
        if not _all_runs_bold(abstract_el):
            problems.append("heading is not bold")
        p_pr = abstract_el.find(f"{WQ}pPr")
        jc = p_pr.find(f"{WQ}jc") if p_pr is not None else None
        if jc is None or jc.get(f"{WQ}val") != "center":
            problems.append("heading is not centred")

    body_paras = _abstract_body_paragraphs(paras, abstract_el)
    if body_paras:
        ind = _first_effective_ind(body_paras[0])
        first_line = ind.get("firstLine")
        if first_line not in (None, "0") or (ind.get("left") or "0") != "0":
            problems.append("abstract body is indented")

    if not problems:
        return [_result(
            "APA008", "pass",
            "Abstract heading is bold and centred; body is unindented",
        )]
    return [_result(
        "APA008", "fail",
        f"APA abstract block: {'; '.join(problems)} — the heading must be "
        f"bold and centred and the body a single unindented paragraph",
    )]


def check_keywords_format(docx_path: str) -> list[dict]:
    """APA009: "Keywords:" label is italic; the keywords line is indented."""
    from app.services.abstract_keywords_formatting import (
        _find_keywords_paragraph,
        _keywords_text_paragraph,
    )

    paras, styles_index = _front_matter_paras(docx_path)
    keywords_el = _find_keywords_paragraph(paras)
    if keywords_el is None:
        return []  # absence is reported by FP006

    is_inline = normalise_heading_text(paragraph_text(keywords_el)) != "keywords"
    terms_el = keywords_el if is_inline else _keywords_text_paragraph(
        paras, keywords_el
    )

    problems = []
    # With a standalone Keywords heading the heading IS the label, so that is
    # what must be italic; with the inline form the label is the "Keywords:"
    # run of the terms paragraph.
    label_el = terms_el if is_inline else keywords_el
    if label_el is not None and not _label_is_italic(label_el):
        problems.append('the "Keywords:" label is not italic')

    target = terms_el if terms_el is not None else keywords_el
    style_name = styles_index.get(para_style_id(target), "")
    if style_name == "keywords":
        pass  # the template style carries the 0.5in indent
    else:
        ind = _first_effective_ind(target)
        if (ind.get("left") or "0") != "720":
            problems.append("keywords line is not indented 0.5in")

    if not problems:
        return [_result(
            "APA009", "pass",
            'Keywords label is italic and the line is indented 0.5in',
        )]
    return [_result(
        "APA009", "fail",
        f"APA keywords block: {'; '.join(problems)}",
    )]


def _label_is_italic(label_el: etree._Element) -> bool:
    """True when the first text run of ``label_el`` renders italic.

    Accepts either the ``Keywords Label`` character style or a direct ``w:i``.
    Only the FIRST non-empty run is inspected: that is the label; the keyword
    terms that follow must stay roman.
    """
    for run_el in label_el.iter(f"{WQ}r"):
        t = run_el.find(f"{WQ}t")
        if t is None or not (t.text or "").strip():
            continue
        r_pr = run_el.find(f"{WQ}rPr")
        if r_pr is None:
            return False
        r_style = r_pr.find(f"{WQ}rStyle")
        if r_style is not None and \
                r_style.get(f"{WQ}val", "").lower() == "keywordslabel":
            return True
        i = r_pr.find(f"{WQ}i")
        if i is not None and \
                (i.get(f"{WQ}val", "true") or "true").lower() not in ("false", "0", "off"):
            return True
        return False  # first non-empty run is the label and it is not italic
    return False
