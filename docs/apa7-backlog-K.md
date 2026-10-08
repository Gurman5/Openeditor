# TRACK K — Evaluation Corpus + Conformance Harness · DEV TASK BACKLOG

Verified anchors: `docs/apa7-rework-plan.md` (matrix A rows APA-00..APA-20, eval plan §E),
`docs/Curated Refernce point (1).md`, `docs/track-c-d.md`, `docs/api-contract.md`,
`app/main.py:83-89` (MAX_UPLOAD_MB default 20, MAX_WORD_COUNT default 15000), `app/main.py:794`
(rejects `word/vbaProject.bin` + `word/embeddings/*`), `app/cli_copybot.py` (`--analyse/--build/--output`),
`tests/jutlp_sample_docx_test_pack/` (7 JUTLP-shaped .docx — reference only, NOT part of the APA corpus). `tools/` does **not** exist yet — create it.

**Corpus sourcing decision:** EXACTLY 4 .docx in the corpus, all sourced independently from the web and conforming to APA 7. The local Google Drive pool `C:\Users\daria\Downloads\AI_Pool-20260929T081940Z-1-001\AI_Pool` is JUTLP-shaped and is **rejected** as a source (it may be used ad hoc as a messy-input smoke test, never committed as corpus).

---

## 0. STAGE 0 — SEED SET + MINIMAL HARNESS + BASELINE (do this first)

**Purpose:** a frozen, reproducible measurement of the CURRENT engine before C deletes anything. Gates C's deletions.

### K-0.1 Seed corpus (exactly 4 web-sourced APA-7 docs)
- Scope: create `tests/corpus/seed/` and `tests/corpus/seed/manifest.csv`.
- Description: Source EXACTLY 4 .docx from the web, each conforming to APA 7 (student mode + professional mode coverage, at least one with abstract/tables/figures). Candidate sources: official APA sample papers (apastyle.apa.org sample-papers hub, student + professional .docx), university open repositories (CC-licensed), arXiv/preprints formatted in APA. Verify each passes the upload gate. Defect injection (K-I*) runs FROM these 4 known-good docs — one new defect per matrix row, never replacing the 4.
- Acceptance: `tests/corpus/seed/` holds exactly 4 .docx + `manifest.csv` with a row per file: `id,source_url,license,mode,license_status,defects_injected,expected_pass,expected_fail,notes`. All pass upload gate (zip valid, no vbaProject/embeddings, ≤20 MB, ≤15,000 words; word count via python-docx).
- Verification: `python -m pytest tests/corpus/test_corpus_gate.py` (K-0.2) green and manifest validates.
- Deps: none. Size: M. Risk: sample .docx copyrighted → keep out of git, store under `tests/corpus/seed/samples/README.md` with source URL.

### K-0.2 Upload-gate test
- Scope: create `tests/corpus/test_corpus_gate.py`.
- Description: For every `.docx` under `tests/corpus/`, assert zip-valid, XML well-formed (lxml), no `vbaProject.bin`/`word/embeddings/*` entries, size ≤20 MB, word count ≤15,000.
- Acceptance: parameterized over manifest; fails loudly naming the offending file.
- Verification: `python -m pytest tests/corpus/test_corpus_gate.py -v`
- Size: S.

### K-0.3 Minimal harness (3-5 checks) + accepted-changes view
- Scope: create `tools/corpus/harness.py`, `tools/corpus/docx_view.py`.
- Description: `docx_view.py` must produce two views of an output .docx: (1) **accepted view** — apply all `<w:ins>` and invert `<w:del>` (i.e. use text of inserted runs, drop deleted runs); (2) **rejected view** — the converse, which must equal the input text outside intended edits. All harness checks run on the accepted view AND raw OOXML. `harness.py` implements the first checks: margins=1440 twips on all sectPr; `w:spacing w:line="480"` + lineRule auto on Normal/body paragraphs (via style chain); alignment != `both`; firstLine indent=720 twips on body paragraphs; page-number field (`PAGE`) present in header.
- Acceptance: `python -m tools.corpus.harness --docx <f> --checks margins,spacing,align,indent,pagenum --out <json>` emits per-check pass/fail + evidence (node id, raw value). Rejected-view text equality test passes on 1 sample.
- Verification: `python -m pytest tests/corpus/test_harness_views.py`
- Size: M (L if style-chain resolution included — split K-0.4).

### K-0.4 Effective-format resolver (style inheritance through basedOn + docDefaults)
- Scope: create `tools/corpus/style_resolver.py`.
- Description: Resolve effective font/spacing/indent/alignment for a run by walking: run rPr → paragraph style pPr/rPr → basedOn chain → document defaults. Handle `<w:style w:styleId>`, `basedOn`, `link`, `docDefaults/rPrDefault`, `docDefaults/pPrDefault`, and styles with no explicit value.
- Acceptance: unit test on a synthetic docx where spacing is set only on `Normal` style; resolver returns line=480 rather than "unset".
- Verification: `python -m pytest tests/corpus/test_style_resolver.py -v`
- Size: L → split into K-0.4a (chain walker, S) + K-0.4b (docDefaults + numeric units, M). Risk: fragmented JUTLP styles make chains deep → cache per styleId.

### K-0.5 BASELINE RUN of unmodified engine
- Scope: create `tools/corpus/run_baseline.py`, output to `reports/baseline/<run_id>/`.
- Description: Run current engine on each seed doc: `python -m app.cli_copybot --analyse <in> --build --output <out>`. Capture stdout, output .docx, exit code, wall time, env (python version, `pip freeze` of python-docx/lxml/openai), model name/temp (`OPENAI_MODEL`, `OPENAI_TEMPERATURE` env), git commit hash. LLM stage run N=3 on 5 docs to report variance.
- Acceptance: `reports/baseline/<run_id>/` contains `run_meta.json` (commit, env, model, temperature, timestamps), `outputs/*.docx`, `scores.json` (per doc, per APA-xx check pass/fail from K-0.3 harness), `summary.md` (aggregate conformance %, per-rule counts, #tracked changes per pass family, variance across N=3).
- Verification: `python -m tools.corpus.run_baseline --corpus tests/corpus/seed --out reports/baseline/run1` then `python -m tools.corpus.report --before reports/baseline/run1 --out reports/baseline/run1/summary.md`
- Deps: K-0.1..K-0.4. **This gates C's deletions — highest priority.**
- Size: M. Risk: `cli_copybot --build` may fail on some inputs → record failures in scores.json as `error`, do not abort batch.

### K-0.6 Baseline freeze
- Action (no code): commit `reports/baseline/run1/run_meta.json` + `summary.md`, git tag `apa7-baseline-run1`. Record in `reports/baseline/README.md` how to reproduce (exact env vars, model, command).
- Verification: `git tag -l "apa7-baseline*"` returns the tag; `run_meta.json` contains commit hash matching HEAD at tag time.

---

## 1. TICKETS BY GROUP

### K-Spec — corpus design, manifest, gold labels

| ID | Title | Stage | Scope (create) | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-S1 | Corpus layout + directory contract | 1 | `tests/corpus/{seed,injected,real,samples}/`, `tests/corpus/README.md` | Define layout: seed/, injected/, real/ (gitignored unless consented), samples/ (official .docx, gitignored). | README documents layout, gate, manifest schema. | `ls tests/corpus`; CI job runs gate test. | — | S | Real docs mixed into git → separate gitignored dir. | QA |
| K-S2 | Manifest schema (v1) | 1 | `tests/corpus/manifest.py`, `tests/corpus/MANIFEST.md` | Single CSV per folder + one JSON index; row fields: id, source, mode (student/professional), license_status, consent_ref, defects_injected (list of matrix_ids), expected pass/fail per APA row (map row→pass/fail/na), notes. | Schema enforced by `python -m tests.corpus.manifest --validate` exit 0. | `python -m tests.corpus.manifest --validate tests/corpus` | K-S1 | S | Schema drift → version field. | QA |
| K-S3 | Gold-label spec: per-rule expected verdicts | 1 | `docs/gold-label-spec.md` (create only if client asks to keep in docs/; else `tests/corpus/GOLD_LABELS.md`) | For every APA-00..APA-20 row: which harness check(s) grade it, which injected defect triggers fail, expected direction. | Every matrix row referenced by ≥1 harness check or explicitly marked UNGRADABLE with reason. | Review checklist sign-off; `grep APA- tests/corpus/GOLD_LABELS.md | wc -l` ≥ 21 | K-S2 | S | Some rows (e.g. title-page layout) hard to auto-grade → manual-review column. | QA |
| K-S4 | Coverage matrix seed | 1 | `tests/corpus/coverage_matrix.csv` | Matrix of corpus docs × APA rows marking present/absent/na; target ≥1 positive and ≥1 negative per gradable row. | Every gradable APA row has ≥1 fail-case and ≥1 pass-case in corpus. | `python -m tests.corpus.coverage --report` | K-S2 | S | Coverage gaps → add to inject list. | QA |

### K-Seed — known-good positives

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-P1 | Web-source 4 APA-7 corpus docs | 1 | `tests/corpus/seed/*.docx` (gitignored if license requires), `tests/corpus/seed/SOURCES.md` | Independently download 4 APA-7-conforming .docx from the web (official APA student + professional samples, CC-licensed university repository papers); verify upload gate; run harness — should score high. | 4 files, each scores ≥ ~90% on harness; `SOURCES.md` records URL + license for each. | `python -m tools.corpus.harness --docx <each> --all --out -` | K-0.3 | M | URLs may be dead/changed → UNVERIFIED until fetched; license may forbid commit → gitignore. | QA |
| K-P2 | Mode coverage check on the 4 | 1 | `tests/corpus/coverage_matrix.csv` | Confirm the 4 docs jointly cover student + professional mode, abstract present/absent, tables, figures. | Matrix shows coverage or explicit `na`; gaps noted as risk. | review of manifest | K-P1 | S | 4 docs may not cover everything → mark `na`, do not expand corpus. | QA |

### K-Inject — defect-injection tooling

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-I1 | Injector framework | 2 | `tools/corpus/inject.py` | CLI: `python -m tools.corpus.inject --base good.docx --defect APA-03 --out bad.docx`; seeded RNG; one defect per output; records defect in manifest. | Each invocation emits bad.docx + manifest row with `defects_injected=[APA-xx]`. | `python -m tools.corpus.inject --base seed/<one-of-4>.docx --defect APA-03 --out /tmp/x.docx` then harness reports APA-03 fail. | K-S2 | M | Injected doc may trip other rows → gold labels must allow `na`. | docx-XML |
| K-I2 | Defect recipes: formatting | 2 | `tools/corpus/defects/format_defects.py` | Recipes: justified body (`w:jc="both"`), line spacing 1.15 (`w:line="276"`), font e.g. Times New Roman 11 → set every run/style to TNR 11 where Calibri expected? Use explicit allowed-set member swap; missing first-line indent (remove `w:ind w:firstLine`), missing page number (strip header PAGE field), 1.15 vs double spacing variant. | Each recipe produces exactly its one defect; harness flags exactly that row. | `pytest tests/corpus/test_inject_format.py` | K-I1, K-0.4 | M | Style-level vs run-level mutation confusion → inject at both and record where. | docx-XML |
| K-I3 | Defect recipes: headings/abstract/references | 2 | `tools/corpus/defects/struct_defects.py` | Recipes: heading levels wrong (demote L2→L1), Abstract missing/ >250 words/indented, References not starting on new page, missing hanging indent, references not alphabetical, comma-decimal numbers ("3,5"→"3.5" should fail decimal policy), missing "et al." for 3+ authors, "&" in narrative citation, inline >40-word quote not block-formatted, "Practitioner Notes" section inserted (JUTLP residue), banner/textbox inserted (JUTLP residue), numbered headings. | Same as K-I2 per recipe. | `pytest tests/corpus/test_inject_struct.py` | K-I1 | L → split K-I3a (headings+abstract) / K-I3b (references+citations+residues) | Injectors may produce invalid docx → validate via gate test. | docx-XML |
| K-I4 | Injector round-trip gate | 2 | `tests/corpus/test_injector_ingestible.py` | Every injected doc must be openable by the CURRENT engine (python-docx + cli_copybot --analyse) — the injector must not produce docs the engine crashes on. | All injected fixtures pass `--analyse` (no traceback). | `pytest tests/corpus/test_injector_ingestible.py` | K-I1..K-I3 | M | Current engine may reject valid docs → report to C. | docx-XML |

### K-Real — realistic/messy documents + consent

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-R1 | Consent + anonymisation pipeline | 3 | `tools/corpus/anonymize.py`, `docs/corpus-consent.md` (or `tests/corpus/CONSENT.md`) | Strip author names/affiliations from .docx core properties + front page text where safe; write consent register row; refuse to add to repo without `license_status=consented`. | Anonymised doc opens; no original author name in `docProps/core.xml` or front-page text nodes matching a name list. | `pytest tests/corpus/test_anonymize.py` | K-S2 | M | Over-aggressive strip may break front-page checks → keep title/abstract. | QA + docx-XML |
| K-R2 | Legacy JUTLP pack: reference only | 2 | `tests/corpus/messy/README.md` | Do NOT copy/inject/commit `tests/jutlp_sample_docx_test_pack/` or the local AI_Pool drive as corpus. Document that they are JUTLP-shaped and excluded from the APA-7 corpus; they may only be used ad hoc as messy-input smoke tests. | README present; `tests/corpus/messy/` contains only the README (no .docx). | `Get-ChildItem tests/corpus/messy -Filter *.docx` returns nothing. | K-0.1 | S | Temptation to reuse → keep the exclusion explicit. | QA |
| K-R3 | License audit on the 4 web-sourced docs | 3 | `tests/corpus/seed/SOURCES.md` (extend) | For each of the 4, record license/permission status, whether redistribution is allowed, and whether anonymisation was needed (author names in headers/core props). | All 4 rows: license identified, redistribution decision (commit or gitignore) recorded. | review | K-P1, K-R1 | S | License ambiguity → default to gitignore + fetch-on-demand. | QA |

### K-Harness — conformance checker

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-H1 | OOXML safe-open / validity check | 1 | add to `tools/corpus/docx_view.py` | zip valid, `[Content_Types].xml` present, all XML parts well-formed, `w:document` root, `w:id` values unique & monotonic (revision ids). | Reports per-file `valid: true/false` + reasons. | `pytest tests/corpus/test_validity.py` | K-0.3 | S | Some legit docs reuse ids → report, don't hard-fail. | docx-XML |
| K-H2 | Margins / spacing / align / indent / pagenum checks | 1 | extend `tools/corpus/harness.py` | Checks for APA-00, APA-01 (spacing incl. block quotes + refs, no blank lines before/after headings), APA-03, APA-04, APA-05; each returns pass/fail/evidence via K-0.4 resolver. | ≥5 checks emit pass/fail JSON; on `synthetic_apa7_good.docx` all pass; on injected defect docs exactly the matching row fails. | `pytest tests/corpus/test_harness_core.py` | K-0.4 | M | Effective-format resolver edge cases → evidence strings must show raw path. | docx-XML |
| K-H3 | Font check | 1 | `tools/corpus/checks/fonts.py` | Effective font of every run ∈ allowed set (11 Calibri / 11 Arial / 12 TNR / 11 Georgia / 10 Lucida Sans Unicode); size matches the family's allowed pt. | pass/fail per doc + list of offending runs. | `pytest tests/corpus/test_fonts.py` | K-0.4 | M | Fonts set at style level only → resolver dependency. | docx-XML |
| K-H4 | Heading levels/formatting check | 2 | `tools/corpus/checks/headings.py` | For each heading paragraph: level from style (Heading1..5 / outlineLvl), L1 centered bold, L2 flush-left bold, L3 flush-left bold italic, L4 indented bold, L5 indented bold italic; title case; no "Introduction" heading (APA-10). | pass/fail per heading + evidence. | `pytest tests/corpus/test_headings.py` | K-0.4 | M | Split S/M if needed. | docx-XML |
| K-H5 | References block check | 2 | `tools/corpus/checks/refs.py` | "References" starts on a new page (page break before), bold centered, hanging indent 720, double-spaced, alphabetical order, DOI form `https://doi.org/...` (APA-12, APA-18). | pass/fail per sub-check. | `pytest tests/corpus/test_refs.py` | K-0.4 | M | Order check needs sentence segmentation → simple first-token compare acceptable for v1. | docx-XML |
| K-H6 | Abstract/keywords check | 2 | `tools/corpus/checks/abstract.py` | "Abstract" bold centered, ≤250 words, single unindented paragraph (APA-08); keywords label italic, indented, ≤~1 line (APA-09). | pass/fail. | `pytest tests/corpus/test_abstract.py` | K-0.4 | S | Word count of abstract zone needs boundary detection → reuse heuristic. | docx-XML |
| K-H7 | Negative residue check | 2 | `tools/corpus/checks/residue.py` | Output must NOT contain: "Practitioner Notes", banner textbox shapes, CRediT block, "This Journal" JUTLP phrases, blinded placeholders expecting JUTLP. (APA-20) | pass/fail + matches found. | `pytest tests/corpus/test_residue.py` | — | S | JUTLP template styles may still carry old ids → string scan + style-id scan. | docx-XML |
| K-H8 | Appendices preserved check | 2 | `tools/corpus/checks/appendices.py` | If input had an Appendix, output must still contain it (APA-19); input lacking appendix → n/a. | pass/fail/na per doc. | `pytest tests/corpus/test_appendices.py` | — | S | Appendix detection heuristic → label. | docx-XML |
| K-H9 | Text-preservation check (accepted view) | 2 | `tools/corpus/checks/preservation.py` | Accepted-changes text of output, minus known intended deletions (banner, practitioner notes, heading-name normalisations), must contain the input's substantive text; rejected view must equal input text modulo intended insertions. | pass/fail + diff summary (counts of inserted/deleted chars). | `pytest tests/corpus/test_preservation.py` | K-0.3 | M | Intended-edit whitelist needs care → allow `--allow` list from manifest. | docx-XML |
| K-H10 | Table/figure numbering check | 3 | `tools/corpus/checks/tables_figs.py` | Table captions "Table N" bold + italic title; Figure captions "Figure N" bold + italic title (APA-15, APA-16); numbering monotonic. | pass/fail per caption. | `pytest tests/corpus/test_tables_figs.py` | — | S | Caption detection heuristic. | docx-XML |
| K-H11 | Citation format check | 3 | `tools/corpus/checks/citations.py` | Parenthetical `(A & B, 2020)` / narrative `A and B (2020)`; 3+ authors use et al. (APA-13); block quote ≥40 words is indented block, no quotes, citation after final period (APA-14). | pass/fail + offending instances. | `pytest tests/corpus/test_citations.py` | — | M | Regex-based; v1 acceptable. | docx-XML |
| K-H12 | Harness CLI + score aggregation | 2 | `tools/corpus/harness.py` (extend), `tools/corpus/score.py` | `--all` runs every check; emits per-doc JSON + aggregate: conformance % per doc, per-rule pass rates, #tracked changes per pass family (count `<w:ins>`/`<w:del>` grouped by author/pass if present), regression flag if a known-good doc gets worse vs baseline. | `python -m tools.corpus.harness --docx out.docx --all --baseline reports/baseline/run1 --out scores.json` produces schema-conformant JSON. | `pytest tests/corpus/test_harness_cli.py` | K-H1..K-H11 | M | Keep schema versioned. | QA |

### K-Baseline / K-Final — runs and reports

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-B1 | Baseline run (current engine) | 0 | `reports/baseline/run1/` | See K-0.5/K-0.6. Freeze commit hash, env, model, temperature, N=3 LLM variance on 5 docs. | `run_meta.json` + `summary.md`; git tag. | tag + files present | K-0.5 | M | LLM nondeterminism → report variance, don't block. | QA |
| K-B2 | Mid-sprint run after C stage1 | 2 | `reports/mid/` | Re-run harness on seed corpus; diff per-rule deltas vs baseline. | `reports/mid/summary.md` with per-rule delta table. | compare summary.md before/after | K-B1, K-H12 | S | Pipeline broken mid-sprint → record errors. | QA |
| K-B3 | FINAL run on full corpus | 4 | `reports/final/` | Full corpus (4 seed + injected variants derived from them). | Per-doc table + aggregate conformance % + per-rule before/after delta + regression flags + LLM variance. | `python -m tools.corpus.report --before reports/baseline/run1 --after reports/final --out demo_report.md` | K-B2, K-I4, K-R3 | M | LLM variance → N=3 on 5 docs. | QA |
| K-B4 | Regression gate | 3 | `tools/corpus/gate.py` | Fail if any known-good positive's conformance % drops >X points vs baseline; fail if any injected-defect doc no longer shows the defect fixed for its matrix row when C claims it fixed. | `python -m tools.corpus.gate --baseline reports/baseline/run1 --candidate reports/final` exit code reflects regressions. | run on a deliberately regressed fixture | K-H12 | S | Threshold X client decision → default 0. | QA |

### K-Infra — layout, storage, CI hook

| ID | Title | Stage | Scope | Description | Acceptance | Verification | Deps | Size | Risk | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| K-INT1 | Data governance: consent, anonymisation, storage, LFS | 1 | `docs/corpus-data-governance.md`, `.gitignore` updates, `tests/corpus/real/.gitkeep` | Policy: no identifiable manuscript committed; consent register required; large binaries via git LFS or excluded; samples fetched, not committed. | `.gitignore` covers `tests/corpus/real/`, `samples/`; governance doc present; `git status` shows only manifests/README. | `git check-ignore tests/corpus/real/x.docx` returns ignored. | K-R1 | S | Team confusion → one owner. | QA |
| K-INT2 | Reproducibility pinning | 1 | `tools/corpus/requirements-corpus.txt`, `tools/corpus/RUNBOOK.md` | Pin python-docx, lxml, pytest versions; seed RNG documented; deterministic injector output; record `OPENAI_MODEL`/`OPENAI_TEMPERATURE` used. | `pip install -r tools/corpus/requirements-corpus.txt` then injector twice → byte-identical output. | run injector twice, `sha256` equal | K-I1 | S | Version drift → re-pin. | QA |
| K-INT3 | CI hook (harness as pytest) | 2 | `tests/corpus/test_conformance_smoke.py` | Pytest that runs harness on the seed corpus outputs (committed golden outputs) so CI catches harness breakage; NOT a full pipeline run (too slow) — pipeline runs stay in K-B*. | `python -m pytest tests/corpus -v` green. | same | K-H12 | S | CI time → golden outputs only. | QA |

---

## 2. STAGE GATES & DEMO ARTEFACTS

| Stage | Entry | Exit (runnable check) | Demo artefact |
|---|---|---|---|
| 0 | repo clean, venv active | `python -m pytest tests/corpus -v` green; `reports/baseline/run1/summary.md` exists and is git-tagged | Baseline report: table(doc × APA row pass/fail), aggregate conformance %, per-rule counts, N=3 LLM variance, #tracked changes per family |
| 1 | Stage 0 tagged | `python -m tests.corpus.manifest --validate` green; coverage matrix shows ≥1 pass+fail per gradable row | Corpus manifest + coverage matrix |
| 2 | Stage 1 exit | K-I4 ingestibility test green; K-H2..K-H9 all implemented; mid report vs baseline in `reports/mid/summary.md` | Mid-sprint conformance delta table |
| 3 | Stage 2 exit | K-B4 regression gate green; real-paper intake attempted | Mid report + consent register |
| 4 | Stage 3 exit | K-B3 final report + K-B4 gate green | Final demo report (per-doc + aggregate + per-rule before/after delta + tracked-change counts) |

---

## 3. DEPENDENCY GRAPH & CRITICAL PATH

```
K-0.1 → K-0.2 → K-0.3 → K-0.4a → K-0.4b → K-0.5 → K-0.6 (BASELINE GATE → unblocks C deletions)
K-S1 → K-S2 → K-S3 → K-S4
K-0.3 → K-P1/K-P2 → K-B1(=K-0.6)
K-S2 → K-I1 → K-I2/I3 → K-I4
K-S2 → K-R1 → K-R2/K-R3
K-0.4 → K-H2 → K-H12 → K-B2 → K-B3 → K-B4
K-INT1/2/3 parallel
```

**Critical path to baseline:** K-0.1→K-0.2→K-0.3→K-0.4→K-0.5→K-0.6.
**Critical path to demo:** K-0.6→K-H2..K-H12→K-B2→K-B3→K-B4.
**K unblocks C:** K-0.6 (baseline freeze) — C must not delete before this tag exists.
**K unblocks D:** none directly; D needs K's assertion hook (below) — K-D1.

---

## 4. PARALLELISATION INSIDE K (2 people)

- **Person A (QA/harness):** K-0.1, K-0.2, K-0.3, K-H1, K-H2, K-S2/S3/S4, K-B1/K-B4 gate, K-INT.
- **Person B (docx-XML):** K-0.4a/b, K-P1/P2/P3, K-I1/I2/I3, K-H3..K-H11, K-R1/R2.
- **Shared/blocked:** K-0.5 baseline (needs A+B), K-I4 (needs B + current engine), K-B3 final (needs both).

---

## 5. CROSS-TRACK REQUESTS

**To C (deterministic pipeline):**
1. Confirm `python -m app.cli_copybot --analyse <in> --build --output <out>` works headless on a folder input (currently single-file). If not, provide a folder-runner (UNVERIFIED whether `--build` accepts a directory).
2. Emit **fired matrix_ids** in pipeline output (log or JSON sidecar) so K can assert C's rules fired where gold labels say they should. Currently no such emission exists.
3. Expose per-pass count of tracked changes (#`<w:ins>`/`<w:del>` by author) in build result.
4. Leave `tests/jutlp_sample_docx_test_pack/` untouched (reference only — excluded from the APA-7 corpus; K cannot edit outside `tests/corpus/**`).
5. Decide fate of 2 failing `test_jutlp_validator.py` tests — should not block K.

**To D (LLM layer):**
1. Pluggable assertion hook: K will import a function `d_assert_llm_output(notes, structural_validations)` that D provides, which asserts no "JUTLP"/"Practitioner Notes" strings and schema parse OK. K's harness calls it if present, skips gracefully otherwise.
2. `OPENAI_MODEL`/`OPENAI_TEMPERATURE` (and `OPENAI_MAX_TOKENS`) recorded in run metadata — confirm these env var names (README confirms).

---

## 6. RISKS, OPEN DECISIONS, OUT-OF-SCOPE

**Risks:**
- Style-inheritance resolution (K-0.4) is the hardest piece — split done; if still hard, fallback to checking direct paragraph props only and mark evidence as "direct-only".
- Accepted-vs-rejected view algorithm: implemented as "apply w:ins, drop w:del" for accepted; inverse for rejected. Confirm with C that their comments/tracked-change author marking distinguishes passes.
- LLM nondeterminism pollutes before/after deltas → N=3 on 5 docs, report variance.
- Injected docs may trigger unexpected rows → gold labels use pass/fail/na, and K-I4 forces ingestibility.
- JUTLP-shaped harness checks (e.g. "no banner") may pass trivially before C deletes the banner code → negatives only meaningful post-C; record pre/post.

**Open decisions (client/team):**
1. Gradable threshold for "conformance %" and which APA rows are auto-gradable vs manual-review.
2. Sample .docx licensing/redistribution — default: fetch, don't commit.
3. Allowed font default (client pick) — harness may need to read it from config/env.
4. Regression threshold X for K-B4 (default 0 points).
5. `CAROUSEL_ENABLED` default — carousel is C/D territory, K only needs no JUTLP residue.

**Out of scope for K:** deployment, MemberPress/Stripe, login gate, editing `app/**`, implementing the APA engine itself (C/D), the clean-vs-tracked download toggle.

---

## END — Required outputs

**(1) Minimum K ticket set for a credible next-session demo:**
K-0.1 → K-0.2 → K-0.3 → K-0.4 (split a/b) → K-0.5 → K-0.6 (baseline) · K-S2 (manifest) · K-H2 + K-H3 + K-H7 (core checks) · K-B1 (final baseline report). Plus K-I1 (one defect recipe, e.g. APA-03 justify) on a seed doc to show inject→detect loop.

**(2) First 5 K tickets to start tomorrow (dependency order):**
1. K-0.1 (seed corpus + manifest)
2. K-0.2 (upload-gate test)
3. K-0.3 (harness + accepted/rejected view)
4. K-0.4a (style-chain walker)
5. K-0.4b (docDefaults + units) → then K-0.5 baseline run.

**(3) Decisions needed from client/team:** (client: default font set; US vs AU spelling; student vs professional default; consent for real papers; sample-docx redistribution. team: threshold for "conformance %"; C to confirm headless folder runner + fired matrix_ids; D to confirm assertion hook + model env vars.)

UNVERIFIED items: whether `app.cli_copybot --build` works headless on a folder; exact OPENAI_MODEL default value in code (README says gpt-5.4-mini); `w:id` uniqueness guarantee from C.
