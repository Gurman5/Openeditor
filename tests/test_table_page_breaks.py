from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from app.services.table_page_breaks import apply_table_page_breaks

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"

_MIN_CT = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    b'<Default Extension="xml" ContentType="application/xml"/>'
    b'<Default Extension="rels" '
    b'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    b'<Override PartName="/word/document.xml" '
    b'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    b'</Types>'
)
_MIN_RELS_PKG = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    b'<Relationship Id="rId1" '
    b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    b'Target="word/document.xml"/>'
    b'</Relationships>'
)
_MIN_RELS_DOC = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
)


def _table_xml(rows: int, *, long_text: bool = False) -> str:
    row_xml = []
    text = "This is a deliberately long cell value that should wrap over multiple rendered table lines. "
    for idx in range(rows):
        value = (text * 3) if long_text else f"Row {idx + 1}"
        row_xml.append(
            f"<w:tr><w:tc><w:p><w:r><w:t>{value}</w:t></w:r></w:p></w:tc></w:tr>"
        )
    return f"<w:tbl>{''.join(row_xml)}</w:tbl>"


def _styled_para_xml(style: str, text: str) -> str:
    return (
        f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
        f"<w:r><w:t>{text}</w:t></w:r></w:p>"
    )


def _build_docx(path: Path, body_xml: str) -> None:
    doc_xml = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{body_xml}</w:body></w:document>'
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", _MIN_RELS_DOC)
        z.writestr("word/document.xml", doc_xml)


def _document_root(path: Path) -> etree._Element:
    with zipfile.ZipFile(path, "r") as z:
        return etree.fromstring(z.read("word/document.xml"))


def _page_break_count(path: Path) -> int:
    root = _document_root(path)
    return len([
        br for br in root.findall(f".//{WQ}br")
        if br.get(f"{WQ}type") == "page"
    ])


def test_large_table_gets_page_break_before_it(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        '<w:p><w:r><w:t>Before table.</w:t></w:r></w:p>' + _table_xml(25),
    )

    actions = apply_table_page_breaks(str(inp), str(out))

    assert actions == [
        {"rule": "table_page_break", "table_number": 1, "page_units": 25}
    ]
    root = _document_root(out)
    body_children = list(root.find(f"{WQ}body"))
    table_index = next(i for i, el in enumerate(body_children) if el.tag == f"{WQ}tbl")
    previous = body_children[table_index - 1]
    assert previous.tag == f"{WQ}p"
    assert previous.find(f".//{WQ}br").get(f"{WQ}type") == "page"


def test_large_table_page_break_goes_before_caption_block(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        _styled_para_xml("TableNumber", "Table 1.")
        + _styled_para_xml("TableTitle", "Long table title")
        + _table_xml(25),
    )

    actions = apply_table_page_breaks(str(inp), str(out))

    assert actions == [
        {"rule": "table_page_break", "table_number": 1, "page_units": 25}
    ]
    body_children = list(_document_root(out).find(f"{WQ}body"))
    assert [child.tag for child in body_children[:4]] == [
        f"{WQ}p",
        f"{WQ}p",
        f"{WQ}p",
        f"{WQ}tbl",
    ]
    assert body_children[0].find(f".//{WQ}br").get(f"{WQ}type") == "page"
    assert body_children[1].find(f"{WQ}pPr/{WQ}pStyle").get(f"{WQ}val") == "TableNumber"
    assert body_children[2].find(f"{WQ}pPr/{WQ}pStyle").get(f"{WQ}val") == "TableTitle"


def test_page_break_before_caption_block_is_not_duplicated(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
        + _styled_para_xml("TableNumber", "Table 1.")
        + _styled_para_xml("TableTitle", "Long table title")
        + _table_xml(25),
    )

    actions = apply_table_page_breaks(str(inp), str(out))

    assert actions == []
    assert _page_break_count(out) == 1


def test_small_table_is_left_unchanged(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(inp, _table_xml(5))

    actions = apply_table_page_breaks(str(inp), str(out))

    assert actions == []
    assert _page_break_count(out) == 0


def test_existing_page_break_is_not_duplicated(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>' + _table_xml(30),
    )

    actions = apply_table_page_breaks(str(inp), str(out))

    assert actions == []
    assert _page_break_count(out) == 1


def test_wrapped_text_can_make_short_table_too_tall(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(inp, _table_xml(8, long_text=True))

    actions = apply_table_page_breaks(str(inp), str(out))

    assert len(actions) == 1
    assert actions[0]["page_units"] > 24
    assert _page_break_count(out) == 1
