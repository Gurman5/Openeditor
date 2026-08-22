"""Tests for the input-normalisation pass.

Fixtures are built programmatically (in-memory zip + raw document.xml) so the
test pack stays text-only and we can target the exact XML shapes that python-
docx hides behind its run/paragraph abstractions.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from app.services.document_normalisation_services import (
    GUIDANCE_NOTES_STYLE,
    NormalisationReport,
    normalise_docx,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"

_MIN_RELS = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    b'<Relationship Id="rId1" '
    b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    b'Target="word/document.xml"/>'
    b'</Relationships>'
)
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


def _build_docx(path: Path, document_xml: bytes) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS)
        z.writestr("word/document.xml", document_xml)


def _read_document_xml(path: Path) -> etree._Element:
    with zipfile.ZipFile(path, "r") as z:
        return etree.fromstring(z.read("word/document.xml"))


def _wrap_body(inner: str) -> bytes:
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{inner}</w:body></w:document>'
    ).encode("utf-8")


# ── Tracked-change handling ─────────────────────────────────────────────────


def test_accepts_tracked_insertions_and_deletions(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = (
        '<w:p>'
        '<w:r><w:t xml:space="preserve">Hello </w:t></w:r>'
        '<w:ins w:id="1" w:author="A" w:date="2026-05-04T00:00:00Z">'
        '<w:r><w:t xml:space="preserve">brave </w:t></w:r>'
        '</w:ins>'
        '<w:del w:id="2" w:author="A" w:date="2026-05-04T00:00:00Z">'
        '<w:r><w:delText xml:space="preserve">old </w:delText></w:r>'
        '</w:del>'
        '<w:r><w:t>world</w:t></w:r>'
        '</w:p>'
    )
    _build_docx(inp, _wrap_body(body))

    report = normalise_docx(inp, out)

    assert report.accepted_revisions == 2
    assert report.changed

    root = _read_document_xml(out)
    # No tracked-change wrappers should remain.
    assert root.find(f".//{WQ}ins") is None
    assert root.find(f".//{WQ}del") is None
    # Inserted content stays, deleted content is gone.
    text = "".join(t.text or "" for t in root.iter(f"{WQ}t"))
    assert "brave " in text
    assert "old " not in text
    assert text.startswith("Hello ")
    assert text.endswith("world")


def test_drops_property_change_records(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = (
        '<w:p>'
        '<w:pPr>'
        '<w:pStyle w:val="Normal"/>'
        '<w:pPrChange w:id="3" w:author="A" w:date="2026-05-04T00:00:00Z">'
        '<w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
        '</w:pPrChange>'
        '</w:pPr>'
        '<w:r><w:t>Body</w:t></w:r>'
        '</w:p>'
    )
    _build_docx(inp, _wrap_body(body))

    report = normalise_docx(inp, out)

    assert report.accepted_revisions == 1
    root = _read_document_xml(out)
    assert root.find(f".//{WQ}pPrChange") is None
    # The current property is preserved.
    pstyle = root.find(f".//{WQ}pPr/{WQ}pStyle")
    assert pstyle is not None
    assert pstyle.get(f"{WQ}val") == "Normal"


# ── Colour and highlight stripping ──────────────────────────────────────────


def test_strips_run_colour_and_highlight(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = (
        '<w:p>'
        '<w:r>'
        '<w:rPr>'
        '<w:color w:val="FF0000"/>'
        '<w:highlight w:val="yellow"/>'
        '</w:rPr>'
        '<w:t>Red and highlighted</w:t>'
        '</w:r>'
        '<w:r>'
        '<w:rPr><w:shd w:val="clear" w:color="auto" w:fill="FFFF00"/></w:rPr>'
        '<w:t>Shaded</w:t>'
        '</w:r>'
        '</w:p>'
    )
    _build_docx(inp, _wrap_body(body))

    report = normalise_docx(inp, out)

    assert report.runs_colour_stripped == 1
    assert report.runs_highlight_stripped == 2  # one w:highlight + one w:shd
    root = _read_document_xml(out)
    assert root.find(f".//{WQ}color") is None
    assert root.find(f".//{WQ}highlight") is None
    assert root.find(f".//{WQ}shd") is None
    # Visible text untouched.
    text = "".join(t.text or "" for t in root.iter(f"{WQ}t"))
    assert text == "Red and highlightedShaded"


# ── Guidance Notes deletion ─────────────────────────────────────────────────


def test_deletes_guidance_notes_paragraph(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = (
        '<w:p>'
        '<w:pPr><w:pStyle w:val="Normal"/></w:pPr>'
        '<w:r><w:t>Real content</w:t></w:r>'
        '</w:p>'
        f'<w:p>'
        f'<w:pPr><w:pStyle w:val="{GUIDANCE_NOTES_STYLE}"/></w:pPr>'
        '<w:r><w:t>Delete this template advice please</w:t></w:r>'
        '</w:p>'
        '<w:p>'
        '<w:pPr><w:pStyle w:val="GuidanceNotes"/></w:pPr>'
        '<w:r><w:t>Also a guidance note (no spaces variant)</w:t></w:r>'
        '</w:p>'
    )
    _build_docx(inp, _wrap_body(body))

    report = normalise_docx(inp, out)

    assert report.guidance_paragraphs_deleted == 2
    root = _read_document_xml(out)
    text = "".join(t.text or "" for t in root.iter(f"{WQ}t"))
    assert "Real content" in text
    assert "Delete this template advice" not in text
    assert "Also a guidance note" not in text


# ── Blank paragraph removal ─────────────────────────────────────────────────


def test_removes_blank_paragraphs_between_content(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = (
        '<w:p><w:r><w:t>First</w:t></w:r></w:p>'
        '<w:p/>'
        '<w:p><w:r><w:t>   </w:t></w:r></w:p>'  # whitespace-only
        '<w:p><w:r/></w:p>'                       # run with no text
        '<w:p><w:r><w:t>Second</w:t></w:r></w:p>'
    )
    _build_docx(inp, _wrap_body(body))

    report = normalise_docx(inp, out)

    assert report.blank_paragraphs_removed == 3
    root = _read_document_xml(out)
    paras = list(root.iter(f"{WQ}p"))
    assert len(paras) == 2
    texts = ["".join(t.text or "" for t in p.iter(f"{WQ}t")) for p in paras]
    assert texts == ["First", "Second"]


def test_keeps_paragraph_with_inline_image(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = (
        '<w:p><w:r><w:t>Before</w:t></w:r></w:p>'
        '<w:p><w:r><w:drawing/></w:r></w:p>'
        '<w:p><w:r><w:t>After</w:t></w:r></w:p>'
    )
    _build_docx(inp, _wrap_body(body))

    report = normalise_docx(inp, out)

    assert report.blank_paragraphs_removed == 0
    root = _read_document_xml(out)
    assert len(list(root.iter(f"{WQ}p"))) == 3
    assert root.find(f".//{WQ}drawing") is not None


def test_keeps_paragraph_with_textbox(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = (
        '<w:p><w:r><w:t>Before</w:t></w:r></w:p>'
        '<w:p><w:r><w:txbxContent><w:p><w:r><w:t>Editor box</w:t></w:r></w:p></w:txbxContent></w:r></w:p>'
        '<w:p><w:r><w:t>After</w:t></w:r></w:p>'
    )
    _build_docx(inp, _wrap_body(body))

    report = normalise_docx(inp, out)

    assert report.blank_paragraphs_removed == 0
    root = _read_document_xml(out)
    # 3 top level paragraphs + 1 inside the textbox
    assert len(list(root.iter(f"{WQ}p"))) == 4
    assert root.find(f".//{WQ}txbxContent") is not None


def test_keeps_paragraph_with_section_break(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = (
        '<w:p><w:r><w:t>Section one</w:t></w:r></w:p>'
        '<w:p><w:pPr><w:sectPr><w:type w:val="continuous"/></w:sectPr></w:pPr></w:p>'
        '<w:p><w:r><w:t>Section two</w:t></w:r></w:p>'
    )
    _build_docx(inp, _wrap_body(body))

    report = normalise_docx(inp, out)

    assert report.blank_paragraphs_removed == 0
    root = _read_document_xml(out)
    assert root.find(f".//{WQ}sectPr") is not None


def test_keeps_paragraph_with_bookmark(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = (
        '<w:p><w:r><w:t>Anchor target</w:t></w:r></w:p>'
        '<w:p><w:bookmarkStart w:id="1" w:name="ref1"/>'
        '<w:bookmarkEnd w:id="1"/></w:p>'
        '<w:p><w:r><w:t>After bookmark</w:t></w:r></w:p>'
    )
    _build_docx(inp, _wrap_body(body))

    report = normalise_docx(inp, out)

    assert report.blank_paragraphs_removed == 0
    root = _read_document_xml(out)
    assert root.find(f".//{WQ}bookmarkStart") is not None


def test_keeps_blank_paragraph_inside_table_cell(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = (
        '<w:tbl>'
        '<w:tr><w:tc>'
        '<w:p><w:r><w:t>Cell content</w:t></w:r></w:p>'
        '<w:p/>'  # blank paragraph in cell — must stay for valid table layout
        '</w:tc></w:tr>'
        '</w:tbl>'
        '<w:p><w:r><w:t>After table</w:t></w:r></w:p>'
        '<w:p/>'  # blank at body level — should be removed
    )
    _build_docx(inp, _wrap_body(body))

    report = normalise_docx(inp, out)

    assert report.blank_paragraphs_removed == 1
    root = _read_document_xml(out)
    # The cell still has its blank paragraph.
    tc = root.find(f".//{WQ}tc")
    assert tc is not None
    cell_paras = list(tc.iter(f"{WQ}p"))
    assert len(cell_paras) == 2  # content + blank both kept


def test_blank_paragraph_count_in_summary(tmp_path):
    report = NormalisationReport(blank_paragraphs_removed=4)
    msg = report.summary_text()
    assert "4 blank paragraph" in msg


# ── No-op behaviour and report ──────────────────────────────────────────────


def test_clean_doc_produces_empty_report(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = '<w:p><w:r><w:t>Just a clean paragraph.</w:t></w:r></w:p>'
    _build_docx(inp, _wrap_body(body))

    report = normalise_docx(inp, out)

    assert isinstance(report, NormalisationReport)
    assert not report.changed
    assert report.summary_text() == "No author formatting noise detected."


def test_summary_text_is_human_readable(tmp_path):
    report = NormalisationReport(
        accepted_revisions=3,
        runs_colour_stripped=2,
        runs_highlight_stripped=1,
        guidance_paragraphs_deleted=1,
    )
    msg = report.summary_text()
    assert "3 tracked change" in msg
    assert "colour" in msg
    assert "highlighting" in msg
    assert "Guidance Notes" in msg


def test_does_not_mutate_input(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    body = (
        '<w:p><w:ins w:id="1" w:author="A" w:date="2026-05-04T00:00:00Z">'
        '<w:r><w:t>tracked</w:t></w:r></w:ins></w:p>'
    )
    _build_docx(inp, _wrap_body(body))
    original_bytes = inp.read_bytes()

    normalise_docx(inp, out)

    # Input file is untouched on disk.
    assert inp.read_bytes() == original_bytes
    # Output reflects the normalisation.
    assert _read_document_xml(out).find(f".//{WQ}ins") is None
