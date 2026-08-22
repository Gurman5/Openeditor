"""Tests for the deterministic abbreviation pass — e.g. / i.e. / Fig.

The pass rewrites `e.g.`/`i.e.` missing the trailing comma (including after
brackets, dashes, or commas), normalises bare `eg`/`ie`, and expands
`Fig. N` to `Figure N`. Each change is emitted as a tracked
`<w:del>/<w:ins>` pair so the editor can accept or reject in Word.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from app.services.abbreviation_corrections import (
    _find_first_match,
    apply_abbreviation_corrections,
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


def _build_docx(path: Path, entries: list[tuple[str | None, str]]) -> None:
    """Build a docx where each entry is (style_or_None, text)."""
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


def _ins_texts(doc_root: etree._Element) -> list[str]:
    out: list[str] = []
    for ins in doc_root.iter(f"{WQ}ins"):
        for t in ins.iter(f"{WQ}t"):
            if t.text:
                out.append(t.text)
    return out


def _del_texts(doc_root: etree._Element) -> list[str]:
    return [
        (t.text or "")
        for t in doc_root.iter(f"{WQ}delText")
    ]


def _read_doc_root(path: Path) -> etree._Element:
    with zipfile.ZipFile(path, "r") as z:
        return etree.fromstring(z.read("word/document.xml"))


# ── Regex-level unit tests ──────────────────────────────────────────────────


def test_eg_followed_by_space_gets_comma():
    """`e.g.` followed by whitespace + word becomes `e.g.,`."""
    match = _find_first_match("for example, e.g. apples and oranges")
    assert match is not None
    start, end, replacement, label = match
    assert label == "eg_comma"
    assert replacement == "e.g.,"


def test_eg_after_open_paren_caught():
    match = _find_first_match("(e.g. apples)")
    assert match is not None
    assert match[3] == "eg_comma"


def test_eg_after_em_dash_caught():
    match = _find_first_match("see —e.g. apples")
    assert match is not None
    assert match[3] == "eg_comma"


def test_eg_after_comma_caught():
    match = _find_first_match("see, e.g. apples")
    assert match is not None
    assert match[3] == "eg_comma"


def test_eg_already_correct_left_alone():
    """`e.g.,` already has the comma — no match."""
    assert _find_first_match("for example, e.g., apples") is None


def test_bare_eg_gets_periods_and_comma():
    match = _find_first_match("see eg foo bar")
    assert match is not None
    assert match[3] == "bare_eg"
    assert match[2] == "e.g.,"


def test_eg_mid_word_not_matched():
    """`siege` and `eg` inside `regional` etc. must NOT match."""
    assert _find_first_match("the siege of Vienna") is None
    assert _find_first_match("regional disparities") is None


def test_ie_same_rules_as_eg():
    assert _find_first_match("(i.e. apples)")[3] == "ie_comma"
    assert _find_first_match("see, i.e. apples")[3] == "ie_comma"
    assert _find_first_match("see ie apples")[3] == "bare_ie"


def test_fig_with_number_replaced():
    match = _find_first_match("see Fig. 3 below")
    assert match is not None
    assert match[3] == "fig_expand"
    assert match[2] == "Figure"


def test_fig_lowercase_with_number_also_matched():
    """Per Joey's preference both `Fig.` and `fig.` followed by a digit
    should be normalised to `Figure`."""
    match = _find_first_match("see fig. 3 below")
    assert match is not None
    assert match[3] == "fig_expand"


def test_fig_without_number_not_matched():
    """`Fig.` followed by a word (not a digit) is left alone — Joey's
    answered preference gates lowercase on digit follow-up; we apply the
    same conservative gate to capital `Fig.` too."""
    assert _find_first_match("see Fig. below") is None


def test_fig_mid_word_not_matched():
    """`Configure` must not match the `fig.` part."""
    assert _find_first_match("Configure the system") is None


# ── End-to-end (docx round-trip) tests ──────────────────────────────────────


def test_apply_eg_emits_tracked_change(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [(None, "Authors compare baselines (e.g. ChatGPT) regularly.")])

    next_id, actions = apply_abbreviation_corrections(str(src), str(out), 1)
    assert next_id > 1
    assert any(a["rule"] == "eg_comma" for a in actions)

    doc_root = _read_doc_root(out)
    assert "e.g." in _del_texts(doc_root)
    assert "e.g.," in _ins_texts(doc_root)


def test_apply_fig_emits_tracked_change(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [(None, "Cross-validation results are reported in Fig. 3 below.")])

    _, actions = apply_abbreviation_corrections(str(src), str(out), 1)
    assert any(a["rule"] == "fig_expand" for a in actions)

    doc_root = _read_doc_root(out)
    assert "Fig." in _del_texts(doc_root)
    assert "Figure" in _ins_texts(doc_root)


def test_apply_references_section_skipped(tmp_path: Path):
    """A paragraph styled as a reference list entry must not be touched."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        src,
        [
            ("APA 7 Reference List Entry",
             "Author, A. (2020). Title (e.g. Vol. 1, see Fig. 1)."),
        ],
    )

    _, actions = apply_abbreviation_corrections(str(src), str(out), 1)
    assert actions == []


def test_apply_figure_caption_style_skipped(tmp_path: Path):
    """A `Figure Number` styled paragraph belongs to a caption — leave it."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [("Figure Number", "Fig. 3")])

    _, actions = apply_abbreviation_corrections(str(src), str(out), 1)
    assert actions == []


def test_apply_clean_doc_returns_empty_actions(tmp_path: Path):
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [(None, "A perfectly normal sentence with no abbreviations.")])

    _, actions = apply_abbreviation_corrections(str(src), str(out), 1)
    assert actions == []
    # Output file should still exist as a copy.
    assert out.exists()


def test_match_inside_direct_quotation_is_skipped(tmp_path: Path):
    """A `Fig. 3` reference INSIDE quoted text must not be expanded —
    direct quotations retain the source's original wording."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [(
        None,
        'The author wrote, "see Fig. 3 for details" in the preprint.',
    )])

    _, actions = apply_abbreviation_corrections(str(src), str(out), 1)
    assert actions == []


def test_match_outside_quote_is_still_applied_when_quote_present(tmp_path: Path):
    """An unquoted match in the same paragraph as a quoted (skipped)
    match must still be rewritten."""
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(src, [(
        None,
        'The author wrote "see Fig. 3" and then noted Fig. 4 separately.',
    )])

    _, actions = apply_abbreviation_corrections(str(src), str(out), 1)
    assert len(actions) == 1
    assert actions[0]["rule"] == "fig_expand"


def test_single_paragraph_caption_is_skipped_by_content_shape(tmp_path: Path):
    """Regression: a single-paragraph Figure caption styled as Normal
    must not be touched by mutating passes. The `should_skip_paragraph`
    helper now recognises the ``Figure N. <text>`` shape regardless of
    style, which prevents hyphen-strip and other defects inside
    captions.
    """
    src = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    # `Fig. 3 below` would normally rewrite to `Figure 3 below`. Inside
    # a caption paragraph it must NOT.
    _build_docx(src, [(
        None,
        "Figure 1. Two-stage design for the project. See Fig. 3 below for context.",
    )])

    _, actions = apply_abbreviation_corrections(str(src), str(out), 1)
    assert actions == []
