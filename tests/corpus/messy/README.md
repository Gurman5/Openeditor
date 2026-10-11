# tests/corpus/messy/ — what is NOT in the APA 7 corpus

This folder only holds this README. **Do not put any `.docx` files here.**
A test (`tests/corpus/test_messy_readme.py`) fails if one appears.

## Excluded from the corpus

| Source | Why it's excluded |
|---|---|
| `tests/jutlp_sample_docx_test_pack/` (7 files, listed below) | Built for the old JUTLP journal template, not APA 7 |
| Any local **AI_Pool** drive copies | Same JUTLP shape, and not ours to redistribute |

The JUTLP pack contains:

- `01_valid_identified.docx`
- `02_missing_method_subsection.docx`
- `03_front_page_issues.docx`
- `04_structure_and_endmatter_issues.docx`
- `05_valid_deidentified.docx`
- `06_deidentified_author_leak.docx`
- `06_deidentified_with_author_leak.docx`

These documents follow JUTLP rules (Practitioner Notes, banner/textbox front
matter, journal-specific front-page and end-matter checks). Scoring them
against APA 7 rows would produce misleading conformance numbers, and a
"valid" JUTLP file is not a known-good APA 7 file.

## Rules

- **Don't** copy them into `tests/corpus/**`.
- **Don't** use them as `--base` for `python -m tools.corpus.inject`.
- **Don't** add them to any `manifest.json`.
- **Don't** commit AI_Pool files at all.
- Leave `tests/jutlp_sample_docx_test_pack/` where it is and unchanged
  (Track C asked for that).

## What they *can* be used for

Ad-hoc "does the engine survive messy input?" smoke tests, run by hand from
their current location. Results from them never count toward any conformance
score, baseline, or report.

## Where the real corpus lives

| Folder | Contents | Ticket |
|---|---|---|
| `tests/corpus/seed/` | the 4 web-sourced APA 7 seed docs + `manifest.json` | K-0.1 |
| `tests/corpus/real/` | team-owned, consented docs (git-ignored) | K-P1 |
| made at test time | injected docs from `tools.corpus.inject`, and the synthetic fixture from `tools.corpus.fixtures` | K-I*, K-0.3a |
