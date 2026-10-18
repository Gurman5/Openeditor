import json
import time

from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from app.services import dev_trace
from app.services.config import (
    OPENAI_API_KEY,
    OPENAI_MAX_TOKENS,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
)


class LLMError(Exception):
    """Raised when the LLM call fails after retries."""


def _trace_request(
    call_kind: str,
    system_prompt: str,
    user_prompt: str,
    response_schema: dict | None = None,
) -> dict | None:
    """Persist full prompts of an LLM call when a dev trace is active."""
    tr = dev_trace.current_trace()
    if tr is None:
        return None
    schema_name = ""
    if isinstance(response_schema, dict):
        schema_name = str(response_schema.get("name") or "<unnamed>")
    return tr.llm_request(
        call_kind=call_kind,
        schema_name=schema_name,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )


def _trace_success(
    artifact: dict | None,
    parsed: dict,
    model: str,
    attempts: int,
    token_usage: dict[str, int] | None = None,
) -> None:
    tr = dev_trace.current_trace()
    if tr is None or artifact is None:
        return
    tr.llm_response(
        artifact,
        parsed,
        model=model,
        token_usage=token_usage,
        attempts=attempts,
    )


def _trace_failure(artifact: dict | None, error: str, attempts: int) -> None:
    tr = dev_trace.current_trace()
    if tr is None or artifact is None:
        return
    tr.llm_error(artifact, error=error, attempts=attempts)


EDITORIAL_RESPONSE_SCHEMA = {
    "name": "editorial_review",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "notes": {
                "type": "array",
                "maxItems": 50,
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": [
                                "title_quality",
                                "abstract_quality",
                                "introduction_quality",
                                "method_quality",
                                "results_quality",
                                "discussion_quality",
                                "conclusion_quality",
                                "apa_style",
                                "references_quality",
                                "tables_figures_quality",
                                "general",
                            ],
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                        },
                        "section": {"type": "string"},
                        "message": {"type": "string"},
                        "suggestion": {"type": "string"},
                        "quote": {"type": "string"},
                    },
                    "required": [
                        "category",
                        "severity",
                        "section",
                        "message",
                        "suggestion",
                        "quote",
                    ],
                    "additionalProperties": False,
                },
            },
            "structural_validations": {
                "type": "array",
                "maxItems": 50,
                "items": {
                    "type": "object",
                    "properties": {
                        "rule_id": {"type": "string"},
                        "verdict": {
                            "type": "string",
                            "enum": ["confirm", "false_positive", "needs_review"],
                        },
                        "reason": {"type": "string"},
                    },
                    "required": ["rule_id", "verdict", "reason"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["notes", "structural_validations"],
        "additionalProperties": False,
    },
}

MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1


def get_client() -> OpenAI:
    """Create an OpenAI client."""
    if not OPENAI_API_KEY:
        raise LLMError("OPENAI_API_KEY is not set. Check your .env file.")
    return OpenAI(api_key=OPENAI_API_KEY)


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> dict:
    """Send a structured-output request to the OpenAI Chat Completions API.

    Returns dict with keys: notes, model_used, token_usage.
    Raises LLMError on failure after retries.
    """
    client = get_client()
    target_model = model or OPENAI_MODEL
    trace_artifact = _trace_request(
        "call_llm",
        system_prompt,
        user_prompt,
        response_schema=EDITORIAL_RESPONSE_SCHEMA,
    )

    last_error = None
    attempts_used = 0
    for attempt in range(MAX_RETRIES):
        attempts_used = attempt + 1
        try:
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": EDITORIAL_RESPONSE_SCHEMA,
                },
                temperature=OPENAI_TEMPERATURE,
                max_completion_tokens=OPENAI_MAX_TOKENS,
            )
            break
        except (RateLimitError, APIConnectionError) as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(INITIAL_BACKOFF_SECONDS * (2**attempt))
            continue
        except APIError as e:
            _trace_failure(trace_artifact, f"openai APIError: {e}", attempts_used)
            raise LLMError(f"OpenAI API error: {e}") from e
    else:
        _trace_failure(trace_artifact, f"retries exhausted: {last_error}", attempts_used)
        raise LLMError(
            f"OpenAI API call failed after {MAX_RETRIES} retries: {last_error}"
        ) from last_error

    if response.choices[0].finish_reason == "length":
        _trace_failure(trace_artifact, "response truncated (max_completion_tokens)", attempts_used)
        raise LLMError(
            "LLM response was truncated (hit max_completion_tokens). "
            "Increase OPENAI_MAX_TOKENS in your .env file."
        )

    try:
        content = json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, IndexError, TypeError) as e:
        _trace_failure(trace_artifact, f"parse failure: {e}", attempts_used)
        raise LLMError(f"Failed to parse LLM response: {e}") from e

    token_usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    _trace_success(trace_artifact, content, target_model, attempts_used, token_usage)

    return {
        "notes": content["notes"],
        "structural_validations": content.get("structural_validations", []),
        "model_used": target_model,
        "token_usage": token_usage,
    }

##more general LLM query method - use different prompt/schema pairs for different checks
def call_llm_json(
    system_prompt: str,
    user_prompt: str,
    response_schema: dict,
    model: str | None = None,
) -> dict:
    client = get_client()

    if model is None:
        target_model = OPENAI_MODEL
    else:
        target_model = model

    trace_artifact = _trace_request(
        "call_llm_json",
        system_prompt,
        user_prompt,
        response_schema=response_schema,
    )

    last_error = None
    attempts_used = 0

    for attempt in range(MAX_RETRIES):
        attempts_used = attempt + 1
        try:
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": response_schema,
                },
                temperature=OPENAI_TEMPERATURE,
                max_completion_tokens=OPENAI_MAX_TOKENS,
            )
            break
        except (RateLimitError, APIConnectionError) as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(INITIAL_BACKOFF_SECONDS * (2 ** attempt))
            continue
        except APIError as e:
            _trace_failure(trace_artifact, f"openai APIError: {e}", attempts_used)
            raise LLMError(f"OpenAI API error: {e}") from e
    else:
        _trace_failure(trace_artifact, f"retries exhausted: {last_error}", attempts_used)
        raise LLMError(
            f"OpenAI API call failed after {MAX_RETRIES} retries: {last_error}"
        ) from last_error

    try:
        content = json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, IndexError, TypeError) as e:
        _trace_failure(trace_artifact, f"parse failure: {e}", attempts_used)
        raise LLMError(f"Failed to parse LLM response: {e}") from e

    token_usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    _trace_success(trace_artifact, content, target_model, attempts_used, token_usage)

    return {
        "content": content,
        "model_used": target_model,
        "token_usage": token_usage,
    }

