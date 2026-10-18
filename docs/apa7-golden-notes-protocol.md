# APA 7 Golden-Notes Protocol

Version 1.0 (Track D, D-18). Defines how the LLM editorial-review stage is
evaluated against a human-reviewed golden set, so future runs can be compared
against a fixed baseline.

## Purpose

Produce a human-scored baseline of "what good APA 7 editorial notes look like".
Each note is scored on three binary assertions so a subjective review stays
reproducible.

## The three assertions

For every note, answer yes/no:

1. **Genuine** — the note points at a real, checkable issue in the manuscript
   (not a hallucination or a phantom "missing section").
2. **Actionable** — the suggestion is specific enough that an author could act
   on it (a concrete fix, not vague praise or a full rewrite).
3. **Correctly scoped** — the `category` is in the D-01 enum, the `section`
   matches where the issue actually lives, and the `severity` is proportionate.

## Procedure

1. Run the LLM stage on each corpus document:
   `python -m app.services.ai.cli --docx tests/corpus/seed/seed-NN.docx --out notes-seed-NN.json`
2. For each note, score the three assertions.
3. Record the result in the table below.
4. Flag any note where an assertion fails, with a one-line reason.

## Results (first-pass; confirm before finalising)

| Doc | # | Category | Genuine | Actionable | Scoped | Concern |
|---|---|---|---|---|---|---|
| seed-01 | 1 | conclusion_quality | y | y | y | |
| seed-01 | 2 | conclusion_quality | y | y | y | |
| seed-01 | 3 | general | y | y | y | borderline structural (subheadings) |
| seed-02 | 1 | general | y | y | y | |
| seed-02 | 2 | method_quality | y | y | y | |
| seed-02 | 3 | apa_style | y | y | y | |
| seed-02 | 4 | results_quality | y | y | y | |
| seed-02 | 5 | discussion_quality | y | y | y | |
| seed-02 | 6 | discussion_quality | y | y | y | |
| seed-02 | 7 | conclusion_quality | y | y | y | |
| seed-02 | 8 | conclusion_quality | y | y | y | |
| seed-03 | 1 | title_quality | y | y | y | |
| seed-03 | 2 | abstract_quality | y | y | y | |
| seed-03 | 3 | abstract_quality | **n** | y | y | false premise: "one can conclude" is not first-person |
| seed-03 | 4 | method_quality | y | y | y | |
| seed-03 | 5 | method_quality | y | y | y | |
| seed-03 | 6 | method_quality | y | y | y | |
| seed-03 | 7 | method_quality | y | y | y | |
| seed-03 | 8 | results_quality | y | y | y | |
| seed-03 | 9 | results_quality | y | y | y | |
| seed-03 | 10 | discussion_quality | y | y | y | |
| seed-03 | 11 | discussion_quality | y | y | y | |
| seed-03 | 12 | discussion_quality | y | y | y | |
| seed-03 | 13 | discussion_quality | y | y | y | |
| seed-03 | 14 | conclusion_quality | y | y | **partial** | section says "Discussion > In conclusion" |
| seed-03 | 15 | general | y | y | y | redundant with #6/7/12/13 (first-person) |
| seed-04 | 1 | title_quality | y | y | y | |
| seed-04 | 2 | abstract_quality | y | y | y | |
| seed-04 | 3 | introduction_quality | **n** | **n** | **n** | flags missing intro (deterministic); section "Abstract" |
| seed-04 | 4 | conclusion_quality | y | y | y | |
| seed-04 | 5 | apa_style | y | y | y | |

## Summary

- 31 notes across 4 corpus docs (seed-01..04).
- 28 notes pass all three assertions.
- 3 notes flagged: seed-03 #3 (false premise), seed-04 #3 (false-positive /
  wrong section), seed-03 #15 (redundancy).
- One category/section mismatch (seed-03 #14).

Note: the plan requested 5 docs; only 4 seed docs exist (`seed-01..04`). A 5th
row is added when K completes the corpus seed.
