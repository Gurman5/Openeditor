"""Tests for the APA 7 caption-split recommendation pass.

A figure or table caption that lives in a single paragraph (`Figure 1.
Two-stage design for the project. Stage 1 entailed…`) gets one comment
recommending the editor split it across three paragraphs per APA 7
(label / italic title / Note). The pass is intentionally comment-only.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from app.services.caption_apa7_check import apply_caption_apa7_comments

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


def _build_docx(path: Path, entries: list[tuple[str | None, str]]) -> None:
    body_parts: list[str] = []
    for style, text in entries:
        ppr = "" if style is None else f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
        body_parts.append(
            f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'
        )
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{"".join(body_parts)}</w:body></w:document>'
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", _MIN_RELS_DOC)
        z.writestr("word/document.xml", doc)


def _read_comment_texts(path: Path) -> list[str]:
    with zipfile.ZipFile(path, "r") as z:
        if "word/comments.xml" not in z.namelist():
            return []
        root = etree.fromstring(z.read("word/comments.xml"))
    return [
        "".join(t.text or "" for t in c.iter(f"{WQ}t"))
        for c in root.findall(f"{WQ}comment")
    ]


def test_single_paragraph_figure_caption_flagged(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        (None, "Body paragraph one."),
        (None, (
            "Figure 1. Two-stage design for the BMS Graduate Career Mapping "
            "Project. Stage 1 (2022) entailed an exploratory audit; Stage 2 "
            "used a Qualtrics survey emailed to alumni."
        )),
    ])

    _, actions = apply_caption_apa7_comments(str(src), str(out), 1)
    assert len(actions) == 1
    assert actions[0]["rule"] == "caption_apa7"

    texts = _read_comment_texts(out)
    assert any("APA 7" in t for t in texts)


def test_table_caption_also_flagged(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        (None, (
            "Table 2. Demographic characteristics of survey respondents "
            "across the three institutions sampled."
        )),
    ])

    _, actions = apply_caption_apa7_comments(str(src), str(out), 1)
    assert len(actions) == 1


def test_letter_suffix_caption_flagged(tmp_path: Path):
    """The example in the bug report used `Figure A.` rather than a
    numeric prefix; the detector must catch this too."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        (None, (
            "Figure A. Two-stage design for the project. Detailed "
            "description of stages, participants, and analysis."
        )),
    ])

    _, actions = apply_caption_apa7_comments(str(src), str(out), 1)
    assert len(actions) == 1


def test_canonical_apa7_caption_is_not_flagged(tmp_path: Path):
    """A label-only paragraph styled `Figure Number` is already in
    canonical APA 7 shape — no comment should fire."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        ("Figure Number", "Figure 1"),
        ("Figure Title", "Two-stage design for the project"),
    ])

    _, actions = apply_caption_apa7_comments(str(src), str(out), 1)
    assert actions == []


def test_bare_figure_reference_in_body_prose_is_not_flagged(tmp_path: Path):
    """`Figure 3 shows...` (no period directly after the label) is a
    body reference, not a caption — must not be commented on."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        (None, "Figure 3 shows the participant numbers across cohorts."),
    ])

    _, actions = apply_caption_apa7_comments(str(src), str(out), 1)
    assert actions == []


def test_very_short_caption_with_no_note_not_flagged(tmp_path: Path):
    """A caption that's only ``Figure 1. Title.`` with no descriptive
    note is essentially title-only and splitting it adds no value."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        (None, "Figure 1. Brief title."),  # ~20 chars after label
    ])

    _, actions = apply_caption_apa7_comments(str(src), str(out), 1)
    assert actions == []


def test_clean_doc_writes_no_comments(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        (None, "A perfectly ordinary body paragraph without any captions."),
    ])

    _, actions = apply_caption_apa7_comments(str(src), str(out), 1)
    assert actions == []
    # File must still be a valid docx.
    assert out.exists()
