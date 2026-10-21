# Dev Backlog — Pipeline Issues (Joey's Revisions)

This backlog covers issues **within the document-processing pipeline** surfaced by Joey's changelog
and the 2026-10-20 dev-trace run. Full evidence and code walk-throughs:
`research/joeys-revisions-analysis.md` (root-cause analysis, file:line refs throughout).

Scope note: only pipeline/deterministic/LLM-layer work is tracked here. Frontend-only items from
Joey's changelog ("The structural headings" section, currently an empty heading awaiting his
clarification) are **excluded**.

Ticket IDs are stable (`JB-01`…`JB-12`) so branches/PRs/commits should reference them directly.

---

## Priority legend

| P | Meaning |
|---|---|
| **P0** | Blocking / correctness breakage — must land first |
| **P1** | Comment accuracy — comments the tool emits must match Joey's editorial intent |
| **P2** | Formatting fidelity — tracked changes must not damage the document |
| **P3** | Refactor / engine-level improvements and guideline-only items |

---

## P0 — Critical breakage

### JB-01 — Fix editorial-review result being discarded (pipeline crash)

- **Priority:** P0 · **Source:** trace stage `llm_editorial_review` → `AttributeError: 'EditorialReviewResult' object has no attribute 'get'`
- **Root cause:** `app/pipelines/feedback_gen_pipeline.py:820` treats the `EditorialReviewResult`
  **dataclass** (`app/domain/editorial_feedback.py:23-28`) as a dict. The exception is swallowed by the
  stage `try/except` (opened `:813`, caught `:821-824`) which sets `llm_result = None` and records a
  **"critical"** stage error — a *successful* 10-note AI review (8.7k tokens) is thrown away on every run.
- **Fix:** access the attribute directly (`len(llm_result.notes)` if not None), with a narrow
  parametrised helper so future result shapes can't regress.
- **Acceptance:**
  - Editorial-review stage completes without stage error when the LLM returns notes.
  - `stage_errors` contains no `Editorial review (AI)` entry on a healthy run.
  - Notes from the review appear in the assembled document comments.
- **Tests:** unit test mocking `run_editorial_review` to return the dataclass; assert pipeline
  produces notes and no critical stage error. Regression test for the exact traceback.

### JB-02 — Disable placeholder author/affiliation insertion ("First Authorʳ")

- **Priority:** P0 · **Source:** Joey manuscript item: *"The function that adds an Affiliation
  requirement and Author Name shouldnt be active… keep manually placed author name and affiliation
  (Michael Cowling and Joshua Newn, RMIT University)"*
- **Root cause:** `output_generation_samfix.py`'s `authorFormatCheck()` (**1635-1759**) builds and
  `_apply_author_plan()` (**6785-6842**) applies an `insert_default_authors` plan — placeholder line
  `First Author^a, Second Author^a, and Third Author^b` (`DEFAULT_AUTHORS_LINE`, **375**; superscript
  glyph from `SUPERSCRIPT_CHAR_MAP["r"]="ʳ"`, **2020**), plus default-affiliation insertion from
  `abstractFormatCheck` (**2656-2689, 2817-2836, 6990-6997**). Insertion is **untracked** (no `<w:ins>`).
  Secondary leak: output filename built from the (possibly placeholder) authors line at **9931-9941**.
- **Fix (per team decision):** **comment out the usage sites** — the `insert_default_authors` plan
  construction and both default-affiliation insertion call paths — with an inline rationale comment
  citing Joey's recommendation (placeholder in the code comment: keep real author/affiliation content;
  the function that *adds* an author/affiliation requirement stays inactive). Also make filename
  derivation ignore placeholder author lines. FP002/FP003 (comment-only validator flags) stay.
- **Acceptance:**
  - No `First Author^…` placeholder text is ever inserted into the output document.
  - Real author lines/affiliations are untouched wherever they exist.
  - Editorial-review LLM prompts see the real author line (verify via dev-trace LLM snapshots).
  - Output filenames derive from real authors when present.
- **Tests:** fixture doc with real authors only → no placeholder anywhere in output; fixture doc
  with missing authors → FP002/FP003 comments still emitted, no insertion; filename assertion.

### JB-03 — Gate the acronym pass behind a feature flag (default OFF)

- **Priority:** P0 · **Source:** Joey manuscript item: *"Acronyms Feature shouldnt be active"*
- **Root cause:** stage `acronyms` (`app/pipelines/feedback_gen_pipeline.py:977-991` →
  `acronym_corrections.apply_acronym_corrections`, `app/services/acronym_corrections.py:1014-1124`)
  has **no disable flag**; it produced 6 tracked edits in the trace run.
- **Fix (per team decision):** add env var `ACRONYM_FEATURE_ENABLED` (default `false`), gate the
  stage invocation (skip whole wrapped block when disabled, record nothing in `stage_errors`).
  Settings UI (`/settings/acronyms`, `app/main.py:624-713`), `acronym_store.py` and
  `ACRONYM_DB_PATH`/`ACRONYM_ADMIN_PASSWORD` remain untouched so the feature can be re-enabled later.
  Document the flag in the README env table alongside the existing Acronym vars.
- **Acceptance:**
  - Default run: zero acronym comments/edits; stage does not appear in dev-trace output (or appears
    as explicitly skipped).
  - `ACRONYM_FEATURE_ENABLED=true` restores prior behaviour exactly.
- **Tests:** pipeline-level test with flag off/on; assert no `ACRO` zone mutations in the final docx.

---

## P1 — Comment accuracy

### JB-04 — Blank existing header; keep only the top-right page number

- **Priority:** P1 · **Source:** Joey manuscript item: *"Header should be blank, any pre-existing
  header removed with only the page number on the top right"*
- **Root cause:** `_apply_apa_body_geometry()` (`output_generation_samfix.py:7866-7939`) preserves
  existing header content and only appends a PAGE field if absent (`_make_page_number_header`,
  **7829-7863**). `_apply_apa_title_page_headers` (**8531-8542**) strips picture paragraphs only.
- **Fix:** after ensuring the PAGE paragraph exists, remove any other header content from the
  running headers (keep sectPr structure and header references intact; leave the `w:pgSz`/margins
  logic untouched). Do NOT clear footer content — Joey specified header only.
- **Acceptance:**
  - Output header XML contains exactly one paragraph: the right-aligned PAGE field.
  - Page-number position verified top-right via the Word COM gate (extend word-gate assertions if cheap).
- **Tests:** fixture doc with a pre-existing running head/logo text → header ends up blank + page
  number only; margins unchanged.

### JB-05 — Exempt research questions / hypotheses from short-paragraph and per-paragraph passes

- **Priority:** P1 · **Source:** Joey exemption clause: *"deterministic part should skip questions
  that are single sentence paragraphs that are research questions or hypotheses. So that author
  query number 10 shouldn't be happening."* Trace: RQ1/RQ2 flagged as `[5]`/`[6]`; LLM body-edits
  requested per RQ paragraph (`llm_calls/06`, `07`).
- **Root cause:** no exemption exists anywhere:
  - `app/services/short_paragraph_comments.py:71-235` (flag threshold `count >= 3` skip at ~142)
  - Sam's `_collect_paragraph_development_issues` (`output_generation_samfix.py:3989-4078`)
  - per-paragraph LLM body-edit selection in the tracked-changes pass.
- **Fix:** introduce a shared exemption helper (suggest `document_zones.py` or a new
  `paragraph_classifiers.py`): single-sentence paragraphs matching
  `^RQ\s*\d+` / `^H[0-9]` / starts with `Research question|Hypothesis` (case-insensitive), or any
  single-sentence paragraph ending in `?` in a body zone. Apply it in
  (a) `short_paragraph_comments`, (b) Sam's paragraph-development collector,
  (c) the per-paragraph body-edit LLM selection filter, (d) `sentence_coherence_corrections`
  input list filter.
- **Acceptance:**
  - Manuscript containing only RQ1/RQ2 short paragraphs: zero `PARA_SHORT` queries, zero LLM edit
    requests for those paragraphs, zero coherence flags.
  - A genuinely Gonzo two-sentence body paragraph still gets flagged (no over-exemption).
- **Tests:** fixture with RQ/H single sentences + normal short paragraphs; assert pass outcomes.

### JB-06 — Abstract: relax detection + single consolidated missing-abstract comment

- **Priority:** P1 · **Source:** Joey: *"The abstract should have the title, but the pipeline
  doesnt seem to understand its the abstract, so instead make a comment stating that the abstract
  and/or abstract heading is missing"*
- **Root cause:** exact-match heading requirement — `front_page_summary()` requires a paragraph
  whose text equals `"Abstract"` (`document_analysis_services.py:334`), `extract_abstract()` same
  (`:392-393`). Variants ("ABSTRACT", "Abstract:", merged heading) miss, cascading FP004/FP006/FP007/FP008
  plus a duplicate LLM editorial note (trace: medium-severity abstract note).
- **Fix:**
  1. Heading match: strip whitespace/case, allow trailing colon, allow the styled-but-slightly-off
     heading variants JUTLP templates use (check `canonical_jultp_template.py` label list).
  2. Consolidate: when abstract (heading and/or body) is genuinely missing, emit **one** comment
     with Joey's wording ("the abstract and/or abstract heading is missing; APA 7 places a
     single-paragraph abstract headed 'Abstract' on its own page"), anchored on the title/front
     page (`output_generation.py:658-663` anchor fallback already exists).
  3. Suppress the duplicate LLM editorial note when the deterministic check has fired.
- **Acceptance:**
  - "ABSTRACT"/"Abstract:" heading variants are detected (no missing-abstract comment).
  - Truly missing: exactly one comment, with the agreed wording; FP004/FP007/FP008 do not triple-report.
- **Tests:** fixtures for both variants and the missing case; wording assertion.

### JB-07 — Missing-section comments: align wording to Joey's phrasing

- **Priority:** P1 · **Source:** Joey structure item: *"if theres a section missing… the output is
  inserting a comment to the author: we expected to see a Results heading and Results section,
  however, the bot couldnt find that"* (reminders, never heading insertion)
- **Root cause/scope:** behavior is already comment-only (`domain/reporting_ownership.py:52-58`
  verdict "comment"; no service inserts missing headings) — only wording differs. Messages live in
  `domain/canonical_jultp_template.py:177-190` (`missing_section_queries`), fired by
  `apa7_validator.py:67-94`.
- **Fix:** update the house-policy wording for SEC001–SEC008 to Joey's framing:
  "We expected to see a Results heading and Results section; however, the bot couldn't find that.
  Please check your manuscript includes a Results section." Apply the same shape to Literature,
  Method, Discussion, Conclusion, Acknowledgements, References. Leave combined Results+Discussion
  (SPE001 warn) intact.
- **Acceptance:**
  - SEC fail messages match the agreed phrasing for every missing section.
  - No heading insertion occurs (regression-guard the ownership verdicts in tests).
- **Tests:** update existing SEC wording assertions; add a no-insertion regression check on fixture output.

---

## P2 — Formatting fidelity

### JB-08 — Exclude table headings/captions/content from indent passes; retain uniform line spacing

- **Priority:** P2 · **Source:** Joey tables item: *"The tool has indented the table heading and
  the table subheading… it should actually exclude indenting from tables, and the table row
  headings and content within the tables, however retain uniform line spacing."*
- **Root cause:** the 0.5in first-line indent (`_apply_tracked_body_paragraph_format`,
  `output_generation_samfix.py:7942-7975`, `w:firstLine=720` at 7963-7971) targets `Normal`-styled
  paragraphs in the body window (`_collect_body_formatting_issues`, **4082-4117**). python-docx
  `doc.paragraphs` excludes cell paragraphs, but **captions/table headings/subheadings around the
  table are ordinary paragraphs and get indented**. Any XML-domain pass would see cells too.
- **Fix:**
  1. Audit every indent-writing pass (`_apply_tracked_body_paragraph_format`,
     `reference_indent_corrections.py`, `references_block_corrections.py:46`,
     `abstract_keywords_formatting.py:225-286`) for exposure to table content.
  2. Add table-proximity/caption exclusion using `document_zones.py` (`is_in_table`, **283-292**;
     `should_skip_prose_paragraph` already skips cell paragraphs at **307-321** — extend the spirit
     to the formatting passes).
  3. Verify/force uniform line spacing within each table's rows (no spacing drift introduced by
     other passes).
- **Acceptance:**
  - Table heading, subheading, row headings, and cell content come out with `w:firstLine` unset.
  - Line spacing inside each table is uniform and matches pre-run state.
- **Tests:** fixture docx containing a table in body with heading/subheading — assert final XML:
  no `firstLine=720` on the affected paragraphs; spacing constant across rows.

### JB-09 — Figure APA-7 block check (number + title + description above; in-text reference before)

- **Priority:** P2 · **Source:** Joey figures item: *"APA 7 figures use a bold figure number and an
  italicised figure title positioned above the figure… must be referenced at least once within the
  manuscript… ('as discussed in Figure 1', 'see Figure 1')… the tool should check it's referred to
  at least once before it appears."*
- **Root cause:** `caption_apa7_check.py` only splits single-paragraph captions (`_needs_apa7_split`,
  **97-115**); no callout check exists anywhere (greps confirm absence). Trace: captions_apa7
  fired 0 edits with a Table 1 caption present.
- **Fix:** extend `caption_apa7_check.py` (or sibling new module, wired after stage
  `captions_apa7`, pipeline line ~1049) with discrete checks, comment-only:
  - bold `Figure N` label above the image (image paragraphs = drawing/pict runs),
  - italic title line above/below-number per APA-7, description present,
  - in-text reference regex `Figure N` (case-insensitive variants) occurring in a paragraph index
    *before* the figure's paragraph index; absence → comment "Figure N is not referenced in the
    text before it appears (APA 7: refer to every figure, e.g. 'see Figure 1')."
- **Acceptance:**
  - Figures lacking number/title/description/in-text reference each get a single, correctly anchored
    comment.
  - Correctly formed tables/figures untouched (Table handling remainder unchanged via
    `table_n_notation_comments` / `caption_apa7_check`).
- **Tests:** fixtures: malformed figure, missing callout, correct figure pass-through.

### JB-10 — Reference re-paste hardening (space, italics, DOI tracked-change verification)

- **Priority:** P2 · **Source:** Joey references items: *"removed the space after the dot before
  the URL https://doi.org/... which is both wrong"* · *"Are the italics on the journal and the
  volume number?"* · dev note: *"tool isnt including the Track changes to also change the DOI url"*
- **Root cause:** whole-entry re-paste from CrossRef plain text
  (`reference_format_corrections.py:168-263`): rstrip bug at **227** (no space before URL),
  CrossRef `text/x-bibliography` carries **no italics** (correct APA 7: journal name + volume number
  italic — Joey's question answered), URL goes into a `w:hyperlink → w:ins` run without the space.
- **Fix:**
  1. Prepend the space before the DOI URL in the inserted run (mirror
     `_inject_crossref_doi_links`, pipeline:457).
  2. Preserve/restore italics: diff-aware mapping of original italic spans onto the reconstructed
     text, or authoritative reconstruction of journal-title/volume italics from CrossRef metadata
     when re-inserting; verify old-DOI text deletion is wrapped in `w:del` so the URL change is a
     complete tracked change.
  3. DOI casing: keep the author's original DOI casing when only a URL-space/typo fix is needed.
- **Acceptance:**
  - `28(4). https://doi.org/...` — correct space, every time.
  - Rewritten references carry italic journal title + volume number.
  - Diffing the tracked changes shows both `w:del` (old text incl. old URL) and `w:ins` (new text
    incl. new URL) for URL corrections.
- **Tests:** Cheng & Tsai 2012 fixture reproducing Joey's exact before/after string; italics and
  del/ins assertions on final XML.

---

## P3 — Surgical engine & guidelines

### JB-11 — Reference surgical diff engine (replaces whole-entry re-paste)

- **Priority:** P3 (*promoted onto this branch per team decision; Joey marked the idea "low hanging
  fruit — consider last"*) · **Source:** *"it shouldn't be deleting whole references and then
  re-pasting essentially almost the same thing. It should be removing only the thing that's wrong
  and replacing the thing that's wrong with the thing that's right."*
- **Root cause:** `reference_format_corrections._apply_del_ins()` deletes **all** original runs and
  inserts the full CrossRef reconstruction whenever rough-similarity ≥ 0.70 and
  `references_are_equivalent` fails even URL-less (`reference_checker.py:799-804`).
- **Fix (design):**
  - Compute a character-level diff (difflib `SequenceMatcher` opcodes) between original entry text
    and intended corrected text.
  - Map replacements back onto original runs producing minimal `w:del` + `w:ins` run fragments,
    preserving `pPr`, bookmarks, comment anchors, and existing hyperlinks around untouched text.
  - Only fall back to whole-entry rewrite when structure is unresolvable (merged runs/textboxes or
    the entry itself is malformed).
  - No change should be made when the *only* difference is CrossRef metadata that conflicts with
    what the author actually wrote deliberately — verify against the existing equivalence test
    (`reference_reconstructor.references_are_equivalent`).
- **Acceptance:**
  - A reference needing only a page-range fix shows tracked change only on the page range.
  - A URL-only fix shows tracked change only at the URL.
  - Unchanged references (author's formatting consistent) are never touched at all.
- **Tests:** golden-string fixtures of minimally-changed entries; XML assertions on del/ins span counts.

### JB-12 — Introduction Level-2 subheading guidance (LLM guideline only)

- **Priority:** P3 · **Source:** Joey: *"If your introduction is long and requires subheadings,
  you should use Level 2 headings for those specific subsections."*
- **Fix (per team decision): LLM guideline only** — add to the editorial-review guidelines
  (`app/domain/apa7_guidelines.py`, fetched into the prompt by `ai/prompt_builder.py`) plus the
  surgical-edit prompt guidance if appropriate. **No deterministic check.** Note existing related
  constraints: MET900/DIS900 warn rules for extra subheadings in Method/Discussion
  (`jutlp_validator.py:196-228`), STY002 warns on Heading-3 usage, and pseudo-H2 detection
  (`document_analysis_services._is_pseudo_heading2:263-289`) stays as-is.
- **Acceptance:** guidelines text present in the editorial-review prompt (dev-trace LLM snapshot);
  no new validator rule emitted.
- **Tests:** prompt-content assertion (guidelines file included and rendered).

---

## Dependencies & ordering

```
JB-01 (critical fix) ─┐
JB-02 (no placeholders) ├─ land first on joeys-revisions  (each independently tested)
JB-03 (acronym flag) ─┘
        │
        ▼
JB-04/05/06/07 (P1, independent of each other)
        │
        ▼
JB-08/09/10 (P2, independent; JB-10 informs JB-11)
        │
        ▼
JB-11 (sits ON TOP of JB-10's learned constraints) ─── JB-12 (any time)
```

## Verification strategy (whole backlog)

1. Full pytest suite (`.venv` Windows: `.\.venv\Scripts\Activate.ps1; .venv\python -m pytest`).
2. Re-run the dev-trace harness on the same ASCILITE 2026 concise paper as a starting point  for the run
  
   and diff events:
   - `llm_editorial_review` stage OK with notes applied;
   - `acronyms` stage skipped (flag off);
   - no placeholder author text in any LLM prompt/snapshot;
   - `short_paragraphs` edits ≤ baseline minus RQ flags (11 → 9 in this corpus);
   - `refs_format` produces no corrputed reference (Cheng & Tsai assertion);
   - header XML contains only the PAGE paragraph.
3. Word COM gate must stay OK and not break (`word_gate` event) after every landed ticket.
4. Test with other manuscripts if necessary.
