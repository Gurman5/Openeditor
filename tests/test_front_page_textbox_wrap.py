"""The front-page editorial textbox must wrap text around it, not overlay it.

The JUTLP template's editorial-info box (Editors / Section / Publication /
Copyright) is a floating textbox positioned in the right margin with square
text-wrapping. An earlier revision forced ``wrapNone`` (overlay) on it, which
made the box sit on top of and hide the abstract. These tests lock in square
wrapping so the surrounding content always flows around the box.
"""

from lxml import etree

from app.services.output_generation_samfix import (
    WPQ,
    _make_textbox_wrap_around_text,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
W10 = "urn:schemas-microsoft-com:office:word"


def _anchor_para(wrap_inner: str, *, behind: str = "1") -> etree._Element:
    xml = f'''<w:p xmlns:w="{W}" xmlns:wp="{WP}">
      <w:r><w:drawing><wp:anchor behindDoc="{behind}" distT="0" distL="0">
        <wp:positionH relativeFrom="margin"><wp:posOffset>4354195</wp:posOffset></wp:positionH>
        {wrap_inner}
        <wp:docPr id="1" name="box"/>
      </wp:anchor></w:drawing></w:r>
    </w:p>'''
    return etree.fromstring(xml)


def test_wrapnone_is_converted_to_wrapsquare():
    p = _anchor_para("<wp:wrapNone/>")
    changed = _make_textbox_wrap_around_text(p)

    assert changed is True
    anchor = p.find(f".//{WPQ}anchor")
    assert anchor.find(f"{WPQ}wrapSquare") is not None
    assert anchor.find(f"{WPQ}wrapNone") is None
    assert anchor.find(f"{WPQ}wrapSquare").get("wrapText") == "bothSides"


def test_behinddoc_is_cleared():
    p = _anchor_para("<wp:wrapNone/>", behind="1")
    _make_textbox_wrap_around_text(p)
    assert p.find(f".//{WPQ}anchor").get("behindDoc") == "0"


def test_wrapsquare_placed_before_docpr():
    """Schema order: the wrap element must precede docPr in the anchor."""
    p = _anchor_para("<wp:wrapNone/>")
    _make_textbox_wrap_around_text(p)
    anchor = p.find(f".//{WPQ}anchor")
    names = [etree.QName(c).localname for c in anchor]
    assert names.index("wrapSquare") < names.index("docPr")


def test_existing_wrapsquare_is_preserved():
    p = _anchor_para('<wp:wrapSquare wrapText="bothSides"/>', behind="0")
    _make_textbox_wrap_around_text(p)
    anchor = p.find(f".//{WPQ}anchor")
    # Exactly one wrapSquare, no overlay mode introduced.
    assert len(anchor.findall(f"{WPQ}wrapSquare")) == 1
    assert anchor.find(f"{WPQ}wrapNone") is None


def test_breathing_margins_added():
    p = _anchor_para("<wp:wrapNone/>")
    _make_textbox_wrap_around_text(p)
    anchor = p.find(f".//{WPQ}anchor")
    assert anchor.get("distL") != "0"
    assert anchor.get("distR") != "0"


def test_legacy_vml_wrap_none_becomes_square():
    xml = f'''<w:p xmlns:w="{W}" xmlns:w10="{W10}">
      <w:r><w:pict><w10:wrap type="none"/></w:pict></w:r>
    </w:p>'''
    p = etree.fromstring(xml)
    changed = _make_textbox_wrap_around_text(p)
    assert changed is True
    wrap = next(e for e in p.iter() if etree.QName(e).localname == "wrap")
    assert wrap.get("type") == "square"
