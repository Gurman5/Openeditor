# Joey's Revisions — Root-Cause Analysis

**Inputs used:** `Joeys changelog.md` (My notes from meeting) + `Gaplog.docx` + `dev-trace` run report at
`C:\Users\daria\Downloads\trace_cli\trace_report.html` (run of 2026-10-20 against the
ASCILITE 2026 concise paper, output `reviewed_ASCILITE2026_ConcisePaper_Echo360_SingleClassroom CR.docx`).
**Branch context:** analysis was performed on `dev-pipeline-trace`

---

## 1. Trace run summary

- Total run: **1.7 min**, finished OK, OOXML check OK, Word COM gate OK (3.08 s after final).
- **82 events (1 error)**: 33 pipeline stages, 27 LLM calls, 13 CrossRef/DOI API calls, 5 snapshots, 1 comment-dedup, 1 OOXML check, 1 word gate.
- Stage durations: `deterministic_analysis` 30.48 s (validator ∥ reference checker, parallel), `tracked_changes` (Sam's pass) 43.64 s, `llm_editorial_review` 9.05 s — **errored** (see §2).
- Snapped progression: `after_normalise` (826 KB) → `after_assembly` (827 KB) → `after_tracked_changes` (831 KB) → `after_reference_cluster` (832 KB) → `final` (833 KB).
- Comment dedup: 16 comments in, 16 out, 0 dropped.

Stage inventory with edit counts (from the report):

| Stage | Function | Dur | Edits |
|---|---|---:|---:|
| refs_format | `reference_format_corrections.apply_reference_format_corrections` | 30 ms | **9** |
| acronyms | `acronym_corrections.apply_acronym_corrections` | 57 ms | **6** |
| spell_check | `spell_checker.apply_spell_corrections` | 7.50 s | 1 |
| coherence | `sentence_coherence_corrections` (1 LLM call, 4 flags) | 2.05 s | 2 |
| refs_indent | `reference_indent_corrections` | 30 ms | 16 |
| run_fonts | `run_font_corrections` | 42 ms | 18 |
| short_paragraphs | `short_paragraph_comments` | 32 ms | **11** |
| table_keep_together | | 34 ms | 2 |
| table_sections | | 28 ms | 1 |
| everything else | headings, spelling_au, number_words, abbreviations, decimals, grammar, captions_apa7, table_n, table_page_breaks, appendix, blinded_citations, refs_order | ≤60 ms | 0 |

---

## 2. Critical bug: AI editorial review silently discarded

Trace evidence: stage `llm_editorial_review` → **`AttributeError: 'EditorialReviewResult' object has no attribute 'get'`** despite the LLM call itself returning OK (10 notes, 8,706 tokens, including 21 structural verdicts — SEC004/005/007, MET001–005, DIS001–003, FP002–FP008, FP010, APA002/009/010/012 all "confirm").

Root cause: `app/pipelines/feedback_gen_pipeline.py:820`

```python
st.meta(notes=len((llm_result or {}).get("notes") or []))
```

`run_editorial_review()` returns the **dataclass** `EditorialReviewResult`
(`app/domain/editorial_feedback.py:23-28`: `notes / structural_validations / model_used / token_usage / error`).
Because the `.get()` call sits inside the `try` opened at `:813`, the exception is caught at `:821-824`
which **nulls out the successful result** and records `"Editorial review (AI)"` in `stage_errors` with
severity **"critical"** (`_record_stage_error`, `:776-778`; `"critical"` only at `:822` and `:848`).

Impact: the entire AI editorial-review slot is empty in the delivered document for every
run until this is fixed. Downstream consumers are already object-safe
(`output_generation.py:1188-1233` via `_extract_field`; `main.py:406-434` via `getattr`) —
**only pipeline:820** treats the result as a dict.

---

## 3. Root-cause map: Joey's issues → code

### 3.1 "First Authorʳ" placeholder authors leak (Frontend/Manuscript: affiliation + author-name function)

The trace's second editorial-review LLM prompt shows the author block as
*"First Authorʳ, Second Authorʳ, and Third Authorˢ"* and ignores the real author 
"Michael Cowling and Joshua Newn" that appears in the manuscript.

Mechanism (all in `app/services/output_generation_samfix.py`):

- `DEFAULT_AUTHORS_LINE = "First Author^a, Second Author^a, and Third Author^b"` — line **375**;
  `DEFAULT_AUTHOR_AFFILIATIONS` — line **376**.
- `authorFormatCheck()` **1635-1759**: when `authors_present` is False it builds an
  `insert_default_authors` plan (1646-1671) — reusing markers from existing affiliations via
  `_default_authors_line_for_markers()` (**1552-1557**) → `SUPERSCRIPT_CHAR_MAP`, where
  `"r": "ʳ"` at line **2020** is how the gyri-style glyph appears when extraction regexes
  (`_extract_affiliation_markers_from_text`, 1560-1574) mistake an author-note marker for an
  affiliation marker.
- Applied by `_apply_author_plan` at **6785-6842**: deletes a blank paragraph and inserts the
  placeholder line via `_make_plain_styled_paragraph` (**6165-6172**) — **not wrapped in `<w:ins>`**, i.e. an
  untracked, silent insertion — alongside "Replace these placeholder author names…" comments.
- Default affiliations are also inserted from `abstractFormatCheck` when `affiliations_found` is
  false (**2656-2689, 2817-2836**; applied 6990-6997; suppressed only for de-identified docs).
- Second leak: the output filename is built from the (possibly placeholder) authors line at
  **9931-9941** (`build_output_filename_from_author_line(author_plan.get("corrected_authors_line", ""))`),
  so a placeholder can leak into `FirstAuthor_JUTLP_...docx`.
- No name-replacement pass exists (real names are never overwritten by design) — the leak is
  purely the placeholder **insertion** path plus what it feeds into later prompts/filename.

Joey's requirement: this function/feature must not be active; manually placed author name and
affiliation (Michael Cowling and Joshua Newn / RMIT University) must be kept as-is.

### 3.2 Acronym feature active

Stage `acronyms` at `app/pipelines/feedback_gen_pipeline.py:977-991` calls
`apply_acronym_corrections(...)` (`app/services/acronym_corrections.py:1014-1124`), which produced
**6 tracked edits** in this run (body-zone `<w:del>ACRO</w:del><w:ins>full term (ACRO)</w:ins>` plus a
consolidated comment). **There is no env flag to disable it** — only try/except wiring. The store
(`app/services/acronym_store.py`, seeded from `app/data/acronyms.json`) and settings routes
(`app/main.py:624, 635, 644-678, 684-713`; `ACRONYM_DB_PATH`, `ACRONYM_ADMIN_PASSWORD`) are
separate from the pass and can stay intact behind a flag.

### 3.3 Header content preserved instead of blanked

`_apply_apa_body_geometry()` (samfix **7866-7939**) forces 1-inch margins with a tracked
`sectPrChange` and installs the PAGE number field (`_make_page_number_header`, **7829-7863**;
header refs ensured by `_ensure_header_reference`, 7806-7826). The existing header's **own content
is preserved** — the PAGE paragraph is only appended if absent. `_apply_apa_title_page_headers`
(**8531-8542**) strips header *picture* paragraphs only. So any pre-existing running head/logo text
survives, which is what Joey saw. (There is also a dead first-page banner machinery,
**4983-5346**, never called anywhere — candidate for clean-up while here.)

### 3.4 Short-paragraph flags fired on research questions (Joey's "author query 10")

Evidence: the coherence-pass paragraph dump labels RQ1/RQ2 as items **[5] and [6]**
(`trace_report.html` lines 2484-2485); the short-paragraph pass applied **11 edits**, and the
author-query renumbering (`_renumber_final_author_queries`) then baked them into the final
numbered query list. Sam's body-edit LLM pass even invoked the copy-editor LLM **once per RQ
paragraph** (`llm_calls/06`, `07`) and proposed harmful "edits" on the surrounding prose.

Root cause: `app/services/short_paragraph_comments.py` (stage at pipeline **1221-1230**) has
**no exemption clause** — any body-zone paragraph with <3 sentences is flagged
("PARA_SHORT: This paragraph has N sentence(s). Please expand it to at least three
sentences where appropriate.", file lines 71-235, checkpoint at ~142). Sam's overlapping pass
`_collect_paragraph_development_issues` (samfix **3989-4078**, `_BODY_PARA_MIN_WORDS=35` /
`_BODY_PARA_MIN_SENTENCES=3` at 3932-3934) also lacks an RQ/hypothesis exemption.

Joey's requirement: the deterministic layer should skip single-sentence paragraphs that are
research questions or hypotheses — so queries on RQ1/RQ2 should never have been raised.

### 3.5 Abstract not understood

Validator evidence: FP004 *Abstract heading not found*, FP006 *Keywords heading not found*,
FP007/FP008 *Abstract body not found / length cannot be checked* — all from
`apa7_validator.py:171-208` → `document_analysis_services.front_page_summary()` /
`extract_abstract()`, which require a **literal, exact-match `"Abstract"` paragraph**
(`front_page_summary()` line **334**; `find_first_paragraph` at `:392-393`). Variants
("ABSTRACT", "Abstract:", merged headings) all miss. Detection is comment-only (FP rules are not
in `SAM_FIXED_RULE_IDS`, `domain/reporting_ownership.py:30-34`), but the failure robs the
document of a clear "the abstract and/or abstract heading is missing" comment and instead
cascades into 3–4 separate fails that read as noise (including an editorial-note duplicate
— the LLM also flagged the missing abstract at medium severity).

### 3.6 Missing Results/Discussion/Method — already comment-only (wording only)

SEC rules emit from `CANONICAL_STRUCTURE["main_sections"]` (`domain/canonical_jultp_template.py:72-81`;
validator `apa7_validator.py:67-94`, house-policy wording at `:177-190`) and are verdict **"comment"**
per `reporting_ownership.py:52-58` ("no Sam pass restructures the body"). Heading-alias renaming
exists (`heading_corrections.py:166-238`, tracked del/ins "Findings"→"Results") but no service
**inserts** a missing Results/Discussion/Method heading. Joey's requirement ("output is inserting a
comment to the author encouraging them — you don't need to add headings for them") is therefore
**already the behavior**; the remaining work is aligning the comment wording to his phrasing.

### 3.7 References mangled — the highest-consequence deterministic pass

Joey's example: `...Australasian Journal of Educational Technology, 28(4), 599–618. https://doi.org/10.14742/ajet.830`
came back as `...28(4).https://doi.org/10.14742/ajet.830`.

Chain of events (all confirmed in trace + code):

1. Verification is fine — `crossref-cn GET https://doi.org/10.14742/ajet.830 status=200` (1.67 s).
2. `_verify_with_doi()` (`reference_checker.py:735-814`) fetches CrossRef's
   *content-negotiation* APA string (`_get_apa_via_content_negotiation()`, **647-706**,
   `Accept: text/x-bibliography; style=apa`) and, whenever the entry differs from that string at
   rough-similarity ≥ 0.70 even after URL removal, attaches `reconstructed` (the full CrossRef
   text) + `format_issues=["apa7-correction"]` (**799-804**).
3. `reference_format_corrections.apply_reference_format_corrections()` (pipeline `refs_format`,
   **1151-1163**, before DOI injection) applies it as a **whole-entry re-paste**:
   `_apply_del_ins()` (**168-263**) deletes *all* original runs (hyperlinks and author formatting
   included) into one `w:delText`, then inserts the entire reconstructed string as one `w:ins` run.
   Because CrossRef's plain-text bibliography has lost formatting and sometimes metadata:
   - **page ranges vanish** (CrossRef's `text/x-bibliography` output for this entry lacked
     599–618);
   - **italics are lost** — this answers Joey's question "are the italics on the journal and the
     volume number?": in correct APA 7 yes (journal name + volume italic); CrossRef plain text
     carries no italics, so the re-paste silently de-italicises every rewritten entry;
   - the plain `w:ins` run is **rstripped at line 227** (`new_text[:new_text.find(url)].rstrip()`)
     before the URL goes into its own `w:hyperlink → w:ins` run (**240-259**) with **no leading
     space** → the exact `28(4).https://doi.org/...` artifact. Contrast: pipeline's own
     `_inject_crossref_doi_links` *does* prepend a space (pipeline **355-476**, prepend at 457).
   - DOI casing drifts (Joey saw `l` vs `S` in `10.1016/s0010-0277(02)00017-3`).
4. The dev note "the tool isn't including track changes to also change the DOI url" fits: the
   URL insertion *is* tracked (`w:ins` with its own id), but because the whole entry is one
   del/ins blob, the author-visible diff for a URL-only fix looks like "deleted my reference,
   re-pasted a different one" rather than a surgical correction.

### 3.8 Table indenting

Body first-line indent (0.5in / 720 twips) is applied by Sam's pass:
`_collect_body_formatting_issues()` (**4082-4117**) iterates `doc.paragraphs[body_start:body_end]`
— python-docx excludes table-cell paragraphs from `doc.paragraphs`, so *cell* content is
nominally out of scope, but **table headings/subheadings and captions live in normal paragraphs
around the table** and are styled `Normal`, so they receive `firstLine=720` via
`_apply_tracked_body_paragraph_format()` (**7942-7975**, `w:firstLine` set at 7963-7971). Joey saw a
table heading + table subheading indented. A full audit of every indent-writing pass
(`reference_indent_corrections.py`, `references_block_corrections.py:46`, `abstract_keywords_formatting.py:225-286`)
against table content — including XML-domain iteration that *would* see cell paragraphs — is
required; uniform line spacing must be retained.

### 3.9 Figure APA-7 block — not checked at all

`caption_apa7_check.py` (stage `captions_apa7`, pipeline **1040-1049**; edits_count=0 despite a
Table 1 caption present) only splits single-paragraph captions into label/title/Note
(`_needs_apa7_split()`, **97-115**). There is **no check anywhere** that a figure has a bold
"Figure N" + italic title above it, or that the figure is referenced in text *before* it appears
("as discussed in Figure 1" / "see Figure 1") — greps for callout patterns return nothing.

---

## 4. Evidence excerpts worth keeping

- **Author queries list shape** (coherence pass input, `[1]`–`[22]`): RQ1 = `[5]`, RQ2 = `[6]`;
  the final numbered queries after `_renumber_final_author_queries` carry these flags — the
  direct source of Joey's "author query 10 shouldn't happen" complaint in longer docs.
- **Second editorial prompt** (`llm_calls/25_call_llm_request.json`): author block reads
  "First Authorʳ, Second Authorʳ, and Third Authorˢ" — reproduction of the placeholder leak.
- **LLM body-edit hallucination on intro paragraph** (`llm_calls/05` response):
  proposed `"a question" → "questions"` and a repetition-removal the source didn't have — the
  surgical-edit prompt already forbids this class of edit, but it slipped through validation.
  Worth a guard note during P1 work (with the new exemption in place, these paragraphs are
  skipped outright).
- **Bad body_edit_suggestions responses** (`06`/`07`): LLM asked to "correct" RQ1/RQ2 —
  reinforces JB-05's scope: RQ paragraphs must be excluded from every per-paragraph pass,
  not just the short-paragraph comment.

---

## 5. What does NOT need changing (verified)

- Missing-section handling: comment-only already; no heading insertion exists.
- FP002/FP003 validator rules are comment-only (`document_analysis_services.py:327-336`,
  anchors `output_generation.py:1130-1138`) — style-based detection, no auto-rewrite.
- De-identification never overwrites real names (three-signal detection, `samfix:2601-2642`;
  suppression only).
- `_inject_crossref_doi_links` and `_hyperlink_plain_urls_in_refs` are the *correct* patterns
  for URL-space handling — the fix in §3.7 should mirror them.
- Deterministic timeout behaviour, OOXML check, word gate, temp-file lifecycle: all OK in this run.

## 6. Known gaps noted in passing (not Joey's scope, logged for the team)

- `EditorialReviewResult` bug also proves stage-error severities are under-tested — only two
  `"critical"` sites exist; the guard should be asserted in tests (backlog JB-01).
- Dead first-page-banner machinery (samfix 4983-5346) — candidates for removal in a hygiene pass.
- Output-filename derivation can leak placeholder text (fixed with JB-02 but see also
  `output_filename.py` tests).
