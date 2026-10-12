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
    is_symbol_font,
    rfonts_explicit,
    rfonts_needs_fix,
    set_explicit_font,
)
from app.services.language_corrections import WQ
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
