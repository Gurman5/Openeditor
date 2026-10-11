# TRACK K — Evaluation Corpus + Conformance Harness · DEV TASK BACKLOG

Verified anchors (this revision): `docs/apa7-rework-plan.md` (matrix A rows APA-00..APA-20, eval plan §E),
`docs/Curated Refernce point (1).md`, `docs/track-c-d.md`, `docs/api-contract.md`,
`app/main.py:83-89` (MAX_UPLOAD_MB default 20, MAX_WORD_COUNT default 15000), `app/main.py:794`
(rejects `word/vbaProject.bin` + `word/embeddings/*`), `app/cli_copybot.py`,
`app/pipelines/feedback_gen_pipeline.py:657` (`doc_analysis_pipeline` — the FULL in-process pipeline),
`app/services/document_normalisation_services.py:342` (`normalise_docx`),
`app/services/reference_checker.py:28` (`_CACHE_PATH = app/services/.crossref_cache.json`),
`tests/jutlp_sample_docx_test_pack/` (7 JUTLP-shaped .docx — reference only, NOT part of the APA corpus).
`tools/` and `tests/corpus/` do **not** exist yet — create both, each with an `__init__.py`.

## Revision log — corrections applied this pass (each verified in code)

1. **Baseline entry point corrected.** The baseline MUST call
   `app.pipelines.feedback_gen_pipeline.doc_analysis_pipeline(path, output_path=...)` in-process
   (feedback_gen_pipeline.py:657). It runs `validate()` (line 710), `run_editorial_review` (line 721),
   and every post-pass. `python -m app.cli_copybot --analyse <in> --build` (cli_copybot.py:122-179)
   calls ONLY `build_edited_document` + `check_and_report` + `generate_commented_docx` — it skips
   validation, the LLM review and all post-passes, so it is **not** a valid baseline. The "folder
   runner" request to C is **removed**; K loops over the corpus and calls the pipeline in-process.
2. **C's gate re-specified.** The gate is a **git tag of the pre-deletion commit** plus a documented
   `git worktree` recipe to re-run that commit. K-0.5 split into **K-0.5a capture** (deps K-0.1) and
   **K-0.5b scoring** (deps the harness).
3. **Rejected-view text equality is invalid.** `normalise_docx` pre-accepts author revisions
   (`_accept_tracked_changes`), strips run colour/highlight, deletes Guidance Notes paragraphs and
   removes blank paragraphs; many engine edits are also untracked. The "rejected view == input"
   assertion is therefore false. Preservation compares **accepted-view text against
   `normalise_docx(input)`** using text-diff ratios; formatting checks read the **current** `pPr`/`rPr`
   and ignore `pPrChange`/`rPrChange` snapshots and `delText`.
4. **`w:id` "monotonic" → "unique".** Nothing guarantees monotonicity (`_max_revision_id`,
   feedback_gen_pipeline.py:75, only takes max+1 per reseed). The validity check asserts
   **uniqueness** and reports **duplicate-id counts** as a baseline-vs-after metric.
5. **JUTLP-residue injectors dropped.** K-I3 no longer injects "Practitioner Notes" / banner /
   textbox residue. K-H7 (negative residue) runs **only on docs whose input has no residue** (the
   seeds), so a pass/fail is meaningful.
6. **Conformance % defined:** per-rule `pass / (pass + fail)`, NA excluded, plus a **hard flag** when
   text-preservation fails. Added metrics: **defect-fix rate** on injected docs and **over-editing
   count** (tracked changes introduced on known-good docs).
7. **Two scoreboards.** (A) **LLM-off** — unset `OPENAI_API_KEY`, deterministic; this is the baseline
   that gates C. (B) **LLM-on** — a subset, `N=3` on **all 4 seeds**, for D. Persist
   `.crossref_cache.json` **per run**.
8. **Header/page-number check robust.** K-H2/K-.4 must enumerate `default`/`first`/`even` headers under
   `titlePg` + `evenAndOddHeaders`, and detect a PAGE field in **both** `w:fldSimple` (instr attr) and
   `w:fldChar`/`w:instrText` runs. The effective-format resolver must read `theme1.xml`
   (`a:fontScheme` major/minor) for theme fonts (`w:asciiTheme`, `w:hAnsiTheme`, …). No such reader
   exists today.
9. **K-0.3a added** — a synthetic known-good fixture built at test time with `python-docx`; used by CI
   instead of committing derived outputs. K-I2 font recipe fixed to **disallowed font** + **allowed
   font at the wrong size**. APA-17 (numbers/decimal policy) is marked **manual** until C decides the
   decimal policy.
10. **Corpus stays at 4 web seeds**, plus **multi-defect composite** docs for the headline score, plus
    **5–10 team-owned assignments pulled forward to Stage 1** (consent trivial). Prefer APA sample
    papers, university writing-centre samples, OSF/institutional repositories over arXiv.
11. **Manifest is JSON** (`manifest.json`) with a **per-row verdict map**; K-0.1 and K-S2 schemas
    reconciled to one definition. Added `__init__.py` for `tools/` and `tests/corpus/`. Shell
    commands are **Windows-safe** (PowerShell). Duplicate **K-B1 merged into K-0.5/K-0.6**.
12. **MVP list re-issued and schedule trimmed** — K-H10, K-H11, K-R1, K-INT3 deferred; K-B4 simplified.

---

## 0. STAGE 0 — SEED SET + MINIMAL HARNESS + BASELINE (do this first)

**Purpose:** a frozen, reproducible measurement of the CURRENT engine before C deletes anything. Gates C's deletions.

### K-0.0 Scaffolding
- Scope: create `tools/__init__.py`, `tools/corpus/__init__.py`, `tests/corpus/__init__.py`.
- Description: make `tools.corpus.*` and `tests.corpus.*` importable as packages so `python -m tools.corpus.harness` and `python -m pytest tests/corpus` both work.
- Acceptance: `python -c "import tools.corpus"` and `python -c "import tests.corpus"` exit 0.
- Verification: `python -c "import tools.corpus; import tests.corpus; print('ok')"`
- Deps: none. Size: S.

### K-0.1 Seed corpus (exactly 4 web-sourced APA-7 docs)
- Scope: create `tests/corpus/seed/` and `tests/corpus/seed/manifest.json`.
- Description: Source EXACTLY 4 .docx from the web, each conforming to APA 7 (student + professional mode coverage, at least one with abstract/tables/figures). **Source priority: official APA sample papers (apastyle.apa.org sample-papers hub, student + professional .docx), university writing-centre samples, OSF / institutional repositories — arXiv/preprints only if none of the above cover a gap.** Verify each passes the upload gate. Defect injection (K-I*) runs FROM these 4 known-good docs — one new defect per matrix row, never replacing the 4.
- Acceptance: `tests/corpus/seed/` holds exactly 4 .docx + `manifest.json`. **Schema is the single definition shared with K-S2 (see K-S2):** each row has `id, source_url, license, license_status, mode (student|professional), consent_ref, defects_injected (list), verdicts (map matrix_id → pass|fail|na), notes`. All pass the upload gate (zip valid, no `vbaProject.bin`/`word/embeddings/*`, ≤20 MB, ≤15,000 words; word count via python-docx).
- Verification: `python -m pytest tests/corpus/test_corpus_gate.py` (K-0.2) green and `python -m tests.corpus.manifest --validate tests/corpus/seed` exit 0.
- Deps: K-0.0. Size: M. Risk: sample .docx copyrighted → keep out of git, store under `tests/corpus/seed/samples/README.md` with source URL.

### K-0.2 Upload-gate test
- Scope: create `tests/corpus/test_corpus_gate.py`.
- Description: For every `.docx` under `tests/corpus/`, assert zip-valid, XML well-formed (lxml), no `vbaProject.bin`/`word/embeddings/*` entries, size ≤20 MB, word count ≤15,000.
- Acceptance: parameterized over the manifest; fails loudly naming the offending file.
- Verification: `python -m pytest tests/corpus/test_corpus_gate.py -v`
- Deps: K-0.0. Size: S. 

### K-0.3 Minimal harness (3-5 checks) + accepted-changes view
- Scope: create `tools/corpus/harness.py`, `tools/corpus/docx_view.py`.
- Description: `docx_view.py` produces the **accepted view** of an output .docx — apply all `<w:ins>` (keep inserted runs) and drop `<w:del>` and its `w:delText`; ignore `pPrChange`/`rPrChange`/`sectPrChange` snapshots and read the **current** `pPr`/`rPr`. **There is no "rejected view equals input" test** — `normalise_docx` (document_normalisation_services.py:342) already pre-accepts author revisions, strips colour/highlight and blank paragraphs, and many engine edits are untracked, so byte/text equality against the raw input is invalid. Preservation is measured as a text-diff ratio against **`normalise_docx(input)`** (see K-H9). All harness checks run on the accepted view AND raw OOXML. `harness.py` implements the first checks: margins=1440 twips on all sectPr; `w:spacing w:line="480"` + lineRule auto on Normal/body paragraphs (via style chain); alignment != `both`; firstLine indent=720 twips on body paragraphs; page-number field (`PAGE`) present in header (K-H2 field rules).
- Acceptance: `python -m tools.corpus.harness --docx <f> --checks margins,spacing,align,indent,pagenum --out <json>` emits per-check pass/fail + evidence (node id, raw value). Accepted-view renders on a sample; preservation ratio is computed against `normalise_docx(input)`.
- Verification: `python -m pytest tests/corpus/test_harness_views.py`
- Deps: K-0.0. Size: M (L if style-chain resolution included — split K-0.4).

### K-0.3a Synthetic known-good fixture (python-docx)
- Scope: create `tools/corpus/fixtures.py`.
- Description: build `synthetic_apa7_good.docx` **at test time** with `python-docx` — 1" margins, double spacing, left alignment, 0.5" first-line indent, PAGE field header with `titlePg`, APA heading levels, Calibri 11, abstract/body/references. Never commit the derived `.docx`; the builder is the fixture. Used by K-0.3/K-H2/K-H3 tests and CI instead of committed golden outputs.
- Acceptance: `python -m tools.corpus.fixtures --out <tmp>/synthetic_apa7_good.docx` writes a doc on which all core checks pass.
- Verification: `python -m pytest tests/corpus/test_fixtures.py`
- Deps: K-0.0. Size: M. Risk: a hand-built fixture can diverge from real submissions — keep it minimal and seed-derived where possible.

### K-0.4 Effective-format resolver (style inheritance through basedOn + docDefaults + theme)
- Scope: create `tools/corpus/style_resolver.py`.
- Description: Resolve effective font/spacing/indent/alignment for a run by walking: run rPr → paragraph style pPr/rPr → basedOn chain → document defaults. Handle `<w:style w:styleId>`, `basedOn`, `link`, `docDefaults/rPrDefault`, `docDefaults/pPrDefault`, and styles with no explicit value. **Resolve theme fonts by reading `word/theme/theme1.xml` (`a:themeElements/a:fontScheme/a:majorFont` and `a:minorFont`) when a run/style uses `w:asciiTheme` / `w:hAnsiTheme` / `w:eastAsiaTheme` / `w:cstheme` rather than an explicit `w:ascii` — no such reader exists in the engine today.**
- Acceptance: unit test on a synthetic docx where spacing is set only on `Normal` style returns line=480 rather than "unset"; a theme-font case (`asciiTheme="minorHAnsi"`) resolves to the theme1.xml family.
- Verification: `python -m pytest tests/corpus/test_style_resolver.py -v`
- Deps: K-0.3a. Size: L → split into K-0.4a (chain walker + theme resolution, M) + K-0.4b (docDefaults + numeric units, M). Risk: fragmented styles make chains deep → cache per styleId.

### K-0.5 BASELINE RUN of unmodified engine (capture + score)
> Former K-B1 is merged here; K-B1 is removed to avoid a duplicate baseline ticket.

#### K-0.5a Baseline capture (in-process pipeline; LLM-off)
- Scope: create `tools/corpus/run_baseline.py`, output to `reports/baseline/<run_id>/`.
- Description: For each seed doc, **import and call in-process**:
  `from app.pipelines.feedback_gen_pipeline import doc_analysis_pipeline; doc_analysis_pipeline(in_path, output_path=out_path)`.
  **Do NOT use `python -m app.cli_copybot --build`** — it skips `validate()`, the LLM review and all post-passes (verified cli_copybot.py:122-179). Run with **`OPENAI_API_KEY` unset** (scoreboard A, deterministic). Capture stdout, output .docx, exit/exception, wall time, env (python version, `pip freeze` of python-docx/lxml/openai), git commit hash. **Copy `app/services/.crossref_cache.json` into the run dir after each run** so the run is reproducible standalone.
- Acceptance: `reports/baseline/<run_id>/` contains `run_meta.json` (commit, env, timestamps, api_key_set=false), `outputs/*.docx`, `crossref_cache.json`, and raw per-doc pipeline return JSON.
- Verification: `python -m tools.corpus.run_baseline --corpus tests/corpus/seed --out reports/baseline/run1 --llm off`
- Deps: **K-0.1**. Size: M. Risk: the pipeline may raise on some inputs → record as `error` in the run, do not abort the batch.

#### K-0.5b Baseline scoring (harness)
- Scope: extend `tools/corpus/run_baseline.py` (or `tools/corpus/score.py`), read `reports/baseline/<run_id>/outputs/`.
- Description: run the K-0.3/K-0.4 harness over every captured output and produce `scores.json` (per doc, per APA-xx check pass/fail/na) and `summary.md` (aggregate conformance %, per-rule counts, duplicate-`w:id` counts, #tracked changes per pass family, over-editing count). On top of scoreboard A, run **scoreboard B (LLM-on): `N=3` on all 4 seeds** (set `OPENAI_API_KEY`), recording variance; persist a separate `.crossref_cache.json` per run.
- Acceptance: `scores.json` + `summary.md` exist for both scoreboards; every captured output scored or explicitly `error`.
- Verification: `python -m tools.corpus.report --run reports/baseline/run1 --out reports/baseline/run1/summary.md`
- Deps: **K-0.3, K-0.3a, K-0.4**. Size: M.

### K-0.6 Baseline freeze (gate for C)
- Action (no code): document and freeze the gate. Commit `reports/baseline/run1/run_meta.json` + `summary.md` + `scores.json`. **Create a git tag of the pre-deletion commit** (the commit the baseline ran against) — this tag, not just the report, is what gates C. Record in `reports/baseline/README.md` a **`git worktree` recipe** to re-run that exact commit after C has deleted code:

  ```powershell
  git worktree add ..\openeditor-baseline <pre-deletion-commit-sha>
  # in the worktree:
  $env:OPENAI_API_KEY = $null                       # scoreboard A (deterministic)
  python -m tools.corpus.run_baseline --corpus tests/corpus/seed --out reports/baseline/rerun
  git worktree remove ..\openeditor-baseline
  ```

- Verification: `git tag -l "apa7-baseline*"` returns the tag; `run_meta.json` commit hash matches HEAD at tag time; the worktree recipe re-runs the pipeline at that commit.
- Deps: K-0.5a, K-0.5b. Owner: **Person A**.

---

## 1. TICKETS BY GROUP

### K-Spec — corpus design, manifest, gold labels

| ID | Title | Stage | Scope (create) | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-S1 | Corpus layout + directory contract | 1 | `tests/corpus/{seed,injected,real,composites,samples}/`, `tests/corpus/README.md`, `tests/corpus/__init__.py` | Define layout: seed/, injected/, composites/ (multi-defect headline docs), real/ (gitignored unless consented), samples/ (official .docx, gitignored). | README documents layout, gate, manifest schema. | `Get-ChildItem tests/corpus`; CI job runs gate test. | K-0.0 | S | Real docs mixed into git → separate gitignored dir. | QA |
| K-S2 | Manifest schema (v1, JSON) | 1 | `tests/corpus/manifest.py`, `tests/corpus/MANIFEST.md` | **One JSON manifest per folder** (`manifest.json`); row fields: `id, source_url, license, license_status, mode (student\|professional), consent_ref, defects_injected (list of matrix_ids), verdicts (map matrix_id → pass\|fail\|na), notes`. This is the **same schema K-0.1 declares** — no CSV variant. | Schema enforced by `python -m tests.corpus.manifest --validate` exit 0. | `python -m tests.corpus.manifest --validate tests/corpus` | K-S1 | S | Schema drift → `schema_version` field. | QA |
| K-S3 | Gold-label spec: per-rule expected verdicts | 1 | `docs/gold-label-spec.md` (create only if client asks to keep in docs/; else `tests/corpus/GOLD_LABELS.md`) | For every APA-00..APA-20 row: which harness check(s) grade it, which injected defect triggers fail, expected direction. **APA-17 (numbers / decimal policy) is marked MANUAL until C decides the decimal policy** (see decimal_corrections.py — the "This Journal…" text is JUTLP and the policy itself is undecided). | Every matrix row referenced by ≥1 harness check or explicitly marked UNGRADABLE/MANUAL with reason. | `(Select-String -Path tests/corpus/GOLD_LABELS.md -Pattern 'APA-').Count -ge 21` | K-S2 | S | Some rows (e.g. title-page layout) hard to auto-grade → manual-review column. | QA |
| K-S4 | Coverage matrix seed | 1 | `tests/corpus/coverage_matrix.csv` | Matrix of corpus docs × APA rows marking present/absent/na; target ≥1 positive and ≥1 negative per gradable row. Include the **composite** multi-defect docs (K-I4) that drive the headline score. | Every gradable APA row has ≥1 fail-case and ≥1 pass-case in corpus. | `python -m tests.corpus.coverage --report` | K-S2 | S | Coverage gaps → add to inject list. | QA |

### K-Seed — known-good positives

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-P1 | Team-owned consented corpus docs | 1 | `tests/corpus/real/*.docx` (gitignored), consent register | **Pull 5–10 team-owned assignments forward to Stage 1** (consent is trivial — team members own them). Verify each passes the upload gate; run the harness — should score high. These supplement, never replace, the 4 web seeds. | 5–10 files present (or gitignored + fetch recipe), each gate-passing; consent register row per file. | `python -m tools.corpus.harness --docx <each> --all --out -` | K-0.3 | M | PII in assignments → consent register + gitignore. | QA |
| K-P2 | Mode coverage check on seeds + team docs | 1 | `tests/corpus/coverage_matrix.csv` | Confirm the corpus jointly covers student + professional mode, abstract present/absent, tables, figures. | Matrix shows coverage or explicit `na`; gaps noted as risk. | review of manifest | K-0.1, K-P1 | S | Coverage may still be incomplete → mark `na`, do not expand the web corpus beyond 4. | QA |

> The 4 web-sourced seeds are owned by **K-0.1** (Stage 0); K-P1 adds team-owned docs at Stage 1. This removes the earlier K-0.1/K-P1 overlap.

### K-Inject — defect-injection tooling

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-I1 | Injector framework | 2 | `tools/corpus/inject.py` | CLI: `python -m tools.corpus.inject --base good.docx --defect APA-03 --out bad.docx`; seeded RNG; one defect per output; records defect in manifest. Also supports **`--composite`**: inject several matrix-row defects into one output (the multi-defect docs that drive the headline score). | Each invocation emits bad.docx + manifest row with `defects_injected=[APA-xx,…]`. | `python -m tools.corpus.inject --base tests/corpus/seed/<one>.docx --defect APA-03 --out "$env:TEMP\x.docx"` then harness reports APA-03 fail. | K-S2 | M | Injected doc may trip other rows → gold labels must allow `na`. | docx-XML |
| K-I2 | Defect recipes: formatting | 2 | `tools/corpus/defects/format_defects.py` | Recipes: justified body (`w:jc="both"`), line spacing 1.15 (`w:line="276"`), missing first-line indent (remove `w:ind w:firstLine`), missing page number (strip header PAGE field), and **two font recipes: (a) set body to a DISALLOWED family (e.g. Comic Sans); (b) set an ALLOWED family at the WRONG size (e.g. Arial 12 instead of 11).** | Each recipe produces exactly its one defect; harness flags exactly that row. | `python -m pytest tests/corpus/test_inject_format.py` | K-I1, K-0.4 | M | Style-level vs run-level mutation confusion → inject at both and record where. | docx-XML |
| K-I3 | Defect recipes: headings/abstract/references | 2 | `tools/corpus/defects/struct_defects.py` | Recipes: heading levels wrong (demote L2→L1), Abstract missing / >250 words / indented, References not starting on a new page, missing hanging indent, references not alphabetical, comma-decimal numbers ("3,5"→"3.5"), missing "et al." for 3+ authors, "&" in narrative citation, inline >40-word quote not block-formatted, numbered headings. **The JUTLP-residue injectors ("Practitioner Notes" section, banner/textbox) are DROPPED** — with them gone, K-H7 can run on the clean seeds. | Same as K-I2 per recipe; APA-17 comma-decimal recipe is scored **manual** until C fixes the decimal policy. | `python -m pytest tests/corpus/test_inject_struct.py` | K-I1 | L → split K-I3a (headings+abstract) / K-I3b (references+citations) | Injectors may produce an invalid docx → validate via gate test. | docx-XML |
| K-I4 | Injector round-trip gate + composites | 2 | `tests/corpus/test_injector_ingestible.py` | Every injected doc (single- and multi-defect composites) must be openable by the CURRENT engine via the **in-process `doc_analysis_pipeline`** (not just `--analyse`) — the injector must not produce docs the engine crashes on. | All injected fixtures run `doc_analysis_pipeline` without traceback. | `python -m pytest tests/corpus/test_injector_ingestible.py` | K-I1..K-I3 | M | Current engine may reject valid docs → report to C. | docx-XML |

### K-Real — realistic/messy documents + consent

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-R1 | Consent + anonymisation pipeline | 3 (deferred) | `tools/corpus/anonymize.py`, `docs/corpus-consent.md` (or `tests/corpus/CONSENT.md`) | Strip author names/affiliations from .docx core properties + front-page text where safe; write consent register row; refuse to add to repo without `license_status=consented`. **Deferred this sprint** (see trimmed schedule); the Stage-1 team docs use the consent register directly. | Anonymised doc opens; no original author name in `docProps/core.xml` or front-page text. | `python -m pytest tests/corpus/test_anonymize.py` | K-S2 | M | Over-aggressive strip may break front-page checks → keep title/abstract. | QA + docx-XML |
| K-R2 | Legacy JUTLP pack: reference only | 2 | `tests/corpus/messy/README.md` | Do NOT copy/inject/commit `tests/jutlp_sample_docx_test_pack/` or the local AI_Pool drive as corpus. Document that they are JUTLP-shaped and excluded from the APA-7 corpus; they may be used ad hoc as messy-input smoke tests. | README present; `tests/corpus/messy/` contains only the README (no .docx). | `Get-ChildItem tests/corpus/messy -Filter *.docx` returns nothing. | K-0.1 | S | Temptation to reuse → keep the exclusion explicit. | QA |
| K-R3 | License audit on the 4 web-sourced docs | 3 | `tests/corpus/seed/SOURCES.md` (extend) | For each of the 4, record license/permission status, whether redistribution is allowed, and whether anonymisation was needed. | All 4 rows: license identified, redistribution decision (commit or gitignore) recorded. | review | K-P1 | S | License ambiguity → default to gitignore + fetch-on-demand. | QA |

### K-Harness — conformance checker

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-H1 | OOXML safe-open / validity check | 1 | add to `tools/corpus/docx_view.py` | zip valid, `[Content_Types].xml` present, all XML parts well-formed, `w:document` root, **`w:id` values unique (NOT "monotonic" — nothing guarantees monotonicity; `_max_revision_id` only takes max+1 per reseed).** Report **duplicate-`w:id` counts**. | Reports per-file `valid: true/false` + reasons + duplicate-id count. | `python -m pytest tests/corpus/test_validity.py` | K-0.3 | S | Some legit docs reuse ids → report the count, don't hard-fail. | docx-XML |
| K-H2 | Margins / spacing / align / indent / pagenum checks | 1 | extend `tools/corpus/harness.py` | Checks for APA-00, APA-01 (spacing incl. block quotes + refs, no blank lines before/after headings), APA-03, APA-04, APA-05; each returns pass/fail/evidence via K-0.4 resolver. **Page-number check must enumerate `default`/`first`/`even` `w:headerReference`s under `sectPr/w:titlePg` and `w:evenAndOddHeaders` (settings.xml), and detect a PAGE field in BOTH `w:fldSimple` (`w:instr=" PAGE "`) and `w:fldChar`/`w:instrText` run sequences.** | ≥5 checks emit pass/fail JSON; on `synthetic_apa7_good.docx` (K-0.3a) all pass; on injected defect docs exactly the matching row fails. | `python -m pytest tests/corpus/test_harness_core.py` | K-0.4, K-0.3a | M | Header inheritance across sections → evidence strings must show which header part/type matched. | docx-XML |
| K-H3 | Font check | 1 | `tools/corpus/checks/fonts.py` | Effective font of every run ∈ allowed set (11 Calibri / 11 Arial / 12 TNR / 11 Georgia / 10 Lucida Sans Unicode); size matches the family's allowed pt. Uses theme1.xml resolution from K-0.4. | pass/fail per doc + list of offending runs. | `python -m pytest tests/corpus/test_fonts.py` | K-0.4 | M | Fonts set at style level only → resolver dependency. | docx-XML |
| K-H4 | Heading levels/formatting check | 2 | `tools/corpus/checks/headings.py` | For each heading paragraph: level from style (Heading1..5 / outlineLvl), L1 centered bold, L2 flush-left bold, L3 flush-left bold italic, L4 indented bold, L5 indented bold italic; title case; no "Introduction" heading (APA-10). | pass/fail per heading + evidence. | `python -m pytest tests/corpus/test_headings.py` | K-0.4 | M | Split S/M if needed. | docx-XML |
| K-H5 | References block check | 2 | `tools/corpus/checks/refs.py` | "References" starts on a new page (page break before), bold centered, hanging indent 720, double-spaced, alphabetical order, DOI form `https://doi.org/...` (APA-12, APA-18). | pass/fail per sub-check. | `python -m pytest tests/corpus/test_refs.py` | K-0.4 | M | Order check needs sentence segmentation → simple first-token compare acceptable for v1. | docx-XML |
| K-H6 | Abstract/keywords check | 2 | `tools/corpus/checks/abstract.py` | "Abstract" bold centered, ≤250 words, single unindented paragraph (APA-08); keywords label italic, indented, ≤~1 line (APA-09). | pass/fail. | `python -m pytest tests/corpus/test_abstract.py` | K-0.4 | S | Word count of abstract zone needs boundary detection → reuse heuristic. | docx-XML |
| K-H7 | Negative residue check | 2 | `tools/corpus/checks/residue.py` | Output must NOT contain: "Practitioner Notes", banner textbox shapes, CRediT block, "This Journal" JUTLP phrases, blinded placeholders expecting JUTLP (APA-20). **Runs ONLY on docs whose INPUT has no residue (the seeds) — JUTLP-residue injectors are dropped (K-I3), so a pass is meaningful and not circular.** | pass/fail + matches found; `na` if the input itself carries residue. | `python -m pytest tests/corpus/test_residue.py` | K-0.3 | S | JUTLP template styles may still carry old ids → string scan + style-id scan. | docx-XML |
| K-H8 | Appendices preserved check | 2 | `tools/corpus/checks/appendices.py` | If input had an Appendix, output must still contain it (APA-19); input lacking appendix → n/a. | pass/fail/na per doc. | `python -m pytest tests/corpus/test_appendices.py` | K-0.3 | S | Appendix detection heuristic → label. | docx-XML |
| K-H9 | Text-preservation check (accepted view vs normalised input) | 2 | `tools/corpus/checks/preservation.py` | Accepted-view text of the output is text-diffed against **`normalise_docx(input)`**, NOT the raw input and NOT a "rejected view". **Rejected-view equality is invalid** because `normalise_docx` pre-accepts revisions and strips colour/blank paras, and many engine edits are untracked. Report an **insert/delete-char ratio**; a ratio beyond the configured bound raises the hard preservation flag. | pass/fail + diff ratio + hard-flag boolean. | `python -m pytest tests/corpus/test_preservation.py` | K-0.3 | M | Intended-edit bound needs care → `--allow` list from manifest + ratio tolerance. | docx-XML |
| K-H10 | Table/figure numbering check | 3 (deferred) | `tools/corpus/checks/tables_figs.py` | Table captions "Table N" bold + italic title; Figure captions "Figure N" bold + italic title (APA-15, APA-16); numbering monotonic. **Deferred this sprint.** | pass/fail per caption. | `python -m pytest tests/corpus/test_tables_figs.py` | K-0.3 | S | Caption detection heuristic. | docx-XML |
| K-H11 | Citation format check | 3 (deferred) | `tools/corpus/checks/citations.py` | Parenthetical `(A & B, 2020)` / narrative `A and B (2020)`; 3+ authors use et al. (APA-13); block quote ≥40 words is indented block, no quotes, citation after final period (APA-14). **Deferred this sprint.** | pass/fail + offending instances. | `python -m pytest tests/corpus/test_citations.py` | K-0.3 | M | Regex-based; v1 acceptable. | docx-XML |
| K-H12 | Harness CLI + score aggregation | 2 | `tools/corpus/harness.py` (extend), `tools/corpus/score.py` | `--all` runs every check; emits per-doc JSON + aggregate. **Conformance % = per-rule `pass / (pass + fail)`, NA excluded.** Aggregate adds: **hard text-preservation flag** (from K-H9), **defect-fix rate** on injected/composite docs (fraction of injected matrix rows now passing), **over-editing count** (tracked changes introduced on known-good seed docs), duplicate-`w:id` count, #tracked changes per pass family. Regression flag if a known-good doc gets worse vs baseline. | `python -m tools.corpus.harness --docx out.docx --all --baseline reports/baseline/run1 --out scores.json` produces schema-conformant JSON. | `python -m pytest tests/corpus/test_harness_cli.py` | K-H1..K-H9 | M | Keep schema versioned. | QA |

### K-Baseline / K-Final — runs and reports

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-B2 | Mid-sprint run after C stage1 | 2 | `reports/mid/` | Re-run the harness (capture + score, K-0.5a/b) on the seed corpus; diff per-rule deltas vs baseline. | `reports/mid/summary.md` with per-rule delta table. | compare summary.md before/after | K-0.5a, K-H12 | S | Pipeline broken mid-sprint → record errors. | QA |
| K-B3 | FINAL run on full corpus | 4 | `reports/final/` | Full corpus (4 seeds + team docs + injected + composites). | Per-doc table + aggregate conformance % + per-rule before/after delta + regression flags + preservation flag + defect-fix rate + over-editing count + LLM-on variance. | `python -m tools.corpus.report --before reports/baseline/run1 --after reports/final --out demo_report.md` | K-B2, K-I4, K-R3 | M | LLM variance → **N=3 on all 4 seeds**. | QA |
| K-B4 | Regression gate (simplified) | 3 | `tools/corpus/gate.py` | **Two conditions only:** (1) fail if any known-good seed's conformance % drops > X points vs baseline; (2) fail if the text-preservation hard flag is raised. Defect-fix scrutiny is reported, not gated. | `python -m tools.corpus.gate --baseline reports/baseline/run1 --candidate reports/final` exit code reflects regressions. | run on a deliberately regressed fixture | K-H12 | S | Threshold X client decision → default 0. | QA |

### K-Infra — layout, storage, CI hook

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-INT1 | Data governance: consent, anonymisation, storage, LFS | 1 | `docs/corpus-data-governance.md`, `.gitignore` updates, `tests/corpus/real/.gitkeep` | Policy: no identifiable manuscript committed; consent register required; large binaries via git LFS or excluded; samples fetched, not committed. | `.gitignore` covers `tests/corpus/real/`, `samples/`; governance doc present; `git status` shows only manifests/README. | `git check-ignore tests/corpus/real/x.docx` returns ignored. | K-P1 | S | Team confusion → one owner. | QA |
| K-INT2 | Reproducibility pinning | 1 | `tools/corpus/requirements-corpus.txt`, `tools/corpus/RUNBOOK.md` | Pin python-docx, lxml, pytest versions; seed RNG documented; deterministic injector output; record `OPENAI_MODEL`/`OPENAI_TEMPERATURE` used. | `pip install -r tools/corpus/requirements-corpus.txt` then injector twice → byte-identical output. | run injector twice, compare `(Get-FileHash <a>).Hash -eq (Get-FileHash <b>).Hash` | K-I1 | S | Version drift → re-pin. | QA |
| K-INT3 | CI hook (harness as pytest) | 2 (deferred) | `tests/corpus/test_conformance_smoke.py` | Pytest that runs the harness on the **K-0.3a synthetic fixture** (not committed golden outputs). **Deferred this sprint** — the K-0.3/K-0.3a/K-H2 tests already form the CI surface; when revived, it must use the synthetic builder, not committed derived `.docx`. | `python -m pytest tests/corpus -v` green. | same | K-H12 | S | CI time → synthetic fixture only. | QA |

---

## 2. STAGE GATES & DEMO ARTEFACTS

| Stage | Entry | Exit (runnable check) | Demo artefact |
|---|---|---|---|
| 0 | repo clean, venv active | `python -m pytest tests/corpus -v` green; `reports/baseline/run1/summary.md` exists, is git-tagged, and the **pre-deletion commit tag** + `git worktree` recipe are documented | Baseline report: table(doc × APA row pass/fail), aggregate conformance %, per-rule counts, duplicate-`w:id` count, over-editing count, LLM-on N=3 variance |
| 1 | Stage 0 tagged | `python -m tests.corpus.manifest --validate` green; coverage matrix shows ≥1 pass+fail per gradable row | Corpus manifest (JSON) + coverage matrix + team-owned docs |
| 2 | Stage 1 exit | K-I4 ingestibility green; K-H2..K-H9 all implemented; mid report vs baseline in `reports/mid/summary.md` | Mid-sprint conformance delta table |
| 3 | Stage 2 exit | K-B4 regression gate green | Mid report + consent register |
| 4 | Stage 3 exit | K-B3 final report + K-B4 gate green | Final demo report (per-doc + aggregate + per-rule before/after delta + preservation flag + defect-fix rate + over-editing count) |

---

## 3. DEPENDENCY GRAPH & CRITICAL PATH

```
K-0.0 → K-0.1 → K-0.2 → K-0.3 → K-0.3a → K-0.4a → K-0.4b
K-0.1 → K-0.5a ─┐
K-0.3/K-0.4/K-0.3a → K-0.5b → K-0.6 (BASELINE GATE: tag pre-deletion commit + worktree recipe → unblocks C deletions)
K-S1 → K-S2 → K-S3 → K-S4
K-0.3 → K-P1/K-P2
K-S2 → K-I1 → K-I2/I3 → K-I4
K-0.4 → K-H2 → K-H12 → K-B2 → K-B3 → K-B4
K-INT1/2 parallel
```

**Critical path to baseline:** K-0.0→K-0.1→K-0.2→K-0.3→K-0.3a→K-0.4→K-0.5a→K-0.5b→K-0.6.
**Critical path to demo:** K-0.6→K-H2..K-H9→K-B2→K-B3→K-B4.
**K unblocks C:** K-0.6 — the pre-deletion commit **tag** + worktree recipe; C must not delete before this exists.
**K unblocks D:** none directly; D needs K's assertion hook (below) — K-D1.

---

## 4. PARALLELISATION INSIDE K (2 people)

Track K divides cleanly between 2 people, but **not along the earlier "QA vs docx-XML" ticket labels**. The real seam is at the **file/artifact level**, because several of A's checks (`K-H2` pagenum, `K-H4`–`K-H6`, `K-H9` preservation) consume B's two core modules (`docx_view.py`, `style_resolver.py`). Split by *file ownership*, not ticket type.

| | **Person A — Corpus, runners & reporting** | **Person B — OOXML ground truth** |
|---|---|---|
| Owns files | `tests/corpus/**` (data, manifest), `tools/corpus/run_baseline.py`, `score.py`, `report.py`, `gate.py`, `harness.py` | `tools/corpus/docx_view.py`, `style_resolver.py`, `fixtures.py`, `inject.py`, `defects/**`, `checks/**` |
| Stage 0 tickets | K-0.0, K-0.1, K-0.2, **K-0.3-harness half**, K-0.5a capture, K-0.5b scoring, **K-0.6 freeze** | K-0.3a fixture, **K-0.3-view half**, K-0.4a, K-0.4b |
| Checks | K-H1 (validity), K-H7 (residue), K-H8 (appendices) — no resolver needed | K-H2, K-H3, K-H4, K-H5, K-H6, K-H9 — all resolver-dependent |
| Injectors | — | K-I1, K-I2, K-I3, K-I4 |
| Spec/corpus | K-S1, K-S2, K-S3, K-S4 | — |
| Docs | K-P1, K-P2, K-INT1, K-INT2 | K-R2, K-R3 |
| Runs/reports | K-B2, K-B3, K-B4 | — |

**Sync points (joint milestones — cannot be split):**
- **K-0.5b (scoring)** needs A's capture (K-0.5a) + B's harness modules (`docx_view`, `style_resolver`).
- **K-0.6 (the gate)** needs both; owned by Person A.
- **K-B2 / K-B3** need both.

**Seam statements / frozen interfaces (do these first):**
1. **K-0.0** by A creates `tools/corpus/__init__.py` + `tests/corpus/__init__.py` before anyone writes modules (avoids both creating/diffing them).
2. **`docx_view.accepted_view(docx) -> text/runs`** and **`style_resolver.resolve_effective(run, doc) -> {font,size,spacing,indent,align}`** signatures are agreed up front. A stubs them in tests; B implements. A's K-H2/K-H4–K-H6 call them without ever editing B's files.
3. **Manifest schema (K-S2)** is frozen before B's injectors write rows; only A writes `manifest.json`.

**Schedule reality:**
- Before K-0.4 lands, the critical path is shared: A (corpus + capture + non-resolver checks) runs parallel to B (fixture + resolver). Neither idles.
- **K-0.4 is the single bottleneck** and sits on the gate path. Timebox it; if it slips, use the documented fallback (evaluate direct paragraph props only, evidence `direct-only`) so scoring isn't blocked.
- After K-0.4, rebalance by moving some resolver-dependent checks (e.g. K-H4/K-H5/K-H6) to A, since A's Stage-0 work is done and B is heavier.

**Shared/blocked:** K-0.5a capture (needs corpus), K-I4 (needs B + current engine), K-B3 final (needs both).

---

## 5. CROSS-TRACK REQUESTS

**To C (deterministic pipeline):**
1. No folder runner needed — K calls `doc_analysis_pipeline(path, output_path=...)` in-process and loops the corpus itself. (Earlier "folder-runner" request is withdrawn; also note `--build` alone is not a valid baseline.)
2. Emit **fired matrix_ids** in pipeline output (log or JSON sidecar) so K can assert C's rules fired where gold labels say they should. Currently no such emission exists.
3. Expose per-pass count of tracked changes (#`<w:ins>`/`<w:del>` by author) in the build result.
4. Confirm the **decimal policy** for APA-17 (keep / drop the "This Journal reports to two decimal places" JUTLP text) — K marks APA-17 manual until then.
5. Leave `tests/jutlp_sample_docx_test_pack/` untouched (reference only — excluded from the APA-7 corpus; K cannot edit outside `tests/corpus/**`).
6. Decide fate of 2 failing `test_jutlp_validator.py` tests — should not block K.

**To D (LLM layer):**
1. Pluggable assertion hook: K will import a function `d_assert_llm_output(notes, structural_validations)` that D provides, asserting no "JUTLP"/"Practitioner Notes" strings and schema parse OK. K's harness calls it if present, skips gracefully otherwise.
2. `OPENAI_MODEL`/`OPENAI_TEMPERATURE` (and `OPENAI_MAX_TOKENS`) recorded in run metadata — confirm these env var names (README confirms). Scoreboard B sets `OPENAI_API_KEY`; scoreboard A leaves it unset.

---

## 6. RISKS, OPEN DECISIONS, OUT-OF-SCOPE

**Risks:**
- Style-inheritance resolution (K-0.4) is the hardest piece — split done; theme1.xml adds a second path. Fallback: check direct paragraph props only and mark evidence "direct-only".
- Accepted-view algorithm ("apply `w:ins`, drop `w:del`/`delText`, read current `pPr`/`rPr`) is sound; the earlier "rejected view == input" assumption is **wrong** and is replaced by a text-diff ratio against `normalise_docx(input)`.
- LLM nondeterminism pollutes before/after deltas → two scoreboards; LLM-off for C, LLM-on N=3 on all 4 seeds for D; report variance.
- Injected docs may trigger unexpected rows → gold labels use pass/fail/na, and K-I4 forces ingestibility via the real pipeline.
- JUTLP-shaped residual checks (e.g. "no banner") may pass trivially before C deletes the banner code → K-H7 runs only on residue-free inputs; record pre/post.

**Open decisions (client/team):**
1. Gradable threshold for "conformance %" and which APA rows are auto-gradable vs manual-review (APA-17 manual for now).
2. Sample .docx licensing/redistribution — default: fetch, don't commit.
3. Allowed font default (client pick) — harness reads it from config/env.
4. Regression threshold X for K-B4 (default 0 points).
5. `CAROUSEL_ENABLED` default — carousel is C/D territory, K only needs no JUTLP residue.

**Out of scope for K:** deployment, MemberPress/Stripe, login gate, editing `app/**`, implementing the APA engine itself (C/D), the clean-vs-tracked download toggle.

---

## END — Required outputs

**(1) Minimum K ticket set for a credible next-session demo:**
K-0.0 → K-0.1 → K-0.2 → K-0.3 → K-0.3a → K-0.4 (split a/b) → K-0.5a → K-0.5b → K-0.6 (baseline) · K-S2 (manifest) · K-H2 (margins/spacing/align/indent/pagenum) + K-H3 (fonts) + K-H7 (residue) · K-B2/K-B3 report. Plus K-I1 + one recipe (e.g. APA-03 justify) on a seed doc to show the inject→detect loop.
**Deferred:** K-H10, K-H11, K-R1, K-INT3.

**(2) First 5 K tickets to start tomorrow (dependency order):**
1. K-0.0 (scaffolding / `__init__.py`)
2. K-0.1 (seed corpus + JSON manifest)
3. K-0.2 (upload-gate test)
4. K-0.3 (harness + accepted view vs `normalise_docx(input)`)
5. K-0.3a (synthetic fixture) → K-0.4a → K-0.4b → K-0.5a baseline capture.

**(3) Decisions needed from client/team:** (client: default font set; US vs AU spelling; student vs professional default; consent for real papers; sample-docx redistribution. team: threshold for "conformance %"; C to confirm fired matrix_ids + the APA-17 decimal policy; D to confirm assertion hook + model env vars.)

UNVERIFIED items: exact `OPENAI_MODEL` default value in code (README says gpt-5.4-mini); `w:id` uniqueness guarantee in the current engine (only max+1 reseeding is verified — hence K-H1 reports duplicate counts rather than asserting monotonicity).
