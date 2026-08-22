"""Tests for APA narrative citation ampersand fixes."""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from lxml import etree

from app.services.narrative_citation_corrections import (
    apply_narrative_citation_corrections,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"

_MIN_RELS = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    b'<Relationship Id="rId1" '
    b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    b'Target="word/document.xml"/>'
    b"</Relationships>"
)
_MIN_CT = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    b'<Default Extension="xml" ContentType="application/xml"/>'
    b'<Default Extension="rels" '
    b'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    b'<Override PartName="/word/document.xml" '
    b'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    b"</Types>"
)


def _build_docx(path: Path, runs: list[str], style: str | None = None) -> None:
    if style:
        ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
    else:
        ppr = ""
    run_xml = "".join(
        f'<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'
        for text in runs
    )
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>'
        f"<w:p>{ppr}{run_xml}</w:p>"
        f"</w:body></w:document>"
    ).encode("utf-8")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS)
        z.writestr("word/document.xml", doc)


def _read_visible_text(path: Path) -> str:
    with zipfile.ZipFile(path, "r") as z:
        root = etree.fromstring(z.read("word/document.xml"))
    chunks: list[str] = []
    for run in root.iter(f"{WQ}r"):
        parent = run.getparent()
        if parent is not None and parent.tag == f"{WQ}del":
            continue
        for text_el in run.findall(f"{WQ}t"):
            chunks.append(text_el.text or "")
    return "".join(chunks)


def _count_insertions(path: Path) -> int:
    with zipfile.ZipFile(path, "r") as z:
        root = etree.fromstring(z.read("word/document.xml"))
    return len(root.findall(f".//{WQ}ins"))


def test_replaces_ampersand_in_narrative_citation(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(inp, ["Smith & Jones (2024) found a similar result."])

    _, made = apply_narrative_citation_corrections(str(inp), str(out), 1)

    assert made == [
        {
            "original": "&",
            "replacement": "and",
            "citation": "Smith & Jones (2024)",
        }
    ]
    assert _read_visible_text(out) == "Smith and Jones (2024) found a similar result."
    assert _count_insertions(out) == 1


def test_does_not_change_parenthetical_citation(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(inp, ["The result was consistent with prior work (Smith & Jones, 2024)."])

    _, made = apply_narrative_citation_corrections(str(inp), str(out), 1)

    assert made == []
    assert _read_visible_text(out) == (
        "The result was consistent with prior work (Smith & Jones, 2024)."
    )
    assert _count_insertions(out) == 0


def test_does_not_change_narrative_shape_inside_brackets(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(inp, ["This note [Smith & Jones (2024)] is bracketed."])

    _, made = apply_narrative_citation_corrections(str(inp), str(out), 1)

    assert made == []
    assert _read_visible_text(out) == "This note [Smith & Jones (2024)] is bracketed."


def test_replaces_multiple_narrative_citations(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        ["Smith & Jones (2024) agreed, and Brown & Taylor (2023) extended it."],
    )

    _, made = apply_narrative_citation_corrections(str(inp), str(out), 1)

    assert len(made) == 2
    assert _read_visible_text(out) == (
        "Smith and Jones (2024) agreed, and Brown and Taylor (2023) extended it."
    )


def test_skips_reference_style(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        ["Smith & Jones (2024). Example title. Journal, 1(1), 1-2."],
        style="APA 7 Reference List Entry",
    )

    _, made = apply_narrative_citation_corrections(str(inp), str(out), 1)

    assert made == []
    assert _count_insertions(out) == 0


def test_skips_reference_style_id(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        ["Smith & Jones (2024). Example title. Journal, 1(1), 1-2."],
        style="APA7ReferenceListEntry",
    )

    _, made = apply_narrative_citation_corrections(str(inp), str(out), 1)

    assert made == []
    assert _count_insertions(out) == 0
