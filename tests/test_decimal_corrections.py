"""Tests for the decimal-precision and comma-as-decimal checks."""

from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from app.services.decimal_corrections import (
    _COMMA_DECIMAL,
    _COMMA_DECIMAL_COMMENT,
    _EXCESS_DECIMAL,
    _PRECISION_COMMENT,
    apply_decimal_corrections,
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


def _build_docx(path: Path, paragraphs: list[tuple[str, str]] | list[str]) -> None:
    """Build a minimal docx. Items are either text or (style, text) tuples."""
    body_parts: list[str] = []
    for item in paragraphs:
        if isinstance(item, tuple):
            style, text = item
            ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
        else:
            text = item
            ppr = ""
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


def _read_doc_root(path: Path) -> etree._Element:
    with zipfile.ZipFile(path, "r") as z:
        return etree.fromstring(z.read("word/document.xml"))


def _read_comments_root(path: Path) -> etree._Element | None:
    with zipfile.ZipFile(path, "r") as z:
        if "word/comments.xml" not in z.namelist():
            return None
        return etree.fromstring(z.read("word/comments.xml"))


# ── Regex unit tests ────────────────────────────────────────────────────────


def test_excess_decimal_matches_three_or_more_places():
    assert _EXCESS_DECIMAL.findall("error rate of 0.123") == ["0.123"]
    assert _EXCESS_DECIMAL.findall("a value of 9.105") == ["9.105"]
    assert _EXCESS_DECIMAL.findall("we report 1.2345 here") == ["1.2345"]


def test_excess_decimal_skips_two_or_fewer_places():
    assert _EXCESS_DECIMAL.findall("9.10 percent") == []
    assert _EXCESS_DECIMAL.findall("p < 0.05") == []
    assert _EXCESS_DECIMAL.findall("just 1.2 there") == []


def test_excess_decimal_skips_version_strings_and_money():
    # Version 3.10.5 — 3.10 has 2 places, 10.5 has 1; nothing matches.
    assert _EXCESS_DECIMAL.findall("Python 3.10.5 was used") == []
    # The digit-guarded lookbehind/lookahead means 1.234 inside 1.234.5 is
    # not considered isolated.
    assert _EXCESS_DECIMAL.findall("see version 1.234.5 release notes") == []
    # $1,234.50 — only .50 (2 places) is considered.
    assert _EXCESS_DECIMAL.findall("the price was $1,234.50 each") == []


def test_comma_decimal_matches_one_or_two_digits_after_comma():
    assert _COMMA_DECIMAL.findall("about 36,1% of cases") == ["36,1"]
    assert _COMMA_DECIMAL.findall("we found 36,15 here") == ["36,15"]
    assert _COMMA_DECIMAL.findall("near 0,5 of the time") == ["0,5"]


def test_comma_decimal_skips_thousand_separators():
    assert _COMMA_DECIMAL.findall("a population of 1,000 people") == []
    assert _COMMA_DECIMAL.findall("at least 1,234 students") == []
    assert _COMMA_DECIMAL.findall("all 1,234,567 cases") == []
    # 36,123 — 3 digits after comma. Conservative path: skip.
    assert _COMMA_DECIMAL.findall("a count of 36,123 items") == []


def test_comma_decimal_in_mixed_paragraph():
    """The classic example: thousand separators and comma-decimals together."""
    text = "Of 1,234 students, 36,1% passed and 64,12 enrolled."
    matches = _COMMA_DECIMAL.findall(text)
    assert matches == ["36,1", "64,12"]


# ── End-to-end through apply_decimal_corrections ───────────────────────────


def test_precision_check_fires_once_for_first_occurrence(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        [
            "We report 0.123 in the first paragraph.",
            "Then a follow-up reports 0.456 with similar precision.",
            "And again, 0.789, just to be sure.",
        ],
    )

    next_id, actions = apply_decimal_corrections(str(inp), str(out), 1)

    precision = [a for a in actions if a["check"] == "precision"]
    assert len(precision) == 1
    assert precision[0]["value"] == "0.123"

    comments = _read_comments_root(out)
    assert comments is not None
    txt = "".join(t.text or "" for t in comments.iter(f"{WQ}t"))
    assert "Author Query 1." in txt
    assert "two decimal places in line with APA7" in txt


def test_precision_check_ignores_two_or_fewer_places(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    # The literal "<" must be escaped for the test's raw-XML helper.
    _build_docx(inp, ["The result was 9.10% and p &lt; 0.05."])

    _, actions = apply_decimal_corrections(str(inp), str(out), 1)

    assert actions == []
    assert _read_comments_root(out) is None


def test_comma_check_flags_every_occurrence(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        [
            "First, 36,1% reported A.",
            "Second, 21,7% reported B.",
            "Third, 2,4% reported C.",
        ],
    )

    _, actions = apply_decimal_corrections(str(inp), str(out), 1)

    commas = [a for a in actions if a["check"] == "comma_decimal"]
    assert len(commas) == 3
    assert {a["value"] for a in commas} == {"36,1", "21,7", "2,4"}


def test_comma_check_distinguishes_from_thousand_separator(tmp_path):
    """The example from the client's brief, end-to-end."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        [
            "Of 1,234 students, 36,1% passed and 64,12 enrolled.",
        ],
    )

    _, actions = apply_decimal_corrections(str(inp), str(out), 1)

    values = [a["value"] for a in actions]
    assert values == ["36,1", "64,12"]
    # 1,234 must be left alone.
    assert all("1,234" != v for v in values)


def test_excess_decimal_inside_quotation_is_skipped(tmp_path):
    """A `0.1234` inside `"..."` retains the source's precision."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        ['The author wrote "the coefficient was 0.1234" in their paper.'],
    )

    _, actions = apply_decimal_corrections(str(inp), str(out), 1)
    assert actions == []


def test_comma_decimal_inside_quotation_is_skipped(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        ['Participant said "36,1% of cases were positive" in the interview.'],
    )

    _, actions = apply_decimal_corrections(str(inp), str(out), 1)
    assert actions == []


def test_match_outside_quote_still_flagged_when_quote_present(tmp_path):
    """Unquoted comma-decimal in the same paragraph as a quoted one
    must still be flagged."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        ['Author wrote "36,1% positive" but in our data 21,7% reported A.'],
    )

    _, actions = apply_decimal_corrections(str(inp), str(out), 1)
    values = [a["value"] for a in actions if a["check"] == "comma_decimal"]
    assert values == ["21,7"]


def test_skip_styles_are_respected(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(
        inp,
        [
            ("Heading 1", "Section 0.123"),  # heading: skipped
            ("APA 7 Reference List Entry", "Smith, J. (2024). 0.001 doi:10.123/foo"),  # reference: skipped
            "Body text reports 0.123 here.",  # body: this is the first matched occurrence
        ],
    )

    _, actions = apply_decimal_corrections(str(inp), str(out), 1)

    precision = [a for a in actions if a["check"] == "precision"]
    assert len(precision) == 1
    # Confirm the comment anchored to body, not the heading or reference.
    root = _read_doc_root(out)
    body_paras = [el for el in root.find(f"{WQ}body") if el.tag == f"{WQ}p"]
    # The third paragraph (body) should now contain a commentRangeStart.
    assert body_paras[2].find(f".//{WQ}commentRangeStart") is not None
    assert body_paras[0].find(f".//{WQ}commentRangeStart") is None
    assert body_paras[1].find(f".//{WQ}commentRangeStart") is None


def test_comments_use_author_query_numbering(tmp_path):
    """Comment text should follow the 'Author Query N. ...' format."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(inp, ["A 36,1% drop and a 0.123 score."])

    _, actions = apply_decimal_corrections(str(inp), str(out), 1)

    assert len(actions) == 2
    comments = _read_comments_root(out)
    assert comments is not None
    rendered = []
    for c in comments.findall(f"{WQ}comment"):
        rendered.append("".join(t.text or "" for t in c.iter(f"{WQ}t")))
    # Both comments include the bold-prefix "Author Query N." text.
    assert any(r.startswith("Author Query 1.") for r in rendered)
    assert any(r.startswith("Author Query 2.") for r in rendered)


def test_comment_id_continues_from_existing_comments(tmp_path):
    """A docx that already has comments (e.g., from earlier passes) should
    have new comments numbered starting at max+1."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"

    existing_comments = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:comments xmlns:w="{W}">'
        f'<w:comment w:id="3" w:author="Prev" w:date="2024-01-01T00:00:00Z" w:initials="P">'
        f'<w:p><w:r><w:t>Prior comment</w:t></w:r></w:p>'
        f'</w:comment>'
        f'</w:comments>'
    ).encode("utf-8")
    body = '<w:p><w:r><w:t>The result of 0.555 was striking.</w:t></w:r></w:p>'
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>'
    ).encode("utf-8")
    rels_doc = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="rIdComments" '
        b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" '
        b'Target="comments.xml"/>'
        b'</Relationships>'
    )
    ct_with_comments = _MIN_CT.replace(
        b"</Types>",
        b'<Override PartName="/word/comments.xml" '
        b'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>'
        b"</Types>",
    )
    with zipfile.ZipFile(inp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct_with_comments)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", rels_doc)
        z.writestr("word/document.xml", doc)
        z.writestr("word/comments.xml", existing_comments)

    _, actions = apply_decimal_corrections(str(inp), str(out), 1)

    assert len(actions) == 1
    assert actions[0]["comment_id"] == 4  # 3 + 1


def test_no_findings_returns_clean_pass_through(tmp_path):
    """When nothing matches, the output is byte-equivalent in content and
    no comments file is added."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx(inp, ["Nothing to flag here, just a 9.10 figure."])

    _, actions = apply_decimal_corrections(str(inp), str(out), 1)

    assert actions == []
    assert _read_comments_root(out) is None


def test_constants_export_client_supplied_text():
    # Sanity: the comment text strings are the client-approved wording.
    assert "two decimal places in line with APA7" in _PRECISION_COMMENT
    assert "comma" in _COMMA_DECIMAL_COMMENT.lower()
