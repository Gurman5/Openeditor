import json
import time

from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from app.services.config import (
    OPENAI_API_KEY,
    OPENAI_MAX_TOKENS,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
)


class LLMError(Exception):
    """Raised when the LLM call fails after retries."""


EDITORIAL_RESPONSE_SCHEMA = {
    "name": "editorial_review",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "notes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
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
                "items": {
                    "type": "object",
                    "properties": {
                        "rule_id": {"type": "string"},
                        "verdict": {
                            "type": "string",
                            "enum": ["confirm", "false_positive"],
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

    last_error = None
    for attempt in range(MAX_RETRIES):
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
            raise LLMError(f"OpenAI API error: {e}") from e
    else:
        raise LLMError(
            f"OpenAI API call failed after {MAX_RETRIES} retries: {last_error}"
        ) from last_error

    if response.choices[0].finish_reason == "length":
        raise LLMError(
            "LLM response was truncated (hit max_completion_tokens). "
            "Increase OPENAI_MAX_TOKENS in your .env file."
        )

    try:
        content = json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, IndexError, TypeError) as e:
        raise LLMError(f"Failed to parse LLM response: {e}") from e

    return {
        "notes": content["notes"],
        "structural_validations": content.get("structural_validations", []),
        "model_used": target_model,
        "token_usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
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

    last_error = None

    for attempt in range(MAX_RETRIES):
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
            raise LLMError(f"OpenAI API error: {e}") from e
    else:
        raise LLMError(
            f"OpenAI API call failed after {MAX_RETRIES} retries: {last_error}"
        ) from last_error

    try:
        content = json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, IndexError, TypeError) as e:
        raise LLMError(f"Failed to parse LLM response: {e}") from e

    return {
        "content": content,
        "model_used": target_model,
        "token_usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
    }

