# APA 7 Editorial Review — Output Contract

Version 1.0 (Track D). This is the canonical contract for the LLM editorial-review
stage. Every consumer of `run_editorial_review` MUST implement against this exact
shape. If a field, enum value, or key name changes, bump the version and circulate
before landing the code.

Source of truth in code: `app/services/ai/llm_client.py::EDITORIAL_RESPONSE_SCHEMA`,
`app/domain/editorial_feedback.py`, `app/services/ai/editorial_review_service.py`.

---

## 1. Category enum (`VALID_CATEGORIES`)

Every `note.category` value MUST be one of:

| Value | Applies to |
|---|---|
| `title_quality` | Title phrasing, length advisory, subtitle format |
| `abstract_quality` | Abstract clarity, structure, content |
| `introduction_quality` | Introduction, significance/contribution statement |
| `method_quality` | Method/Methods/Methodology section |
| `results_quality` | Results/Findings section |
| `discussion_quality` | Discussion section |
| `conclusion_quality` | Conclusion(s) section |
| `apa_style` | APA 7 style/formatting issues |
| `references_quality` | Reference list presentation issues (non-matching only) |
| `tables_figures_quality` | Tables and figures presentation |
| `general` | Cross-cutting prose/paragraph issues, other |

Retired (JUTLP-only) categories that MUST NOT be emitted: `practitioner_notes_quality`,
`literature_quality`, `acknowledgements_quality`, `appendices_quality`.

## 2. Verdict enum (`StructuralValidation.verdict`)

| Value | Meaning |
|---|---|
| `confirm` | The deterministic structural failure is genuine |
| `false_positive` | The check fired incorrectly |
| `needs_review` | Advisory — neither confirmed nor false-positive; surfaced for the editor to look at, not acted on automatically |

`needs_review` semantics: it is **advisory only**. Consumers MUST NOT treat it as
`confirm` (i.e. must not escalate the underlying rule) and MUST NOT treat it as
`false_positive` (i.e. must not suppress the rule). It is surfaced as-is for human
review. The `fp_overrides` consumer must ignore `needs_review` (neither override nor
confirm).

## 3. Editorial response schema (LLM structured output)

```json
{
  "name": "editorial_review",
  "strict": true,
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
                "general"
              ]
            },
            "severity": {
              "type": "string",
              "enum": ["high", "medium", "low"]
            },
            "section": { "type": "string" },
            "message": { "type": "string" },
            "suggestion": { "type": "string" },
            "quote": { "type": "string" }
          },
          "required": ["category", "severity", "section", "message", "suggestion", "quote"],
          "additionalProperties": false
        }
      },
      "structural_validations": {
        "type": "array",
        "maxItems": 50,
        "items": {
          "type": "object",
          "properties": {
            "rule_id": { "type": "string" },
            "verdict": {
              "type": "string",
              "enum": ["confirm", "false_positive", "needs_review"]
            },
            "reason": { "type": "string" }
          },
          "required": ["rule_id", "verdict", "reason"],
          "additionalProperties": false
        }
      }
    },
    "required": ["notes", "structural_validations"],
    "additionalProperties": false
  }
}
```

## 4. `run_editorial_review` return shape (`EditorialReviewResult`)

```python
{
    "notes": [                     # list[EditorialNote]
        {
            "category": str,       # enum per §1
            "severity": str,       # "high" | "medium" | "low"
            "section": str,
            "message": str,
            "suggestion": str,
            "quote": str,          # "" when section-level, no verbatim text
        }
    ],
    "structural_validations": [    # list[StructuralValidation]
        {
            "rule_id": str,
            "verdict": str,        # enum per §2
            "reason": str,
        }
    ],
    "model_used": str,             # e.g. "gpt-5.4-mini"
    "token_usage": {
        "prompt_tokens": int,
        "completion_tokens": int,
        "total_tokens": int,
    },
}
```

## 5. Failure semantics

- `call_llm` raises `LLMError` after `MAX_RETRIES` (3) attempts with exponential
  backoff, or on JSON parse failure / truncated (`finish_reason == "length"`)
  responses.
- `run_editorial_review` propagates `LLMError` to its caller. The pipeline boundary
  is responsible for recording the failure in `stage_errors` (see D-14). The review
  stage never returns a silent partial result on failure.
- A truncated response is a hard failure (raises), never silently accepted.

## 6. Notes

- `notes` and `structural_validations` are capped at 50 items each (`maxItems`).
- `strict: true` is retained so the LLM cannot emit out-of-schema keys.
