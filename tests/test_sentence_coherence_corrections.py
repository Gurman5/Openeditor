"""Tests for the sentence-coherence LLM pass.

We stub the LLM call so the tests are deterministic and offline. The pass
under test sorts and caps flags, dedupes against grammar originals, and
anchors a Word comment at each flag.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from docx import Document
from lxml import etree

from app.services import sentence_coherence_corrections as scc
from app.services.sentence_coherence_corrections import (
    _MAX_FLAGS_PER_DOC,
    apply_sentence_coherence_corrections,
    get_sentence_coherence_flags,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"


def _make_doc(tmp_path: Path, paragraphs: list[str]) -> str:
    docx_path = tmp_path / "in.docx"
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    doc.save(docx_path)
    return str(docx_path)


def _stub_llm(flags: list[dict]):
    """Return a function compatible with ``call_llm_json``'s signature."""
    def _call(system_prompt, user_prompt, response_schema, model=None):
        return {"content": {"flags": flags}}
    return _call


_LONG_PARA = (
    "The participants completed a survey designed to measure attitudes "
    "towards collaborative learning across a twelve-week semester block."
)


def test_well_formed_paragraph_returns_no_flags(monkeypatch, tmp_path):
    """LLM returns empty list — pass produces zero flags."""
    monkeypatch.setattr(scc, "call_llm_json", _stub_llm([]))
    path = _make_doc(tmp_path, [_LONG_PARA])
    assert get_sentence_coherence_flags(path) == []


def test_garbled_sentence_returns_one_flag(monkeypatch, tmp_path):
    monkeypatch.setattr(
        scc,
        "call_llm_json",
        _stub_llm(
            [{"original": "Some students learning the.", "reason": "missing object"}]
        ),
    )
    path = _make_doc(
        tmp_path,
        [_LONG_PARA + " Some students learning the. " + _LONG_PARA],
    )
    flags = get_sentence_coherence_flags(path)
    assert len(flags) == 1
    assert flags[0]["original"] == "Some students learning the."


def test_paragraph_below_min_length_skipped(monkeypatch, tmp_path):
    """A short paragraph should not be sent to the LLM at all — we still
    need a stub but assert it never gets non-empty input."""
    seen: list[str] = []

    def _spy(system_prompt, user_prompt, response_schema, model=None):
        seen.append(user_prompt)
        return {"content": {"flags": []}}

    monkeypatch.setattr(scc, "call_llm_json", _spy)
    path = _make_doc(tmp_path, ["Too short."])  # ~10 chars
    get_sentence_coherence_flags(path)
    # When every paragraph is filtered out, the pass short-circuits without
    # calling the LLM at all.
    assert seen == []


def test_dedupe_against_grammar_originals(monkeypatch, tmp_path):
    monkeypatch.setattr(
        scc,
        "call_llm_json",
        _stub_llm(
            [
                {"original": "Some students learning the.", "reason": "missing object"},
                {"original": "Another fine sentence here is.", "reason": "garbled"},
            ]
        ),
    )
    path = _make_doc(
        tmp_path,
        [_LONG_PARA + " Some students learning the. Another fine sentence here is."],
    )
    flags = get_sentence_coherence_flags(
        path,
        grammar_originals={"some students learning the."},
    )
    # The overlapping flag is dropped — only the second remains.
    assert len(flags) == 1
    assert flags[0]["original"] == "Another fine sentence here is."


def test_per_document_cap_enforced(monkeypatch, tmp_path):
    """Returning more than `_MAX_FLAGS_PER_DOC` flags from the LLM should
    be truncated."""
    too_many = [
        {"original": f"Sentence number {i} here is.", "reason": f"reason {i:02d}"}
        for i in range(_MAX_FLAGS_PER_DOC + 4)
    ]
    monkeypatch.setattr(scc, "call_llm_json", _stub_llm(too_many))
    path = _make_doc(tmp_path, [_LONG_PARA])
    flags = get_sentence_coherence_flags(path)
    assert len(flags) == _MAX_FLAGS_PER_DOC


def test_overlong_original_dropped(monkeypatch, tmp_path):
    """LLM returns a multi-sentence span — drop it (we can't anchor cleanly)."""
    over = " ".join(["word"] * 60) + "."
    monkeypatch.setattr(
        scc,
        "call_llm_json",
        _stub_llm([{"original": over, "reason": "spans many sentences"}]),
    )
    path = _make_doc(tmp_path, [_LONG_PARA])
    assert get_sentence_coherence_flags(path) == []


def test_degenerate_reason_no_is_dropped(monkeypatch, tmp_path):
    """Regression: a flag whose reason is a bare "No" must not surface — it's
    the model answering the wrong question, not a coherence explanation."""
    monkeypatch.setattr(
        scc,
        "call_llm_json",
        _stub_llm([{"original": "Some students learning the.", "reason": "No"}]),
    )
    path = _make_doc(tmp_path, [_LONG_PARA + " Some students learning the. " + _LONG_PARA])
    assert get_sentence_coherence_flags(path) == []


@pytest.mark.parametrize("bad_reason", ["No", "Yes", "n/a", "none", "ok", "No.", "  yes  "])
def test_bare_verdict_reasons_rejected(monkeypatch, tmp_path, bad_reason):
    monkeypatch.setattr(
        scc,
        "call_llm_json",
        _stub_llm([{"original": "Some students learning the.", "reason": bad_reason}]),
    )
    path = _make_doc(tmp_path, [_LONG_PARA + " Some students learning the. " + _LONG_PARA])
    assert get_sentence_coherence_flags(path) == []


def test_degenerate_reason_does_not_displace_a_real_flag(monkeypatch, tmp_path):
    """The shortest-reason-first sort must not let "No" rank above a real
    explanation: the good flag survives, the degenerate one is gone."""
    monkeypatch.setattr(
        scc,
        "call_llm_json",
        _stub_llm([
            {"original": "Some students learning the.", "reason": "No"},
            {"original": "Others is going to school.", "reason": "subject-verb disagreement"},
        ]),
    )
    path = _make_doc(
        tmp_path,
        [_LONG_PARA + " Some students learning the. Others is going to school. " + _LONG_PARA],
    )
    flags = get_sentence_coherence_flags(path)
    assert len(flags) == 1
    assert flags[0]["reason"] == "subject-verb disagreement"


def test_legitimate_terse_reason_is_kept(monkeypatch, tmp_path):
    """A short but genuine explanation ("missing main verb") clears the bar."""
    monkeypatch.setattr(
        scc,
        "call_llm_json",
        _stub_llm([{"original": "Some students learning the.", "reason": "missing main verb"}]),
    )
    path = _make_doc(tmp_path, [_LONG_PARA + " Some students learning the. " + _LONG_PARA])
    flags = get_sentence_coherence_flags(path)
    assert len(flags) == 1
    assert flags[0]["reason"] == "missing main verb"


def test_apply_anchors_a_comment(monkeypatch, tmp_path):
    """End-to-end: stub returns a flag whose `original` is in the doc;
    the apply pass writes a comment range and a comment element."""
    target_sentence = "Some students learning the new method."
    monkeypatch.setattr(
        scc,
        "call_llm_json",
        _stub_llm(
            [{"original": target_sentence, "reason": "verb phrase is incomplete"}]
        ),
    )
    src = _make_doc(tmp_path, [_LONG_PARA + " " + target_sentence + " " + _LONG_PARA])
    out = str(tmp_path / "out.docx")

    next_id, applied = apply_sentence_coherence_corrections(src, out, 1)
    assert len(applied) == 1
    assert applied[0]["original"] == target_sentence

    with zipfile.ZipFile(out, "r") as z:
        assert "word/comments.xml" in z.namelist()
        comments_root = etree.fromstring(z.read("word/comments.xml"))
        comments = comments_root.findall(f"{WQ}comment")
        comment_texts = []
        for c in comments:
            for t in c.iter(f"{WQ}t"):
                if t.text:
                    comment_texts.append(t.text)
        assert any("verb phrase is incomplete" in t for t in comment_texts)


def test_apply_no_flags_short_circuits(monkeypatch, tmp_path):
    """When the LLM returns nothing, apply pass copies through and reports
    zero actions."""
    monkeypatch.setattr(scc, "call_llm_json", _stub_llm([]))
    src = _make_doc(tmp_path, [_LONG_PARA])
    out = str(tmp_path / "out.docx")
    next_id, applied = apply_sentence_coherence_corrections(src, out, 1)
    assert applied == []
    assert next_id == 1
    # File should still be a valid docx.
    with zipfile.ZipFile(out, "r") as z:
        assert "word/document.xml" in z.namelist()


def test_flag_inside_direct_quotation_is_dropped(monkeypatch, tmp_path):
    """A coherence flag whose `original` sits inside a quoted span must
    be dropped — direct quotations retain the source's wording."""
    quoted_sentence = "Some students learning the."
    monkeypatch.setattr(
        scc,
        "call_llm_json",
        _stub_llm([{"original": quoted_sentence, "reason": "verb phrase incomplete"}]),
    )
    para = (
        _LONG_PARA
        + ' The participant said "' + quoted_sentence + '" verbatim.'
    )
    path = _make_doc(tmp_path, [para])
    flags = get_sentence_coherence_flags(path)
    assert flags == []


def test_flag_outside_quote_still_kept_when_paragraph_has_a_quote(monkeypatch, tmp_path):
    target = "Another fine sentence here is."
    monkeypatch.setattr(
        scc,
        "call_llm_json",
        _stub_llm([{"original": target, "reason": "garbled"}]),
    )
    # Same paragraph has a quote, but the flagged sentence is outside it.
    para = (
        _LONG_PARA
        + ' He said "irrelevant quote here". '
        + target
    )
    path = _make_doc(tmp_path, [para])
    flags = get_sentence_coherence_flags(path)
    assert len(flags) == 1
    assert flags[0]["original"] == target
