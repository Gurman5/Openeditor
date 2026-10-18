# APA 7 LLM Cost / Latency

Generated 2026-10-18. Model: `gpt-5.4-mini`. Corpus: `tests/corpus/seed` (4 docs).

## Per-document measurement

| doc | prompt_tokens | completion_tokens | total_tokens | latency (s) |
|---|---|---|---|---|
| seed-01.docx | 4450 | 392 | 4842 | 3.7 |
| seed-02.docx | 7249 | 1091 | 8340 | 5.1 |
| seed-03.docx | 6168 | 1555 | 7723 | 6.7 |
| seed-04.docx | 4591 | 496 | 5087 | 3.2 |

## Totals

- Prompt tokens: 22,458
- Completion tokens: 3,534
- Total tokens: 25,992
- Total latency: 18.7 s (avg 4.7 s/doc)

## Cost extrapolation

Pricing (VERIFY against current OpenAI pricing page; date-stamped above because
prices drift):

- Input: `$0.15 / 1M tokens`
- Output: `$0.60 / 1M tokens`

Using those placeholder rates:

- 4-doc batch: input `22458 × 0.15 / 1M ≈ $0.0034` + output `3534 × 0.60 / 1M ≈ $0.0021` → **≈ $0.0055**
- Per-doc average: **≈ $0.0014**
- Extrapolated 30-doc corpus: **≈ $0.04**

## Budget flag

- Cost is negligible; the binding constraint is **latency** (~5 s/doc, ~2 min for
  a 30-doc corpus) and the **15k-word manuscript cap** (D-13), not money.
- Flag for review if any single document's `total_tokens` approaches the
  `OPENAI_MAX_TOKENS` ceiling (16384). The largest observed was 8,340
  (seed-02), ~51% of ceiling.
