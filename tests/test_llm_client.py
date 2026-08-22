import json
from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError, APIError, RateLimitError

from app.services.ai.llm_client import LLMError, call_llm


def _mock_response(notes=None):
    """Build a mock ChatCompletion response."""
    if notes is None:
        notes = [
            {
                "category": "introduction_quality",
                "severity": "requires_attention",
                "section": "Introduction",
                "message": "No clear practice problem stated.",
                "suggestion": "Add a paragraph identifying the learning and teaching challenge.",
            }
        ]
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = json.dumps({"notes": notes})
    response.usage.prompt_tokens = 1000
    response.usage.completion_tokens = 200
    response.usage.total_tokens = 1200
    return response


@patch("app.services.ai.llm_client.OPENAI_API_KEY", "test-key")
class TestCallLlm:
    @patch("app.services.ai.llm_client.get_client")
    def test_successful_call(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response()
        mock_get_client.return_value = mock_client

        result = call_llm("system prompt", "user prompt")

        assert len(result["notes"]) == 1
        assert result["notes"][0]["category"] == "introduction_quality"
        assert result["model_used"] == "gpt-5.4-mini"
        assert result["token_usage"]["total_tokens"] == 1200

    @patch("app.services.ai.llm_client.get_client")
    def test_model_override(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response()
        mock_get_client.return_value = mock_client

        result = call_llm("system", "user", model="gpt-5.4")

        assert result["model_used"] == "gpt-5.4"

    @patch("app.services.ai.llm_client.get_client")
    def test_empty_notes(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response(notes=[])
        mock_get_client.return_value = mock_client

        result = call_llm("system", "user")

        assert result["notes"] == []

    @patch("app.services.ai.llm_client.INITIAL_BACKOFF_SECONDS", 0)
    @patch("app.services.ai.llm_client.get_client")
    def test_retry_on_rate_limit(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            RateLimitError(
                message="rate limited",
                response=MagicMock(status_code=429),
                body=None,
            ),
            _mock_response(),
        ]
        mock_get_client.return_value = mock_client

        result = call_llm("system", "user")

        assert len(result["notes"]) == 1
        assert mock_client.chat.completions.create.call_count == 2

    @patch("app.services.ai.llm_client.INITIAL_BACKOFF_SECONDS", 0)
    @patch("app.services.ai.llm_client.get_client")
    def test_retry_on_connection_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            APIConnectionError(request=MagicMock()),
            _mock_response(),
        ]
        mock_get_client.return_value = mock_client

        result = call_llm("system", "user")

        assert len(result["notes"]) == 1

    @patch("app.services.ai.llm_client.INITIAL_BACKOFF_SECONDS", 0)
    @patch("app.services.ai.llm_client.get_client")
    def test_max_retries_exceeded(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RateLimitError(
            message="rate limited",
            response=MagicMock(status_code=429),
            body=None,
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(LLMError, match="failed after 3 retries"):
            call_llm("system", "user")

    @patch("app.services.ai.llm_client.get_client")
    def test_api_error_no_retry(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APIError(
            message="bad request",
            request=MagicMock(),
            body=None,
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(LLMError, match="OpenAI API error"):
            call_llm("system", "user")

        assert mock_client.chat.completions.create.call_count == 1

    @patch("app.services.ai.llm_client.get_client")
    def test_malformed_json_response(self, mock_get_client):
        mock_client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "not valid json"
        mock_client.chat.completions.create.return_value = response
        mock_get_client.return_value = mock_client

        with pytest.raises(LLMError, match="Failed to parse"):
            call_llm("system", "user")


class TestGetClient:
    @patch("app.services.ai.llm_client.OPENAI_API_KEY", "")
    def test_missing_api_key(self):
        with pytest.raises(LLMError, match="OPENAI_API_KEY is not set"):
            call_llm("system", "user")
