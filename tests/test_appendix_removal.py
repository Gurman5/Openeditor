"""Tests for the appendix-comment pass.

JUTLP does not accept appendices: the manuscript must end with References.
Any content after the reference list gets a single explanatory comment
anchored at the first appendix paragraph advising the author to move it into
the body. The pass is comment-only — it does NOT delete the content.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from app.services.appendix_removal import (
    _find_appendix_start,
    _is_appendix_heading,
    apply_appendix_removal,
)

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


def _p(style: str | None, text: str = "", *, image: bool = False) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    run = ""
    if text:
        run += f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r>'
    if image:
        run += '<w:r><w:drawing><wp:inline xmlns:wp="x"/></w:drawing></w:r>'
    return f"<w:p>{ppr}{run}</w:p>"


def _build_docx(path: Path, body_parts: list[str]) -> None:
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{"".join(body_parts)}</w:body></w:document>'
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", _MIN_RELS_DOC)
        z.writestr("word/document.xml", doc)


def _read_doc_root(path: Path) -> etree._Element:
    with zipfile.ZipFile(path, "r") as z:
        return etree.fromstring(z.read("word/document.xml"))


def _del_texts(root: etree._Element) -> list[str]:
    return [(t.text or "") for t in root.iter(f"{WQ}delText")]


def _comment_texts(path: Path) -> list[str]:
    with zipfile.ZipFile(path, "r") as z:
        if "word/comments.xml" not in z.namelist():
            return []
        root = etree.fromstring(z.read("word/comments.xml"))
    return [
        "".join(t.text or "" for t in c.iter(f"{WQ}t"))
        for c in root.findall(f"{WQ}comment")
    ]


# A typical body → references → appendix document.
_BODY_WITH_APPENDIX = [
    _p("Heading 1", "Introduction"),
    _p(None, "Body prose here."),
    _p("Heading 1", "References"),
    _p(None, "Smith, J. (2020). A study. Journal, 1(1), 1."),
    _p(None, "Jones, A. (2021). Another study. Journal, 2(2), 2."),
    _p("Heading 1", "Appendix A"),
    _p(None, "Supplementary detail that should not be in the paper."),
]


def test_find_appendix_start_after_references(tmp_path):
    src = tmp_path / "in.docx"
    _build_docx(src, _BODY_WITH_APPENDIX)
    body = _read_doc_root(src).find(f"{WQ}body")
    assert _find_appendix_start(body) == 5  # the "Appendix A" heading


def test_comment_anchored_and_content_not_deleted(tmp_path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, _BODY_WITH_APPENDIX)

    next_id, actions = apply_appendix_removal(str(src), str(out), 1)

    assert len(actions) == 1
    assert actions[0]["rule"] == "appendix_comment"
    # Comment-only: nothing is tracked-deleted.
    assert _del_texts(_read_doc_root(out)) == []
    comments = _comment_texts(out)
    assert len(comments) == 1
    assert "JUTLP does not accept appendices" in comments[0]


def test_appendix_heading_styled_as_reference_entry_is_detected(tmp_path):
    """The real-world bug: the appendix heading carries the reference style
    (NOT a Heading style), so it must be detected by TEXT — otherwise the
    appendix goes completely unflagged."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        _p("Heading 1", "References"),
        _p("APA7ReferenceListEntry", "Smith, J. (2020). A study."),
        # Appendix heading + prompts all carry the reference style.
        _p("APA7ReferenceListEntry", "Appendix A. Research-Skills Prompts"),
        _p("APA7ReferenceListEntry", "What makes a research study credible?"),
    ])

    next_id, actions = apply_appendix_removal(str(src), str(out), 1)

    assert len(actions) == 1
    assert actions[0]["rule"] == "appendix_comment"
    assert "Appendix A" in actions[0]["snippet"]
    assert _del_texts(_read_doc_root(out)) == []  # comment-only
    assert "JUTLP does not accept appendices" in _comment_texts(out)[0]


def test_image_after_references_is_flagged(tmp_path):
    """An unlabelled supplementary figure after the reference list (no
    heading) is still caught because it carries a drawing — comment-only."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        _p("Heading 1", "References"),
        _p(None, "Smith, J. (2020). A study."),
        _p(None, "", image=True),  # stray figure, no heading
    ])

    next_id, actions = apply_appendix_removal(str(src), str(out), 1)
    assert len(actions) == 1
    assert _del_texts(_read_doc_root(out)) == []
    assert len(_comment_texts(out)) == 1


def test_no_appendix_is_noop(tmp_path):
    """A document that ends cleanly with the reference list is untouched."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        _p("Heading 1", "Introduction"),
        _p(None, "Body prose."),
        _p("Heading 1", "References"),
        _p(None, "Smith, J. (2020). A study."),
        _p(None, "Jones, A. (2021). Another study."),
    ])

    next_id, actions = apply_appendix_removal(str(src), str(out), 1)
    assert actions == []
    assert _comment_texts(out) == []


def test_document_without_references_is_noop(tmp_path):
    """No References heading → nothing to anchor to → no-op."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        _p("Heading 1", "Introduction"),
        _p(None, "Body prose only, no references section."),
    ])

    next_id, actions = apply_appendix_removal(str(src), str(out), 1)
    assert actions == []


def test_empty_paragraphs_after_references_do_not_trigger(tmp_path):
    """Trailing blank paragraphs after the reference list (common in Word)
    are not headings/appendix-headings/images, so no appendix starts."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [
        _p("Heading 1", "References"),
        _p(None, "Smith, J. (2020). A study."),
        _p(None, ""),
        _p(None, ""),
    ])

    next_id, actions = apply_appendix_removal(str(src), str(out), 1)
    assert actions == []


def test_change_id_unchanged_comment_only(tmp_path):
    """Comment-only pass must thread the change id back unchanged."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, _BODY_WITH_APPENDIX)

    next_id, actions = apply_appendix_removal(str(src), str(out), 5000)
    assert next_id == 5000


def test_is_appendix_heading_matches_and_rejects():
    assert _is_appendix_heading("Appendix")
    assert _is_appendix_heading("Appendix A. Prompts")
    assert _is_appendix_heading("appendices")
    assert not _is_appendix_heading("The appendix contains data.")
    assert not _is_appendix_heading("Smith, J. (2020). A study.")
