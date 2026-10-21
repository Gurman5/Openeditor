# Joey's Revisions — Full Code Mapping (12 pipeline areas)

Primary source: deep code-walk report produced during the root-cause investigation
(companion: `research/joeys-revisions-analysis.md` for the trace evidence and symptom→issue map;
`docs/joeys-revisions-backlog.md` / `docs/joeys-revisions-execution-plan.md` for the work items).
Reproduced here in full, verbatim, as the durable code reference.

---

## 1. Acronym feature

**Pipeline call:** `feedback_gen_pipeline.py:977-991` — stage `"acronyms"`,
`apply_acronym_corrections(resolved_output_path, resolved_output_path, next_lang_id)` at **line 985**.

Behavior: `app/services/acronym_corrections.py`
- `apply_acronym_corrections()` at **lines 1014-1124**. Builds one consolidated Word comment (intro
  string `_CONSOLIDATED_INTRO`, lines 75-81) listing every acronym whose first use in its zone
  (abstract vs body are independent — lines 3-36) isn't introduced as `full term (ACRO)`.
- Detection: `_ACRONYM_PATTERN` (line 92), hard block-list `_ACRONYM_BLOCKLIST` lines 111-139
  (USA, PhD, iOS, …), CC-licence paragraph skip (lines 142-148). Allow-list comes from
  `acronym_store.load_acronyms()` (line 1027-1031 override param `accepted_acronyms`).
- Body-zone known expansions also produce a tracked change
  `<w:del>ACRO</w:del><w:ins>full term (ACRO)</w:ins>` (docstring lines 27-31, mutations at
  `_apply_mutations`/`_split_run_for_action`).
- Title zone deliberately skipped (line 10-12); acknowledgements/references "outside" silent
  (line 20). Skipped styles via `_SKIP_STYLES` (line 63) and zones via `document_zones.py`.

**Env flag: none.** No env var or constant disables the pass; only the pipeline try/except
(line 984-991) records failure in `stage_errors`. Related env vars are storage/auth only:
`ACRONYM_DB_PATH` (`acronym_store.py:33-35`) and `ACRONYM_ADMIN_PASSWORD` (`main.py:624`).

**Store/settings route:** `app/services/acronym_store.py` (JSON store, seed at
`app/data/acronyms.json`, atomic writes lines 66-83). Routes in `app/main.py`: page
`/settings/acronyms` (line 644), admin login/logout (660, 678), API `GET/POST /api/acronyms`
(684, 691), `DELETE /api/acronyms/<key>` (713), gated by `_require_acronym_admin()` (635).

## 2. FP002/FP003 + author/affiliation replacement

### Validator rules

- `apa7_validator.py:171-183` `check_front_page()` — FP002 "Authors block found / not found"
  (line 175), FP003 "Affiliations block" (line 176). Fields come from
  `document_analysis_services.front_page_summary()` (`document_analysis_services.py:327-336`):
  `authors_found` = any paragraph with style `"Authors"` (line 332), `affiliations_found` =
  style `"Author Affiliations"` (line 333). Pure style-based detection — fail = comment only.
- `jutlp_validator.py:233-247` (`check_front_page`, lines 238-239) has equivalent messages for
  the legacy validator.

### Yes — there IS non-comment insertion of author/affiliation content, all inside `output_generation_samfix.py`

- Constants: `DEFAULT_AUTHORS_LINE = "First Author^a, Second Author^a, and Third Author^b"`
  (**line 375**), `DEFAULT_AUTHOR_AFFILIATIONS = ("a Affiliation 1; b Affiliation 2",)`
  (**line 376**).
- `authorFormatCheck()` (**1635-1759**): when `authors_present` is False it builds an
  `"insert_default_authors"` plan (1646-1671) — either reusing real markers extracted from the
  existing affiliations (`_find_existing_affiliations_for_missing_authors`, 1577) via
  `_default_authors_line_for_markers()` (**1552-1557**), or the full default line + default
  affiliations; also appends a children's-note "a Affiliation 2" if only one marker exists
  (1658-1659).
- Application: `_apply_author_plan` handles `action == "insert_default_authors"` at
  **lines 6785-6842** — it deletes a blank paragraph and inserts the placeholder authors line via
  `_make_plain_styled_paragraph` (**6165-6172**), which is **NOT wrapped in `<w:ins>`**
  (silent/untracked insertion) but is followed by comment "Replace these placeholder author names
  with the correct author list." (6822-6827) and "Replace these placeholder affiliations…"
  (6828-6841). Insertion of default affiliations at line 6814-6819.
- Separately, abstractFormatCheck inserts default affiliations when `.affiliations_found` false
  (**2656-2689, 2817-2836**, applied at **6990-6997**) — but suppressed when the doc is
  de-identified.
- Tracked variant for a *malformed but present* authors line: `replace_in_place` plan →
  `_apply_tracked_replace` (6844-6890). (This correction path is legitimate and stays — see backlog JB-02.)
- The **"First Authorʳ" superscript glyph**: `SUPERSCRIPT_CHAR_MAP` (**1993-2029**, includes
  `"r": "ʳ"` at line **2020**) converts `^r`/caret markers to unicode superscripts via
  `_caret_markers_to_superscript_text` (**2033-2055**), used in
  `_append_text_with_superscript_markers` (2059-2060) and `_make_inserted_styled_paragraph`
  (**6198**). So a placeholder line built with marker `r` (or an author-note marker mistakenly
  accepted by the extraction regexes `_extract_affiliation_markers_from_text`, 1560-1574)
  renders/writes as `First Authorʳ`. The LLM-visible prompt side is `AUTHOR_NAMING_PATTERN`
  (**lines 68-107**), which is fed the current authors line and returns `corrected_authors_line`
  (call at 1738-1748) — a placeholder/labeled line can flow in and out of that LLM cycle.

### Anonymisation / de-identification pass (`output_generation_samfix.py`)

- `_is_deidentified_manuscript()` (**2601-2642**) — three signals: filename regex
  `_DEIDENTIFIED_FILENAME_RE` (**2553-2560**), placeholder regex `_DEIDENTIFIED_PLACEHOLDER_RE`
  (**2566-2569**, `[Authors removed for review]` etc.) and `_DEIDENTIFIED_NUMBERED_AUTHOR_RE`
  (**2575-2578**, `[Author 1]`).
- Used in `abstractFormatCheck` (**2661, 2680-2687**) to suppress the "Author affiliations section
  was not found" query and the default-affiliation insertion on blinded submissions. No name
  *replacement* pass exists — real names are never overwritten, only suppressed/commented.
- Companion comment pass: `blinded_citation_comments.py` (pipeline stage `blinded_citations`,
  pipeline lines 1125-1138) flags `[University]`/`[Affiliation]`/self-references, comment-only.

## 3. Document header handling

All in `output_generation_samfix.py` (Sam's pass), called from `build_edited_document` line **9795**:

- `_apply_apa_body_geometry()` (**7866-7939**): forces 1in margins with tracked `sectPrChange`
  (`_apply_apa_section_margins`, 7770-7796) and installs a **right-aligned PAGE field** in the
  running header (`_make_page_number_header`, **7829-7863**), ensuring both `default` and `first`
  header refs exist (`_ensure_header_reference`, 7806-7826). Existing header content preserved;
  PAGE paragraph only appended if absent.
- `_apply_apa_title_page_headers()` (**8531-8542**, called 8633 from `_apply_apa_title_page`,
  8545): strips header picture paragraphs (`_strip_header_picture_paragraphs`) and ensures a
  running head for professional mode — this is the header *normalisation* in place.
- First-page banner machinery (currently **dead code**): `_find_header_picture_part`
  (**4983-5001**), `_doc_has_first_page_header_picture` (**5003-5022**), `_ensure_first_header`
  (**5043-5072**), `_patch_header_content_type` (**5075**+),
  `_insert_front_page_banner_from_template` (**5209-5346**) — copies a logo picture from a template
  zip into the *first-page* header; `_insert_front_page_banner_from_template` is never called
  anywhere in `app/`.
- `sectionPr` guards: `document_normalisation_services.py` — blank-paragraph detection preserves
  paragraphs carrying `w:sectPr` (`_is_paragraph_blank`, **276-298**) and drops `w:sectPrChange`
  change records (line 129, 152).
- `output_generation.py:1474` touches `body/sectPr` (comment-fragment attachment context).
  `run_font_corrections.py:56-64` sweeps run fonts inside `header*.xml` / `footer*.xml` parts.
- Detection-side only: `apa7_formatting_checks.py:65` reads headers/footers for font checks.

No general "header normalisation" beyond page-number insertion + APA title-page header rewrite exists.

## 4. `short_paragraph_comments.py` (read in full)

File: `app/services/short_paragraph_comments.py` (235 lines). Entry:
`apply_short_paragraph_comments` (**71-235**), pipeline stage `short_paragraphs`
(pipeline **1221-1230**). Comment-only, rule label `PARA_SHORT`.

**Trigger:** paragraph has <3 sentences (`_sentence_count`, 51-61; threshold `count >= 3` skip at
**142**), in `body` zone only (104-110), after skips: `should_skip_prose_paragraph` (111) — which
excludes headings, captions, refs, front-matter, **table cells (`is_in_table`), list items**
(`document_zones.py:307-321`). Additional guards: single-token/short fragments skipped (needs ≥1
space and ≥12 alpha chars, **124-127**); heading-like Normal paragraphs skipped via
terminal-punctuation + length heuristic (<80 chars not ending `.!?`, **136-139**). Message:
"This paragraph has N sentence(s). Please expand it to at least three sentences where
appropriate." (164-167).

**No research-question / hypothesis / single-sentence exemption exists.** There is no
RQ/hypothesis detection anywhere in this file, `document_zones.py`, `samfix`, or
`prompt_builder.py` (only a front-page *label* list mentioning `"research questions"` in samfix
1229, unrelated). Two overlapping short-paragraph passes exist — this one, and Sam's
`_collect_paragraph_development_issues` (`output_generation_samfix.py:3989-4078`, thresholds
`_BODY_PARA_MIN_WORDS=35`, `_BODY_PARA_MIN_SENTENCES=3` at 3932-3934, capped at 5 comments, skips
quote-led/colon lead-ins `_is_skippable_para` 3970-3986, Method/Acks ranges 4001-4027) — neither
exempts rhetorical questions or one-sentence-per-argument paragraphs. Only the LLM *system prompt*
touches it indirectly (prompt-builder pseudo-heading guard, `prompt_builder.py:213-230`).

## 5. Abstract detection (FP004/FP006/FP007/FP008)

### Detection (`document_analysis_services.py`)

- `front_page_summary()` (**327-336**): `abstract_heading_found = any(p.text == "Abstract" for p
  in front)` (**line 334**) — **exact, case-sensitive full-paragraph equality**.
- `extract_abstract()` (**392-427**): `find_first_paragraph(paragraphs, "Abstract")` (**393**,
  exact-match helper at 154-158) then collects body paragraphs until an abstract boundary
  (`_is_abstract_boundary` 380-388: heading styles, "keywords"/"citation" texts, legacy
  "Practitioner Notes"). Word cap FP008 = 250 (`canonical_jultp_template.py:67`).
- `get_front_page()` (**312-323**) bounds the scan to everything before the first Introduction
  match — **if the Introduction heading isn't found, `front` becomes the whole document**
  (line 321-322).

### Why a real abstract can be missed

The heading paragraph text must be exactly `"Abstract"` — "ABSTRACT", "Abstract:", "Introduction
Abstract", a merged heading, or an abstract heading styled/carried inside a text box can all
fail; similarly an unnumbered-but-lowercase "abstract", or an "Abstract" heading that appears
*after* something matched as Introduction. The validator consumes it from `parse_docx_structure`
(`document_analysis_services.py:480-504`, line 494) via `apa7_validator.check_front_page`
(FP004 at **apa7_validator.py:177**) and `check_abstract` (FP007/FP008 at **186-208**:
"Abstract body not found" / length fail). `apa7_formatting_checks.check_abstract_format`
(APA008, **265-303**) explicitly returns `[]` when the heading isn't found ("absence is reported
by FP004", line 273-274).

### Comment (vs auto-fix)

Yes — FP004/FP007/FP008 are **not** in `SAM_FIXED_RULE_IDS`
(`domain/reporting_ownership.py:30-34` — explicitly "FP004/FP007 were removed from the Sam-fixed
set: no Sam pass repairs them"), so `generate_commented_docx` attaches comment-only: the anchor
resolution is `output_generation.py:658-663` (falls back to title/front-page first para) and
family category at 363-366. Additionally Sam's pass emits its own comment-only
"Missing 'Abstract' heading on the front page after author affiliations."
(`output_generation_samfix.py:2659-2677`, action `add_abstract_comment` — no heading insertion).
No tracked-change insertion of a missing Abstract heading exists anywhere.

## 6. Missing sections SEC004/SEC005 + heading_corrections

**SEC rules:** `apa7_validator.py:67-94` `check_required_sections()` (same code in the newer copy
is `jutlp_validator.py:61-93`). Rule IDs are generated from `CANONICAL_STRUCTURE["main_sections"]`
order (`domain/canonical_jultp_template.py:72-81`): SEC001 Introduction, SEC002 Literature,
SEC003 Method, **SEC004 Results**, **SEC005 Discussion**, SEC006 Conclusion, SEC007
Acknowledgements, SEC008 References. Missing → `fail` with `missing_section_queries` house-policy
wording for Literature/Method/Results (**canonical_jultp_template.py:177-190**; the "Results"
house-policy message at 186-189 is what SEC004 fires as). Combined Results+Discussion → SEC fail
("found combined") / SPE001 warn (`jutlp_validator.check_combined_results_discussion`, 307-316).
All **comment-only** — `reporting_ownership.py:52-58` family verdict `"SEC": "comment"` ("no Sam
pass restructures the body"). Anchoring for those comments:
`output_generation.py:_find_missing_section_anchor` (**684-750+**), `_SEC_RULE_TO_SECTION` mapping
at **341-342 / 804-807 / 994-998**.

**`heading_corrections.py` does NOT insert headings.** `apply_heading_corrections()`
(**166-238**) only (a) strips leading section numbers and (b) renames alias H1 headings
("Findings"→"Results") via tracked `w:del`/`w:ins` (`_apply_tracked_edit`, **133-163**), levelling
from `styles.xml` (`_build_style_level_map`, 63-96; only levels 1-2, line 188). Merged headings
deliberately not renamed (docstring 18-20). Called in the pipeline at **911-920** and again inside
Sam's builder at `output_generation_samfix.py:9850`. Related non-inserting restyling:
`_required_body_heading_style` (samfix 8766-8789) restyles unstyled section headings by text match
(silent style edit), `_apply_heading_1_text_normalization` (9913) replaces literal "Introduction"
heading with the paper title. **No service inserts a missing Results/Discussion/Method heading.**

## 7. Reference "format corrections" (item of high concern)

**Reconstruction source:** reference_checker imports ONLY `references_are_equivalent` from
`reference_reconstructor.py` (`app/services/reference_checker.py:19-21`). The APA string used for
correction comes from **CrossRef content negotiation** — `_get_apa_via_content_negotiation()`
(`reference_checker.py:647-706`, `Accept: text/x-bibliography; style=apa`).
`reference_reconstructor.py`'s `build_apa7_from_crossref`/`detect_format_issues` are only
exercised by `tests/smoke_reconstructor.py` (aspirational tier-2 code).

**Decision to rewrite:** `_verify_with_doi()` (**735-814**): entry passes on pure verification but
if the entry differs from the CrossRef APA *without the URL* (`references_are_equivalent` fails)
**and rough similarity ≥0.70**, the result carries `r["reconstructed"]` = the FULL CrossRef APA
string **including DOI URL** and `r["format_issues"] = ["apa7-correction"]` (**799-804**).

**Write:** `reference_format_corrections.py:apply_reference_format_corrections()` (**268-456**;
pipeline stage `refs_format` at **1151-1163**, before DOI injection, per comment block 1140-1149).
**This is a whole-entry re-paste, not surgical replace**: `_apply_del_ins()` (**168-263**) deletes
ALL original runs (including hyperlinks and any author DOI formatting — everything not
`pPr`/bookmark/comment anchors) into one `w:delText`, then inserts the entire reconstructed string
as one `w:ins` run.

- **Page-number loss risk:** the reconstructed text is CrossRef's bibliography output verbatim; if
  CrossRef's metadata lacks/differs page data, the re-paste can drop or alter the author's page
  numbers (whole-content replacement).
- **Space-before-URL removal:** line **227**
  `text_before = new_text[:new_text.find(url)].rstrip()` — the plain `w:ins` run is rstripped,
  then the URL goes into a separate black `w:hyperlink`→`w:ins` run (**240-259**) with **no
  leading space** — producing exactly `28(4).https://doi.org/...` if the reconstruction had
  `…28(4). https://doi.org/…`. Contrast: the pipeline's own `_inject_crossref_doi_links`
  (pipeline **355-476**) *does* prepend a space (`" " + doi_url`, line **457**).
- **DOI-URL-only changes as tracked changes:** yes — even a pure missing/wrongly-typed DOI
  triggers the whole-entry del/ins because similarity ≥0.70 holds; the URL part is its own tracked
  insertion (`w:hyperlink → w:ins` with its own `w:id`, lines 240-259, 3 IDs per entry at
  388-397), so the DOI-only change *is* representable as tracked change — but it is implemented as
  a full-entry rewrite rather than a DOI-only patch. Skip guard for pre-tracked paragraphs at 379.
- Other reference tracked-change stages: `_inject_crossref_doi_links` (1166-1172 wiring, pipeline
  1166-1172) and `_hyperlink_plain_urls_in_refs` (pipeline 479-594, wired 1241-1245); hanging
  indent `reference_indent_corrections.py` (stage pipeline 1182-1189); font sweep
  `run_font_corrections.py`.

## 8. Table-indent exclusion / who applies first-line indents

**Body first-line indent (0.5in = 720 twips):** `output_generation_samfix.py`

- `_body_indent_ok()` (**3883-3898**, helper `_is_zero_indent_length` 3867): APA-04 check.
- Issue collection `_collect_body_formatting_issues()` (**4082-4117**) iterates
  `paragraph_records` indices `body_start_index..body_end_index` and `doc.paragraphs[i]` —
  python-docx `doc.paragraphs` excludes table-cell paragraphs entirely, so table content is
  inherently out of scope of this pass. It also only touches `BODY_REQUIRED_STYLE` ("Normal")
  paragraphs (4093).
- Application of the 0.5in indent: `_apply_tracked_body_paragraph_format()` (**7942-7975**) sets
  `w:firstLine=720` when `fix["indent"]` is true (**7963-7971**), as a tracked `pPrChange`;
  invoked from `_apply_document_body_plan`/`_apply_body_run_format` chain (fix flags built at
  4099-4113; `fix.get("indent")` also applied at **8067**).
- Constants: `APA_FIRST_LINE_INDENT_TWIPS` (`services/config.py:36` = "720"), re-exported in
  samfix 3650.

**Other indent writers:** `reference_indent_corrections.py` — hanging indent 720/−720 on
reference entries (stage pipeline 1182-1189; direct/`firstLine` override removal rules at 117-130);
`references_block_corrections.py` (`_HANGING = "720"`, line 46); `abstract_keywords_formatting.py`
— removes abstract-body indent and sets keywords-line `left=720/firstLine=0` (225-286). None of
these target table cells (they operate on front-matter/reference or reference-window paragraphs
only). The comment-generation skip for table content is `document_zones.is_in_table` (283-292)
used by `should_skip_prose_paragraph` (307-321) — relevant to future indent passes.

## 9. `caption_apa7_check.py` (read in full)

File: `app/services/caption_apa7_check.py` (245 lines), entry `apply_caption_apa7_comments`
(**118-245**), pipeline stage `captions_apa7` (**1040-1049**). Comment-only.

**What it checks:** single-paragraph captions that should be split into APA 7's three paragraphs
(label / italic title / Note). `_needs_apa7_split()` (**97-115**): skip styles already canonical
(`_SKIP_STYLES` 56-65); regex `_SINGLE_PARAGRAPH_CAPTION_RE` (**47-52**, `Figure/Fig./Table N.` +
content); remainder after the label must be ≥ `_MIN_BODY_CHARS = 30` (line 70, 113). One comment
per offending caption, anchored on the "Figure N." label (159-195), template text at 72-79. Zones
via `iter_paragraphs_with_zone` — skips `outside` (153).

**In-text reference check ("see Figure 1" / "as discussed in Figure 1" before the figure):**
**does not exist.** No code in this module (or anywhere in `app/services` — grep for "see
figure"/"discussed in figure"/cross-ref found nothing) verifies that a figure is referenced in
text before/at its position, or that a Figure N has an in-text callout. It purely checks the
caption's own shape.

## 10. Introduction subsections / Level 2 headings

- **No rule or comment about Introduction subheadings exists.** `_extra_subheading_result`
  extras-warn rules are **MET900** (`jutlp_validator.py:196-198`) and **DIS900** (**226-228**) for
  Method/Discussion only; `apa7_validator.py:121-126, 134` has the equivalents without extras.
- Heading-3 usage is discouraged: STY002 warn (`jutlp_validator.py:319-324`).
- "Level 2" appears only as prose in guidelines (`domain/apa7_guidelines.py:56` "Level 2: Flush
  Left, Bold, Title Case" — LLM prompt material) and in samfix's H2 alignment helpers
  (`output_generation_samfix.py:8165, 8212` — per-match jc normalisation; cannot tell L1 from L2
  by text).
- Pseudo-H2 detection (bold short no-punct) exists for validation and LLM prompt:
  `document_analysis_services._is_pseudo_heading2` (**263-289**), `prompt_builder.SUBHEADING_MARKER
  = "[Subheading]"` (**199**) with internal-marker stripping in
  `editorial_review_service._strip_internal_markers` (**17-30**). `jutlp_guidelines.py:62` says
  "Subheadings should be used only when they genuinely improve the structure" — again LLM
  guidance, not a code rule. If a dev item is "flag intro subheadings or create them," it's
  greenfield.

## 11. `EditorialReviewResult` attribute error

`run_editorial_review()` returns a **dataclass** `EditorialReviewResult`
(`domain/editorial_feedback.py:23-28`: `notes`, `structural_validations`, `model_used`,
`token_usage`, `error`) — `app/services/ai/editorial_review_service.py:33-88`.

**The offending line:** `app/pipelines/feedback_gen_pipeline.py:820`

```python
st.meta(notes=len((llm_result or {}).get("notes") or []))
```

`(llm_result or {})` is truthy dataclass → `.get(...)` raises `AttributeError:
'EditorialReviewResult' object has no attribute 'get'`. Because it's inside the `try` opened at
813, the exception is caught at 821-824, which **discards a successful LLM result**
(`llm_result = None`), records `"Editorial review (AI)"` in `stage_errors` with severity
"critical" (marker via `_record_stage_error`, 776-778), and the run proceeds without any editorial
notes — so the downstream `generate_commented_docx(llm_results=llm_result)` (840-846) and
`_llm_notes_to_results` consumers (`output_generation.py:1188-1233`, dict/object-safe via
`_extract_field`; `main.py:406-434`, getattr-based) never see it. All other call sites treat the
result as an object correctly (`output_generation.py:1188-1192`, `main.py:410, 1186`); only
pipeline line 820 does the dict-treatment.

## 12. Pipeline orchestration (`app/pipelines/feedback_gen_pipeline.py`, `doc_analysis_pipeline`, lines 744-1303)

Ordered stages (all wrapped in `dev_trace.stage()` + per-stage try/except `_record_stage_error`
— `_record_stage_error` defined at **776-778**, default severity `"minor"`; only two sites record
`"critical"`: LLM stage at **822** and document generation at **848**):

| # | Stage | Function / detail |
|---|-------|-------------------|
| 1 | normalise | `normalise_docx` on a temp working copy (785-797) |
| 2 | deterministic_analysis | parallel, ThreadPoolExecutor max_workers=2 — `apa7_validator.validate` + `reference_checker.check_and_report` (799-809) |
| 3 | llm_editorial_review | `run_editorial_review(...)` (811-825; contains the item-11 bug) |
| 4 | — | Filter `SAM_FIXED_RULE_IDS` out of validator results (`filtered_report`, 827-833) |
| 5 | assemble_comments | `output_generation.generate_commented_docx` writes the comment-bearing docx (835-849; no-copy raise if fails) |
| 6 | normalise_summary / normalise_sidecar | summary comment + audit sidecar (854-872) |
| 7 | tracked_changes | `output_generation_samfix.build_edited_document` (in-place; see internal order below) + `_remove_duplicate_sam_comments` (879-899; `_max_revision_id` seeding, 904) |
| 8 | headings | `apply_heading_corrections` (911-920) |
| 9 | spelling_au | `apply_au_spelling_corrections` (922-932) |
| 10 | number_words | `apply_number_word_corrections` (934-944) |
| 11 | abbreviations | `apply_abbreviation_corrections` (946-959) |
| 12 | spell_check | `apply_spell_corrections` (961-975) |
| 13 | acronyms | `apply_acronym_corrections` (977-991) — item 1 |
| 14 | decimals | `apply_decimal_corrections` (993-1004) |
| 15 | coherence | `apply_sentence_coherence_corrections` (1006-1019) |
| 16 | grammar | `apply_contingent_grammar_comments` (1021-1034) |
| 17 | captions_apa7 | `apply_caption_apa7_comments` (1036-1049) — item 9 |
| 18 | table_n | `apply_table_n_notation_comments` (1051-1063) |
| 19 | table_sections | `apply_table_section_boundary_comments` (1065-1077) |
| 20 | table_keep_together | `apply_table_keep_together` (1079-1094) |
| 21 | table_page_breaks | `apply_table_page_breaks` (1096-1108) |
| 22 | appendix | `apply_appendix_removal` (1110-1123) |
| 23 | blinded_citations | `apply_blinded_citation_comments` (1125-1138) — item 2 |
| 24 | Reference cluster | ordering rationale comment 1140-1149: `refs_format` — `apply_reference_format_corrections` (1148-1163) item 7 → `refs_doi` — `_inject_crossref_doi_links` (1165-1172) → id re-seed (1177) → `refs_indent` — `apply_reference_indent_corrections` (1179-1189) → `run_fonts` — `apply_run_font_corrections` (1191-1203) → `refs_order` — `apply_reference_order_comments` (1205-1217) |
| 25 | short_paragraphs | `apply_short_paragraph_comments` (1219-1230) — item 4 |
| 26 | suspicious_refs | `_insert_suspicious_ref_comments` (1232-1237) |
| 27 | urls_hyperlink | `_hyperlink_plain_urls_in_refs` (1239-1245) |
| 28 | markup_view | `_patch_settings_show_markup` (1247-1253) |
| 29 | author_queries | `_renumber_final_author_queries` (1255-1263) |
| 30 | close-out | Dev-trace snapshot/word gate (1265-1274), result dict 1276-1303 |

### Inside `build_edited_document` (samfix 9735-9997; `__main__` smoke entry 10000-10013)

title plan → abstract plan (`abstractFormatCheck`, incl. de-id suppression + default
affiliations) → keywords plan (+ missing-keywords stub applied at 9860-9865) → citation plan →
intro page break (9775) → APA heading styles → Normal-style fix → `_apply_apa_body_geometry`
margins + PAGE header (9795, item 3) → body plan (font/spacing/indent via
`_apply_tracked_body_paragraph_format`, item 8) → author plan (`authorFormatCheck`, incl.
`insert_default_authors`, item 2) → body-edit plan → narrative citations → editorial-review
comment plan → body/reference style fixes → Heading-2 title case → `apply_heading_corrections`
(9850) → table formatting (9855) → heading keepNext (9867-9870) → bold/italic strip (9872-9878) →
`apply_references_block_corrections` (9880-9889, order rationale in comment) →
`apply_abstract_keywords_formatting` (9891-9898, runs before the font sweep so its runs get
normalised) → APA title page (`_apply_apa_title_page` + `_apply_apa_title_page_headers`,
9900-9908) → `_apply_heading_1_text_normalization` (9910-9918, runs after title page and heading
corrections) → run fonts (9920-9923) → fallback plain copy if nothing applied (9925-9926) →
author-query renumbering + line-number removal (9928-9929) → **output filename rebuilt from the
authors line at 9931-9941**
(`build_output_filename_from_author_line(author_plan.get("corrected_authors_line", ""))` — a
placeholder "First Author^a…" can leak into the delivered filename) → result dict (9943-9997).

### Where disabling/insertions would go

Each pass is independently wrapped — removing/disabling any item is a matter of
deleting/commenting its `stage(...)` block (e.g. lines 982-991 for acronyms; 1148-1163 + helpers
for risky ref-format re-paste). **There is no env-flag framework for stage gating** (only
`PIPELINE_TRACE`, `WORD_GATE_ENV`, `CROSSREF_CACHE`, `APA7_TITLE_PAGE_MODE`), so a
`DISABLE_*`/`FEATURE_*` env switch would be new plumbing; major content insertions should slot
after stage 12 (normalisation-confirmed working copy, pre tracked-changes pass) or into samfix's
front-page plan chain.

## Verification addendum (final pass — all report claims confirmed against direct reads)

- FP rule definitions pinned exactly: `apa7_validator.py:174-178` (tuple-emitted
  FP001/FP002/FP003/FP004/FP006), FP007/FP008 fails at 193-194, pass/status at 206-207;
  `jutlp_validator.py:237-241` (legacy) + 257-258/275-276; anchors at `output_generation.py:357-367,
  625-673, 1130-1138`.
- `build_edited_document` read to end of file (10013 = `__main__` only); stage list above includes
  the confirmed tail, plus the filename-leak detail (samfix 9931-9941).
- Severity wiring confirmed: `_record_stage_error` at pipeline 776-778; `"critical"` only at 822
  (LLM) and 848 (document generation) — confirming item 11's impact path.
- Two previously "best-explanation" items are now closed: (a) "First Authorʳ" — mechanism is
  `_default_authors_line_for_markers` → `SUPERSCRIPT_CHAR_MAP["r"] = "ʳ"` (samfix:2020), with the
  additional filename-leak path via 9931-9941; (b) reference re-paste — sourced from CrossRef
  content negotiation (not `reference_reconstructor.py`), whole-entry del/ins,
  no-space-before-URL bug at `reference_format_corrections.py:227`.
