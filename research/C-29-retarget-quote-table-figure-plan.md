# C-29 — Retarget block quote / table / figure (plan)

Backlog row (`docs/apa7-backlog-C.md:78`):

> C-29 | Retarget block quote/table/figure | 2 | M | docx-XML |
> `quotation_utils.py`, `caption_apa7_check.py`, `table_*`, `_apply_tracked_table_formatting` |
> SPE004/quote style, tab/figure numbering still pass; no JUTLP strings |
> existing table/figure tests ported | C-20a |
> Low risk (logic is generic) — sweep strings only

## Decision summary

- **Scope of sweep:** the row's named files **plus the adjacent quote-protection set**
  (`document_zones.py:3` / `:72`) and the quote test docstring (`tests/test_quotation_utils.py:3`).
- **Acceptance bar:** measured on the **emitted document** — the built output gains no JUTLP
  residue (`tools/corpus/checks/residue.py`, K-H7). Internal docstrings/comments are swept as the
  row's directive, but the go/no-go gate is emitted-document residue.
- **Tests:** existing suite only — no new tests.

## Reality vs. the row

The row says "logic is generic — sweep strings only", which is confirmed: every pass in this area
is already APA-generic. The only work is removing residual JUTLP wording and verifying.

### Residual JUTLP strings (cosmetic only — docstrings/comments, zero behaviour change)

| File:line | Current | Change to |
|---|---|---|
| `app/services/quotation_utils.py:3` | "JUTLP house policy: direct quotations must retain…" | "House policy: direct quotations must retain…" |
| `app/services/quotation_utils.py:28` | "…some JUTLP submissions cite non-English sources" | "…manuscripts may cite non-English sources" |
| `app/services/table_section_boundary_comments.py:3` | "JUTLP/APA style expects a table…" | "APA style expects a table…" |
| `app/services/document_zones.py:3` | "A JUTLP paper has three distinct zones…" | "An APA manuscript has three distinct zones…" |
| `app/services/document_zones.py:72` | "…punctuation — JUTLP house policy." | "…punctuation — house policy." |
| `tests/test_quotation_utils.py:3` | "…underpins JUTLP's policy that direct quotations…" | "…underpins the policy that direct quotations…" |

### Already clean / out of scope (no change)

- `caption_apa7_check.py` — docstring + `_COMMENT_TEMPLATE` already say "APA 7"; no JUTLP.
- `table_n_notation_comments.py`, `table_keep_together.py`, `table_page_breaks.py` — no JUTLP.
- `_apply_tracked_table_formatting` (`app/services/output_generation_samfix.py:9237`) and the
  quote/figure path in `_apply_body_and_reference_style_fixes` (`:9308`) — no JUTLP strings;
  captions/quote styles are journal-neutral ("Table Number", "Table Title", `FIGURE_NUMBER_STYLE`,
  `QUOTE_STYLE_ID`, "Quote"). **Correction (see outcome):** the *file* DOES emit JUTLP strings
  elsewhere (`:948`, `:2742`, `:4851`, `:4855`) — the row's named function does not, but the
  emitted-document gate covers the whole build, so those were swept too.
- `output_generation_samfix.py:8200` ("JUTLP/Word-default heading definitions") — belongs to C-23,
  not this row.

## Implementation outcome — the residue gate widened the sweep

The plan's 6-string sweep was **not sufficient** to pass the emitted-document gate. Building
`seed-01` and running K-H7 failed with `JUTLP-specific residue … in word/comments.xml`. Root
cause: `app/domain/canonical_jultp_template.py` emits author-facing **Author Queries** prefixed
`"JUTLP policy: …"` (`missing_section_queries`, `combined_results_discussion_query`). The gate
scans every `word/*.xml` part (incl. `comments.xml`), so the real scope is *every string that can
be emitted*, not just the row's named files.

Widened sweep (all author-facing / emitted — verified no residual `JUTLP` in these files):

| File:line | Change |
|---|---|
| `app/domain/canonical_jultp_template.py:179,183,187,192` | `"JUTLP policy: …"` → `"House policy: …"` |
| `app/services/output_generation_samfix.py:948` | `"…matches JUTLP title formatting."` → `"…matches APA title formatting."` |
| `app/services/output_generation_samfix.py:2742` | `"…as required by JUTLP style…"` → `"…as required by house style…"` |
| `app/services/output_generation_samfix.py:4851` | `"…paste in the JUTLP banner."` → `"…paste in the banner."` |
| `app/services/output_generation_samfix.py:4855` | `"…insert the JUTLP text box."` → `"…insert the text box."` |
| `app/services/appendix_removal.py:58` | `"JUTLP does not accept appendices…"` → `"Appendices are not accepted…"` |
| `app/services/blinded_citation_comments.py:59` | `"JUTLP publishes identified…"` → `"The journal publishes identified…"` |
| `app/services/reference_order_comments.py:63` | `"APA 7 (JUTLP house style) requires…"` → `"APA 7 requires…"` |
| `app/services/jutlp_validator.py:173` | `"…not in the JUTLP expected set…"` → `"…not in the expected set…"` |

Same-policy *source* docstrings swept for consistency with the adjacent quote set (non-emitted):
`abbreviation_corrections.py:12,134`, `decimal_corrections.py:150`.

**Residue-pattern trap:** K-H7 also flags `\bThis\s+Journal\b`. The obvious wording
`"This journal publishes…"` (blinded-citation comment) trip-wires it — use `"The journal…"`.

**Test knock-ons updated** (both asserted the old emitted wording):
- `tests/test_appendix_removal.py:3,124,147` — `"JUTLP does not accept appendices"` → `"Appendices are not accepted"`.
- `tests/test_blinded_citation_comments.py:49` — was `assert "jutlp" in texts[0].lower()` → now asserts `"identified"` / `"non-blinded"`.
- `tests/test_output_generation.py:275,280` — MET900 pass-through literal updated to `"not in the expected set"`.

**Gate result after the widened sweep:** `seed-01`, `seed-03`, `seed-04` → `residue: pass`;
`seed-02` → `na` (input already contains residue, by design). 188 focused C-29 tests pass.

### Second batch — non-`JUTLP` residue patterns the seeds don't trigger

The gate scans for `Practitioner Notes`, `CRediT`, `This Journal` too, not just `JUTLP`. Cheap,
same-class fixes applied (still string-only):

| File:line | Change |
|---|---|
| `app/domain/canonical_jultp_template.py:193` | `"…This Journal does not include…"` → `"…The journal does not include…"` |
| `app/services/decimal_corrections.py:58` | `"This Journal reports to two decimal places…"` → `"The journal reports…"` |
| `app/services/output_generation_samfix.py:3249` | dropped stale `"under Practitioner Notes"` from the keywords comment |
| `app/services/jutlp_validator.py:82,388,397` | `"JUTLP requires it…"` / `"the JUTLP template requires one"` → `"The template…"` |
| `app/services/jutlp_validator.py:707` | `"JUTLP does not accept equal contributing author statements."` → `"equal-author statements are not accepted."` |

### Open scope decisions (NOT changed — need a call)

These emitted strings still trip K-H7, but changing them is a **product/oracle** decision, not a
"retarget" string:

1. **`CRediT` guidance comments** — `output_generation_samfix.py:4571` (`_NUMBERED_AUTHOR_BODY_COMMENT`),
   `:4605` (empty-Acknowledgements message), `:4649` ("Acknowledgements is missing CRediT author
   contributions" + `https://credit.niso.org/` URL). Do we still want CRediT guidance? If yes, K-H7
   must stop treating the word as residue; if no, delete the guidance.
2. **Over-broad `credit` pattern** — K-H7's `credit` rule is `re.compile(r"\bCRediT\b", re.IGNORECASE)`.
   `IGNORECASE` makes it match the ordinary word **"credit"** (and the `credit.niso.org` URL) anywhere.
   That is very likely a **checker bug**: the pattern should be case-sensitive, or match the
   JUTLP-specific "CRediT author statement" block rather than the bare word.
3. **Other `JUTLP` literals outside the emitted path** — `output_filename.py` `JOURNAL_NAME = "JUTLP"`
   (filename convention, separate task), `jutlp_articles.py` fallback article prose (real article
   text, not emitted), and `__main__`/path literals. Left alone.

**Verdict:** the row's "2 points, low risk, sweep strings only" is only true for the emitted path
the seeds exercise; a truly residue-clean build across all documents needs decisions 1–2 above —
**deferred to backlog row `C-31`** (`docs/apa7-backlog-C.md`).

## Tests (already present, APA-neutral)

`tests/test_quotation_utils.py` (~12), `test_caption_apa7_check.py` (7),
`test_table_n_notation_comments.py` (6), `test_table_keep_together.py` (7),
`test_table_section_boundary_comments.py` (8), `test_table_page_breaks.py` (6);
style passes in `tests/test_body_llm_edits.py` (quote + `_apply_tracked_table_formatting`,
lines 470–1016), `tests/test_sam_fixes_validator_rules.py` (STY003/STY004/TAB001).

## Verification (PowerShell, from repo root)

1. Subsystem behaviour unchanged (widened to every touched module):
   `.venv\Scripts\python.exe -m pytest -q tests/test_quotation_utils.py tests/test_caption_apa7_check.py tests/test_table_n_notation_comments.py tests/test_table_keep_together.py tests/test_table_section_boundary_comments.py tests/test_table_page_breaks.py tests/test_body_llm_edits.py tests/corpus/test_residue.py tests/test_appendix_removal.py tests/test_blinded_citation_comments.py tests/test_reference_order_comments.py tests/test_abbreviation_corrections.py tests/test_decimal_corrections.py tests/test_output_generation.py`
   → `188 passed`.
2. Quote / figure-table validator checks — SPE004 (`jutlp_validator.py:614` → APA-14),
   `check_figure_table_structure` (`:632`, FIG001/FIG002/TAB001/TAB002 → APA-15) via
   `tests/test_sam_fixes_validator_rules.py`.
3. Emitted-document acceptance — build an output over a clean seed doc, then:
   `.venv\Scripts\python.exe -m tools.corpus.harness --docx <built output>.docx --input tests\corpus\seed\seed-01.docx --checks residue`
   Expect `pass`; plus `tests/corpus/test_residue.py`.
4. Ruff on touched files (expect only pre-existing findings):
   `.venv\Scripts\ruff.exe check app/services/quotation_utils.py app/services/table_section_boundary_comments.py app/services/document_zones.py tests/test_quotation_utils.py`

## Notes

- Backlog row lists dep **C-20a**, but the graph (`docs/apa7-backlog-C.md:139`) shows
  `C-25 ─ C-26 ─ C-29`; confirm C-25/C-26 are done first.
- On completion, add the C-29 done-marker to `docs/apa7-backlog-C.md:78`.
