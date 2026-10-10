"""Schema parse tests for run_editorial_review (mocked LLM)."""

from unittest.mock import patch

from app.domain.editorial_feedback import EditorialNote, StructuralValidation
from app.services.ai.editorial_review_service import run_editorial_review

PACK = "tests/jutlp_sample_docx_test_pack"


def _response(structural_validations=None, notes=None):
    payload = {
        "notes": notes if notes is not None else [],
        "model_used": "gpt-5.4-mini",
        "token_usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    if structural_validations is not None:
        payload["structural_validations"] = structural_validations
    return payload


class TestStructuralValidationParsing:
    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_all_verdicts_parsed(self, mock_call_llm):
        mock_call_llm.return_value = _response(
            structural_validations=[
                {"rule_id": "STY001", "verdict": "confirm", "reason": "genuine"},
                {"rule_id": "STY002", "verdict": "false_positive", "reason": "mismatch"},
                {"rule_id": "STY003", "verdict": "needs_review", "reason": "unclear"},
            ]
        )

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

        assert len(result.structural_validations) == 3
        for sv in result.structural_validations:
            assert isinstance(sv, StructuralValidation)

    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_needs_review_verdict_preserved(self, mock_call_llm):
        mock_call_llm.return_value = _response(
            structural_validations=[
                {"rule_id": "STY001", "verdict": "needs_review", "reason": "advisory"}
            ]
        )

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

        sv = result.structural_validations[0]
        assert sv.rule_id == "STY001"
        assert sv.verdict == "needs_review"
        assert sv.reason == "advisory"

    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_missing_structural_validations_defaults_to_empty(self, mock_call_llm):
        mock_call_llm.return_value = _response(structural_validations=None)

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

        assert result.structural_validations == []


class TestNewCategoriesAccepted:
    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_references_quality_note_parses(self, mock_call_llm):
        mock_call_llm.return_value = _response(
            notes=[
                {
                    "category": "references_quality",
                    "severity": "medium",
                    "section": "References",
                    "message": "DOI uses bare form.",
                    "suggestion": "Use https://doi.org/ form.",
                    "quote": "doi:10.1000/xyz",
                }
            ]
        )

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

        assert len(result.notes) == 1
        assert isinstance(result.notes[0], EditorialNote)
        assert result.notes[0].category == "references_quality"

    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_tables_figures_quality_note_parses(self, mock_call_llm):
        mock_call_llm.return_value = _response(
            notes=[
                {
                    "category": "tables_figures_quality",
                    "severity": "low",
                    "section": "Results",
                    "message": "Table missing an italic title.",
                    "suggestion": "Add an italic title under 'Table 1'.",
                    "quote": "",
                }
            ]
        )

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

        assert result.notes[0].category == "tables_figures_quality"
        assert result.notes[0].quote == ""
