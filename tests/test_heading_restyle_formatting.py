"""A body paragraph restyled to a heading must shed its body formatting.

When the bot promotes a plain/bold paragraph (e.g. an author's "Discussion"
heading typed as Normal) to Heading 1, the direct run font size and paragraph
spacing it carried as body text would otherwise override the heading style —
so the heading renders at 11pt with body spacing, visibly different from a
natively-styled Heading 1. These tests lock in that the conflicting direct
formatting is stripped (while the tracked pPrChange still preserves the
original for accept/reject), and that non-heading restyles are untouched.
"""

from lxml import etree

from app.services.output_generation_samfix import (
    HEADING_1_STYLE_ID,
    HEADING_2_STYLE_ID,
    REFERENCE_ENTRY_REQUIRED_STYLE_ID,
    WQ,
    _apply_tracked_style_change,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _body_para(text="Discussion", *, sz="22", with_spacing=True):
    spacing = (
        '<w:spacing w:before="0" w:after="120" w:line="276" w:lineRule="auto"/>'
        if with_spacing else ""
    )
    return etree.fromstring(
        f'<w:p xmlns:w="{W}"><w:pPr><w:pStyle w:val="Normal"/>{spacing}'
        f'<w:ind w:firstLine="720"/><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:pPr>'
        f'<w:r><w:rPr><w:b/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr>'
        f'<w:t>{text}</w:t></w:r></w:p>'
    )


def _ppr(p):
    return p.find(f"{WQ}pPr")


def test_restyle_to_heading1_strips_run_size_and_spacing():
    p = _body_para()
    _apply_tracked_style_change(p, HEADING_1_STYLE_ID, "Normal", 6101)

    ppr = _ppr(p)
    assert ppr.find(f"{WQ}pStyle").get(f"{WQ}val") == HEADING_1_STYLE_ID
    assert ppr.find(f"{WQ}spacing") is None
    assert ppr.find(f"{WQ}ind") is None
    assert p.find(f"{WQ}r").find(f"{WQ}rPr").find(f"{WQ}sz") is None
    assert p.find(f"{WQ}r").find(f"{WQ}rPr").find(f"{WQ}szCs") is None
    # The paragraph-mark size is cleared too.
    assert ppr.find(f"{WQ}rPr/{WQ}sz") is None


def test_pprchange_preserves_original_for_accept_reject():
    p = _body_para()
    _apply_tracked_style_change(p, HEADING_1_STYLE_ID, "Normal", 6101)

    old_ppr = _ppr(p).find(f"{WQ}pPrChange/{WQ}pPr")
    assert old_ppr is not None
    assert old_ppr.find(f"{WQ}pStyle").get(f"{WQ}val") == "Normal"
    assert old_ppr.find(f"{WQ}spacing") is not None  # original spacing retained


def test_bold_is_preserved():
    """Only size/spacing are stripped — bold stays (headings are bold anyway)."""
    p = _body_para()
    _apply_tracked_style_change(p, HEADING_1_STYLE_ID, "Normal", 6101)
    assert p.find(f"{WQ}r").find(f"{WQ}rPr").find(f"{WQ}b") is not None


def test_restyle_to_heading2_also_strips():
    p = _body_para(text="Practical Implications")
    _apply_tracked_style_change(p, HEADING_2_STYLE_ID, "Normal", 6102)
    assert p.find(f"{WQ}r").find(f"{WQ}rPr").find(f"{WQ}sz") is None


def test_non_heading_restyle_keeps_direct_size():
    """Restyling to the reference style must NOT strip the run size — only
    heading promotions do."""
    p = _body_para(text="Smith, J. (2020). A study.")
    _apply_tracked_style_change(p, REFERENCE_ENTRY_REQUIRED_STYLE_ID, "Normal", 5001)
    assert p.find(f"{WQ}r").find(f"{WQ}rPr").find(f"{WQ}sz") is not None
