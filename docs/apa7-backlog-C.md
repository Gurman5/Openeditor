# DEV TASK BACKLOG — TRACK C (APA‑7 deterministic/output layer)

Repo verified at commit `6159ea1` (branch `dev`). Every path below verified in-repo unless marked **UNVERIFIED**.
Plan-vs-code contradictions are called out inline.

## Locked client decisions (this revision)

| # | Decision | Value | Backlog impact |
|---|---|---|---|
| D1 | Student vs professional default | **Auto-detect + manual override** | C-24b keeps env/arg override |
| D2 | Default font / headings | **Calibri, 11pt, kept for headings + body** | C-15 defaults; C-23 headings Calibri; C-27 sweeps to allowed set with Calibri default |
| D3 | Spelling variant | **AU (confirmed)** | No inversion of `language_corrections.AU_CORRECTIONS` (already US→AU); C-16 is label-only |
| D4 | Article carousel | **KEEP** (do not remove) | C-14 retargets/de-JUTLPs the carousel instead of deleting it |
| D5 | Corpus | **Assume a Track K corpus exists** | C-02 baseline, C-44 CLI and gates run against K's corpus |

## Key verifications / plan-vs-code contradictions

- Config path: notes say `app/config.py`; repo has **`app/services/config.py`** and **no `app/config.py`** (verified). Backlog targets `app/services/config.py`.
- `canonical_jultp_template` is imported in **13 files / 17 references** (8 app modules, 4 tests) — not "~15 files". Full list: `output_generation.py` (x2), `heading_corrections.py`, `output_generation_samfix.py`, `document_analysis_services.py`, `reference_checker.py`, `document_zones.py`, `jutlp_validator.py`, `document_styling_fixes.py`; tests `test_abstract_length_rule.py`, `test_heading_corrections.py`, `test_jutlp_validator.py`, `test_front_page_style_fixes.py`.
- `reporting_ownership.py`: `is_sam_fixed`/`SAM_FIXED_RULE_IDS` used by `main.py:33,1126,1156` and `feedback_gen_pipeline.py:51,736`; **`FAMILY_VERDICTS` has no production consumer** — only `tests/test_reporting_ownership.py`. `main.py` categories (lines 1132–1150) and `openeditor.js` (lines 59–63) hardcode JUTLP prefixes independently. No ticket existed — added.
- `_to_title_case_title` (line 479) **is NOT the bug locus**: running it in isolation returns `'Task One' -> 'Task One'`, `'TASK ONE' -> 'Task One'` (verified). The "Task One→lowercase" defect is in the replacement/integration path (`_apply_title_text_tracked_changes` line 6059, `_apply_heading_2_title_case` line 9547, `_set_paragraph_text_direct` line 9073, or `_fix_au_spellings_in_text` ordering). C-30 is scoped accordingly.
- Frontend: `writer.html` loads **`openeditor.js`** (lines 9, 379). `script.js` is a **dead duplicate** carousel (not loaded). Since the carousel is kept (D4), C-14 removes the dead copy and retargets the live one rather than deleting the feature.
- `build_edited_document` is **9831 lines**; `_TEMPLATE_PATH` at line 291 → `domain/JUTLP Template 2026.docx` (exists). No APA base `.docx`.
- No headless whole-pipeline batch runner exists: `cli_copybot.py` runs `build_edited_document` only (no `validate`/refs/LLM). New CLI needed (C-44).
- `feedback_gen_pipeline.py` reseeds `next_lang_id = _max_revision_id(...) + 1` at line 797 and again line 1034. `_max_revision_id` at line 75.
- `_build_changes_made` (`main.py:511`) reads `appendix_actions` (line 536) — deleting the appendix pass must remove this key or the count undercounts. `short_paragraph_actions` already uncounted.

---

## 0. STAGE 0 — SAFETY NET

| ID | Title | Stage | Size | Owner | Scope (verified) | Acceptance | Verification | Deps | Risk + mitigation |
|---|---|---|---|---|---|---|---|---|---|
| C-00 | Branch + freeze + baseline test snapshot | 0 | S | backend/QA | `git`; no src edits | Branch `apa7-rework` off `6159ea1`; `pytest` result snapshot committed to `docs/`; tag `apa7-baseline` | `git checkout -b apa7-rework && python -m pytest -q \| Tee-Object docs/baseline-pytest.txt` | K corpus present (D5) | Tests fail on `06_deidentified_author_leak.docx` fixture (known) — record as baseline, not new breakage |
| C-01 | Pass-order + revision-id ledger for `feedback_gen_pipeline.py` | 0 | M | backend | `feedback_gen_pipeline.py` whole `doc_analysis_pipeline` | Markdown table: every pass in order, its terminal state, whether it takes `next_lang_id` vs hardcodes `change_id` (e.g. `_apply_title_text_tracked_changes` seeds 1; samfix table pass seeds 8000; pipeline reseeds at 797/1034), and comment-only vs tracked-change | Review doc against code; a new pass's placement and id source is unambiguous from the table | none | Ledger drifts from code — regenerate from a `grep` recipe embedded in the doc |
| C-02 | Baseline output artefacts over K corpus | 0 | S | QA | K corpus docs; `docs/apa7-baseline-outputs/` | 3–5 original→reviewed pairs saved before any change; SHA recorded | Re-run current engine, compare bytes/notes | C-00 + K corpus | LLM nondeterminism — run with `OPENAI_API_KEY` unset for the deterministic baseline |

**Gate 0 exit:** branch exists, baseline pytest + baseline output pairs recorded, pass-order ledger exists. Nothing is deleted before K's baseline run exists.

---

## 1. STAGE 1 — CUT JUTLP

### C‑Create

| ID | Title | Stage | Size | Owner | Scope (verified) | Acceptance | Verification | Deps | Risk + mitigation |
|---|---|---|---|---|---|---|---|---|---|
| C-10 | Create `app/domain/apa7_template.py` | 1 | M | backend | new file; port `strip_leading_section_number`, `_normalise_subsection`, `subsection_alias_match` from `canonical_jultp_template.py:11–53`; define `CANONICAL_STRUCTURE_APA7` (student/prof front page, abstract ≤250 no line-region, Method/Results/Discussion expected, References, appendices allowed) | Imports clean; no `practitioner_notes*`/`abstract_line_region` keys; exports the 3 helpers by same names | `python -c "from app.domain.apa7_template import CANONICAL_STRUCTURE_APA7 as C; assert 'practitioner_notes_heading' not in C['front_page']; print('ok')"` | none | Behaviour drift from old helpers — copy helpers verbatim, add unit tests (C-46) |
| C-11 | Atomic import sweep → `apa7_template` | 1 | M | backend | 8 app modules + 4 tests (list above) | Every `from app.domain.canonical_jultp_template import X` now imports from `apa7_template`; tree never half-imports | `rg "canonical_jultp_template" app tests` returns **0**; `python -c "import app.main"` clean | C-10 | Missed dynamic/local import (`output_generation.py:838,925` are function-local) — grep exactly, not just top-of-file |
| C-12 | Delete JUTLP domain files | 1 | S | backend | `app/domain/canonical_jultp_template.py`, `jutlp_guidelines.py`, `jutlp_editorial_examples.py`; defer `jutlp_template_style_map.json` until C-47 | Files gone; `pytest` collection still green | `python -m pytest --collect-only -q` | C-11 | `jutlp_guidelines`/`examples` imported only by D-owned `prompt_builder.py:3–4` — **CROSS-TRACK REQUEST D‑1**, do not delete before D repoints |
| C-13 | Delete JUTLP-only passes + pipeline rows | 1 | M | backend | `app/services/appendix_removal.py`, `short_paragraph_comments.py`, `blinded_citation_comments.py`; `feedback_gen_pipeline.py` imports (17,18,44) + call blocks (981,994,1074) + return keys (1129,1133) | Removed; pipeline returns no `appendix_actions`/`short_paragraph_actions` | `python -c "import app.pipelines.feedback_gen_pipeline"`; run C‑44 CLI on a doc → no appendix/blinded comment | C-00 | `_build_changes_made` still reads `appendix_actions` (C-42 must land same PR) |
| C-14 | Keep carousel; de-JUTLP + retarget feed | 1 | M | frontend | keep `app/main.py` `/api/jutlp-articles` feature; rename endpoint/copy to generic (e.g. `/api/articles`); `writer.html:90–101`, `openeditor.js:17–26,322–353`, `api.js:162+`; **delete dead `script.js` carousel duplicate** | Carousel still renders and rotates; no JUTLP branding in UI/copy; no duplicate dead implementation | `rg -i "jutlp" app/templates app/static` returns 0 branding hits; carousel visible in `writer.html` run | **Client D4 = KEEP** | Feed still scrapes `open-publishing.org` (JUTLP journal) — confirm data source (see Open decisions); keep fallback article as safety net |
| C-15 | APA config module | 1 | S | backend | `app/services/config.py` (append); **no `app/config.py`** | Adds `ALLOWED_FONTS`, `DEFAULT_FONT="Calibri"`, `DEFAULT_FONT_SIZE=11`, `HEADING_FONT="Calibri"`, `DEFAULT_MODE="auto"`, `SPELLING_VARIANT="AU"`, `MARGIN_IN=1.0`, `DOUBLE_SPACING_TWIPS=480`, `FIRST_LINE_INDENT_IN=0.5` | `python -c "from app.services import config as c; print(c.DEFAULT_FONT, c.SPELLING_VARIANT)"` | D2, D3 | Config duplication (services vs a new app/config) — keep single module, document in AGENTS |
| C-16 | De-JUTLP user-facing strings sweep | 1 | M | backend | `decimal_corrections.py:150`, `keywords_generation.py:3,36,68,77` (D-owned — coordinate), `spell_checker.py`, `acronym_corrections.py`, `reference_format_corrections.py`/`reference_order_comments.py` comments, `main.py:_build_summary`, `output_generation.py` labels; **keep AU correction direction** | No `"JUTLP"`/`"Practitioner Notes"` in any author-facing string; AU→ output unchanged (`AU_CORRECTIONS` stays US→AU) | `rg -i "jutlp\|practitioner notes" app/services app/templates` in author-facing comment constants returns 0; `pytest tests/test_language_corrections.py tests/test_spell_checker.py` | C-12/C-13, D3 | D-owned files — split scope; C does message text, D does prompt framing (**CROSS-TRACK D‑2**). Do **not** invert `language_corrections.py` (D3=AU) |
| C-17 | Output filename scheme | 1 | S | backend | `output_filename.py:9` `JOURNAL_NAME="JUTLP"`; `cli_copybot.py:61` `_JUTLP_` check | Filename `Author_OpenEditor_Year_CopyEdit1.docx` (or client-chosen); no `_JUTLP_` | `python -m pytest tests/test_output_filename.py` (updated) | C-15 | Other callers may assert `_JUTLP_` — grep tests |

### C‑Validator

| ID | Title | Stage | Size | Owner | Scope (verified) | Acceptance | Verification | Deps | Risk + mitigation |
|---|---|---|---|---|---|---|---|---|---|
| C-20a | `apa7_validator.py` scaffold + family triage | 2 | M | backend | new file from `jutlp_validator.py`; `validate()` (755–784) keeps STY/TAB/FIG/SPE004/REF; **disables** SEC/MET/DIS/FP/CON/AFF/ANDOR/ETC/DOTPT/SPE001–3/STY002; every emitted result has `matrix_id` | `validate()` emits only kept + new APA ids; each dict has `matrix_id` | `python -c "from app.services.apa7_validator import validate; r=validate('tests/jutlp_sample_docx_test_pack/01_valid_identified.docx'); assert all('matrix_id' in x for x in r['results'])"` | C-10 | Removing SEC kills `REF001` duplicate-suppression assumptions in `main.py:1193` (C-40) |
| C-20b | APA‑00..APA‑20 checks | 2 | L→split M+M | backend/docx-XML | New `check_*` for APA-00,01,02,03,04,05,08,09,10,11,19; APA-06/07/12–18 retarget/verify existing | One check per matrix row, each returns `matrix_id`; fires on a purpose-built bad doc | `python -m pytest tests/test_apa7_validator.py` | C-20a, C-47 (reads base styles) | XML reading duplicates output passes — share a helper `apa7_xml_probe.py` so validator and builder agree |
| C-21 | Matrix-id map + tests | 2 | M | backend | new `app/domain/apa7_matrix.py` `MATRIX_ID_MAP` (legacy id → matrix_id, e.g. `FP001→APA-07`, `SPE004→APA-14`, `TAB001→APA-15`, `STY003/4→APA-01/03`, `new APA001→APA-00`) | Single source consumed by validator, main.py, CLI; K's gold labels resolve 1:1 | `python -m pytest tests/test_apa7_matrix.py`; every matrix row has ≥1 id and no id maps to 2 rows | C-20a, **K's agreed matrix (K-1)** | Ambiguous mapping — publish provisional map, mark edges provisional, K ratifies |

### C‑Output

| ID | Title | Stage | Size | Owner | Scope (verified) | Acceptance | Verification | Deps | Risk + mitigation |
|---|---|---|---|---|---|---|---|---|---|
| C-22a | APA body: margins + spacing + align | 2 | M | docx-XML | new `_apply_apa_body_geometry` in `output_generation_samfix.py`; `sectPr` (APA-00, 1440 twips), Normal `w:spacing line=480`, `w:jc=left` (APA-01/03) | `sectPr` pgMar all 1440; Normal line=480; body `jc=left`; tracked | Open output zip: assert `pgMar`=1440, `w:spacing w:line="480"`, no `w:jc val="both"` | C-47, C-01 | Replaces `BODY_REQUIRED_LINE_SPACING=1.15` (3795) & justified pin — remove those constants same PR |
| C-22b | APA first-line indent + page number | 2 | M | docx-XML | `_apply_apa_body_geometry` continues; first-line indent 720 twips (APA-04); PAGE field top-right header (APA-05) | Body paras `w:ind firstLine=720`; header has PAGE field, right-aligned, present on title page | XML assert on a doc with no header | C-22a | Header inherits from template — ensure sectPr titlePg semantics |
| C-23 | APA heading levels 1–5 (Calibri) | 2 | M | docx-XML | replace `CENTER_ALIGNED_HEADING_TEXTS` (3862) policy; restyle `Heading 1..5` per APA-11; **Calibri** per D2; keep `keepNext` (9707) | L1 centered bold, L2 flush-left bold, L3 flush-left bold-italic, L4 indent bold, L5 indent bold-italic; title case; no break after; font Calibri | `python -m pytest tests/test_heading_restyle_formatting.py` (ported) | C-47, D2 | Style ids come from base .docx — blocked by C-47 |
| C-24a | Title page rebuild (student) | 2 | M | docx-XML | new `_apply_apa_title_page`; delete `_insert_front_page_banner_from_template` (5373) + `_insert_front_page_text_box_from_template` (5519) calls | No `w:txbxContent`/banner; title bold centered upper half, authors, affiliation, course, instructor, due date | `python -c "...iter over txbxContent == []"`; screenshot of title page | C-47 | Existing `_apply_title_plan` overlaps — merge, don't stack |
| C-24b | Title page professional variant | 2 | M | docx-XML | `_apply_apa_title_page(mode=…)`; running head (APA-06); auto-detect + override (D1) | Pro adds ≤50-char ALL-CAPS running head, author note; no course line; `mode` override honoured | toggle mode arg in test | C-24a, C-15, D1 | Mode detection ambiguity — default auto-detect + env override |
| C-25 | References block APA-12 | 2 | M | docx-XML | page-break before References (keep `check_page_break_before_references`), bold centered heading, keep `reference_indent_corrections.py` hanging indent, order comment | References start new page; "References" bold centered; hanging indent 720; alpha order comment retained | existing ref indent tests + new page-break assert | C-47 | Reference style string `"APA 7 Reference List Entry"` is template-bound — retarget to APA base |
| C-26 | Abstract/keywords APA-08/09 | 2 | M | docx-XML | `document_analysis_services.extract_abstract/extract_keywords` boundaries, delete `extract_practitioner_notes`; `_apply_abstract_plan`/`_apply_keywords_plan` | "Abstract" bold centered, ≤250 word comment; italic "Keywords:" indented | ported `test_abstract_length_rule.py` (no line-region) | C-47 | JUTLP line-region logic embedded — remove, not toggle |
| C-27 | Allowed-font sweep APA-02 (Calibri default) | 2 | M | docx-XML | `run_font_corrections.py:30 _TARGET_FONT="Arial"` → `config.DEFAULT_FONT` (Calibri); `_apply_normal_style_fix` (5982) Arial pin → allowed set with Calibri default | Every run/normal style ∈ `ALLOWED_FONTS`; non-allowed swapped, tracked; Calibri untouched | `python -m pytest tests/test_run_font_corrections.py tests/test_body_font_enforcement.py` (ported) | C-15, C-47, D2 | Client default locked (Calibri) — constant-driven |
| C-28 | Intro heading APA-10 | 2 | S | docx-XML | `_apply_heading_1_text_normalization` (9521) → repeats title bold centered, no literal "Introduction" heading | Output has no "Introduction" H1; title repeated | XML assert | C-47 | Overlaps C-23 heading pass — order: C-23 before C-28 |
| C-29 | Retarget block quote/table/figure | 2 | M | docx-XML | `quotation_utils.py`, `caption_apa7_check.py`, `table_*`, `_apply_tracked_table_formatting` (9079) | SPE004/quote style, tab/figure numbering still pass; no JUTLP strings | existing table/figure tests ported | C-20a | Low risk (logic is generic) — sweep strings only |
| C-30 | Title-case replacement bug | 3 | S | docx-XML | **not** `_to_title_case_title` (verified correct); suspect `_apply_title_text_tracked_changes` (6059) word-diff or `_apply_heading_2_title_case` (9547) re-caser or `_fix_au_spellings_in_text` ordering (795/823/873) | Failing integration test first: doc titled `task one` → output `Task One` (not lowercase); fix identified path | `python -m pytest tests/test_title_fixes.py -k task_one` | C-02 repro | Root cause unconfirmed — write the failing test before touching logic (**UNVERIFIED** mechanism) |

**Gate 2 exit:** a bad input doc produces an output with 1" margins, `line=480`, left-aligned, 0.5" indent, PAGE field, APA heading levels (Calibri), APA title page, References new page + hanging indent, allowed fonts, no txbxContent/banner/Practitioner Notes. Demo artefact: before/after pair.

---

## 2. STAGE 3 — PLUMBING, TESTS, SHIP

### C‑Plumbing

| ID | Title | Stage | Size | Owner | Scope (verified) | Acceptance | Verification | Deps | Risk + mitigation |
|---|---|---|---|---|---|---|---|---|---|
| C-40 | `main.py results()` categories via matrix map | 3 | M | backend | replace prefix buckets (1132–1150) and warn-include prefix test (1178–1183) with `MATRIX_ID_MAP` lookups; keep `fp_overrides` (1111–1115) | Categories derived from matrix rows; no JUTLP prefix strings in `results()` | `rg "SEC\|MET\|DIS\|FP\|STY" app/main.py` → only map refs | C-21 | `REF001` suppression (1193) assumed SEC008 — re-derive from matrix |
| C-41 | `reporting_ownership.py` rewrite | 3 | M | backend | `SAM_FIXED_RULE_IDS` (28–31), `FAMILY_VERDICTS` (49–101) → APA rule ids; both test files (`test_reporting_ownership.py`, `test_sam_fixes_validator_rules.py`) updated incl. hardcoded path `jutlp_validator.py` (line 39) and set assertion (line 200) | Tests green; `FAMILY_VERDICTS` matches APA families | `python -m pytest tests/test_reporting_ownership.py tests/test_sam_fixes_validator_rules.py` | C-20a | Tests read `app/services/jutlp_validator.py` by literal path — must repoint to `apa7_validator.py` |
| C-42 | `_build_changes_made` key sweep | 3 | S | backend | `main.py:511–560`: drop `appendix_actions` (536); add new APA pass keys; ensure no undercount | `changes_made.total` equals sum of live pass outputs | unit test feeding a synthetic pipeline_result | C-13, C-22/C-23 | Silent undercount — assert total == sum(groups) |
| C-43 | Frontend category mapping | 3 | M | frontend | `openeditor.js:59–63 _manualReviewCategory`; `writer.html` result render; `api.js` | Categories match payload; no JUTLP regex | manual run + `rg "SEC\|MET\|DIS\|CON\|SPE\|FIG\|TAB\|FP\|AFF\|STY" openeditor.js` → only matrix-aware | C-40 | Frontend reads both `category` and prefixes — align to matrix |
| C-44 | Headless batch runner + fired matrix_ids export | 3 | M | backend | new `app/cli_apa7.py` (or extend `cli_copybot.py`); runs normalize→validate→refs→editorial→build over **K corpus** folder; writes `{file: [matrix_ids fired], ...}` JSON; add `matrix_ids` to results payload (`main.py:1250`) | `python -m app.cli_apa7 <K-corpus>/ --out results.json` runs headless; JSON has per-doc matrix_ids | run on K corpus | C-20a, C-21, K corpus, K-2 schema | **K interface** — schema agreed with K before build |
| C-45 | C↔D review-enum wiring | 3 | M | backend | `main.py _llm_notes_to_results` (401), `fp_overrides` (1111), `llm_client.py` schema (D-owned); `editorial_review_comments.py` aliases | New category/verdict enums flow end-to-end without JUTLP names | smoke test on 1 doc | **D's spec (blocked)** | Do not guess enums — dependency D‑3 |

### C‑Tests + base template

| ID | Title | Stage | Size | Owner | Scope (verified) | Acceptance | Verification | Deps | Risk + mitigation |
|---|---|---|---|---|---|---|---|---|---|
| C-46 | JUTLP test delete-vs-port sweep | 1–3 | M | QA | see table below | Green `pytest`; no test references deleted modules | `python -m pytest -q` | per-file owner | Fixture `06_deidentified_author_leak.docx` already broken — carry as xfail |
| C-47 | APA base `.docx` (BLOCKING) + `_TEMPLATE_PATH` | 1 | L→split | docx-XML | produce `app/domain/APA7 Base Template.docx` (fallback: generate via python-docx with setup-guide values, **Calibri 11**); repoint `output_generation_samfix.py:291`; delete `jutlp_template_style_map.json`; retarget `extract_template_styles` (311) | Base has APA Normal/Heading1–5/Reference styles in Calibri; all style-id resolvers point at it | open base, assert style names/fonts; full pipeline run | C-02, D2 | **Producer required** (client or C fallback). Styling tickets C-23/24/25/26/27/28 blocked until this lands |

**JUTLP test triage** (best-effort; **UNVERIFIED** where noted):

| Action | Files |
|---|---|
| Delete | `test_appendix_removal.py`, `test_short_paragraph_comments.py`, `test_blinded_citation_comments.py` |
| Replace | `test_jutlp_validator.py` → `test_apa7_validator.py`; `test_abstract_length_rule.py`; `test_intro_page_break.py`; `test_front_page_textbox_wrap.py`; `test_front_page_style_fixes.py` |
| Rewrite | `test_reporting_ownership.py`, `test_sam_fixes_validator_rules.py` |
| Port/adapt | `test_heading_corrections.py`, `test_heading_restyle_formatting.py`, `test_document_analysis_services.py`, `test_document_zones.py`, `test_editorial_review_comments.py`, `test_output_generation.py`, `test_output_filename.py`, `test_reference_*`, `test_table_*`, `test_body_font_enforcement.py`, `test_reference_justification.py`, `test_numeric_style_zoning.py`, `test_numbered_section_detection.py` |
| Keep | `test_upload_guardrails.py`, `test_access_validation.py`, `test_acronym_*`, `test_timestamps.py`, `test_placeholder.py`, `test_llm_client.py` |
| D-owned (coordinate) | `test_prompt_builder.py`, `test_body_llm_edits.py`, `test_grammar_corrections.py`, `test_sentence_coherence_corrections.py`, `test_keywords_generation.py` |
| Dead scripts | `tests/inspect_*.py`, `tests/count_refs.py`, `tests/smoke_reconstructor.py` — leave (not pytest-collected) |

---

## 2. STAGE GATES (runnable)

| Gate | Entry | Exit check | Demo artefact |
|---|---|---|---|
| 0 Safety | K corpus present | `git tag apa7-baseline`; `docs/baseline-pytest.txt`; pass-order ledger | baseline pytest log |
| 1 Cut JUTLP | Gate 0 | `rg -i "canonical_jultp\|jutlp_guidelines\|jutlp_editorial" app tests` = 0 (carousel copy de-JUTLP'd per D4); `pytest --collect-only` green | clean import tree + live carousel |
| 2 APA structural | Gate 1 + C-47 base docx | C‑22…C‑29 exit commands pass on bad doc | before/after .docx pair |
| 3 Ship | Gate 2 + D enum (C-45) | C-44 batch run over K corpus; results payload matrix_ids present | batch JSON + conformance table |

---

## 3. DEPENDENCY GRAPH + CRITICAL PATH

```
K corpus (D5) ─┐
C-00 ── C-01 ──┤
               ├─ C-10 ─ C-11 ─ C-12 ─ C-13 ─ C-42
               ├─ C-15 ─ C-27
               └─ C-47 (APA base docx) ─┬─ C-22a ─ C-22b ─ C-23 ─ C-28
                                        ├─ C-24a ─ C-24b
                                        ├─ C-25 ─ C-26 ─ C-29
C-20a ─ C-20b ─ C-21 ─┬─ C-40 ─ C-43
                      ├─ C-41
                      └─ C-44
D's spec (D-3) ─ C-45
C-30 independent after C-02
```

**Critical path:** `C-47 (APA base docx)` → C‑22a → C‑23 → C‑25 → C‑40 → C‑44. C‑47 is the single largest schedule risk.

---

## 4. PARALLELISATION INSIDE C (3–4 people) + HOT FILES

| Workstream | Tickets | Files (hard boundaries) |
|---|---|---|
| A — Delete/plumbing | C-10, C-11, C-12, C-13, C-15, C-16, C-17, C-40, C-42 | `apa7_template.py`, `config.py`, `main.py`, `output_filename.py`, pipeline imports |
| B — Validator | C-20a, C-20b, C-21, C-41, C-46 | `apa7_validator.py`, `apa7_matrix.py`, `reporting_ownership.py`, `tests/` |
| C — Output/docx-XML | C-22a/b, C-23, C-24a/b, C-25, C-26, C-27, C-28, C-29, C-30, C-47 | `output_generation_samfix.py` (**hot**) |
| D — Frontend/CLI | C-14, C-43, C-44 | `openeditor.js`, `writer.html`, `api.js`, `cli_apa7.py` |

**Hot files & merge-conflict strategy**
- `output_generation_samfix.py` (9831 lines) — **one writer at a time**. Serialise workstream C; land C‑47 first; each pass in its own commit; no two agents touch `build_edited_document` (9569) concurrently.
- `feedback_gen_pipeline.py` — C‑13 + C‑01 owner only; new passes take `next_lang_id` from the pipeline reseed, never hardcode.
- `main.py` — C‑40/C‑42/C‑45 serialise; C‑45 waits on D.
- Strategy: rebase-on-green; require `pytest -q` per PR; lock hot files via a shared "claimed" note; small commits per matrix row.

---

## 5. CROSS-TRACK REQUESTS

**To D**
- **D‑1:** D repoints `app/services/ai/prompt_builder.py:3–4` off `jutlp_guidelines`/`jutlp_editorial_examples` onto `apa7_guidelines`/`apa7_editorial_examples` **before** C‑12 deletes the originals. Ask: exact commit/PR so C can sequence.
- **D‑2:** D owns prompt-side de-JUTLP framing in `body_llm_edits.py`, `grammar_corrections.py`, `sentence_coherence_corrections.py`, `keywords_generation.py`; C only touches author-facing message constants. Keep spelling **AU** (D3). Ask: confirm the split so C‑16 doesn't collide.
- **D‑3 (blocking C‑45):** D to publish the `EDITORIAL_RESPONSE_SCHEMA` **category enum** and **verdict enum** (new values, incl. `needs_review`) as a short spec. C will not guess values.
- **D‑4:** D owns `grammar_corrections.py`/`body_llm_edits.py` but C owns `tests/` — confirm C may edit `test_grammar_corrections.py`/`test_body_llm_edits.py`.

**To K**
- **K‑00:** Provide the corpus path + run command + baseline score location; C‑00/C‑02 and the Demo consume it (D5).
- **K‑1:** K to ratify the **matrix_id → rule_id map** (C‑21) — the single join key between C's fired ids and K's gold labels. Ask: confirm APA‑00..APA‑20 coverage and whether K needs a `severity` per row.
- **K‑2:** K's output-.docx checker must read C's fired `matrix_id`s. Agree the JSON schema for C‑44 before build: `{ "file": str, "matrix_ids": [str], "counts": {matrix_id: int} }`.
- **K‑3:** Confirm corpus contains ≥1 intentional-error doc per matrix row (so C‑20b checks are exercisable).

---

## 6. RISKS / OPEN DECISIONS / OUT OF SCOPE

**Risks**
- C‑47 APA base docx is blocking for 6 styling tickets — mitigate with python-docx fallback generator (Calibri 11) so C can proceed if the client artefact slips.
- `FAMILY_VERDICTS` has no production consumer while `main.py`/frontend hardcode prefixes — three sources of truth (C‑21/C‑40/C‑41/C‑43 must converge).
- `_build_changes_made` double-counts/undercounts when pass keys change (C‑42).
- Integration bug C‑30 root cause unknown; write failing test first.
- D's enum spec gates C‑45 — if it slips, ship with `stage_errors` path and defer.
- Carousel (kept, D4) still depends on the external `open-publishing.org` scrape + 6h cache + fallback article — silent degradation possible.

**Open decisions (default assumption → impact if different)**
1. Student vs professional → **auto-detect + override** (locked D1).
2. Default font → **Calibri 11pt, headings Calibri** (locked D2).
3. US vs AU spelling → **AU** (locked D3). No `language_corrections` inversion.
4. Carousel → **keep** (locked D4). Remaining sub-decision: keep scraping JUTLP journal vs switch to a static/APA-resources feed — if static, C‑14 drops the scraper and serves a local list.
5. APA base `.docx` producer: client artefact vs C python-docx fallback (Calibri 11).

**Out of scope (confirmed):** Railway/Cloudflare deploy; MemberPress/Stripe verifiers (stay disabled); `/login`+`APP_PASSWORD` gate; clean-vs-tracked toggle (deferred, per G‑04); `references[].title` gap; D‑01/D‑02 verification.

---

## Closing deliverables

**(1) Minimum C ticket set for a credible next-session demo**
C‑00, C‑01, C‑10, C‑11, C‑13, C‑14, C‑15, C‑47, C‑22a, C‑23, C‑24a, C‑25, C‑27, C‑30, C‑42, C‑43, C‑44 (+C‑46 subset). That yields one real paper visibly transformed to APA (margins/spacing/align/indent/page number/headings/title page/References/hanging indent/fonts) with the carousel still live, and a batch JSON K can score.

**(2) First 5 C tickets to start tomorrow (dependency order)**
1. **C‑00** branch + baseline snapshot (unblocks everything; needs K corpus).
2. **C‑47** APA base `.docx` + `_TEMPLATE_PATH` (critical path; longest lead; Calibri 11).
3. **C‑01** pass-order + revision-id ledger (needed before any pipeline edit).
4. **C‑10 → C‑11** `apa7_template.py` + atomic import sweep (unblocks delete + validator).
5. **C‑15** APA config constants (unblocks C‑22/C‑27; encodes Calibri/AU locked decisions).

**(3) Client decisions needed**
- Student vs professional default — **auto-detect + override confirmed**; confirm acceptable.
- Default font/size — **Calibri 11pt confirmed**; confirm headings Calibri.
- US vs AU spelling — **AU confirmed**.
- Carousel — **kept confirmed**; confirm data source (keep JUTLP-journal scrape vs static APA-resources feed).
- APA base `.docx` producer and date (client artefact vs C python-docx fallback).
