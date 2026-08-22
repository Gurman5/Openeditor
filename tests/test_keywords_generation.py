"""Tests for the LLM-driven Keywords generator.

We stub ``call_llm_json`` so the tests are deterministic and offline.
"""

from __future__ import annotations

from app.services import keywords_generation as kg
from app.services.ai.llm_client import LLMError
from app.services.keywords_generation import _MAX_KEYWORDS, generate_keywords

_TITLE = "A study of collaborative learning in higher education"
_ABSTRACT = (
    "This article investigates how undergraduate students engage with "
    "collaborative learning tasks across a twelve-week semester block. "
    "We surveyed 200 participants and ran follow-up interviews to "
    "explore peer feedback practices and reflective learning."
)


def _stub(keywords):
    def _call(system_prompt, user_prompt, response_schema, model=None):
        return {"content": {"keywords": list(keywords)}}
    return _call


def _raising_stub():
    def _call(system_prompt, user_prompt, response_schema, model=None):
        raise LLMError("simulated LLM outage")
    return _call


def test_returns_five_keywords_on_clean_llm_response(monkeypatch):
    monkeypatch.setattr(
        kg, "call_llm_json",
        _stub([
            "collaborative learning",
            "higher education",
            "peer feedback",
            "student engagement",
            "reflective practice",
        ]),
    )
    out = generate_keywords(_TITLE, _ABSTRACT)
    assert len(out) == _MAX_KEYWORDS
    assert "collaborative learning" in out


def test_caps_at_five_when_llm_returns_more(monkeypatch):
    monkeypatch.setattr(
        kg, "call_llm_json",
        _stub([f"keyword_{i}" for i in range(_MAX_KEYWORDS + 4)]),
    )
    out = generate_keywords(_TITLE, _ABSTRACT)
    assert len(out) == _MAX_KEYWORDS


def test_drops_acronyms_and_overlong_keywords(monkeypatch):
    monkeypatch.setattr(
        kg, "call_llm_json",
        _stub([
            "AI",                                                # acronym → drop
            "machine learning",                                  # keep
            "natural language processing of academic texts and journals",  # >4 words → drop
            "peer review",                                       # keep
            "PR",                                                # acronym → drop
            "learning analytics",                                # keep
        ]),
    )
    out = generate_keywords(_TITLE, _ABSTRACT)
    assert "AI" not in out
    assert "PR" not in out
    assert all(len(k.split()) <= 4 for k in out)
    assert "machine learning" in out
    assert "peer review" in out


def test_dedupes_case_insensitively(monkeypatch):
    monkeypatch.setattr(
        kg, "call_llm_json",
        _stub(["Learning", "learning", "LEARNING", "feedback"]),
    )
    out = generate_keywords(_TITLE, _ABSTRACT)
    lowered = [k.lower() for k in out]
    assert lowered.count("learning") == 1
    assert "feedback" in out


def test_returns_empty_on_llm_error(monkeypatch):
    monkeypatch.setattr(kg, "call_llm_json", _raising_stub())
    assert generate_keywords(_TITLE, _ABSTRACT) == []


def test_empty_abstract_short_circuits(monkeypatch):
    """When the abstract is too short to derive a meaningful keyword set the
    pass returns ``[]`` WITHOUT calling the LLM."""
    seen = []

    def _spy(system_prompt, user_prompt, response_schema, model=None):
        seen.append(user_prompt)
        return {"content": {"keywords": ["x"]}}

    monkeypatch.setattr(kg, "call_llm_json", _spy)
    out = generate_keywords(_TITLE, "short.")
    assert out == []
    assert seen == []  # spy never called


def test_generic_filler_words_dropped(monkeypatch):
    monkeypatch.setattr(
        kg, "call_llm_json",
        _stub(["study", "research", "feedback", "engagement", "assessment"]),
    )
    out = generate_keywords(_TITLE, _ABSTRACT)
    assert "study" not in out
    assert "research" not in out
    assert "feedback" in out


def test_strips_surrounding_quotes(monkeypatch):
    monkeypatch.setattr(
        kg, "call_llm_json",
        _stub(['"feedback"', "'engagement'", "  spaced  out  "]),
    )
    out = generate_keywords(_TITLE, _ABSTRACT)
    # Quoting and whitespace stripped, internal whitespace collapsed.
    assert "feedback" in out
    assert "engagement" in out
    assert "spaced out" in out


def test_rejects_keyword_containing_full_stop(monkeypatch):
    """LLM regressing to phrasal output (a sentence) must be filtered."""
    monkeypatch.setattr(
        kg, "call_llm_json",
        _stub(["feedback.", "engagement", "this is a sentence."]),
    )
    out = generate_keywords(_TITLE, _ABSTRACT)
    assert "engagement" in out
    assert all("." not in k for k in out)
