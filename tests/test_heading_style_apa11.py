"""C-23 benchmarks: APA heading levels 1-5 (APA-11).

Replaces the old `CENTER_ALIGNED_HEADING_TEXTS` / `LEFT_ALIGNED_HEADING_TEXTS`
text-matching policy, which guessed a heading's level from its *text* and wrote
a paragraph-level alignment per match. Text matching cannot tell Level 1 from
Level 2, so it centred every listed section heading regardless of level.

Two things are asserted here:

  * the heading *style definitions* in `word/styles.xml` carry APA-11 values for
    all five levels, and
  * no heading paragraph carries a direct `w:jc` that would override them.

`tests/test_heading_restyle_formatting.py` is NOT the benchmark for this ticket
- it only exercises `_apply_tracked_style_change` (Normal -> Heading promotion)
on detached XML elements and never reads `word/styles.xml`, so it would pass
even against a broken C-23.
"""
import os
import shutil
import sys
import tempfile
import zipfile

import pytest
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.output_generation_samfix import (  # noqa: E402
    _apply_apa_heading_styles,
    _apply_heading_2_title_case,
    _strip_heading_direct_jc,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"

# APA-11: L1 centred bold, L2 flush-left bold, L3 flush-left bold-italic,
# L4 indented bold, L5 indented bold-italic. All Calibri, line=480, after=0,
# keepNext, and no break before the following paragraph.
APA11 = {
    1: {"jc": "center", "bold": True, "italic": False, "left": None},
    2: {"jc": "left", "bold": True, "italic": False, "left": None},
    3: {"jc": "left", "bold": True, "italic": True, "left": None},
    4: {"jc": "left", "bold": True, "italic": False, "left": "720"},
    5: {"jc": "left", "bold": True, "italic": True, "left": "720"},
}

HEADING_STYLE_IDS = {n: f"Heading{n}" for n in range(1, 6)}


def _flag_on(element):
    """A Word boolean element counts as ON when present with val != 0."""
    if element is None:
        return False
    val = element.get(f"{WQ}val")
    return val not in ("0", "false", "off")


def _read_styles(docx_path):
    with zipfile.ZipFile(docx_path, "r") as z:
        styles_root = etree.fromstring(z.read("word/styles.xml"))
        doc_root = etree.fromstring(z.read("word/document.xml"))
    return styles_root, doc_root


def _find_style(styles_root, style_id):
    for style_el in styles_root.findall(f"{WQ}style"):
        if style_el.get(f"{WQ}styleId") == style_id:
            return style_el
    return None


def _heading_paragraphs(doc_root):
    """Yield (style_id, element) for every paragraph with a Heading 1-5 style."""
    body = doc_root.find(f"{WQ}body")
    for para in body.iter(f"{WQ}p"):
        p_style = para.find(f"{WQ}pPr/{WQ}pStyle")
        if p_style is None:
            continue
        style_id = p_style.get(f"{WQ}val", "")
        if style_id.startswith("Heading") and style_id[-1:].isdigit():
            yield style_id, para


@pytest.fixture
def synthetic_doc(tmp_path):
    """A docx carrying Word's *default* Heading 1-5 definitions.

    Word's defaults are deliberately wrong for APA-11 (no `jc` at all, `before`
    != 0, a hanging indent), so any test that still sees them after the pass
    proves the template styles were never copied in.
    """
    path = tmp_path / "input.docx"
    doc = Document()
    for level in range(1, 6):
        doc.add_paragraph(f"level {level} heading", style=f"Heading {level}")
    doc.save(str(path))
    return path


def test_word_default_heading_styles_actually_differ_from_apa11(synthetic_doc):
    """Guards the benchmark itself: without this the asserts below are vacuous."""
    styles_root, _ = _read_styles(synthetic_doc)
    h1 = _find_style(styles_root, "Heading1")
    assert h1 is not None
    assert h1.find(f"{WQ}pPr/{WQ}jc") is None, "Word default Heading 1 has no jc"
    spacing = h1.find(f"{WQ}pPr/{WQ}spacing")
    assert spacing is None or spacing.get(f"{WQ}line") != "480", (
        "Word default Heading 1 is not double spaced"
    )


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
def test_heading_style_matches_apa11(synthetic_doc, level):
    out = synthetic_doc.parent / "out.docx"
    _apply_apa_heading_styles(str(synthetic_doc), str(out))

    styles_root, _ = _read_styles(out)
    style_el = _find_style(styles_root, HEADING_STYLE_IDS[level])
    assert style_el is not None, f"Heading {level} missing after pass"

    expected = APA11[level]
    p_pr = style_el.find(f"{WQ}pPr")
    assert p_pr is not None, f"Heading {level} has no pPr"

    jc = p_pr.find(f"{WQ}jc")
    assert jc is not None, f"Heading {level} has no jc"
    assert jc.get(f"{WQ}val") == expected["jc"], (
        f"Heading {level} jc = {jc.get(f'{WQ}val')}, want {expected['jc']}"
    )

    spacing = p_pr.find(f"{WQ}spacing")
    assert spacing is not None, f"Heading {level} has no spacing"
    assert spacing.get(f"{WQ}line") == "480", f"Heading {level} not double spaced"
    assert spacing.get(f"{WQ}after") in (None, "0"), f"Heading {level} after != 0"
    assert spacing.get(f"{WQ}before") in (None, "0"), (
        f"Heading {level} still carries Word's before spacing"
    )

    # APA-11: heading must not be orphaned from its first body paragraph.
    assert p_pr.find(f"{WQ}keepNext") is not None, f"Heading {level} lost keepNext"

    ind = p_pr.find(f"{WQ}ind")
    if expected["left"] is None:
        # Levels 1-3 sit flush to the margin; Word's default hanging indent
        # must not survive.
        assert ind is None or ind.get(f"{WQ}left") in (None, "0"), (
            f"Heading {level} has a non-zero left indent"
        )
        assert ind is None or ind.get(f"{WQ}hanging") is None, (
            f"Heading {level} still has Word's hanging indent"
        )
    else:
        assert ind is not None, f"Heading {level} has no ind"
        assert ind.get(f"{WQ}left") == expected["left"], (
            f"Heading {level} ind left = {ind.get(f'{WQ}left')}, want {expected['left']}"
        )

    r_pr = style_el.find(f"{WQ}rPr")
    assert r_pr is not None, f"Heading {level} has no rPr"
    assert _flag_on(r_pr.find(f"{WQ}b")) is expected["bold"], (
        f"Heading {level} bold wrong"
    )
    assert _flag_on(r_pr.find(f"{WQ}i")) is expected["italic"], (
        f"Heading {level} italic wrong"
    )

    # C-27 / D2: headings render in the body typeface.
    fonts = r_pr.find(f"{WQ}rFonts")
    assert fonts is not None, f"Heading {level} has no rFonts"
    assert fonts.get(f"{WQ}ascii") == "Calibri", (
        f"Heading {level} font = {fonts.get(f'{WQ}ascii')}, want Calibri"
    )


def test_direct_jc_is_stripped_from_headings(synthetic_doc):
    """A paragraph-level alignment overrides the style, so it has to go."""
    doc = Document(str(synthetic_doc))
    doc.paragraphs[1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[3].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    doc.save(str(synthetic_doc))

    out = synthetic_doc.parent / "out.docx"
    _apply_apa_heading_styles(str(synthetic_doc), str(out))

    _, doc_root = _read_styles(out)
    seen = 0
    for style_id, para in _heading_paragraphs(doc_root):
        seen += 1
        assert para.find(f"{WQ}pPr/{WQ}jc") is None, (
            f"{style_id} kept a direct jc override"
        )
    assert seen == 5, f"expected 5 heading paragraphs, saw {seen}"


def test_level_two_heading_is_not_centred_by_its_text(synthetic_doc):
    """The regression the old text-matching policy caused.

    "Literature" sits in the old CENTER_ALIGNED_HEADING_TEXTS list, so the old
    pass wrote `jc=center` onto it *regardless of heading level*. On APA the
    same string as a Level 2 heading must stay flush-left.
    """
    doc = Document(str(synthetic_doc))
    doc.paragraphs[1].text = "Literature"
    doc.save(str(synthetic_doc))

    out = synthetic_doc.parent / "out.docx"
    _apply_apa_heading_styles(str(synthetic_doc), str(out))

    _, doc_root = _read_styles(out)
    h2 = [p for sid, p in _heading_paragraphs(doc_root) if sid == "Heading2"]
    assert len(h2) == 1
    assert h2[0].find(f"{WQ}pPr/{WQ}jc") is None, "Level 2 heading was centred"

    styles_root, _ = _read_styles(out)
    jc = _find_style(styles_root, "Heading2").find(f"{WQ}pPr/{WQ}jc")
    assert jc.get(f"{WQ}val") == "left"


def test_body_paragraphs_keep_their_direct_alignment(synthetic_doc):
    """Regression guard for C-22: only heading paragraphs are stripped."""
    doc = Document(str(synthetic_doc))
    # A heading with a direct override so the strip has something to remove,
    # plus a body paragraph that must be left alone.
    doc.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    body = doc.add_paragraph("body text")
    body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    doc.save(str(synthetic_doc))

    out = synthetic_doc.parent / "out.docx"
    changed = _strip_heading_direct_jc(str(synthetic_doc), str(out))
    assert changed is True, "heading jc strip reported no change"

    _, doc_root = _read_styles(out)
    body_paras = [
        p for p in doc_root.find(f"{WQ}body").iter(f"{WQ}p")
        if p.find(f"{WQ}pPr/{WQ}pStyle") is None
    ]
    assert body_paras, "no plain body paragraph found"
    kept = [p for p in body_paras if p.find(f"{WQ}pPr/{WQ}jc") is not None]
    assert kept, "body paragraph alignment was stripped too"


def test_strip_is_a_no_op_without_heading_jc(synthetic_doc):
    out = synthetic_doc.parent / "out.docx"
    assert _strip_heading_direct_jc(str(synthetic_doc), str(out)) is False
    assert not out.exists(), "no-op must not write an output file"


def test_heading_two_text_is_title_cased(tmp_path):
    """APA-11: heading text is title case (folded into this benchmark per C-23).

    Runs after the style pass in `build_edited_document`, so the heading the
    styles restyle is also the heading whose wording gets normalised.
    """
    path = tmp_path / "in.docx"
    doc = Document()
    doc.add_paragraph("an empirical study of graph databases", style="Heading 2")
    doc.save(str(path))

    out = tmp_path / "out.docx"
    assert _apply_heading_2_title_case(str(path), str(out)) is True
    assert Document(str(out)).paragraphs[0].text == (
        "An Empirical Study of Graph Databases"
    )


def test_heading_styles_pass_is_no_op_when_already_apa(tmp_path):
    """Idempotence: a second run must not rewrite what is already correct."""
    src = tmp_path / "src.docx"
    first = tmp_path / "first.docx"
    second = tmp_path / "second.docx"

    doc = Document()
    for level in range(1, 6):
        doc.add_paragraph(f"level {level} heading", style=f"Heading {level}")
    doc.save(str(src))

    assert _apply_apa_heading_styles(str(src), str(first)) is True
    assert _apply_apa_heading_styles(str(first), str(second)) is False
    assert second.exists() is False, "second run should not rewrite the file"
