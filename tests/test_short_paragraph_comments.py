from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from app.services.short_paragraph_comments import apply_short_paragraph_comments

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


def _build_zoned_docx(path: Path, entries: list[tuple[str | None, str]]) -> None:
    body_parts = []
    for style, text in entries:
        if style is None:
            ppr = ""
        else:
            ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
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


def _read_comments_root(path: Path) -> etree._Element | None:
    with zipfile.ZipFile(path, "r") as z:
        if "word/comments.xml" not in z.namelist():
            return None
        return etree.fromstring(z.read("word/comments.xml"))


def _comment_texts(path: Path) -> list[str]:
    root = _read_comments_root(path)
    if root is None:
        return []
    texts: list[str] = []
    for comment in root.findall(f"{WQ}comment"):
        texts.append("".join(t.text or "" for t in comment.iter(f"{WQ}t")))
    return texts


def test_adds_comments_for_paragraphs_with_under_three_sentences(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "One sentence only."),
            (None, "Sentence one. Sentence two."),
            (None, "Sentence one. Sentence two. Sentence three."),
        ],
    )

    next_id, actions = apply_short_paragraph_comments(str(inp), str(out), next_change_id=7)

    assert next_id == 7
    assert len(actions) == 2
    assert [a["sentence_count"] for a in actions] == [1, 2]

    comments = _comment_texts(out)
    assert len(comments) == 2
    assert all("at least three sentences" in txt for txt in comments)


def test_skips_title_heading_and_outside_zone(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Article Title", "AI in Education"),
            ("Heading 1", "Introduction"),
            (None, "Short body paragraph."),
            ("Heading 1", "References"),
            (None, "Short reference line."),
        ],
    )

    _, actions = apply_short_paragraph_comments(str(inp), str(out))

    assert len(actions) == 1
    assert actions[0]["sentence_count"] == 1


def test_no_changes_when_every_paragraph_has_three_or_more_sentences(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "First sentence. Second sentence. Third sentence."),
            (None, "Alpha. Beta. Gamma."),
        ],
    )

    _, actions = apply_short_paragraph_comments(str(inp), str(out))

    assert actions == []
    assert _read_comments_root(out) is None
