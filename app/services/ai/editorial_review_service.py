import re

from app.domain.editorial_feedback import (
    EditorialNote,
    EditorialReviewResult,
    StructuralValidation,
)
from app.services.ai.llm_client import call_llm
from app.services.ai.prompt_builder import build_prompts
from app.services.document_analysis_services import load_paragraphs, parse_docx_structure

# Defense-in-depth: even with prompt rules forbidding it, the LLM sometimes
# quotes the "[Subheading]" marker (or legacy "### ") we inject into section
# bodies. These patterns leak our prompt scaffolding into user-facing
# feedback. We strip any stray occurrences from message/suggestion fields
# before the notes leave this service.
_MARKER_PATTERNS = [
    re.compile(r"\[Subheading\]\s*", re.IGNORECASE),
    # Legacy markdown heading prefix, kept for safety if the LLM pattern-matches
    # on generic "### " from its training data.
    re.compile(r"(?m)^###\s+"),
]


def _strip_internal_markers(text: str) -> str:
    if not text:
        return text
    for pattern in _MARKER_PATTERNS:
        text = pattern.sub("", text)
    return text


def run_editorial_review(
    docx_path: str,
    deterministic_check_result: dict | None = None,
    ref_check_result: dict | None = None,
) -> EditorialReviewResult:
    """Run LLM-based editorial review on a JUTLP manuscript.

    Pipeline:
    1. Parse DOCX into paragraphs + structure
    2. Build system + user prompts
    3. Call OpenAI API
    4. Parse response into EditorialReviewResult (stripping any internal
       prompt markers the LLM may have quoted)
    """
    paragraphs = load_paragraphs(docx_path)
    parsed = parse_docx_structure(docx_path)

    system_prompt, user_prompt = build_prompts(
        paragraphs, parsed, deterministic_check_result, ref_check_result
    )
    raw_result = call_llm(system_prompt, user_prompt)

    notes = [
        EditorialNote(
            category=n["category"],
            severity=n["severity"],
            section=n["section"],
            message=_strip_internal_markers(n["message"]),
            suggestion=_strip_internal_markers(n["suggestion"]),
            quote=n.get("quote", ""),
        )
        for n in raw_result["notes"]
    ]

    structural_validations = [
        StructuralValidation(
            rule_id=v["rule_id"],
            verdict=v["verdict"],
            reason=v["reason"],
        )
        for v in raw_result.get("structural_validations", [])
    ]

    return EditorialReviewResult(
        notes=notes,
        structural_validations=structural_validations,
        model_used=raw_result["model_used"],
        token_usage=raw_result["token_usage"],
    )
