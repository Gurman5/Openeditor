# APA 7 LLM Assertions Contract

Version 1.0 (Track D, D-19). This defines the machine-checkable assertions that
the LLM regression harness (Track K) enforces on every
`run_editorial_review` output. K implements these as the automated gate (K-02).

Sources of truth in code:

- Note schema: `docs/apa7-editorial-contract.md` (D-01) and
  `app/domain/editorial_feedback.py`
- `VALID_CATEGORIES`: `app/services/ai/prompt_builder.py`
- Verdict enum: `app/services/ai/llm_client.py` (`EDITORIAL_RESPONSE_SCHEMA`)

---

## Assertions

For every note `n` in `notes[]` and every validation `v` in
`structural_validations[]`, all of the following MUST hold. A run fails if any
assertion fails on any item.

### (a) Schema conformance

`n` has exactly these keys, all strings:

```json
{ "category": str, "severity": str, "section": str, "message": str, "suggestion": str, "quote": str }
```

`quote` may be the empty string `""`; no other field may be empty.

### (b) No JUTLP residue

None of the following substrings appears (case-insensitive) in any string field
of `n` (`message`, `suggestion`, `section`, `quote`, `category`):

- `jutlp`
- `practitioner notes`
- `credit` (covers the CRediT taxonomy)

### (c) Valid category

`n.category` MUST be one of:

```text
title_quality, abstract_quality, introduction_quality, method_quality,
results_quality, discussion_quality, conclusion_quality, apa_style,
references_quality, tables_figures_quality, general
```

### (d) Valid verdict

`v.verdict` MUST be one of:

```text
confirm, false_positive, needs_review
```

### (e) No duplication of deterministic flags

A note MUST NOT re-report an issue the deterministic validator already flagged
for the same document. Practically: `n.message`, `n.suggestion`, and `n.quote`
MUST NOT contain a deterministic rule_id (e.g. `SEC001`, `FP005`, `MET002`) or
a matrix_id (e.g. `APA-07`) verbatim, nor restate a deterministic check message.
The notes are expected to cover only what the deterministic checker missed.

### (f) Quote length

`n.quote` is either the empty string `""` (a section-level note with no
verbatim text) or at most ~20 words.

---

## Notes

- This document is versioned. If an assertion or enum value changes, bump the
  version and circulate before the harness is updated.
- Assertions (a)–(d) and (f) are independent of Track C. Assertion (e) consumes
  the deterministic rule/matrix ids from `app/domain/apa7_matrix.py`
  (`MATRIX_ID_MAP`), which C owns.
