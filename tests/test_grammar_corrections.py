"""Tests for the grammar-corrections LLM pass.

We stub ``call_llm_json`` so the tests are deterministic and offline.
Focus is on the post-LLM filtering rules — these run after the model
returns and discard edits that violate the journal's hard-no list.
"""

from __future__ import annotations

import zipfile

from docx import Document
from lxml import etree

from app.services import grammar_corrections as gc
from app.services.grammar_corrections import (
    WQ,
    W,
    apply_contingent_grammar_comments,
    get_grammar_corrections,
)

_LONG_PARA = (
    "The participants completed a comprehensive survey designed to "
    "measure attitudes toward collaborative learning across a twelve-week "
    "semester block in higher education."
)


def _make_doc(tmp_path, paragraphs):
    path = tmp_path / "in.docx"
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    doc.save(path)
    return str(path)


def _stub_llm(corrections):
    def _call(system_prompt, user_prompt, response_schema, model=None):
        return {"content": {"corrections": list(corrections)}}
    return _call


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


def _build_min_docx(path, paragraph_xml: str) -> None:
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{paragraph_xml}</w:body></w:document>'
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", _MIN_RELS_DOC)
        z.writestr("word/document.xml", doc)


def _comments_text(path) -> str:
    with zipfile.ZipFile(path, "r") as z:
        if "word/comments.xml" not in z.namelist():
            return ""
        root = etree.fromstring(z.read("word/comments.xml"))
    return "".join(t.text or "" for t in root.iter(f"{WQ}t"))


def test_hyphen_strip_edit_is_filtered_out(monkeypatch, tmp_path):
    """Regression: the LLM proposed `Two-stage → Twostage`. Without the
    post-filter the hyphen was silently dropped from the manuscript."""
    monkeypatch.setattr(
        gc, "call_llm_json",
        _stub_llm([
            {"original": "Two-stage", "replacement": "Twostage", "reason": "compound"},
        ]),
    )
    path = _make_doc(tmp_path, [_LONG_PARA])
    out = get_grammar_corrections(path)
    assert out == []


def test_hyphen_strip_edit_with_case_flip_also_filtered(monkeypatch, tmp_path):
    """Companion case: `Evidences-Based → evidencesbased`. The
    case-insensitive compare in the new guard catches this too."""
    monkeypatch.setattr(
        gc, "call_llm_json",
        _stub_llm([
            {"original": "Evidences-Based", "replacement": "evidencesbased", "reason": "compound"},
        ]),
    )
    path = _make_doc(tmp_path, [_LONG_PARA])
    out = get_grammar_corrections(path)
    assert out == []


def test_legitimate_edit_that_keeps_the_hyphen_passes(monkeypatch, tmp_path):
    """An edit that genuinely fixes a different word and KEEPS the
    hyphen must still survive the filter. We use a lower-case
    `two-stage` so the unrelated proper-noun-correction guard doesn't
    pre-empt the test (it flags any word starting with a capital
    letter that isn't in a known sentence-start list)."""
    monkeypatch.setattr(
        gc, "call_llm_json",
        _stub_llm([
            {"original": "two-stage interveiw", "replacement": "two-stage interview", "reason": "typo"},
        ]),
    )
    path = _make_doc(tmp_path, [_LONG_PARA])
    out = get_grammar_corrections(path)
    assert len(out) == 1
    assert out[0]["replacement"] == "two-stage interview"


def test_edit_with_no_hyphens_anywhere_passes_unchanged(monkeypatch, tmp_path):
    """The hyphen guard must only fire when at least one side actually
    has a hyphen — otherwise it would suppress unrelated edits."""
    monkeypatch.setattr(
        gc, "call_llm_json",
        _stub_llm([
            {"original": "the data was", "replacement": "the data were", "reason": "subj-verb"},
        ]),
    )
    path = _make_doc(tmp_path, [_LONG_PARA])
    out = get_grammar_corrections(path)
    assert len(out) == 1
    assert out[0]["replacement"] == "the data were"


def test_au_to_us_spelling_edits_are_filtered(monkeypatch, tmp_path):
    monkeypatch.setattr(
        gc, "call_llm_json",
        _stub_llm([
            {"original": "organised", "replacement": "organized", "reason": "spelling"},
            {"original": "licence", "replacement": "license", "reason": "spelling"},
        ]),
    )
    path = _make_doc(
        tmp_path,
        ["The organised licence conditions were reviewed by the committee."],
    )
    assert get_grammar_corrections(path) == []


def test_au_to_us_guard_catches_derived_spellings():
    pairs = [
        ("underutilised", "underutilized"),
        ("disorganisation", "disorganization"),
        ("anonymised", "anonymized"),
        ("empathise", "empathize"),
        ("Lemmatisation", "Lemmatization"),
        ("unrecognised", "unrecognized"),
        ("behaviour", "behavior"),
    ]
    for original, replacement in pairs:
        assert gc._is_au_to_us_replacement(original, replacement) is True


def test_contingent_grammar_comment_flags_their_work_are(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_min_docx(
        inp,
        (
            '<w:p><w:r><w:t xml:space="preserve">'
            "The authors explain that their work are central to the programme."
            "</w:t></w:r></w:p>"
        ),
    )

    _, actions = apply_contingent_grammar_comments(str(inp), str(out), 10)

    assert actions == [
        {
            "rule": "CONTINGENT_SVA",
            "phrase": "their work are",
            "subject": "their work",
            "verb": "are",
            "comment_id": 1,
        }
    ]
    assert "Author Query 1." in _comments_text(out)
    assert "subject-verb agreement" in _comments_text(out)
    assert "'are' may need to be revised to 'is'" in _comments_text(out)


def test_contingent_grammar_comment_reads_tracked_insertions(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_min_docx(
        inp,
        (
            '<w:p>'
            '<w:r><w:t xml:space="preserve">The authors explain that their </w:t></w:r>'
            '<w:del w:id="1" w:author="CopyEditor AI" w:date="2026-06-07T00:00:00Z">'
            '<w:r><w:delText>works</w:delText></w:r>'
            '</w:del>'
            '<w:ins w:id="2" w:author="CopyEditor AI" w:date="2026-06-07T00:00:00Z">'
            '<w:r><w:t>work</w:t></w:r>'
            '</w:ins>'
            '<w:r><w:t xml:space="preserve"> are central to the programme.</w:t></w:r>'
            '</w:p>'
        ),
    )

    _, actions = apply_contingent_grammar_comments(str(inp), str(out), 10)

    assert len(actions) == 1
    assert actions[0]["phrase"] == "their work are"
    assert "subject-verb agreement" in _comments_text(out)


def test_contingent_grammar_comment_flags_similar_singular_subjects(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_min_docx(
        inp,
        (
            '<w:p><w:r><w:t xml:space="preserve">'
            "This analysis are central to the article."
            "</w:t></w:r></w:p>"
            '<w:p><w:r><w:t xml:space="preserve">'
            "The proposed study were designed for first-year students."
            "</w:t></w:r></w:p>"
            '<w:p><w:r><w:t xml:space="preserve">'
            "Our framework have implications for curriculum design."
            "</w:t></w:r></w:p>"
        ),
    )

    _, actions = apply_contingent_grammar_comments(str(inp), str(out), 10)

    assert [a["phrase"] for a in actions] == [
        "This analysis are",
        "The proposed study were",
        "Our framework have",
    ]
    comments = _comments_text(out)
    assert "'are' may need to be revised to 'is'" in comments
    assert "'were' may need to be revised to 'was'" in comments
    assert "'have' may need to be revised to 'has'" in comments
