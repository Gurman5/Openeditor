# Execution Plan — `joeys-revisions`

**Doc owner:** pipeline dev team (author: analysis from Joey's changelog + dev-trace run of 2026-10-20)
**Companion docs (read these first):**

| Doc | Path | Use it for |
|---|---|---|
| Root-cause analysis | `research/joeys-revisions-analysis.md` | Evidence, trace findings, code walk-throughs (file:line) |
| Dev backlog | `docs/joeys-revisions-backlog.md` | Ticket definitions JB-01…JB-12, acceptance criteria |
| This document | `docs/joeys-revisions-execution-plan.md` | How we implement, verify, and land the work |

---

## 1. Why this branch exists

Joey reviewed a pipeline output (ASCILITE 2026 concise paper) and reported a set of defects: an
editorial-AI crash that silently discards its own review, placeholder author blocks ("First
Authorʳ") polluting output and LLM prompts, an active acronym feature he wants inactive, preserved
running heads where he wants blank headers + page number, deep false positives on research
questions from the short-paragraph checker, missing-abstract confusion, corrupted re-written
references (lost page numbers, missing space before DOI URL, lost italics), table headings getting
indented, and no figure-block check at all.

The 2026-10-20 trace run qualifies all of these against the code (see the analysis doc for the
complete root-cause map). The pipeline is 31 stages; the branch touches **7 stage bodies, 3 new
exemption helpers, 1 feature flag, and 1 diff engine** — no orchestration surgery.

## 2. Branch, environment, commands

- Branch: `joeys-revisions` (cut from `dev-pipeline-trace` @ `1addaf0`).
- PR target when tickets land: `dev-pipeline-trace` (stay consistent with prior sprint flow).
- Windows dev: `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt`.
- Tests: `.\.venv\Scripts\Activate.ps1; .venv\python -m pytest` — the suite existing before this work
  is baseline (`docs/baseline-pytest.txt` documents suite conventions).
- Verify behaviour with the trace harness: `PIPELINE_TRACE=1` run against the same manuscript used
  for the analysis (`trace_cli` output dir), then diff the HTML report against
  `C:\Users\daria\Downloads\trace_cli\trace_report.html` as the "before" golden.
- Lint: `ruff` (project `ruff.toml`: py311, line-length 100, E/F/W/I).

## 3. Locked team decisions (recorded — do not re-open without email trail)

1. **Acronyms**: gate stage behind `ACRONYM_FEATURE_ENABLED`, default **off**. Settings UI/storage stay.
2. **Placeholder authors/affiliations**: **comment out the function usage** (not parameterise), with
   an inline rationale comment quoting Joey's recommendation; no placeholder text may ever reach the
   document, prompts, or output filename. FP002/FP003 comment-only rules stay.
3. **Intro Level-2 subheadings**: LLM-guideline text only — **no deterministic rule**.
4. **Reference surgery**: full diff-based surgical engine is **in scope on this branch**, built on
   JB-10's fixed primitives (Joey's "consider last" applies to ordering, not exclusion).

## 4. Implementation playbook (per ticket)

Ordering: **JB-01 → JB-02 → JB-03** (P0, can run in parallel once JB-01's pipeline file is not
contended), then **JB-05 → JB-06 → JB-07** (P1), then **JB-04 → JB-08 → JB-09 → JB-10** (P2), then
**JB-11** (builds on JB-10) and **JB-12** anytime. One ticket per PR; each PR must end with green
tests + a dev-trace spot run if it touches a stage body.

### 4.1 JB-01 — pipeline crash fix (half-day)

**Files:** `app/pipelines/feedback_gen_pipeline.py` (line 820 only), `tests/`.

- Replace `(llm_result or {}).get("notes")` with a shape-safe read:
  `notes_count = len(getattr(llm_result, "notes", []) or []) if llm_result else 0`.
- While there, audit the two `"critical"` severity sites (`:820`, `:848`) — nothing else treats
  dataclasses as dicts; the audit is a grep for `.get("notes")` on result objects.
- **Definition of done:** regression test reproduces the AttributeError with the dataclass mock and
  passes post-fix; trace run shows `llm_editorial_review` green and editorial notes present in the
  assembled document (assemble_comments count reflects them).

### 4.2 JB-02 — placeholder author/affiliation insertion disabled (1 day)

**Files:** `app/services/output_generation_samfix.py` (plan construction + application), filename
data in `build_edited_document` tail.

- Comment out (do not delete; Joey may want this later behind a flag):
  1. `authorFormatCheck()` plan construction returning `insert_default_authors` (**1646-1671**) —
     leave `replace_in_place` tracked-replace plans for *malformed but present* author lines intact
     (that is a correction, not an invention).
  2. `_apply_author_plan` handler arm for `insert_default_authors` (**6785-6842**).
  3. `abstractFormatCheck` default-affiliation insertion paths (**2656-2689**, **2817-2836**,
     application 6990-6997).
- Add the rationale block comment at both work sites:
  > Disabled per Joey's reviewer instruction (2026-10): the tool must keep manually placed author
  > name and affiliation exactly as authored (e.g. Michael Cowling and Joshua Newn, RMIT University)
  > and must not inject "First Author^a…" placeholder blocks. Missing author/affiliation is covered
  > by FP002/FP003 comment-only flags.
- Keep `SUPERSCRIPT_CHAR_MAP` etc. (used for legitimate markers in other paths).
- Filename: `build_output_filename_from_author_line(author_plan.get("corrected_authors_line", ""))`
  (**9931-9941**) must fall back to the uploaded filename when the line contains placeholder markers —
  guard with the same marker regex used for extraction.
- Sanity check the `llm_calls/25` scenario: rerun trace and confirm the second editorial prompt shows
  real authors ("Michael Cowling and Joshua Newn").

### 4.3 JB-03 — acronym feature flag (half-day)

**Files:** `app/services/config.py` (flag constant), `app/pipelines/feedback_gen_pipeline.py:977-991`.

- Add `ACRONYM_FEATURE_ENABLED = env_flag("ACRONYM_FEATURE_ENABLED", default=False)` parallel to how
  other env flags are parsed in `config.py` (see `CROSSREF_CACHE`, `APA7_TITLE_PAGE_MODE` and the
  D-11 `max_upload_mb`/`max_word_count` pattern for the established way).
- Gate at the pipeline site: `if ACRONYM_FEATURE_ENABLED: <existing wrapped block>`.
- README: add the flag to the Railway env table (README "Railway Deployment" section).
- Settings routes untouched. `ACRONYM_DB_PATH`/`ACRONYM_ADMIN_PASSWORD` remain documented as-is.

### 4.4 JB-05 — RQ/hypothesis exemption (1 day, shared helper first)

**Files:** new `app/services/paragraph_classifiers.py` (or `document_zones.py` extension);
`app/services/short_paragraph_comments.py`; `app/services/output_generation_samfix.py`
(`_collect_paragraph_development_issues`, **3989-4078**); `sentence_coherence_corrections.py`
input filter; the per-paragraph LLM body-edit selection in the tracked-changes pass.

- Build the helper first and unit-test it standalone:
  - single sentence (`_sentence_count` semantics reused, `short_paragraph_comments.py:51-61`);
  - matches `^RQ\s*\d+|^H\s*\d+` OR starts `"Research question"|"Hypothesis"` (case-insensitive)
    OR single-sentence `<80 chars` ending `?` within a body zone.
  - Return `false` (not exempt) for anything with ≥2 sentences so the over-exemption risk is nil.
- Wire into: (a) `apply_short_paragraph_comments` guard list, (b) Sam's paragraph-development
  collector, (c) body-edit LLM selection, (d) coherence input list.
- Trace-target: `short_paragraphs` edits 11 → 9 on the analysis corpus; LLM calls 06/07 disappear.

### 4.5 JB-06 — abstract detection + consolidated comment (1 day)

**Files:** `app/services/document_analysis_services.py` (**334**, **392-393**),
`app/services/apa7_validator.py` (**171-208**), `app/services/output_generation.py` anchors
(**658-663**, family map **357-367**), prompt-side suppression in `ai/prompt_builder.py`.

- Normalise heading text (strip, casefold, strip trailing `:`) before the equality checks; accept
  the JUTLP label set (`canonical_jultp_template.py`).
- Replace the FP004/FP007/FP008 triple-fire with a single genuine-missing comment carrying Joey's
  wording ("the abstract and/or abstract heading is missing…"). Suppress FP006/FP008 when FP007
  already fired (they cascade from the same cause).
- Suppress the duplicate editorial LLM note: prompt-builder already lists automated failures —
  the consolidation makes this automatic; verify via trace (`llm_calls/02` had a duplicate).

### 4.6 JB-07 — missing-section wording alignment (half-day)

**Files:** `app/domain/canonical_jultp_template.py:177-190` (`missing_section_queries`); wording
assertions in `tests/test_jutlp_validator.py` / validator tests.

- Rewrite per-section message templates to the agreed phrasing shape; keep rule IDs and verdicts
  unchanged so downstream maps (`output_generation.py:_SEC_RULE_TO_SECTION`, **341-342/804-807/994-998**)
  need no edits.
- Regression-guard no-insertion: assert no new headings in output for a fixture missing
  Method/Results/Discussion (verdict "comment" per `reporting_ownership.py:52-58`).

### 4.7 JB-04 — header blanking (1 day, touches tracked-change surface)

**Files:** `app/services/output_generation_samfix.py` (`_apply_apa_body_geometry` **7866-7939**,
`_make_page_number_header` **7829-7863**, `_apply_apa_title_page_headers` **8531-8542**).

- Sequence: (1) ensure PAGE paragraph; (2) iterate running-header parts (default + first) and delete
  any paragraph not the PAGE one (except the PAGE paragraph itself); keep `sectPr` intact.
- Do NOT touch footers. Do NOT mark header removals as track-changes (headers don't need revision
  markup; confirm with Joey-informed lint notes in PR description).
- While there: consider extracting unused machinery `_find_header_picture_part` /
  `_doc_has_first_page_header_picture` / `_ensure_first_header` / `_patch_header_content_type` /
  `_insert_front_page_banner_from_template` (samfix **4983-5346**) — dead code, zero callers;
  removal optional, separate commit.
- Word COM gate assertion: page number renders top-right (word_gate already opens the output).

### 4.8 JB-08 — table indent exclusion (1 day)

**Files:** `app/services/output_generation_samfix.py` (body-format issue collection
(`_collect_body_formatting_issues` **4082-4117**, `_apply_tracked_body_paragraph_format` **7942-7975**),
indent passes in `reference_indent.py`, `references_block_corrections.py`,
`abstract_keywords_formatting.py`; `document_zones.py`.

- Treat a `Normal` paragraph inside ±table-range as "table caption/head": excluded from
  firstLine=720. Detect table membership by consecutive `w:tbl` neighbour scan (python-docx:
  sibling element inspection, no new dependency).
- Assert spacing uniformity inside tables remains untouched (spacing pass should skip table
  paragraphs entirely).
- Fixture: table 3×3 + heading paragraph above (Normal), subheading below; XML assertions after run.

### 4.9 JB-09 — figure block + callout check (1 day)

**Files:** `app/services/caption_apa7_check.py` (extend), wiring in
`app/pipelines/feedback_gen_pipeline.py` (stage right after `captions_apa7`, ~line 1049).

- New checks (comment-only, anchored on the figure label paragraph):
  1. `Figure N` bold, above image;
  2. italic title line;
  3. description/description note present;
  4. in-text callout before the figure: regex `\bFigure\s*N\b` in any paragraph with a lower index.
- Reuse `iter_paragraphs_with_zone` / skip `outside` zones as the existing flow does (`:153`).
- Note: Table 1's callout check behaviour should mirror this if cheap (tables arguably already
  covered by `table_n_notation_comments` — review, don't force).

### 4.10 JB-10 — reference rewrite hardening (2 days)

**Files:** `app/services/reference_format_corrections.py` (**168-263** apply, **227** rstrip bug),
`app/services/reference_checker.py` (`_verify_with_doi` **735-814**), dev-trace snapshots for
visual asserts.

- Fix 1: space handling — build the inserted plain text as `text_before + " " + url`
  (mirroring pipeline's `_inject_crossref_doi_links` at `feedback_gen_pipeline.py:457`). Failure
  mode to regress: `28(4).https://doi.org/...`.
- Fix 2: italics — during re-insert, split the reconstructed string into (journal volume italic /
  plain) spans using CrossRef metadata (`_get_apa_via_content_negotiation` at `reference_checker.py:647-706`
  currently returns raw text; extend to also capture `title`/journal fields, which retrieval already
  has structured — see Z-06 gap note "title is always null" as a related follow-up seam). APA 7: journal
  name + volume number italic, issue number not. Deliberately conservative: italicise only when both
  fields resolve; never guess.
- Fix 3: tracked-change completeness — assert in a test that a URL correction produces `w:del`
  (old URL) + `w:ins` (new URL) rather than a single blob replacing the entry.
- DOI casing: when similarity is driven by casing only, skip rewriting (casing is cosmetic diff noise;
  CrossRef content-negotiation normalises case).

### 4.11 JB-11 — surgical reference diff engine (2-3 days, after JB-10)

**Files:** `app/services/reference_format_corrections.py` (new `_apply_surgical_del_ins`);
`app/services/reference_reconstructor.py` (`references_are_equivalent` reused as-is).

- Engine: `difflib.SequenceMatcher(None, old_text, new_text).get_opcodes()` → for each
  `replace/delete/insert` opcode emit minimal `w:del`/`w:ins` **run fragments**, preserving original
  `pPr`, bookmarks, comment anchors, hyperlinks, and untouched run formatting (italics/hyperlinks
  survive because untouched runs are never re-wrapped).
- Map: `equal` runs stay untouched; `replace/delete` are wrapped; `insert` appended at the opsite position.
- Fallback: whole-entry `_apply_del_ins` for unresolvable structures — same NC ITE semantics.
- Insight for review: **equivalence gate stays**: `reconstructed` only attached when
  `references_are_equivalent` fails URL-less and similarity ≥ 0.70 (`reference_checker.py:799-804`);
  the engine changes *how* the correction is written, not *when* it is decided.
- Golden fixtures: preserve (a) whole-entry unchanged → zero ops, (b) page-range-only change →
  one del+ins pair around the digits, (c) URL-only change → hyperlinked pair, (d) PubMed-style
  "et al." suffix normalization, (e) mixed.

### 4.12 JB-12 — LLM guideline addition (quarter-day)

**Files:** `app/domain/apa7_guidelines.py` (guidelines under the existing headings section),
`ai/prompt_builder.py` assembly check.

- Copy: "Introduction subsections: if the introduction is long and requires subheadings, use
  APA-7 Level 2 headings (bold, flush left, title case) for those subsections."
- Per decision: no validator rule; no new stage. Verify via trace that the guidelines block is
  rendered in the editorial-review prompt (grep the `llm_calls/02` snapshot).

## 5. Verification & release gates

| Gate | Requirement |
|---|---|
| Tests | `pytest` green; each ticket adds/extends fixtures as in the backlog |
| Lint | `ruff check . && ruff format --check .` (line-length 100) |
| Trace diff | Run the harness on the analysis manuscript; confirm: editorial stage OK, `acronyms` skipped, no `First Author` in any prompt/snapshot, `short_paragraphs` count drops by the RQ count, no `28(4).https://…` artifacts, header XML = PAGE only |
| Word COM gate | `word_gate ok=true` on final snapshot (unattended Office must remain available) |
| Output filename | Not placeholder-derived; `FirstAuthor_JUTLP_…` only from real authors |

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Commenting out author/affiliation insertion hides a different intended code path (replace_in_place for malformed-but-present lines is legitimate) | JB-02 restricts to `insert_default_authors` arms only; commented code + rationale keep intent visible |
| Header blanking strips `sectPr`-carrying paragraphs (regression → blank pages) | header-level iteration only; sectPr guards already exist in normalisation (`document_normalisation_services.py:276-298`); OOXML check catches breakage in trace runs |
| RQ exemption over-fires (real short paragraphs skipped everywhere) | helper is opt-in per tick (a)–(d) call sites, never global; over-exemption handled by the ≥2-sentence rule and body-zone-only scoping |
| Diff engine regressions produce corrupted `w:xml` in complex reference paragraphs | engine falls back to the existing whole-entry path; `ooxml_check` + having the Cheng & Tsai golden test |
| Placeholder suppression breaks filename generation when real authors are absent | explicit fallback to uploaded filename using the marker regex (covered by acceptance tests) |
| Feature flag rot | flag is asserted in tests both ways; README documents it beside the Acronym vars |

## 7. Open items (not in this branch's scope — surface to Joey/team)


1. **References[].title always null** (Z-06 known gap): JB-10's italic resolution would benefit from
   filling it; a second CrossRef call per verified reference is the blocking cost — ticket if JB-10
   uncovers it's necessary, otherwise defer.
2. **Clean-vs-tracked-changes download binary** remains deferred (G-04 contract: tracked-only for current scope).
3. **LLM body-edit hallucinations on clean paragraphs** (trace `llm_calls/05`: invented edit) —
   orthogonal to this branch; recommend a separate guard ticket if it recurs after JB-05's filter
   removes the RQ cases.

## 8. Suggested PR slicing

| PR | Tickets | Title line |
|---|---|---|
| 1 | JB-01 | fix(pipeline): editorial-review result attribute error discards successful AI review |
| 2 | JB-02 | fix(samfix): disable placeholder author/affiliation insertion (Joey revision) |
| 3 | JB-03 | feat(config): gate acronym stage behind ACRONYM_FEATURE_ENABLED (default off) |
| 4 | JB-05 | fix(comments): exempt research questions/hypotheses from short-paragraph & per-para passes |
| 5 | JB-06, JB-07 | fix(validator+comments): abstract detection + missing-section wording (Joey phrasing) |
| 6 | JB-04, JB-08 | fix(samfix): blank running header, exclude table headings/captions from indenting |
| 7 | JB-09 | feat(captions): figure number/title/description + in-text callout check |
| 8 | JB-10 | fix(references): preserve italics, DOI URL spacing, complete tracked URL changes |
| 9 | JB-11 | feat(references): surgical diff engine replacing whole-entry rewrites |
| 10 | JB-12 | docs(prompt): introduction Level-2 subheading guidance (LLM only) |

Each PR carries its own ticket-linked tests; PR 9 depends on PR 8; nothing else serialises (see the
dependency diagram in the backlog).
