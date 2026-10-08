# Graph Report - Openeditor  (2026-10-08)

## Corpus Check
- 166 files · ~213,344 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 4, .css 2, .example 1)

## Summary
- 2920 nodes · 6985 edges · 125 communities (110 shown, 15 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 169 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `01fd20b6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- output_generation_samfix.py
- apply_acronym_corrections
- jutlp_validator.py
- document_zones.py
- lxml
- _apply_body_and_reference_style_fixes
- sentence_coherence_corrections.py
- load_paragraphs
- main.py
- document_analysis_services.py
- normalise_docx
- test_abbreviation_corrections.py
- reference_reconstructor.py
- feedback_gen_pipeline.py
- run_font_corrections.py
- test_front_page_style_fixes.py
- test_heading_corrections.py
- get_comment_anchor_texts
- apply_caption_apa7_comments
- rules
- _Element
- test_access_validation.py
- openeditor.js
- build_edited_document
- test_spell_checker.py
- blinded_citation_comments.py
- generate_keywords
- _make_comment_element
- keywordsFound
- Frontend-Backend API Contract
- spell_checker.py
- test_decimal_corrections.py
- appendix_removal.py
- script.js
- acronym_store.py
- test_narrative_citation_corrections.py
- build_prompts
- apply_number_word_corrections
- _find_target_para_index
- _validate_edit
- reference_checker.py
- test_table_keep_together.py
- TRACK K — Evaluation Corpus + Conformance Harness · DEV TASK BACKLOG
- table_page_breaks.py
- jutlp_articles.py
- body_llm_edits.py
- _remove_tracked_property_change
- document_styling_fixes.py
- test_copyeditor_comment_regressions.py
- _to_title_case_title
- extract_references
- cli_copybot.py
- apply_table_n_notation_comments
- TestFiveFailuresFiveComments
- _llm_edits_for_paragraph
- test_upload_guardrails.py
- apply_short_paragraph_comments
- reference_order_comments.py
- test_acronym_api.py
- grammar_corrections.py
- run_editorial_review
- test_abstract_length_rule.py
- _normalise_heading_text
- reference_type_checker.py
- abstractFound
- output_filename.py
- _propagate_repeated_edits
- test_reference_checker.py
- test_document_zones.py
- now_sydney_iso
- _read_doc_root
- test_output_generation.py
- check_references
- _iter_paren_citations
- apply_table_section_boundary_comments
- _apply_tracked_style_change
- apply_reference_indent_corrections
- _make_textbox_wrap_around_text
- _normalise_surname
- _read_comments_root
- test_body_llm_edits.py
- output_generation.py
- prompt_builder.py
- test_suspicious_ref_comments.py
- canonical_jultp_template.py
- test_body_font_enforcement.py
- _extract_ref_author_part
- TestPresentUnstyledDiscussionNoStub
- _is_appendix_heading
- check_method_subsections
- _ref_surname_keys
- test_reference_justification.py
- inspect_abstract.py
- _apply_intro_page_break
- TestValidDoc
- _update_progress
- Path
- graphify.js
- _apply_mutations
- number_word_corrections.py
- setup.sh
- opencode.json
- app/__init__.py
- copybot
- titleFound
- docx
- _apply_author_plan
- _insert_front_page_text_box_from_template
- DEV TASK BACKLOG — TRACK C (APA‑7 deterministic/output layer)
- _accepted_paragraph_text
- _make_comment_element
- pathlib
- vercel.json
- read_docx
- deployment.md
- test_discussion_required_section_passes_when_unstyled
- Track C — Deterministic / Output
- _front_page_paragraphs_for_deid
- Curated Refernce point (1).md
- test_abstract_stops_at_introduction_heading
- test_normal_styled_abstract_is_measured
- test_parse_docx_finds_sections_by_heading_2

## God Nodes (most connected - your core abstractions)
1. `load_paragraphs()` - 91 edges
2. `build_edited_document()` - 59 edges
3. `validate()` - 55 edges
4. `generate_commented_docx()` - 44 edges
5. `apply_acronym_corrections()` - 41 edges
6. `doc_analysis_pipeline()` - 41 edges
7. `ParagraphRecord` - 39 edges
8. `documentBodyFormatCheck()` - 36 edges
9. `_apply_author_plan()` - 29 edges
10. `documentBodyFound()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `C‑Validator` --references--> `validate()`  [INFERRED]
  docs/apa7-backlog-C.md → app/services/jutlp_validator.py
- `C‑Plumbing` --references--> `results()`  [INFERRED]
  docs/apa7-backlog-C.md → app/main.py
- `C‑Tests + base template` --references--> `extract_template_styles()`  [INFERRED]
  docs/apa7-backlog-C.md → app/services/document_styling_fixes.py
- `4. PARALLELISATION INSIDE C (3–4 people) + HOT FILES` --references--> `build_edited_document()`  [INFERRED]
  docs/apa7-backlog-C.md → app/services/output_generation_samfix.py
- `0.1 LLM call sites (verified via grep — no site missed)` --references--> `_llm_edits_for_paragraph()`  [INFERRED]
  docs/apa7-backlog-D.md → app/services/body_llm_edits.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Canonical API Screen Flow** — app_templates_writer_four_stage_manuscript_workflow, docs_api_contract_processing_state_machine, docs_api_contract_results_status_mapping, docs_api_contract_idempotent_download [EXTRACTED 1.00]
- **Deterministic Validation Stack** — jutlp_validator_checklist_deterministic_jutlp_validation, jutlp_validator_checklist_paragraph_row_model, jutlp_validator_checklist_required_section_checks, jutlp_validator_checklist_front_page_checks, jutlp_validator_checklist_rule_report_format [EXTRACTED 1.00]
- **Manuscript Review Pipeline** — readme_open_editor_bot, readme_jutlp_manuscript_review, readme_openai_editorial_review, readme_flask_document_processing_pipeline [EXTRACTED 1.00]

## Communities (125 total, 15 thin omitted)

### Community 0 - "output_generation_samfix.py"
Cohesion: 0.04
Nodes (96): _append_author_query_runs(), _author_affiliation_marker_count(), _author_naming_pattern_valid(), _author_query_parts(), authorFormatCheck(), _authors_with_multiple_affiliation_markers(), _body_alignment_ok(), _body_font_ok() (+88 more)

### Community 1 - "apply_acronym_corrections"
Cohesion: 0.07
Nodes (38): apply_acronym_corrections(), Run the full acronym pass against ``input_path``, writing to ``output_path``.…, _build_zoned_docx(), An introduction in the abstract does NOT satisfy the body's first-use rule., Truly unknown acronyms in the abstract (no allow-list, no inline def anywhere)…, Conversely, text inside ``<w:del>`` represents tracked deletions — content the…, Block-listed tokens (USA, OK, NASA, iOS, …) never produce issues even when bare…, If the editor adds a well-known org (e.g. NASA) to the allow-list, the block-… (+30 more)

### Community 2 - "jutlp_validator.py"
Cohesion: 0.10
Nodes (43): build_report(), check_abstract_single_paragraph(), check_block_quote_style(), check_body_paragraph_styles(), check_conclusion_length(), check_figure_table_structure(), check_forbidden_styles(), check_front_page() (+35 more)

### Community 3 - "document_zones.py"
Cohesion: 0.08
Nodes (44): Deterministic abbreviation / journal-style fixes emitted as tracked changes.…, _patch_content_types(), _patch_rels(), _needs_apa7_split(), Flag figure/table captions that aren't split into APA 7 paragraphs. APA 7…, Return True when the paragraph holds a full single-paragraph figure/table…, get_style_name(), initial_zone() (+36 more)

### Community 4 - "lxml"
Cohesion: 0.06
Nodes (60): apply_citation_formatting_corrections(), _apply_corrections_to_para(), _Element, Insert missing space after p. / pp. in in-text page references. APA style…, Add a space after p./pp. before page numbers as tracked changes. Returns…, _apply_corrections_to_para(), apply_et_al_corrections(), _corrected_bracket() (+52 more)

### Community 5 - "_apply_body_and_reference_style_fixes"
Cohesion: 0.15
Nodes (11): _apply_body_and_reference_style_fixes(), Apply tracked style changes for body and reference paragraphs: - Required body…, test_body_style_fix_changes_bold_body_subheading_to_heading2(), test_body_style_fix_changes_long_quote_to_quote_style(), test_body_style_fix_changes_required_body_styles(), test_body_style_fix_does_not_change_bold_sentence_to_heading2(), test_body_style_fix_does_not_quote_style_mixed_paragraph(), test_body_style_fix_does_not_split_prose_like_figure_reference_before_image() (+3 more)

### Community 6 - "sentence_coherence_corrections.py"
Cohesion: 0.09
Nodes (43): _anchor_flag(), apply_sentence_coherence_corrections(), _build_user_prompt(), get_sentence_coherence_flags(), _is_usable_reason(), _iter_text_runs(), _Element, Sentence-coherence LLM pass — flag sentences that fail to parse. Joey's… (+35 more)

### Community 7 - "load_paragraphs"
Cohesion: 0.08
Nodes (48): detect_heading_level_1(), extract_main_sections(), extract_subsections(), load_paragraphs(), Scan a .docx file and return its Heading 1 section text and positions., _add_inserted_paragraph(), _add_paragraph_with_deletion(), _add_paragraph_with_textbox() (+40 more)

### Community 8 - "main.py"
Cohesion: 0.05
Nodes (56): _acronym_admin_active(), _acronym_admin_authed(), acronyms_admin_login(), acronyms_admin_logout(), acronyms_admin_page(), add_acronym_api(), analyse_cli(), _body_edit_items() (+48 more)

### Community 9 - "document_analysis_services.py"
Cohesion: 0.12
Nodes (36): ParagraphRecord, _extract_front_page_content(), Extract front page content using style-based matching first, then positional…, count_styles(), estimate_line_count(), extract_abstract(), extract_heading_level_1_sections(), extract_keywords() (+28 more)

### Community 10 - "normalise_docx"
Cohesion: 0.06
Nodes (61): _accept_tracked_changes(), _ancestor_paragraph_index(), _delete_guidance_paragraphs(), _is_paragraph_blank(), NormalisationReport, normalise_docx(), _Element, Path (+53 more)

### Community 11 - "test_abbreviation_corrections.py"
Cohesion: 0.08
Nodes (49): apply_abbreviation_corrections(), _find_first_match(), _iter_text_runs(), _overlaps_quote(), _process_paragraph(), _Element, Return the earliest rule-match in ``text`` as ``(start, end, replacement,…, Apply every matching rule in ``para_el``, returning updated ``next_change_id``.… (+41 more)

### Community 12 - "reference_reconstructor.py"
Cohesion: 0.08
Nodes (48): build_apa7_from_crossref(), _build_book(), _build_book_chapter(), _build_dataset(), _build_dissertation(), _build_edited_book(), _build_journal_article(), _build_preprint() (+40 more)

### Community 13 - "feedback_gen_pipeline.py"
Cohesion: 0.12
Nodes (18): doc_analysis_pipeline(), _hyperlink_plain_urls_in_refs(), _inject_crossref_doi_links(), _max_revision_id(), _normalise(), _patch_settings_show_markup(), Path, Remove Sam's comments (id > our_max_id) that duplicate our validator output.… (+10 more)

### Community 14 - "run_font_corrections.py"
Cohesion: 0.13
Nodes (24): apply_run_font_corrections(), _apply_tracked_run_font(), _current_font(), _current_sz(), _direct_text_runs(), _is_inside_insertion(), _para_style_val(), _Element (+16 more)

### Community 15 - "test_front_page_style_fixes.py"
Cohesion: 0.05
Nodes (79): abstractFormatCheck(), _append_body_comment(), _apply_document_body_plan(), _apply_normal_style_fix(), authorFound(), build_author_check_plan(), _build_missing_abstract_components_message(), _check_abstract_components_with_llm() (+71 more)

### Community 16 - "test_heading_corrections.py"
Cohesion: 0.08
Nodes (41): apply_heading_corrections(), _apply_tracked_edit(), _build_style_level_map(), _corrected_heading(), _direct_text_runs(), _heading_level(), _level_from_name(), _norm() (+33 more)

### Community 17 - "get_comment_anchor_texts"
Cohesion: 0.08
Nodes (33): _format_author_query_text(), generate_commented_docx(), Generate a reviewed `.docx` with inline comments and a validation summary page., Return the canonical section a fail-rule belongs to, or None. SEC001-008 map…, True if a Heading-1 paragraph is the section itself (exact / 'name:' prefix),…, _section_for_rule(), _section_heading_present(), count_comments_in_docx() (+25 more)

### Community 18 - "apply_caption_apa7_comments"
Cohesion: 0.20
Nodes (20): apply_caption_apa7_comments(), _iter_text_runs(), _Element, Emit one APA 7 caption-split comment per offending paragraph. Returns…, Yield (run_el, text) for runs we may safely anchor a comment on., _build_docx(), Path, Tests for the APA 7 caption-split recommendation pass. A figure or table… (+12 more)

### Community 19 - "rules"
Cohesion: 0.08
Nodes (7): fixture, rules(), TestFrontPageIssues, TestMissingMethodSubsection, TestStructureAndEndmatterIssues, TestValidDeidentified, TestValidIdentified

### Community 20 - "_Element"
Cohesion: 0.12
Nodes (30): _append_author_query_runs(), _author_query_parts(), _bracketed_spans(), _build_zone_map(), _collect_inline_definitions(), _find_run_at_offset(), _find_title_paragraph_indices(), _format_author_query_text() (+22 more)

### Community 21 - "test_access_validation.py"
Cohesion: 0.13
Nodes (26): _require_access(), AccessResult, AccessStatus, check_access(), check_local_bypass(), Access validation service — G-07. Defines the authentication contract for…, Single entry point the Flask gate calls. Tries, in order: 1. Local SKIP_AUTH…, SKIP_AUTH must be explicitly 'true' (case-insensitive) — any other value,… (+18 more)

### Community 22 - "openeditor.js"
Cohesion: 0.09
Nodes (26): cancelJob(), CAROUSEL_ENABLED, downloadUrl(), fetchCarouselArticles(), _mapUploadErrorCode(), pollResults(), pollUntilDone(), STAGE_TO_STEP (+18 more)

### Community 23 - "build_edited_document"
Cohesion: 0.06
Nodes (63): _append_plain_text_run(), _style_fix_pass(), _apply_citation_plan(), _apply_editorial_review_comment_plan(), _apply_heading_1_text_normalization(), _apply_heading_2_title_case(), _apply_heading_keep_next(), _apply_inline_keywords_split() (+55 more)

### Community 24 - "test_spell_checker.py"
Cohesion: 0.06
Nodes (45): find_quote_spans(), is_in_quote(), Return True when the half-open range ``[start, end)`` overlaps any quotation…, Return a list of ``(start, end)`` half-open intervals locating every paired-…, _build_word_counts(), _classify_word(), _freq_ratio(), get_spell_corrections() (+37 more)

### Community 25 - "blinded_citation_comments.py"
Cohesion: 0.17
Nodes (21): _anchor_paragraph_comment(), apply_blinded_citation_comments(), _build_comment(), _classify(), _distinct(), _own_text_runs(), _Element, Flag blinded / placeholder citations and self-references. For peer review… (+13 more)

### Community 26 - "generate_keywords"
Cohesion: 0.14
Nodes (24): _build_user_prompt(), _clean_one(), _dedupe_case_insensitive(), generate_keywords(), _is_acceptable(), LLM-driven keyword generation for manuscripts missing a Keywords section.…, Strip surrounding whitespace and quotes; collapse internal whitespace., Return up to ``_MAX_KEYWORDS`` keyword candidates for the manuscript. Best-… (+16 more)

### Community 27 - "_make_comment_element"
Cohesion: 0.16
Nodes (17): _build_comment_ref_run(), _find_span(), _inject_comment_markers(), _inject_comment_markers_for_phrase(), _make_inserted_heading_paragraph(), _Element, Fallback comment anchor: wrap the whole paragraph. We only use this when…, Build `<w:r><w:commentReference .../></w:r>` for the inline comment mark. (+9 more)

### Community 28 - "keywordsFound"
Cohesion: 0.06
Nodes (36): _apply_missing_keywords_stub(), citationFound(), _extract_keywords_list(), _find_abstract_heading_in_front(), _find_blank_line_after_index(), _find_citation_heading_in_front(), _find_introduction_heading_in_front(), _find_keywords_heading_in_front() (+28 more)

### Community 29 - "Frontend-Backend API Contract"
Cohesion: 0.07
Nodes (32): Graphify Knowledge Graph, OAPA Brand Mark, Acronym Management UI, Editor Admin Authentication, Persistent Acronym Storage, Editorial Access Gate, Shared Password Authentication, Client-Side Manuscript Validation (+24 more)

### Community 30 - "spell_checker.py"
Cohesion: 0.11
Nodes (25): _make_comment_element(), Replace the run with (before | comment-anchored content | after). When…, _split_run_for_action(), _find_next_action(), _get_style_name(), _has_corrected_form_in_tracked_ins(), _iter_text_runs(), _process_paragraph() (+17 more)

### Community 31 - "test_decimal_corrections.py"
Cohesion: 0.11
Nodes (28): apply_decimal_corrections(), Run both decimal checks over ``input_path`` and write to ``output_path``.…, _build_docx(), _Element, Path, Tests for the decimal-precision and comma-as-decimal checks., The classic example: thousand separators and comma-decimals together., The example from the client's brief, end-to-end. (+20 more)

### Community 32 - "appendix_removal.py"
Cohesion: 0.06
Nodes (64): _anchor_comment_on_paragraph(), apply_appendix_removal(), _find_appendix_start(), _is_appendix_heading(), _is_heading_paragraph(), _paragraph_has_image(), _passthrough(), _Element (+56 more)

### Community 33 - "script.js"
Cohesion: 0.10
Nodes (28): _activateStep(), _clearPollDelay(), clearUploadError(), displayFile(), fetchJutlpArticles(), finishStepAnimation(), groupItems(), JUTLP_FALLBACK_ARTICLE (+20 more)

### Community 34 - "acronym_store.py"
Cohesion: 0.10
Nodes (31): list_acronyms_api(), add_acronym(), _ensure_file_exists(), load_acronyms(), _load_seed(), Path, Persistent store for the editor-managed acronym allow-list. The list lives as a…, Restore the on-disk store to the bundled seed. Used by tests. (+23 more)

### Community 35 - "test_narrative_citation_corrections.py"
Cohesion: 0.19
Nodes (22): _apply_corrections_to_para(), apply_narrative_citation_corrections(), _bracket_spans(), _in_any_span(), _plain_text(), _Element, Replace narrative-citation ampersands in one paragraph., Apply tracked "&" -> "and" fixes for APA narrative citations. (+14 more)

### Community 36 - "build_prompts"
Cohesion: 0.17
Nodes (11): build_prompts(), Build (system_prompt, user_prompt) from parsed document data., _make_paragraphs(), _make_parsed_structure(), Build a minimal set of ParagraphRecord objects for testing., The prompt instructs the LLM to use specific severity labels. Originally…, Regression: sections headed by an ALIAS ("Methodology", "Findings", "Literature…, A titled heading ("Introduction: Background") maps to its canonical section so… (+3 more)

### Community 37 - "apply_number_word_corrections"
Cohesion: 0.16
Nodes (30): apply_number_word_corrections(), Scan body paragraphs and emit tracked-change replacements for digits 0-9.…, _build_docx_with_paragraph(), _count_changes(), Path, Tests for digit-to-word tracked-change corrections. These tests build minimal…, A digit INSIDE quoted text retains the source's form., Unquoted digit in a paragraph that also has a quoted digit must still be… (+22 more)

### Community 38 - "_find_target_para_index"
Cohesion: 0.11
Nodes (31): _find_after(), _find_first_heading(), _find_first_non_empty_para(), _find_front_matter_anchor(), _find_front_matter_rule_anchor(), _find_front_style(), _find_front_text(), _find_heading() (+23 more)

### Community 39 - "_validate_edit"
Cohesion: 0.08
Nodes (25): Return the symmetric token difference between ``find`` and ``replace``. Tokens…, Normalise curly quotes/apostrophes to ASCII for comparison only., _strip_quotes(), _token_diff(), _validate_edit(), Regression: `Evidences-Based → evidencesbased` slipped past a case-sensitive…, An edit that keeps the hyphen and fixes a real typo must still pass., JUTLP policy: text inside `"..."` retains the source's spelling. (+17 more)

### Community 40 - "reference_checker.py"
Cohesion: 0.09
Nodes (35): Remove a leading heading number from ``text`` (e.g. "2. Literature" ->…, strip_leading_section_number(), build_reference_report(), _cache_get(), _cache_set(), check_and_report(), check_duplicate_references(), check_orphan_citations() (+27 more)

### Community 41 - "test_table_keep_together.py"
Cohesion: 0.14
Nodes (26): _apply_caption_keep_next(), apply_table_keep_together(), _ensure_keep_next(), _ensure_trpr(), _ensure_trpr_child(), _para_style(), _para_text(), _Element (+18 more)

### Community 42 - "TRACK K — Evaluation Corpus + Conformance Harness · DEV TASK BACKLOG"
Cohesion: 0.09
Nodes (22): 0. STAGE 0 — SEED SET + MINIMAL HARNESS + BASELINE (do this first), 1. TICKETS BY GROUP, 2. STAGE GATES & DEMO ARTEFACTS, 3. DEPENDENCY GRAPH & CRITICAL PATH, 4. PARALLELISATION INSIDE K (2 people), 5. CROSS-TRACK REQUESTS, 6. RISKS, OPEN DECISIONS, OUT-OF-SCOPE, END — Required outputs (+14 more)

### Community 43 - "table_page_breaks.py"
Cohesion: 0.20
Nodes (26): apply_table_page_breaks(), _cell_text(), _make_page_break_paragraph(), _page_break_anchor(), _para_has_page_break(), _para_style(), _para_text(), _preceded_by_page_break() (+18 more)

### Community 44 - "jutlp_articles.py"
Cohesion: 0.17
Nodes (26): _abstract_candidates(), _article_details_url(), _clean_abstract_candidate(), _clean_text(), _extract_abstract(), _extract_article_urls(), _extract_author(), _extract_title() (+18 more)

### Community 45 - "body_llm_edits.py"
Cohesion: 0.12
Nodes (23): call_llm(), call_llm_json(), get_client(), LLMError, Exception, Raised when the LLM call fails after retries., Create an OpenAI client., Send a structured-output request to the OpenAI Chat Completions API. Returns… (+15 more)

### Community 46 - "_remove_tracked_property_change"
Cohesion: 0.21
Nodes (16): _apply_body_run_format(), _apply_tracked_body_format_fixes(), _apply_tracked_body_paragraph_format(), _apply_tracked_body_run_format(), _apply_tracked_table_cell_borders(), _apply_tracked_table_properties(), _apply_tracked_table_run_format(), _copy_properties_without_change() (+8 more)

### Community 47 - "document_styling_fixes.py"
Cohesion: 0.31
Nodes (12): get_section_bounds(), _canonical_index(), _collect_until(), compare_document_styles(), compare_template_and_document(), extract_headings(), extract_template_styles(), _find_first_text() (+4 more)

### Community 48 - "test_copyeditor_comment_regressions.py"
Cohesion: 0.09
Nodes (41): Renumber visible Author Query labels after every comment pass has run., _renumber_final_author_queries(), apply_au_spelling_corrections(), Scan every eligible paragraph and apply AU spelling tracked changes. Returns…, Return one summary entry per repeated spelling correction. The tracked-change…, summarize_spelling_correction_repeats(), _comment_ids_in_document_order(), _inject_comment_markers() (+33 more)

### Community 49 - "_to_title_case_title"
Cohesion: 0.10
Nodes (21): Return ``text`` rewritten in academic title case. Rules applied (APA 7 /…, _to_title_case_title(), A. APA 7 rule matrix (from apastyle.apa.org primary sources), APA 7 Rework Plan — OpenEditor (planning-only audit), C. Architecture recommendation, D. Prioritised work breakdown — stages, not weeks, E. Evaluation plan, F. Risks & open questions (+13 more)

### Community 50 - "extract_references"
Cohesion: 0.16
Nodes (12): extract_references(), Return ``(start_index, end_index)`` bounding the References section. ``start``…, Two-tier reference selection used by BOTH extraction and comment anchoring so…, _references_window(), _select_reference_entries(), _build_docx_with_sections(), A paper with reference-styled paragraphs but NO References heading still has…, Build a docx from a list of (kind, text) blocks. kind: "h1" → Heading 1, "ref"… (+4 more)

### Community 51 - "cli_copybot.py"
Cohesion: 0.23
Nodes (17): _heading_level_1_sections(), _is_generic_copyedit_output(), main(), _print_heading_normalization_summary(), Path, _rename_generic_copyedit_output(), _show_heading_level_1_sections(), _status() (+9 more)

### Community 52 - "apply_table_n_notation_comments"
Cohesion: 0.23
Nodes (15): apply_table_n_notation_comments(), Emit one comment per table column header that is a bare capital "N". Returns…, _comment_texts(), Tests for the capital-N table-header notation comment., Comment-only pass must return the change id it was given., Build a docx with one table whose first row holds ``headers``., A data cell holding a number, and a header that merely contains N as part of a…, A lone "N" outside any table must not be flagged. (+7 more)

### Community 53 - "TestFiveFailuresFiveComments"
Cohesion: 0.10
Nodes (8): has_comments_content_type(), has_comments_relationship(), Return ordered list of (text, has_ins, [commentRangeStart ids]) for every…, The combined 'Results and Discussion' fixture has no standalone Discussion…, SEC005 + DIS001-003 comments anchor inside the inserted Discussion stub, NOT on…, The inserted Discussion stub sits after Results and before References in…, TestFiveFailuresFiveComments, TestOneFailureOneComment

### Community 54 - "_llm_edits_for_paragraph"
Cohesion: 0.19
Nodes (11): build_body_edit_plan(), _fix_au_spellings(), _llm_edits_for_paragraph(), Replace any US spellings in text with AU equivalents., Return True when the LLM reason is specific enough for display., _reason_identifies_change(), patch, test_body_edit_plan_propagates_accepted_exact_repeat() (+3 more)

### Community 55 - "test_upload_guardrails.py"
Cohesion: 0.15
Nodes (16): _document_word_count(), Total word count across every paragraph (whole-document count)., io, pytest, _client(), _poll_until_final(), Tests for the upload guardrails added to app.main: 1. Whole-document word-count…, A pipeline that stalls without ever calling progress still flips the session to… (+8 more)

### Community 56 - "apply_short_paragraph_comments"
Cohesion: 0.19
Nodes (18): apply_short_paragraph_comments(), _first_token_span(), _iter_text_runs(), _paragraph_text(), _Element, Flag short prose paragraphs (<3 sentences) with Word comments. This pass emits…, Yield editable visible text runs from ``para_el``. Runs inside tracked-change…, Count sentence-like spans in ``text``. A sentence is any non-empty chunk after… (+10 more)

### Community 57 - "reference_order_comments.py"
Cohesion: 0.15
Nodes (23): _anchor_comment_on_paragraph(), apply_reference_order_comments(), _build_comment(), _find_references_heading(), _first_inversion(), _passthrough(), _Element, Flag a reference list that is not in alphabetical order. APA 7 (which JUTLP… (+15 more)

### Community 58 - "test_acronym_api.py"
Cohesion: 0.10
Nodes (8): client(), gated_client(), fixture, Smoke tests for the acronym admin HTTP endpoints. Skipped when Flask isn't…, Read-only access stays open so the pipeline can still load the list., Boot the Flask app with auth disabled and the store pointed at tmp., Boot the app with the editor-password gate enabled., test_gated_get_still_open_when_not_authed()

### Community 59 - "grammar_corrections.py"
Cohesion: 0.07
Nodes (49): app_services, _anchor_visible_span(), apply_contingent_grammar_comments(), apply_grammar_corrections(), _apply_phrase_correction(), _build_user_prompt(), _contingent_sva_comment(), _find_phrase_in_runs() (+41 more)

### Community 60 - "run_editorial_review"
Cohesion: 0.06
Nodes (50): EditorialNote, EditorialReviewResult, LLM verdict on a single deterministic structural check result., StructuralValidation, Run LLM-based editorial review on a JUTLP manuscript. Pipeline: 1. Parse DOCX…, run_editorial_review(), _strip_internal_markers(), build_editorial_review_comment_plan() (+42 more)

### Community 61 - "test_abstract_length_rule.py"
Cohesion: 0.29
Nodes (13): check_abstract(), _fp008(), _long_abstract_doc(), _parsed(), Tests for the JUTLP abstract length rule: the abstract must fit lines 7–23 of…, The length flag must be its OWN comment (not folded into the merge/style…, test_abstract_at_the_limit_passes(), test_abstract_length_comment_is_a_standalone_comment() (+5 more)

### Community 62 - "_normalise_heading_text"
Cohesion: 0.10
Nodes (26): _ack_contains(), _all_alias_norms(), _apply_heading_center_alignment(), _collect_acknowledgements_issues(), _collect_discussion_subheading_issues(), _collect_method_subheading_issues(), _collect_results_reference_issues(), _find_heading1_index() (+18 more)

### Community 63 - "reference_type_checker.py"
Cohesion: 0.19
Nodes (18): _check_book(), _check_book_chapter(), _check_conference(), _check_dataset(), _check_journal(), _check_podcast(), check_reference_type_style(), _check_report() (+10 more)

### Community 64 - "abstractFound"
Cohesion: 0.12
Nodes (16): abstractFound(), _apply_abstract_plan(), _apply_missing_practitioner_stub(), _count_abstract_lines(), _count_title_lines(), _ensure_template_styles_available(), _is_abstract_body_end_marker(), _load_template_style_names() (+8 more)

### Community 65 - "output_filename.py"
Cohesion: 0.27
Nodes (15): build_output_filename(), build_output_filename_from_author_line(), _first_author_last_name(), _get_author_line_and_markers(), _get_document_year(), _remove_superscript_runs_from_author_line(), _unique_output_filename(), test_corrected_author_line_uses_doc_affiliation_markers() (+7 more)

### Community 66 - "_propagate_repeated_edits"
Cohesion: 0.50
Nodes (4): _propagate_repeated_edits(), Apply accepted exact edits to repeated matching body text. The LLM reviews each…, test_propagate_repeated_edits_adds_matching_body_paragraph(), test_propagate_repeated_edits_skips_quote_only_body_paragraph()

### Community 67 - "test_reference_checker.py"
Cohesion: 0.16
Nodes (11): check_entry_author(), check_text_dois(), DOIT: Validate every DOI-shaped substring found in the plain text of each…, _cr_item(), Return a fake ``_lookup_doi`` that resolves DOIs from a dict. ``None`` value…, A reference that quotes the same DOI twice (bare + URL form) should only hit…, _stub_lookup(), TestCheckTextDOIs (+3 more)

### Community 68 - "test_document_zones.py"
Cohesion: 0.54
Nodes (7): _make_doc(), test_body_sentence_mentioning_references_is_not_boundary(), test_decimal_checks_skip_unstyled_acknowledgements_and_refs(), test_number_words_skip_unstyled_references_section(), test_unstyled_intro_and_reference_aliases_set_zones(), test_unstyled_references_without_intro_starts_as_body_then_exits(), _zones()

### Community 69 - "now_sydney_iso"
Cohesion: 0.18
Nodes (14): now_sydney_iso(), Shared timestamp helper for Word comments and tracked changes. Word stores the…, Return the current time as an ISO-8601 string with the Sydney offset. Example:…, _sydney_tz(), datetime, Tests for the shared Sydney-time stamp helper. Word comments and tracked…, Sydney is UTC+10 (standard) or UTC+11 (daylight saving). If the tz database is…, Second precision only — keeps the stamp tidy and matches the previous format's… (+6 more)

### Community 70 - "_read_doc_root"
Cohesion: 0.13
Nodes (22): _matches_definition(), Attempt to align ``letters`` against the leading section of ``words``. Walks…, If `words` contain a valid full form for `acro`, return the phrase. Walks the…, _try_match_definition(), Tests for acronym detection + consolidated comment + tracked-change rewrites., Five problematic acronyms still produce exactly one Word comment., Allow-listed acronyms still need a first-use introduction in the body. A…, First body use is rewritten as 'full term (ACRO)', not just 'full term'. (+14 more)

### Community 71 - "test_output_generation.py"
Cohesion: 0.17
Nodes (14): _canonical_insert_index(), _next_h1_after(), _heading_para_index(), _para_style_val(), _para_text(), Return the pStyle val used by existing Heading-1 paragraphs. Documents vary:…, Index within ``all_paras`` of the Heading-1 paragraph that IS ``section``…, Return the index within ``all_paras`` to insert the stub for ``section``. Place… (+6 more)

### Community 73 - "_iter_paren_citations"
Cohesion: 0.20
Nodes (7): _iter_paren_citations(), Yield ``(surname, year)`` tuples for every parenthetical citation. Handles…, Coverage for the multi-citation parenthesis parser., The reported bug: a four-citation paren block produced ZERO matches because the…, APA disambiguators like ``2020a`` must survive., A `(see ...)` aside without a Surname,Year pair must yield nothing — even…, TestParenCitationIterator

### Community 74 - "apply_table_section_boundary_comments"
Cohesion: 0.39
Nodes (14): apply_table_section_boundary_comments(), Comment on sections that open and/or close directly with a table. Returns…, _add_table(), _comment_texts(), _new_doc(), Tests for the table section-boundary (open/close with a table) check., test_no_tables_is_noop(), test_opening_and_closing_different_tables_both_flagged() (+6 more)

### Community 75 - "_apply_tracked_style_change"
Cohesion: 0.25
Nodes (14): _apply_style_if_needed(), _apply_tracked_style_change(), Remove direct formatting that would override a heading style. A paragraph that…, _strip_conflicting_direct_format_for_heading(), _body_para(), _ppr(), A body paragraph restyled to a heading must shed its body formatting. When the…, Only size/spacing are stripped — bold stays (headings are bold anyway). (+6 more)

### Community 76 - "apply_reference_indent_corrections"
Cohesion: 0.14
Nodes (21): _already_correct(), apply_reference_indent_corrections(), _is_heading(), _resolved_name(), _build_style_hanging_map(), _resolve(), _build_style_name_map(), _Element (+13 more)

### Community 77 - "_make_textbox_wrap_around_text"
Cohesion: 0.29
Nodes (12): _make_textbox_wrap_around_text(), Make a front-page floating textbox use *square* text-wrapping so the…, _anchor_para(), _Element, The front-page editorial textbox must wrap text around it, not overlay it. The…, Schema order: the wrap element must precede docPr in the anchor., test_behinddoc_is_cleared(), test_breathing_margins_added() (+4 more)

### Community 78 - "_normalise_surname"
Cohesion: 0.22
Nodes (7): check_submitted_hyperlinks(), _lookup_doi(), _normalise_surname(), Lowercase, strip accents, punctuation, and possessive 's for fuzzy match.…, Query CrossRef by DOI and return the work item, or None on failure., HREF: Verify that user-submitted hyperlinks point to the cited work. For each…, TestNormaliseSurname

### Community 79 - "_read_comments_root"
Cohesion: 0.22
Nodes (11): _comment_visible_text(), _Element, Concatenate every ``<w:t>`` text under the comments root., When the author DID introduce the acronym in the body, no issue fires., Allow-listed acronyms in the abstract are silent — no flagging., When a track change is proposed, the bullet mentions it so the editor knows…, _read_comments_root(), test_abstract_allow_listed_silent() (+3 more)

### Community 80 - "test_body_llm_edits.py"
Cohesion: 0.15
Nodes (18): _dedupe_edits(), _apply_body_edit_plan(), _apply_intra_paragraph_tracked_replace(), docx_oxml, _paragraph_with_runs(), test_body_edit_plan_applies_all_repeated_occurrences_in_paragraph(), test_body_edit_plan_skips_repeated_occurrence_inside_direct_quote(), test_dedupe_edits_drops_duplicates() (+10 more)

### Community 81 - "output_generation.py"
Cohesion: 0.11
Nodes (23): _append_author_query_runs(), _append_validation_summary(), _author_query_parts(), _comment_group_key(), _dedupe_pending_comments(), _extract_field(), _format_summary_line(), _group_pending_comments() (+15 more)

### Community 82 - "prompt_builder.py"
Cohesion: 0.18
Nodes (14): Few-shot editorial examples extracted from real JUTLP editor decisions. These…, JUTLP editorial guidelines extracted from 'JUTLP Template 2026.docx'. Last…, _build_system_prompt(), _build_user_prompt(), _canonical_section_for(), _find_sections_by_text(), _format_flagged_results(), _get_section_text_by_bounds() (+6 more)

### Community 83 - "test_suspicious_ref_comments.py"
Cohesion: 0.22
Nodes (15): _has_reference_issue_summary_comment(), _insert_suspicious_ref_comments(), Add Word comments for reference issues: - CONS001/CONS002 citation-consistency…, _build_docx(), _comment_anchor_texts(), _comment_texts(), Path, Regression test for the suspicious-reference comment pass. This pass… (+7 more)

### Community 84 - "canonical_jultp_template.py"
Cohesion: 0.14
Nodes (15): _build_section_rename_map(), _merges_two_sections(), _normalise_subsection(), Lower-case, collapse whitespace, strip a leading heading number and any…, Return the canonical main section a heading fragment names, or None. Matches…, True when ``alias`` merges two *distinct* canonical sections (e.g. "Results and…, ``normalised alias -> canonical label`` for safe heading renames. Built from…, Return True when ``canonical_label`` is satisfied by ``found_subs``.… (+7 more)

### Community 85 - "test_body_font_enforcement.py"
Cohesion: 0.31
Nodes (9): _ensure_normal_style_body_rpr(), _passthrough_copy(), Pin the body font + size on the Normal style's run properties. The template's…, _doc_with_normal(), _normal_rpr(), Tests for body-font enforcement: the Normal style must carry Arial 11pt so…, A docx whose Normal style is a non-template font/size., test_already_correct_normal_style_no_change() (+1 more)

### Community 86 - "_extract_ref_author_part"
Cohesion: 0.17
Nodes (6): _extract_ref_author_part(), _normalise_text(), Return the author/group-author portion of a reference entry. Slices everything…, Replace curly quotes with their straight ASCII equivalents., TestCitationRegexes, TestExtractRefAuthorPart

### Community 87 - "TestPresentUnstyledDiscussionNoStub"
Cohesion: 0.31
Nodes (4): A Discussion section that is present but not yet Heading-1 styled (the author…, No tracked-inserted 'Discussion' heading paragraph should exist., The Discussion-subsection comment must anchor on the original (non-inserted)…, TestPresentUnstyledDiscussionNoStub

### Community 88 - "_is_appendix_heading"
Cohesion: 0.38
Nodes (5): _extract_ref_hyperlinks(), _is_appendix_heading(), Return (entry_num, ref_text, url) for reference entries that already have a…, parametrize, TestIsAppendixHeading

### Community 89 - "check_method_subsections"
Cohesion: 0.15
Nodes (10): check_discussion_subsections(), check_method_subsections(), _extra_subheadings(), _looks_like_subheading(), True if ``text`` is plausibly a subheading, not a mis-styled body line. Mirrors…, Return heading-like found subheadings that match no required subsection (or…, Method/Discussion subheadings that aren't in the template's expected set are…, TestDiscussionSubsectionsWithAliases (+2 more)

### Community 90 - "_ref_surname_keys"
Cohesion: 0.36
Nodes (4): Return every normalised surname-key a reference can plausibly match. For person…, _ref_surname_keys(), Person refs (with a comma) must NOT have an acronym alias generated — otherwise…, TestRefSurnameKeys

### Community 91 - "test_reference_justification.py"
Cohesion: 0.32
Nodes (7): docx_enum_style, docx_enum_text, Reference entries must be justified (w:jc=both), not left-aligned. Two layers…, Return the w:jc value of the APA 7 reference style, or None., _ref_style_jc(), test_left_aligned_author_reference_style_is_replaced_with_justified(), test_template_reference_style_is_justified()

### Community 92 - "inspect_abstract.py"
Cohesion: 0.29
Nodes (5): get_comment_anchors(), get_ref_entries(), Inspect the processed output vs the original to find comment placement issues., Map comment id -> paragraph text snippet where the anchor sits., Return numbered reference entries from the document.

### Community 93 - "_apply_intro_page_break"
Cohesion: 0.48
Nodes (6): _doc(), _intro_has_page_break(), Tests for the front-page / body page break before the Introduction., Regression: a numbered "1. Introduction" heading must still get the front-…, test_page_break_inserted_before_numbered_introduction(), test_page_break_inserted_before_plain_introduction()

### Community 94 - "TestValidDoc"
Cohesion: 0.31
Nodes (3): fixture, rules(), TestValidDoc

### Community 95 - "_update_progress"
Cohesion: 0.47
Nodes (6): ProcessingCancelled, ProcessingTimeout, Exception, _run(), _pipeline(), _update_progress()

### Community 96 - "Path"
Cohesion: 0.29
Nodes (7): _build_docx(), _build_docx_with_inserted_run(), Path, The scanner must read text inside ``<w:ins>`` runs — that's what upstream…, Build a minimal docx with one paragraph per supplied text., Build a docx where each entry is ``(style, text, inside_ins)``. When…, test_acronyms_inside_inserted_runs_are_detected()

### Community 97 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 98 - "_apply_mutations"
Cohesion: 0.22
Nodes (8): _apply_mutations(), _build_bullet(), _build_replacement(), Replace `run_el` with (before | <w:del> | <w:ins> | after). Like…, Return the introduction text ``full term (ACRO)`` for a track change., Render one issue as a single bullet line for the consolidated comment. Title…, Apply tracked-change rewrites and the comment-range anchor. Mutations are…, _split_run_for_track_change_only()

### Community 99 - "number_word_corrections.py"
Cohesion: 0.17
Nodes (14): _apply_corrections_to_para(), _bracket_spans(), _in_any_span(), _is_sentence_start(), _para_plain_text(), _Element, Spell out whole numbers 0-9 in running prose as tracked changes. Most academic…, Return character spans (start, end) covered by paren/bracket/brace pairs.… (+6 more)

### Community 107 - "titleFound"
Cohesion: 0.16
Nodes (15): _collect_quote_formatting_issues(), _count_title_words(), _extract_quoted_segments(), _find_anchor_above(), _find_content_authors(), _fix_au_spellings_in_text(), _has_known_title(), _has_long_quote() (+7 more)

### Community 108 - "docx"
Cohesion: 0.17
Nodes (11): check_combined_results_discussion(), check_dot_points(), Flag bullet/numbered list paragraphs — continuous prose is expected in JUTLP., docx, docx_oxml_ns, _make_numbered(), results_by_rule(), test_combined_findings_discussion_reports_long_policy_comment() (+3 more)

### Community 109 - "_apply_author_plan"
Cohesion: 0.19
Nodes (14): _append_affiliation_before_notes(), _append_plain_text_run_with_size(), _append_text_with_line_breaks(), _append_text_with_superscript_markers(), _append_tracked_replace(), _apply_author_plan(), _flush(), _build_authors_tracked_change_comment() (+6 more)

### Community 110 - "_insert_front_page_text_box_from_template"
Cohesion: 0.21
Nodes (14): _apply_front_page_asset_plan(), build_front_page_asset_check_plan(), _collect_relationship_ids(), _element_has_textbox(), _front_page_body_paras(), _insert_front_page_text_box_from_template(), _paragraph_visible_text(), _strip_paragraph_to_textbox() (+6 more)

### Community 111 - "DEV TASK BACKLOG — TRACK C (APA‑7 deterministic/output layer)"
Cohesion: 0.15
Nodes (12): 0. STAGE 0 — SAFETY NET, 2. STAGE 3 — PLUMBING, TESTS, SHIP, 2. STAGE GATES (runnable), 3. DEPENDENCY GRAPH + CRITICAL PATH, 4. PARALLELISATION INSIDE C (3–4 people) + HOT FILES, 5. CROSS-TRACK REQUESTS, 6. RISKS / OPEN DECISIONS / OUT OF SCOPE, C‑Plumbing (+4 more)

### Community 112 - "_accepted_paragraph_text"
Cohesion: 0.50
Nodes (4): _accepted_paragraph_text(), True if ``run_el`` should NOT contribute to ``para_p``'s text. Walks up to the…, Return a paragraph's *own* text as if all tracked changes were accepted.…, _run_skipped()

### Community 113 - "_make_comment_element"
Cohesion: 0.20
Nodes (12): add_document_summary_comment(), add_paragraph_comment(), _make_comment_element(), _patch_content_types(), _patch_rels(), Ensure `document.xml.rels` contains the comments relationship., Ensure `[Content_Types].xml` declares `word/comments.xml`., Attach a single document-level Word comment to the first body paragraph. Used… (+4 more)

### Community 114 - "pathlib"
Cohesion: 0.32
Nodes (5): Document, Path, read_docx(), hashlib, pathlib

### Community 115 - "vercel.json"
Cohesion: 0.50
Nodes (3): builds, routes, version

### Community 116 - "read_docx"
Cohesion: 0.67
Nodes (3): Document, Path, read_docx()

### Community 119 - "Track C — Deterministic / Output"
Cohesion: 0.29
Nodes (6): Create, Delete, Track C — Deterministic / Output, Track C & Track D — Comprehensive Checklists, Track D — LLM Layer, Verification gates between tracks

## Knowledge Gaps
- **73 isolated node(s):** `Curated Refernce point`, `Locked client decisions (this revision)`, `2. STAGE GATES (runnable)`, `3. DEPENDENCY GRAPH + CRITICAL PATH`, `5. CROSS-TRACK REQUESTS` (+68 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 890 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_paragraphs()` connect `load_paragraphs` to `output_generation_samfix.py`, `jutlp_validator.py`, `sentence_coherence_corrections.py`, `main.py`, `document_analysis_services.py`, `test_front_page_style_fixes.py`, `test_heading_corrections.py`, `get_comment_anchor_texts`, `test_spell_checker.py`, `keywordsFound`, `spell_checker.py`, `build_prompts`, `reference_checker.py`, `body_llm_edits.py`, `document_styling_fixes.py`, `extract_references`, `_llm_edits_for_paragraph`, `test_upload_guardrails.py`, `grammar_corrections.py`, `run_editorial_review`, `test_abstract_length_rule.py`, `abstractFound`, `output_filename.py`, `test_reference_checker.py`, `output_generation.py`, `titleFound`, `_accepted_paragraph_text`, `_front_page_paragraphs_for_deid`, `test_abstract_stops_at_introduction_heading`, `test_normal_styled_abstract_is_measured`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `generate_keywords()` connect `generate_keywords` to `output_generation_samfix.py`, `keywordsFound`, `body_llm_edits.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `generate_commented_docx()` connect `get_comment_anchor_texts` to `_find_target_para_index`, `test_output_generation.py`, `load_paragraphs`, `normalise_docx`, `feedback_gen_pipeline.py`, `output_generation.py`, `_make_comment_element`, `cli_copybot.py`, `TestFiveFailuresFiveComments`, `build_edited_document`, `_make_comment_element`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `build_edited_document()` (e.g. with `4. PARALLELISATION INSIDE C (3–4 people) + HOT FILES` and `Key verifications / plan-vs-code contradictions`) actually correct?**
  _`build_edited_document()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `validate()` (e.g. with `C‑Validator` and `Key verifications / plan-vs-code contradictions`) actually correct?**
  _`validate()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Curated Refernce point`, `Locked client decisions (this revision)`, `2. STAGE GATES (runnable)` to the rest of the system?**
  _73 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `output_generation_samfix.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0384391380314502 - nodes in this community are weakly interconnected._