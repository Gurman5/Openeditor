"""LLM smoke test: one document through run_editorial_review.

Mocked by default (no API key needed). A live run is gated behind the
``RUN_LIVE_LLM`` environment variable.
"""

import os
from unittest.mock import patch

import pytest

from app.services.ai.editorial_review_service import run_editorial_review
from app.services.ai.prompt_builder import VALID_CATEGORIES

PACK = "tests/jutlp_sample_docx_test_pack"

FORBIDDEN = ("jutlp", "practitioner notes", "credit")

_VALID_RESPONSE = {
    "notes": [
        {
            "category": "title_quality",
            "severity": "medium",
            "section": "Title",
            "message": "The title is in sentence case.",
            "suggestion": "Use title case.",
            "quote": "exploring how students learn",
        },
        {
            "category": "apa_style",
            "severity": "low",
            "section": "References",
            "message": "DOI uses bare form.",
            "suggestion": "Use https://doi.org/ form.",
            "quote": "doi:10.1000/xyz",
        },
    ],
    "structural_validations": [
        {"rule_id": "STY001", "verdict": "needs_review", "reason": "advisory"},
    ],
    "model_used": "gpt-5.4-mini",
    "token_usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
}


@patch("app.services.ai.editorial_review_service.call_llm")
def test_notes_parse_and_categories_valid(mock_call_llm):
    mock_call_llm.return_value = _VALID_RESPONSE

    result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

    assert len(result.notes) == 2
    for note in result.notes:
        assert note.category in VALID_CATEGORIES
        lowered = (note.message + note.suggestion + note.quote).lower()
        for bad in FORBIDDEN:
            assert bad not in lowered

    assert result.structural_validations[0].verdict == "needs_review"


@pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_LLM"),
    reason="live run requires RUN_LIVE_LLM=1 and OPENAI_API_KEY",
)
def test_live_run():
    result = run_editorial_review(f"{PACK}/01_valid_identified.docx")
    assert isinstance(result.model_used, str)
    assert result.model_used
