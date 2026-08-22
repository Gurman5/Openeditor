"""Tests for digit-to-word tracked-change corrections.

These tests build minimal docx fixtures programmatically to exercise the
exclusion logic without needing real Word files.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from app.services.number_word_corrections import apply_number_word_corrections

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


def _build_docx_with_paragraph(path: Path, text: str, style: str | None = None) -> None:
    """Build a docx with a single paragraph carrying `text`."""
    if style:
        ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
    else:
        ppr = ""
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>'
        f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'
        f'</w:body></w:document>'
    ).encode("utf-8")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS)
        z.writestr("word/document.xml", doc)


def _read_visible_text(path: Path) -> str:
    """Reconstruct the post-correction visible text.

    Walks the document.xml and concatenates the text of every run that is NOT
    inside a `w:del` wrapper (i.e. the text that the editor would see if they
    accepted every tracked change).
    """
    with zipfile.ZipFile(path, "r") as z:
        root = etree.fromstring(z.read("word/document.xml"))
    out: list[str] = []
    for r in root.iter(f"{WQ}r"):
        parent = r.getparent()
        if parent is not None and parent.tag == f"{WQ}del":
            continue
        for t in r.findall(f"{WQ}t"):
            out.append(t.text or "")
    return "".join(out)


def _count_changes(path: Path) -> int:
    with zipfile.ZipFile(path, "r") as z:
        root = etree.fromstring(z.read("word/document.xml"))
    return len(root.findall(f".//{WQ}ins"))


# ── Positive cases ──────────────────────────────────────────────────────────


def test_replaces_simple_digit_in_prose(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(inp, "We surveyed 9 participants in the study.")

    next_id, made = apply_number_word_corrections(str(inp), str(out), 1)

    assert len(made) == 1
    assert made[0]["original"] == "9"
    assert made[0]["replacement"] == "nine"
    assert _read_visible_text(out) == "We surveyed nine participants in the study."


def test_replaces_multiple_digits_in_one_paragraph(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(
        inp,
        "We invited 5 students and 3 staff to participate.",
    )

    next_id, made = apply_number_word_corrections(str(inp), str(out), 1)

    assert len(made) == 2
    text = _read_visible_text(out)
    assert "five students" in text
    assert "three staff" in text


def test_each_digit_zero_through_nine_is_spelled_out(tmp_path):
    expected = {
        "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
        "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
    }
    for digit, word in expected.items():
        inp = tmp_path / f"in_{digit}.docx"
        out = tmp_path / f"out_{digit}.docx"
        _build_docx_with_paragraph(inp, f"There were {digit} cases observed.")

        _, made = apply_number_word_corrections(str(inp), str(out), 1)

        assert len(made) == 1, f"digit {digit} should have been replaced"
        assert made[0]["replacement"] == word


# ── Exclusion: brackets ─────────────────────────────────────────────────────


def test_skips_digit_inside_parentheses(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(inp, "The result (n = 9) supports the hypothesis.")

    _, made = apply_number_word_corrections(str(inp), str(out), 1)

    assert made == []
    assert _count_changes(out) == 0


def test_skips_digit_inside_square_brackets(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(inp, "See reference [3] for details.")

    _, made = apply_number_word_corrections(str(inp), str(out), 1)

    assert made == []


# ── Exclusion: decimals and multi-digit numbers ─────────────────────────────


def test_skips_decimals(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(
        inp,
        "The error rate was 9.10% with a standard deviation of 0.05.",
    )

    _, made = apply_number_word_corrections(str(inp), str(out), 1)

    assert made == []


def test_skips_multi_digit_numbers(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(inp, "We surveyed 15 students and 100 staff.")

    _, made = apply_number_word_corrections(str(inp), str(out), 1)

    assert made == []


# ── Exclusion: label words ──────────────────────────────────────────────────


def test_skips_after_label_words(tmp_path):
    cases = [
        "See Section 3 for the full method.",
        "The data appears in Table 2.",
        "Figure 5 shows the distribution.",
        "Step 4 of the procedure was repeated.",
        "Refer to Appendix 1.",
        "On page 7 of the report.",
        "In Chapter 8 of the textbook.",
    ]
    for text in cases:
        inp = tmp_path / "in.docx"
        out = tmp_path / "out.docx"
        _build_docx_with_paragraph(inp, text)

        _, made = apply_number_word_corrections(str(inp), str(out), 1)

        assert made == [], f"label-word case should be skipped: {text!r}"


def test_skips_after_stat_labels(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(inp, "Across the sample n = 8 was sufficient.")

    _, made = apply_number_word_corrections(str(inp), str(out), 1)

    assert made == []


# ── Exclusion: units of measurement ─────────────────────────────────────────


def test_skips_digit_followed_by_unit(tmp_path):
    cases = [
        "The temperature rose by 5°C overnight.",
        "Participants walked 3 km each session.",
        "Each trial lasted 8 min on average.",
        "Memory usage stayed under 2 GB.",
        "Accuracy was 7% better than baseline.",
    ]
    for text in cases:
        inp = tmp_path / "in.docx"
        out = tmp_path / "out.docx"
        _build_docx_with_paragraph(inp, text)

        _, made = apply_number_word_corrections(str(inp), str(out), 1)

        assert made == [], f"unit case should be skipped: {text!r}"


# ── Exclusion: dates ────────────────────────────────────────────────────────


def test_skips_date_patterns(tmp_path):
    cases = [
        "The session was held on 5 May 2024.",
        "Data collection ran until May 5, 2024.",
        "Submitted on 7/2024 for review.",
    ]
    for text in cases:
        inp = tmp_path / "in.docx"
        out = tmp_path / "out.docx"
        _build_docx_with_paragraph(inp, text)

        _, made = apply_number_word_corrections(str(inp), str(out), 1)

        assert made == [], f"date case should be skipped: {text!r}"


# ── Exclusion: hyphenated compounds ─────────────────────────────────────────


def test_skips_hyphenated_compounds(tmp_path):
    cases = [
        "We recruited 5-year-old children for the study.",
        "A 9-point Likert scale was used.",
    ]
    for text in cases:
        inp = tmp_path / "in.docx"
        out = tmp_path / "out.docx"
        _build_docx_with_paragraph(inp, text)

        _, made = apply_number_word_corrections(str(inp), str(out), 1)

        assert made == [], f"hyphen case should be skipped: {text!r}"


# ── Exclusion: sentence start ───────────────────────────────────────────────


def test_skips_digit_at_sentence_start(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(
        inp,
        "The study had two phases. 5 participants completed both.",
    )

    _, made = apply_number_word_corrections(str(inp), str(out), 1)

    # Sentence-initial digit is left alone (capitalisation handled by human).
    assert made == []


# ── Exclusion: paragraph styles ─────────────────────────────────────────────


def test_skips_heading_paragraphs(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(inp, "5 Key Findings", style="Heading 1")

    _, made = apply_number_word_corrections(str(inp), str(out), 1)

    assert made == []


def test_skips_reference_list_paragraphs(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(
        inp,
        "Smith, J. (2024). 5 ways to improve learning. Journal of Education, 12, 1-5.",
        style="APA 7 Reference List Entry",
    )

    _, made = apply_number_word_corrections(str(inp), str(out), 1)

    assert made == []


def test_skips_author_affiliations_style_id(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(
        inp,
        "a Affiliation 1; b Affiliation 2",
        style="AuthorAffiliations",
    )

    _, made = apply_number_word_corrections(str(inp), str(out), 1)

    assert made == []
    assert _read_visible_text(out) == "a Affiliation 1; b Affiliation 2"
    assert _count_changes(out) == 0


# ── Tracked-change shape ────────────────────────────────────────────────────


def test_emits_del_ins_pair_with_correct_text(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(inp, "We tested 4 hypotheses.")

    apply_number_word_corrections(str(inp), str(out), 1)

    with zipfile.ZipFile(out, "r") as z:
        root = etree.fromstring(z.read("word/document.xml"))

    dels = root.findall(f".//{WQ}del")
    ins = root.findall(f".//{WQ}ins")
    assert len(dels) == 1
    assert len(ins) == 1
    del_text = "".join(t.text or "" for t in dels[0].iter(f"{WQ}delText"))
    ins_text = "".join(t.text or "" for t in ins[0].iter(f"{WQ}t"))
    assert del_text == "4"
    assert ins_text == "four"


def test_digit_inside_direct_quotation_is_skipped(tmp_path):
    """A digit INSIDE quoted text retains the source's form."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(
        inp,
        'The author wrote "we surveyed 9 participants" in the paper.',
    )

    _, made = apply_number_word_corrections(str(inp), str(out), 1)
    assert made == []


def test_digit_outside_quote_still_replaced_when_quote_present(tmp_path):
    """Unquoted digit in a paragraph that also has a quoted digit must
    still be spelled out."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_paragraph(
        inp,
        'Author wrote "we surveyed 9 participants" but we surveyed 8 others.',
    )

    _, made = apply_number_word_corrections(str(inp), str(out), 1)
    assert len(made) == 1
    assert made[0]["original"] == "8"
    assert made[0]["replacement"] == "eight"
