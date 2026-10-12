"""APA-08 abstract length rule: at most 250 words.

The JUTLP companion rule — "the abstract must fit lines 7-23 of the front
page (max 17 lines)" — was removed with the rest of the JUTLP front matter in
C-26. This file now covers the APA rule alone; the absence of the line-region
constants and the ``line_count`` payload is asserted explicitly so the rule
cannot creep back in unnoticed.
"""

from docx import Document

from app.domain.canonical_jultp_template import CANONICAL_STRUCTURE
from app.services.document_analysis_services import extract_abstract, load_paragraphs
from app.services.jutlp_validator import check_abstract
from app.services.output_generation_samfix import abstractFormatCheck, abstractFound

_FRONT = CANONICAL_STRUCTURE["front_page"]


def _parsed(found=True, word_count=0):
    return {"front_page": {"abstract": {"found": found, "word_count": word_count}}}


def _fp008(results):
    return next(r for r in results if r["rule_id"] == "FP008")


# ── canonical wiring ─────────────────────────────────────────────────────────

def test_rule_constants_match_template():
    assert _FRONT["abstract_max_words"] == 250


def test_line_region_constants_are_gone():
    """C-26 removed the JUTLP front-page line region. These keys must not
    return — a consumer reading them would crash or silently mis-report."""
    assert "abstract_line_region" not in _FRONT
    assert "abstract_max_lines" not in _FRONT
    assert "abstract_words_per_line_estimate" not in _FRONT


def test_practitioner_notes_keys_are_gone():
    """C-26 removed Practitioner Notes (APA-20)."""
    for key in (
        "practitioner_notes_heading",
        "practitioner_notes_style",
        "practitioner_notes_count",
    ):
        assert key not in _FRONT, f"{key} should have been removed"


# ── validator FP008 ──────────────────────────────────────────────────────────

def test_abstract_within_limit_passes():
    r = _fp008(check_abstract(_parsed(word_count=200)))
    assert r["status"] == "pass"


def test_abstract_at_the_limit_passes():
    r = _fp008(check_abstract(_parsed(word_count=250)))
    assert r["status"] == "pass"


def test_abstract_over_word_limit_fails():
    r = _fp008(check_abstract(_parsed(word_count=300)))
    assert r["status"] == "fail"
    assert "300 words" in r["message"]
    assert "250" in r["message"]


def test_long_abstract_with_hard_breaks_is_measured_in_words_only():
    """Regression guard for the retired line-region rule: a short abstract
    padded with manual line breaks is within the APA word limit and must pass.
    Under the old JUTLP rule this failed on estimated line count alone."""
    r = _fp008(check_abstract(_parsed(word_count=120)))
    assert r["status"] == "pass"
    assert "line" not in r["message"].lower()


def test_abstract_not_found_fails():
    r = _fp008(check_abstract(_parsed(found=False)))
    assert r["status"] == "fail"


# ── extract_abstract measures non-template (Normal) abstracts ────────────────

def test_normal_styled_abstract_is_measured(tmp_path):
    """Regression: an abstract that is NOT styled 'Front Page Text' (authors
    routinely leave it Normal) must still be counted — it was previously read
    as 0 words and never flagged."""
    doc = Document()
    doc.add_paragraph("Abstract", style="Heading 1")
    doc.add_paragraph(" ".join(["word"] * 260), style="Normal")
    doc.add_paragraph("Keywords: alpha; beta; gamma", style="Normal")
    doc.add_paragraph("Introduction", style="Heading 1")
    path = tmp_path / "doc.docx"
    doc.save(str(path))

    ab = extract_abstract(load_paragraphs(str(path)))
    assert ab["found"] is True
    assert ab["paragraph_count"] == 1          # keyword line excluded
    assert ab["word_count"] == 260             # over the 250 limit


def test_extract_abstract_no_longer_returns_line_count(tmp_path):
    doc = Document()
    doc.add_paragraph("Abstract", style="Heading 1")
    doc.add_paragraph("Short abstract sentence.", style="Normal")
    path = tmp_path / "doc.docx"
    doc.save(str(path))

    ab = extract_abstract(load_paragraphs(str(path)))
    assert "line_count" not in ab


def test_abstract_stops_at_introduction_heading(tmp_path):
    """The body (after Introduction) must not be swallowed into the abstract."""
    doc = Document()
    doc.add_paragraph("Abstract", style="Heading 1")
    doc.add_paragraph("Short abstract sentence.", style="Normal")
    doc.add_paragraph("Introduction", style="Heading 1")
    doc.add_paragraph(" ".join(["body"] * 500), style="Normal")
    path = tmp_path / "doc.docx"
    doc.save(str(path))

    ab = extract_abstract(load_paragraphs(str(path)))
    assert ab["paragraph_count"] == 1
    assert ab["word_count"] < 10               # only the abstract sentence


# ── Sam's abstract-length comment is standalone (survives comment de-dup) ─────

def _long_abstract_doc(tmp_path):
    doc = Document()
    doc.add_paragraph("A Study of Things")           # title
    doc.add_paragraph("Abstract", style="Heading 1")  # abstract heading (by text)
    doc.add_paragraph(" ".join(["word"] * 260))       # 260-word body (over limit)
    doc.add_paragraph("Keywords")
    doc.add_paragraph("Introduction", style="Heading 1")
    path = tmp_path / "doc.docx"
    doc.save(str(path))
    return str(path)


def test_abstract_length_comment_is_a_standalone_comment(tmp_path):
    """The length flag must be its OWN comment (not folded into the merge/style
    bundle) so the pipeline's Sam-comment de-dup can't drop it with the bundle."""
    path = _long_abstract_doc(tmp_path)
    plan = abstractFormatCheck(path, abstractFound(path))

    length_comments = [
        c for c in plan.get("comments", [])
        if c["message"].startswith("Abstract is too long")
    ]
    assert len(length_comments) == 1
    msg = length_comments[0]["message"]
    # standalone: not concatenated with the merge / style messages
    assert "Abstract merged" not in msg
    assert "Tracked style change" not in msg
    assert "250 words" in msg


def test_length_comment_has_no_line_region_wording(tmp_path):
    path = _long_abstract_doc(tmp_path)
    plan = abstractFormatCheck(path, abstractFound(path))
    msg = " ".join(c["message"] for c in plan.get("comments", []))
    assert "lines 7" not in msg
    assert "7 to 23" not in msg
    assert "JUTLP" not in msg


# ── Practitioner Notes must not be required or emitted ──────────────────────

def test_abstract_plan_never_schedules_a_practitioner_stub(tmp_path):
    """A manuscript with no Practitioner Notes must produce no stub request —
    that requirement (FP005/FP009/FP012) was deleted in C-26."""
    doc = Document()
    doc.add_paragraph("Abstract", style="Heading 1")
    doc.add_paragraph("A short abstract.", style="Normal")
    doc.add_paragraph("Keywords", style="Heading 1")
    doc.add_paragraph("Introduction", style="Heading 1")
    path = tmp_path / "doc.docx"
    doc.save(str(path))

    plan = abstractFormatCheck(str(path), abstractFound(str(path)))
    blob = repr(plan)
    assert "practitioner" not in blob.lower()


def test_front_page_summary_has_no_practitioner_keys(tmp_path):
    from app.services.document_analysis_services import front_page_summary

    doc = Document()
    doc.add_paragraph("Abstract", style="Heading 1")
    path = tmp_path / "doc.docx"
    doc.save(str(path))

    summary = front_page_summary(load_paragraphs(str(path)))
    assert "practitioner_notes_heading_found" not in summary
    assert "practitioner_notes_count" not in summary