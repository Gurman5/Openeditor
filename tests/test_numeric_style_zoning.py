"""Regression tests for the numeric-style-id ordering bug: documents converted
from Google Docs/Word give heading styles numeric ids ("3" not "Heading1"), so
style-name checks (``style.startswith("Heading")`` / ``in ("Heading 1",…)``)
silently failed — collapsing front/body/outside zoning and disabling APA-7
reference reformatting."""

from lxml import etree

from app.services.document_zones import (
    heading_zone_transition,
    initial_zone,
    iter_paragraphs_with_zone,
)
from app.services.reference_format_corrections import _collect_ref_paragraphs

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"


def _doc_root(paras):
    """paras: list of (style_id, text)."""
    body = "".join(
        f'<w:p><w:pPr><w:pStyle w:val="{sid}"/></w:pPr>'
        f'<w:r><w:t>{text}</w:t></w:r></w:p>'
        for sid, text in paras
    )
    xml = (
        f'<w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>'
    )
    return etree.fromstring(xml.encode())


# ── zoning ───────────────────────────────────────────────────────────────────

def test_transition_trusts_heading_text_with_numeric_style():
    # Numeric style id "3"/"4" (not "Heading…") must still transition on an
    # exact transition-heading text match.
    assert heading_zone_transition("3", "1. Introduction", "front") == "body"
    assert heading_zone_transition("4", "References", "body") == "outside"
    # A non-heading body paragraph must NOT transition.
    assert heading_zone_transition("Normal", "We introduce the topic here.", "front") == "front"


def test_initial_zone_front_with_numeric_intro():
    root = _doc_root([
        ("3", "A Title"),
        ("3", "1. Introduction"),
        ("1", "Body."),
    ])
    assert initial_zone(root) == "front"


def test_full_zoning_split_with_numeric_styles():
    root = _doc_root([
        ("1", "A Title"),            # front
        ("1", "Abstract"),
        ("1", "Some abstract text."),
        ("3", "1. Introduction"),    # body starts
        ("1", "Intro body."),
        ("3", "5. Conclusion"),
        ("1", "Conclusion body."),
        ("3", "References"),         # outside starts
        ("1", "Author, A. (2020). A work. Journal."),
    ])
    zones = [z for _, z in iter_paragraphs_with_zone(root)]
    assert "front" in zones and "body" in zones and "outside" in zones
    # the References entry must be in the 'outside' zone (so it is skipped by
    # body-text passes like decimal/number-word/acronym checks)
    assert zones[-1] == "outside"


# ── reference reformatting ────────────────────────────────────────────────────

def test_collect_ref_paragraphs_with_numeric_heading_style():
    body = _doc_root([
        ("3", "References"),  # numeric style id, name resolves to "heading 1"
        ("1", "Adams, B. (2020). A study. Journal of Things, 1(1), 1-10."),
        ("1", "Brown, C. (2019). Another study. Journal of Stuff, 2(2), 20-30."),
    ]).find(f"{WQ}body")
    paras = [p for p in body if p.tag == f"{WQ}p"]
    style_names = {"3": "heading 1", "1": "normal"}

    found = _collect_ref_paragraphs(paras, style_names)
    assert len(found) == 2  # was 0 before the fix (heading not recognised)


def test_collect_ref_paragraphs_without_style_map_falls_back_to_friendly():
    # Friendly style ids keep working with no map (back-compat).
    body = _doc_root([
        ("Heading1", "References"),
        ("1", "Adams, B. (2020). A study. Journal, 1(1), 1-10."),
    ]).find(f"{WQ}body")
    paras = [p for p in body if p.tag == f"{WQ}p"]
    assert len(_collect_ref_paragraphs(paras)) == 1
