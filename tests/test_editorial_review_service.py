from unittest.mock import patch

from app.domain.editorial_feedback import EditorialNote, EditorialReviewResult
from app.services.ai.editorial_review_service import run_editorial_review

PACK = "tests/jutlp_sample_docx_test_pack"

MOCK_LLM_RESPONSE = {
    "notes": [
        {
            "category": "introduction_quality",
            "severity": "high",
            "section": "Introduction",
            "message": "The introduction does not establish a clear practice problem.",
            "suggestion": "Add a paragraph that explicitly identifies the learning and teaching challenge.",
        },
        {
            "category": "abstract_quality",
            "severity": "medium",
            "section": "Abstract",
            "message": "The abstract does not mention the theoretical framework used.",
            "suggestion": "Include a brief reference to the theoretical framework guiding the study.",
        },
    ],
    "model_used": "gpt-5.4-mini",
    "token_usage": {
        "prompt_tokens": 5000,
        "completion_tokens": 300,
        "total_tokens": 5300,
    },
}


class TestEditorialReviewService:
    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_returns_editorial_review_result(self, mock_call_llm):
        mock_call_llm.return_value = MOCK_LLM_RESPONSE

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

        assert isinstance(result, EditorialReviewResult)

    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_note_count(self, mock_call_llm):
        mock_call_llm.return_value = MOCK_LLM_RESPONSE

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

        assert len(result.notes) == 2

    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_notes_are_editorial_note_instances(self, mock_call_llm):
        mock_call_llm.return_value = MOCK_LLM_RESPONSE

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

        for note in result.notes:
            assert isinstance(note, EditorialNote)

    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_note_fields_mapped_correctly(self, mock_call_llm):
        mock_call_llm.return_value = MOCK_LLM_RESPONSE

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")
        first = result.notes[0]

        assert first.category == "introduction_quality"
        assert first.severity == "high"
        assert first.section == "Introduction"
        assert "practice problem" in first.message
        assert "learning and teaching challenge" in first.suggestion

    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_model_used_propagated(self, mock_call_llm):
        mock_call_llm.return_value = MOCK_LLM_RESPONSE

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

        assert result.model_used == "gpt-5.4-mini"

    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_token_usage_propagated(self, mock_call_llm):
        mock_call_llm.return_value = MOCK_LLM_RESPONSE

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

        assert result.token_usage["total_tokens"] == 5300

    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_empty_notes(self, mock_call_llm):
        mock_call_llm.return_value = {
            "notes": [],
            "model_used": "gpt-5.4-mini",
            "token_usage": {
                "prompt_tokens": 5000,
                "completion_tokens": 10,
                "total_tokens": 5010,
            },
        }

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")

        assert result.notes == []

    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_prompts_passed_to_llm(self, mock_call_llm):
        mock_call_llm.return_value = MOCK_LLM_RESPONSE

        run_editorial_review(f"{PACK}/01_valid_identified.docx")

        mock_call_llm.assert_called_once()
        args = mock_call_llm.call_args
        system_prompt = args[0][0]
        user_prompt = args[0][1]

        assert "JUTLP Editorial Guidelines" in system_prompt
        assert "## Section: Introduction" in user_prompt

    @patch("app.services.ai.editorial_review_service.call_llm")
    def test_internal_markers_stripped_from_notes(self, mock_call_llm):
        """The LLM occasionally quotes our '[Subheading]' or '###' markers
        verbatim in its feedback, leaking prompt scaffolding into user-facing
        output. The service must strip those markers before returning notes.
        """
        mock_call_llm.return_value = {
            "notes": [
                {
                    "category": "general",
                    "severity": "advisory",
                    "section": "Introduction",
                    "message": (
                        "The '[Subheading] Theoretical Framework' section is "
                        "followed by no body text."
                    ),
                    "suggestion": "### Add an introductory paragraph.",
                },
            ],
            "model_used": "gpt-5.4-mini",
            "token_usage": {
                "prompt_tokens": 100,
                "completion_tokens": 10,
                "total_tokens": 110,
            },
        }

        result = run_editorial_review(f"{PACK}/01_valid_identified.docx")
        note = result.notes[0]

        assert "[Subheading]" not in note.message
        assert "Theoretical Framework" in note.message  # content preserved
        assert not note.suggestion.startswith("###")
        assert "Add an introductory paragraph." in note.suggestion
