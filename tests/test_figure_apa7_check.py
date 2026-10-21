"""Tests for the APA 7 figure-block check (JB-09).

A well-formed APA 7 figure has a bold ``Figure N`` label, an italicised title,
a descriptive ``Note.`` paragraph, and is referenced in the text before it
appears. The pass is comment-only and emits one comment per missing property.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from app.services.figure_apa7_check import apply_figure_apa7_comments

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


def _p(text, *, style=None, bold=False, italic=False) -> dict:
    return {"style": style, "runs": [(text, bold, italic)]}


def _build_docx(path: Path, paragraphs: list[dict]) -> None:
    body_parts: list[str] = []
    for spec in paragraphs:
        style = spec.get("style")
        ppr = "" if style is None else f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
        runs_xml = ""
        for text, bold, italic in spec["runs"]:
            rpr_parts = []
            if bold:
                rpr_parts.append("<w:b/>")
            if italic:
                rpr_parts.append("<w:i/>")
            rpr = f"<w:rPr>{''.join(rpr_parts)}</w:rPr>" if rpr_parts else ""
            runs_xml += f'<w:r>{rpr}<w:t xml:space="preserve">{text}</w:t></w:r>'
        body_parts.append(f"<w:p>{ppr}{runs_xml}</w:p>")
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{"".join(body_parts)}</w:body></w:document>'
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", _MIN_RELS_DOC)
        z.writestr("word/document.xml", doc)


def _read_comments(path: Path) -> list[str]:
    with zipfile.ZipFile(path, "r") as z:
        if "word/comments.xml" not in z.namelist():
            return []
        root = etree.fromstring(z.read("word/comments.xml"))
    return [
        "".join(t.text or "" for t in c.iter(f"{WQ}t"))
        for c in root.findall(f"{WQ}comment")
    ]


def _correct_figure():
    """Reference → bold label → italic title → note."""
    return [
        _p("As shown in Figure 1, the trend is upward."),
        _p("Figure 1", bold=True),
        _p("Results of the experiment", italic=True),
        _p("Note. This figure summarises the main findings."),
    ]


def test_correct_figure_is_not_flagged(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, _correct_figure())

    _, actions = apply_figure_apa7_comments(str(src), str(out), 1)

    assert actions == []


def test_missing_bold_label_flagged(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    paras = _correct_figure()
    paras[1] = _p("Figure 1", bold=False)
    _build_docx(src, paras)

    _, actions = apply_figure_apa7_comments(str(src), str(out), 1)

    rules = {a["rule"] for a in actions}
    assert "figure_apa7_bold" in rules
    assert any("bold" in t for t in _read_comments(out))


def test_missing_italic_title_flagged(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    paras = _correct_figure()
    paras[2] = _p("Results of the experiment", italic=False)
    _build_docx(src, paras)

    _, actions = apply_figure_apa7_comments(str(src), str(out), 1)

    rules = {a["rule"] for a in actions}
    assert "figure_apa7_title" in rules
    assert any("italicised" in t for t in _read_comments(out))


def test_missing_description_flagged(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, _correct_figure()[:-1])  # drop the note

    _, actions = apply_figure_apa7_comments(str(src), str(out), 1)

    rules = {a["rule"] for a in actions}
    assert "figure_apa7_description" in rules
    assert any("Note." in t for t in _read_comments(out))


def test_missing_callout_flagged(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, _correct_figure()[1:])  # drop the reference paragraph

    _, actions = apply_figure_apa7_comments(str(src), str(out), 1)

    rules = {a["rule"] for a in actions}
    assert "figure_apa7_callout" in rules
    assert any("referenced" in t for t in _read_comments(out))


def test_reference_to_other_figure_does_not_satisfy_callout(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        _p("As shown in Figure 2, the trend is upward."),
        _p("Figure 1", bold=True),
        _p("Results of the experiment", italic=True),
        _p("Note. This figure summarises the main findings."),
    ])

    _, actions = apply_figure_apa7_comments(str(src), str(out), 1)

    rules = {a["rule"] for a in actions}
    assert "figure_apa7_callout" in rules


def test_clean_doc_writes_no_comments(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [_p("An ordinary body paragraph with no figures.")])

    _, actions = apply_figure_apa7_comments(str(src), str(out), 1)

    assert actions == []
    assert out.exists()
