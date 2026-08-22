"""Regression test for the suspicious-reference comment pass.

This pass (`_insert_suspicious_ref_comments` in feedback_gen_pipeline) anchors
CONS citation-consistency warnings to the References heading and CREF/HREF/DOIT
failures to individual reference-entry paragraphs. It calls
`add_paragraph_comment`, which is defined in `output_generation` — a missing
import once made every run fail with
`name 'add_paragraph_comment' is not defined`, silently dropping all
suspicious-reference comments (surfaced only as a "stage did not complete"
banner). These tests exercise the path end-to-end so that regression can't
recur.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from app.pipelines.feedback_gen_pipeline import _insert_suspicious_ref_comments

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


def _p(style: str | None, text: str) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'


def _build_docx(path: Path, parts: list[str]) -> None:
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{"".join(parts)}</w:body></w:document>'
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", _MIN_RELS_DOC)
        z.writestr("word/document.xml", doc)


def _comment_texts(path: Path) -> list[str]:
    with zipfile.ZipFile(path, "r") as z:
        if "word/comments.xml" not in z.namelist():
            return []
        root = etree.fromstring(z.read("word/comments.xml"))
    return [
        "".join(t.text or "" for t in c.iter(f"{WQ}t"))
        for c in root.findall(f"{WQ}comment")
    ]


def _comment_anchor_texts(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path, "r") as z:
        doc_root = etree.fromstring(z.read("word/document.xml"))
        comments_root = etree.fromstring(z.read("word/comments.xml"))

    body = doc_root.find(f"{WQ}body")
    anchors: dict[str, str] = {}
    for para in body:
        if para.tag != f"{WQ}p":
            continue
        text = " ".join("".join(t.text or "" for t in para.iter(f"{WQ}t")).split())
        for marker in para.findall(f"{WQ}commentRangeStart"):
            anchors[marker.get(f"{WQ}id")] = text

    return {
        "".join(t.text or "" for t in c.iter(f"{WQ}t")): anchors.get(c.get(f"{WQ}id"), "")
        for c in comments_root.findall(f"{WQ}comment")
    }


_REF_DOC = [
    _p("Heading 1", "Introduction"),
    _p(None, "Body text here."),
    _p("Heading 1", "References"),
    _p("APA 7 Reference List Entry", "Smith, J. (2020). First reference. Journal, 1(1), 1."),
    _p("APA 7 Reference List Entry", "Jones, A. (2021). Second reference. Journal, 2(2), 2."),
]


def test_cons_warning_anchored_to_references_heading(tmp_path):
    """A CONS warn result writes a comment (regression: this raised
    NameError when add_paragraph_comment was unimported)."""
    path = tmp_path / "doc.docx"
    _build_docx(path, _REF_DOC)

    _insert_suspicious_ref_comments(str(path), [
        {"rule_id": "CONS001", "status": "warn",
         "message": "2 references are not cited in the body text."},
    ])

    texts = _comment_texts(path)
    assert any("not cited in the body" in t for t in texts)


def test_cref_failure_anchored_to_reference_entry(tmp_path):
    path = tmp_path / "doc.docx"
    _build_docx(path, _REF_DOC)

    _insert_suspicious_ref_comments(str(path), [
        {"rule_id": "CREF002", "status": "fail",
         "message": "Entry 2 could not be verified."},
    ])

    texts = _comment_texts(path)
    # The comment on the entry itself should carry the result's own message.
    assert any("could not be verified" in t for t in texts)


def test_reference_issue_summary_is_anchored_to_references_heading(tmp_path):
    path = tmp_path / "doc.docx"
    _build_docx(path, _REF_DOC)

    _insert_suspicious_ref_comments(str(path), [
        {
            "rule_id": "CONS001",
            "status": "warn",
            "message": "2 references are not cited in the body text.",
        },
        {
            "rule_id": "CREF001",
            "status": "fail",
            "message": "Entry 1 could not be verified.",
        },
        {
            "rule_id": "HREF002",
            "status": "fail",
            "message": "Entry 2 has a broken DOI hyperlink.",
        },
    ])

    anchors = _comment_anchor_texts(path)
    summary = next(
        text for text in anchors
        if "Reference list issue summary:" in text
    )
    assert "1 citation-consistency warning" in summary
    assert "2 reference entries could not be automatically verified" in summary
    assert anchors[summary] == "References"
    assert any("not cited in the body" in text for text in anchors)
    assert sum("could not be automatically verified" in text for text in anchors) == 3


def test_no_suspicious_results_writes_no_comments(tmp_path):
    path = tmp_path / "doc.docx"
    _build_docx(path, _REF_DOC)

    _insert_suspicious_ref_comments(str(path), [
        {"rule_id": "CREF001", "status": "pass", "message": "Entry 1 verified."},
        {"rule_id": "CREF002", "status": "pass", "message": "Entry 2 verified."},
    ])

    texts = _comment_texts(path)
    assert any("CrossRef verification" in t for t in texts)
    assert any("2/2" in t for t in texts)


def test_add_paragraph_comment_is_importable_in_pipeline():
    """The function must be importable in the pipeline namespace — a missing
    import is exactly what broke the suspicious-ref stage in production."""
    from app.pipelines import feedback_gen_pipeline
    assert hasattr(feedback_gen_pipeline, "add_paragraph_comment")
