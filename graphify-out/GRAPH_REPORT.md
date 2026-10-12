# Graph Report - Openeditor  (2026-10-13)

## Corpus Check
- 184 files · ~218,587 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 3, .css 2, .example 1)

## Summary
- 3431 nodes · 8236 edges · 152 communities (128 shown, 24 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 326 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `944ff633`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- 8. Dead-code reachability after C-24a
- _build_zoned_docx
- jutlp_validator.py
- test_front_page_style_fixes.py
- output_generation.py
- apa7_formatting_checks.py
- test_sentence_coherence_corrections.py
- load_paragraphs
- main.py
- document_analysis_services.py
- test_document_normalisation.py
- test_abbreviation_corrections.py
- reference_reconstructor.py
- apply_caption_apa7_comments
- gen_apa7_base_template.py
- output_generation_samfix.py
- test_heading_corrections.py
- generate_commented_docx
- test_heading_style_apa11.py
- rules
- acronym_corrections.py
- test_access_validation.py
- openeditor.js
- test_intro_page_break.py
- test_spell_checker.py
- lxml
- test_appendix_removal.py
- test_grammar_corrections.py
- keywordsFound
- Frontend-Backend API Contract
- short_paragraph_comments.py
- test_decimal_corrections.py
- reference_format_corrections.py
- script.js
- acronym_store.py
- titleFound
- build_prompts
- apply_number_word_corrections
- test_sam_fixes_validator_rules.py
- cli_copybot.py
- reference_checker.py
- test_table_keep_together.py
- LLMError
- table_page_breaks.py
- jutlp_articles.py
- test_font_sweep.py
- results
- document_styling_fixes.py
- test_copyeditor_comment_regressions.py
- feedback_gen_pipeline.py
- extract_references
- pathlib
- table_n_notation_comments.py
- TestFiveFailuresFiveComments
- build_edited_document
- pytest
- test_references_block_corrections.py
- apply_reference_order_comments
- test_acronym_api.py
- test_reference_indent_corrections.py
- run_editorial_review
- test_abstract_length_rule.py
- _make_textbox_wrap_around_text
- reference_type_checker.py
- test_abstract_keywords_formatting.py
- apa7_validator.py
- patch
- test_reference_checker.py
- abstract_keywords_formatting.py
- abstractFound
- _read_doc_root
- _find_target_para_index
- check_references
- _iter_paren_citations
- _llm_edits_for_paragraph
- _apply_tracked_style_change
- test_reporting_ownership.py
- find_quote_spans
- _normalise_surname
- _read_comments_root
- docx
- fixture
- test_acronym_corrections.py
- count_comments_in_docx
- test_language_corrections.py
- test_body_llm_edits.py
- _extract_ref_author_part
- TestPresentUnstyledDiscussionNoStub
- _is_appendix_heading
- _apply_inline_keywords_split
- _ref_surname_keys
- appendix_removal.py
- inspect_abstract.py
- test_jutlp_validator.py
- TestValidDoc
- Gurman — Sprint 2 Wiring Tasks (Frontend ↔ Backend Reference)
- Path
- graphify.js
- session_manager.py
- timestamps.py
- setup.sh
- permission
- os
- copybot
- _canonical_insert_index
- Gurman — Data / Endpoint Tasks (Source of Truth)
- check_entry_author
- test_reference_justification.py
- test_output_generation.py
- test_block_list_does_not_swallow_real_acronyms
- 2. Amendment spec
- TestNonTemplateSubheadingComment
- vercel.json
- Research — APA 7 Base Template styles inventory
- deployment.md
- body_llm_edits.py
- test_blinded_citation_comments.py
- test_body_font_enforcement.py
- apply_table_section_boundary_comments
- Gurman — Wrong File Type + Cancel + Solo Demo
- zac-ux-tasks.md
- _fake_llm
- api.js
- startProcessing
- _strip_heading_direct_jc
- applyFile
- resetToUpload
- number_word_corrections.py
- document_zones.py
- downloadUrl
- _apply_apa_heading_styles
- test_abstract_silent_when_introduced_in_abstract
- test_inline_def_in_body_silences_subsequent_body_uses
- Research — APA base template amendment plan (viability for C-24a)
- test_bare_use_before_inline_def_still_flagged
- test_acronym_inside_parentheses_is_skipped
- test_zone_transition_handles_numbered_heading_prefix
- Path
- _llm_notes_to_results
- _apply_intra_paragraph_tracked_replace
- synthetic_doc
- _italicise_keyword_label
- read_docx
- test_not_sam_fixed
- Document
- Path

## God Nodes (most connected - your core abstractions)
1. `load_paragraphs()` - 92 edges
2. `build_edited_document()` - 65 edges
3. `validate()` - 54 edges
4. `doc_analysis_pipeline()` - 41 edges
5. `apply_acronym_corrections()` - 40 edges
6. `generate_commented_docx()` - 38 edges
7. `documentBodyFormatCheck()` - 35 edges
8. `apply_run_font_corrections()` - 34 edges
9. `3. Pipeline wiring in `build_edited_document` (9752–10006)` - 34 edges
10. `_apply_author_plan()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `2.3 MUST — de-colour `Heading1`–`Heading5` (this is also a C-23 defect)` --references--> `_apply_apa_heading_styles()`  [INFERRED]
  research/05-apa-base-template-amendment-plan.md → app/services/output_generation_samfix.py
- `3.1 Classifiers (new, near `_looks_like_author_list_text` at 1145)` --references--> `_looks_like_author_list_text()`  [INFERRED]
  research/04-implementation-plan-c24a-c24b.md → app/services/output_generation_samfix.py
- `Phase 3 — C-26 Abstract/Keywords + APA-20 (two commits)` --references--> `apply_front_matter_styles()`  [INFERRED]
  research/06-plan-c25-c26-c27.md → scripts/gen_apa7_base_template.py
- `3. Pipeline wiring in `build_edited_document` (9752–10006)` --references--> `_apply_front_page_asset_plan()`  [INFERRED]
  research/03-implementation-context.md → app/services/output_generation_samfix.py
- `3. Pipeline wiring in `build_edited_document` (9752–10006)` --references--> `_apply_title_plan()`  [INFERRED]
  research/03-implementation-context.md → app/services/output_generation_samfix.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Canonical API Screen Flow** — app_templates_writer_four_stage_manuscript_workflow, docs_api_contract_processing_state_machine, docs_api_contract_results_status_mapping, docs_api_contract_idempotent_download [EXTRACTED 1.00]
- **Deterministic Validation Stack** — jutlp_validator_checklist_deterministic_jutlp_validation, jutlp_validator_checklist_paragraph_row_model, jutlp_validator_checklist_required_section_checks, jutlp_validator_checklist_front_page_checks, jutlp_validator_checklist_rule_report_format [EXTRACTED 1.00]
- **Manuscript Review Pipeline** — readme_open_editor_bot, readme_jutlp_manuscript_review, readme_openai_editorial_review, readme_flask_document_processing_pipeline [EXTRACTED 1.00]

## Communities (152 total, 24 thin omitted)

### Community 0 - "8. Dead-code reachability after C-24a"
Cohesion: 0.06
Nodes (76): _apply_apa_body_geometry(), _apply_front_page_asset_plan(), _apply_title_plan(), build_front_page_asset_check_plan(), _collect_image_rel_ids(), _collect_relationship_ids(), _doc_has_first_page_header_picture(), _element_has_textbox() (+68 more)

### Community 1 - "_build_zoned_docx"
Cohesion: 0.10
Nodes (20): _build_zoned_docx(), An introduction in the abstract does NOT satisfy the body's first-use rule., Truly unknown acronyms in the abstract (no allow-list, no inline def anywhere)…, Block-listed tokens (USA, OK, NASA, iOS, …) never produce issues even when bare…, If the editor adds a well-known org (e.g. NASA) to the allow-list, the block-…, OECD and UNESCO are on the client's approved-acronyms list — bare body use…, The abstract is an independent zone and needs its OWN introduction. An acronym…, Anything from Acknowledgements onwards is outside the bot's scope. (+12 more)

### Community 2 - "jutlp_validator.py"
Cohesion: 0.08
Nodes (52): build_report(), check_abstract_single_paragraph(), check_block_quote_style(), check_body_paragraph_styles(), check_combined_results_discussion(), check_conclusion_length(), check_discussion_subsections(), check_dot_points() (+44 more)

### Community 3 - "test_front_page_style_fixes.py"
Cohesion: 0.04
Nodes (99): _append_affiliation_before_notes(), _append_body_comment(), _apply_author_plan(), _flush(), _apply_document_body_plan(), _apply_heading_1_text_normalization(), build_author_check_plan(), _build_authors_tracked_change_comment() (+91 more)

### Community 4 - "output_generation.py"
Cohesion: 0.04
Nodes (90): apply_citation_formatting_corrections(), _apply_corrections_to_para(), _Element, Insert missing space after p. / pp. in in-text page references. APA style…, Add a space after p./pp. before page numbers as tracked changes. Returns…, _apply_corrections_to_para(), apply_et_al_corrections(), _corrected_bracket() (+82 more)

### Community 5 - "apa7_formatting_checks.py"
Cohesion: 0.11
Nodes (32): _abstract_body_paragraphs(), _find_keywords_paragraph(), _keywords_text_paragraph(), _Element, Return the Keywords paragraph — either a heading or the inline label., The paragraph carrying the keyword terms (after a Keywords heading)., Non-empty paragraphs between the Abstract heading and the next boundary.…, Direct-or-hyperlink text runs belonging to this paragraph. (+24 more)

### Community 6 - "test_sentence_coherence_corrections.py"
Cohesion: 0.11
Nodes (34): get_sentence_coherence_flags(), _is_usable_reason(), Call the LLM and return a list of ``{original, reason}`` dicts.…, True if ``reason`` is a real explanation, not a degenerate verdict. Guards…, _make_doc(), parametrize, Path, Tests for the sentence-coherence LLM pass. We stub the LLM call so the tests… (+26 more)

### Community 7 - "load_paragraphs"
Cohesion: 0.07
Nodes (52): detect_heading_level_1(), extract_subsections(), get_section_bounds(), load_paragraphs(), Scan a .docx file and return its Heading 1 section text and positions., _find_existing_affiliations_for_missing_authors(), _maybe_generate_keywords_for_missing_section(), test_extract_abstract_no_longer_returns_line_count() (+44 more)

### Community 8 - "main.py"
Cohesion: 0.06
Nodes (50): _acronym_admin_active(), _acronym_admin_authed(), acronyms_admin_login(), acronyms_admin_logout(), acronyms_admin_page(), add_acronym_api(), analyse_cli(), _body_edit_items() (+42 more)

### Community 9 - "document_analysis_services.py"
Cohesion: 0.08
Nodes (47): _accepted_paragraph_text(), count_styles(), estimate_line_count(), extract_abstract(), extract_heading_level_1_sections(), extract_keywords(), extract_main_sections(), find_all_by_style() (+39 more)

### Community 10 - "test_document_normalisation.py"
Cohesion: 0.10
Nodes (45): _accept_tracked_changes(), _ancestor_paragraph_index(), _delete_guidance_paragraphs(), _is_paragraph_blank(), NormalisationReport, normalise_docx(), _Element, Path (+37 more)

### Community 11 - "test_abbreviation_corrections.py"
Cohesion: 0.08
Nodes (49): apply_abbreviation_corrections(), _find_first_match(), _iter_text_runs(), _overlaps_quote(), _process_paragraph(), _Element, Return the earliest rule-match in ``text`` as ``(start, end, replacement,…, Apply every matching rule in ``para_el``, returning updated ``next_change_id``.… (+41 more)

### Community 12 - "reference_reconstructor.py"
Cohesion: 0.09
Nodes (47): build_apa7_from_crossref(), _build_book(), _build_book_chapter(), _build_dataset(), _build_dissertation(), _build_edited_book(), _build_journal_article(), _build_preprint() (+39 more)

### Community 13 - "apply_caption_apa7_comments"
Cohesion: 0.20
Nodes (20): apply_caption_apa7_comments(), _iter_text_runs(), _Element, Emit one APA 7 caption-split comment per offending paragraph. Returns…, Yield (run_el, text) for runs we may safely anchor a comment on., _build_docx(), Path, Tests for the APA 7 caption-split recommendation pass. A figure or table… (+12 more)

### Community 14 - "gen_apa7_base_template.py"
Cohesion: 0.13
Nodes (38): add_first_page_banner(), apply_caption_styles(), apply_front_matter_styles(), apply_heading_style(), apply_normal_style(), apply_page_margins(), apply_page_numbers(), apply_quote_style() (+30 more)

### Community 15 - "output_generation_samfix.py"
Cohesion: 0.03
Nodes (122): _ack_contains(), _all_alias_norms(), _append_author_query_runs(), _apply_apa_section_margins(), _apply_apa_title_page_headers(), _apply_body_run_format(), _apply_tracked_body_format_fixes(), _apply_tracked_body_paragraph_format() (+114 more)

### Community 16 - "test_heading_corrections.py"
Cohesion: 0.06
Nodes (51): _build_section_rename_map(), _merges_two_sections(), _normalise_subsection(), Remove a leading heading number from ``text`` (e.g. "2. Literature" ->…, Lower-case, collapse whitespace, strip a leading heading number and any…, Return the canonical main section a heading fragment names, or None. Matches…, True when ``alias`` merges two *distinct* canonical sections (e.g. "Results and…, ``normalised alias -> canonical label`` for safe heading renames. Built from… (+43 more)

### Community 17 - "generate_commented_docx"
Cohesion: 0.14
Nodes (20): _dedupe_pending_comments(), generate_commented_docx(), _infer_target_phrase(), _patch_hyperlink_color_styles(), Collapse exact duplicate comments for the same document anchor., Set the Hyperlink character style to black via raw lxml (no python-docx)., Generate a reviewed `.docx` with inline comments and a validation summary page., Guess which phrase inside a paragraph should receive the comment. This gives… (+12 more)

### Community 18 - "test_heading_style_apa11.py"
Cohesion: 0.18
Nodes (17): parametrize, _find_style(), _flag_on(), _heading_paragraphs(), C-23 benchmarks: APA heading levels 1-5 (APA-11). Replaces the old…, Guards the benchmark itself: without this the asserts below are vacuous., A paragraph-level alignment overrides the style, so it has to go., The regression the old text-matching policy caused. "Literature" sits in the… (+9 more)

### Community 19 - "rules"
Cohesion: 0.08
Nodes (8): fixture, rules(), TestDeidentifiedWithAuthorLeak, TestFrontPageIssues, TestMissingMethodSubsection, TestStructureAndEndmatterIssues, TestValidDeidentified, TestValidIdentified

### Community 20 - "acronym_corrections.py"
Cohesion: 0.10
Nodes (38): _append_author_query_runs(), apply_acronym_corrections(), _apply_mutations(), _author_query_parts(), _bracketed_spans(), _build_bullet(), _build_replacement(), _build_zone_map() (+30 more)

### Community 21 - "test_access_validation.py"
Cohesion: 0.13
Nodes (26): _require_access(), AccessResult, AccessStatus, check_access(), check_local_bypass(), Access validation service — G-07. Defines the authentication contract for…, Single entry point the Flask gate calls. Tries, in order: 1. Local SKIP_AUTH…, SKIP_AUTH must be explicitly 'true' (case-insensitive) — any other value,… (+18 more)

### Community 23 - "test_intro_page_break.py"
Cohesion: 0.48
Nodes (6): _doc(), _intro_has_page_break(), Tests for the front-page / body page break before the Introduction., Regression: a numbered "1. Introduction" heading must still get the front-…, test_page_break_inserted_before_numbered_introduction(), test_page_break_inserted_before_plain_introduction()

### Community 24 - "test_spell_checker.py"
Cohesion: 0.10
Nodes (37): _build_word_counts(), _classify_word(), _freq_ratio(), get_spell_corrections(), _levenshtein(), Return ``(verdict, candidate)`` for a single suspect word. Verdict is one of: *…, Cheap Levenshtein implementation — we only ever compare short words so the…, Ratio of dictionary frequency between candidate and source word. Both… (+29 more)

### Community 25 - "lxml"
Cohesion: 0.06
Nodes (31): Apply APA-style hanging indent to reference list paragraphs as tracked changes.…, # NOTE: do NOT skip _SKIP_STYLES here. That set (shared with the, jutlp_validator_validator, lxml, C-22 direct-formatting path test. The 01_valid_identified fixture carries no…, # TODO: Delete script after completion of Track C, Runs build_edited_document on the 01_valid_identified.docx fixture and asserts…, # TODO: Delete script after completion of Track C (+23 more)

### Community 26 - "test_appendix_removal.py"
Cohesion: 0.17
Nodes (24): _is_appendix_heading(), _build_docx(), _comment_texts(), _del_texts(), _p(), _Element, Path, Tests for the appendix-comment pass. JUTLP does not accept appendices: the… (+16 more)

### Community 27 - "test_grammar_corrections.py"
Cohesion: 0.10
Nodes (31): _build_user_prompt(), _fix_au_spellings(), get_grammar_corrections(), _has_au_us_suffix_swap(), _is_au_to_us_replacement(), _is_proper_noun_correction(), Remove parenthetical citations and URLs before sending to LLM., Return True if original looks like a proper noun, surname, acronym, or tech… (+23 more)

### Community 28 - "keywordsFound"
Cohesion: 0.13
Nodes (20): _extract_keywords_list(), _find_abstract_heading_in_front(), _find_blank_line_after_index(), _find_citation_heading_in_front(), _find_introduction_heading_in_front(), _find_keywords_heading_in_front(), _is_citation_body_end_marker(), _is_keywords_body_end_marker() (+12 more)

### Community 29 - "Frontend-Backend API Contract"
Cohesion: 0.07
Nodes (31): OAPA Brand Mark, Acronym Management UI, Editor Admin Authentication, Persistent Acronym Storage, Editorial Access Gate, Shared Password Authentication, Client-Side Manuscript Validation, Four-Stage Manuscript Workflow (+23 more)

### Community 30 - "short_paragraph_comments.py"
Cohesion: 0.19
Nodes (18): apply_short_paragraph_comments(), _first_token_span(), _iter_text_runs(), _paragraph_text(), _Element, Flag short prose paragraphs (<3 sentences) with Word comments. This pass emits…, Yield editable visible text runs from ``para_el``. Runs inside tracked-change…, Count sentence-like spans in ``text``. A sentence is any non-empty chunk after… (+10 more)

### Community 31 - "test_decimal_corrections.py"
Cohesion: 0.09
Nodes (26): _build_docx(), _Element, Path, Tests for the decimal-precision and comma-as-decimal checks., The classic example: thousand separators and comma-decimals together., The example from the client's brief, end-to-end., A `0.1234` inside `"..."` retains the source's precision., Unquoted comma-decimal in the same paragraph as a quoted one must still be… (+18 more)

### Community 32 - "reference_format_corrections.py"
Cohesion: 0.10
Nodes (29): heading_zone_transition(), initial_zone(), normalise_heading(), Lower-case, strip numeric prefix and trailing colon-suffix., Return the new zone given a heading paragraph's style and text. A real Heading…, Determine the starting zone for the very first paragraph. If the document has…, _apply_del_ins(), apply_reference_format_corrections() (+21 more)

### Community 33 - "script.js"
Cohesion: 0.10
Nodes (28): _activateStep(), _clearPollDelay(), clearUploadError(), displayFile(), fetchJutlpArticles(), finishStepAnimation(), groupItems(), JUTLP_FALLBACK_ARTICLE (+20 more)

### Community 34 - "acronym_store.py"
Cohesion: 0.11
Nodes (28): add_acronym(), _ensure_file_exists(), load_acronyms(), _load_seed(), Path, Persistent store for the editor-managed acronym allow-list. The list lives as a…, Restore the on-disk store to the bundled seed. Used by tests., Return the bundled seed JSON as a fresh dict. (+20 more)

### Community 35 - "titleFound"
Cohesion: 0.08
Nodes (29): _apply_apa_title_page(), _collect_quote_formatting_issues(), _count_title_lines(), _count_title_words(), _extract_quoted_segments(), _find_anchor_above(), _find_content_authors(), _fix_au_spellings_in_text() (+21 more)

### Community 36 - "build_prompts"
Cohesion: 0.10
Nodes (28): Few-shot editorial examples extracted from real JUTLP editor decisions. These…, JUTLP editorial guidelines extracted from 'JUTLP Template 2026.docx'. Last…, ParagraphRecord, build_prompts(), _build_system_prompt(), _build_user_prompt(), _canonical_section_for(), _extract_front_page_content() (+20 more)

### Community 37 - "apply_number_word_corrections"
Cohesion: 0.16
Nodes (30): apply_number_word_corrections(), Scan body paragraphs and emit tracked-change replacements for digits 0-9.…, _build_docx_with_paragraph(), _count_changes(), Path, Tests for digit-to-word tracked-change corrections. These tests build minimal…, A digit INSIDE quoted text retains the source's form., Unquoted digit in a paragraph that also has a quoted digit must still be… (+22 more)

### Community 38 - "test_sam_fixes_validator_rules.py"
Cohesion: 0.14
Nodes (25): app_services, _add_style(), D-01 Phase 2 evidence tests: one test per validator rule id, proving the…, FP011 fixed by S._apply_abstract_plan (tracked change)., STY003 fixed by S._apply_body_and_reference_style_fixes (tracked style change)., STY004 fixed by S._apply_body_and_reference_style_fixes (tracked style change)., SPE002 fixed by S._apply_intro_page_break (silent pageBreakBefore)., TAB001 fixed by S._apply_tracked_table_formatting (silent style retag). (+17 more)

### Community 39 - "cli_copybot.py"
Cohesion: 0.18
Nodes (20): _heading_level_1_sections(), _is_generic_copyedit_output(), main(), _print_heading_normalization_summary(), Path, _rename_generic_copyedit_output(), _show_heading_level_1_sections(), _status() (+12 more)

### Community 40 - "reference_checker.py"
Cohesion: 0.08
Nodes (42): call_llm_json(), _check_citation_components_with_llm(), _build_structured_reference(), _cache_get(), _cache_set(), check_duplicate_references(), check_orphan_citations(), check_reference_citations() (+34 more)

### Community 41 - "test_table_keep_together.py"
Cohesion: 0.15
Nodes (27): _apply_caption_keep_next(), apply_table_keep_together(), _ensure_keep_next(), _ensure_trpr(), _ensure_trpr_child(), _para_style(), _para_text(), _Element (+19 more)

### Community 42 - "LLMError"
Cohesion: 0.09
Nodes (37): call_llm(), get_client(), LLMError, Exception, Raised when the LLM call fails after retries., Create an OpenAI client., Send a structured-output request to the OpenAI Chat Completions API. Returns…, _build_user_prompt() (+29 more)

### Community 43 - "table_page_breaks.py"
Cohesion: 0.20
Nodes (26): apply_table_page_breaks(), _cell_text(), _make_page_break_paragraph(), _page_break_anchor(), _para_has_page_break(), _para_style(), _para_text(), _preceded_by_page_break() (+18 more)

### Community 44 - "jutlp_articles.py"
Cohesion: 0.18
Nodes (25): _abstract_candidates(), _article_details_url(), _clean_abstract_candidate(), _clean_text(), _extract_abstract(), _extract_article_urls(), _extract_author(), _extract_title() (+17 more)

### Community 45 - "test_font_sweep.py"
Cohesion: 0.06
Nodes (55): check_fonts(), APA002: every typeface resolves to the APA default (Calibri). Inspects text…, apply_run_font_corrections(), _apply_tracked_run_font(), _char_style_font_map(), _current_sz(), _direct_text_runs(), _is_inside_insertion() (+47 more)

### Community 46 - "results"
Cohesion: 0.10
Nodes (18): is_sam_fixed(), Reporting ownership: which layer reports each validation finding. A finding…, True when Sam's builder fixes this validator rule, so no other layer should…, _build_changes_made(), _build_summary(), _count_sam_changes(), _dedup_sam_issues(), _llm_notes_to_results() (+10 more)

### Community 47 - "document_styling_fixes.py"
Cohesion: 0.29
Nodes (11): APA-7 Template Definitions and Formatting Constants. Locked Decisions: Calibri…, _canonical_index(), _collect_until(), compare_document_styles(), compare_template_and_document(), extract_headings(), extract_template_styles(), _find_first_text() (+3 more)

### Community 48 - "test_copyeditor_comment_regressions.py"
Cohesion: 0.22
Nodes (19): Renumber visible Author Query labels after every comment pass has run., _renumber_final_author_queries(), _comment_ids_in_document_order(), _renumber_author_queries_by_anchor_order(), _accepted_visible_text(), _assert_no_visible_timestamp(), _comment_text(), _comment_texts() (+11 more)

### Community 49 - "feedback_gen_pipeline.py"
Cohesion: 0.13
Nodes (17): doc_analysis_pipeline(), _hyperlink_plain_urls_in_refs(), _inject_crossref_doi_links(), _max_revision_id(), _normalise(), _patch_settings_show_markup(), Remove Sam's comments (id > our_max_id) that duplicate our validator output.…, Append CrossRef-verified DOI hyperlinks as tracked insertions to reference… (+9 more)

### Community 50 - "extract_references"
Cohesion: 0.14
Nodes (13): extract_references(), _get_style_name(), Return ``(start_index, end_index)`` bounding the References section. ``start``…, Two-tier reference selection used by BOTH extraction and comment anchoring so…, _references_window(), _select_reference_entries(), _build_docx_with_sections(), A paper with reference-styled paragraphs but NO References heading still has… (+5 more)

### Community 51 - "pathlib"
Cohesion: 0.08
Nodes (43): _has_reference_issue_summary_comment(), _insert_suspicious_ref_comments(), Add Word comments for reference issues: - CONS001/CONS002 citation-consistency…, Document, Path, read_docx(), _apply_corrections_to_para(), apply_narrative_citation_corrections() (+35 more)

### Community 52 - "table_n_notation_comments.py"
Cohesion: 0.15
Nodes (21): apply_table_n_notation_comments(), _is_capital_n_header(), _iter_text_runs(), _Element, Flag capital "N" used as a table column header. In statistical reporting the…, Yield (run_el, text) for runs we may safely anchor a comment on., True when the paragraph is a table cell whose only content is "N"., Emit one comment per table column header that is a bare capital "N". Returns… (+13 more)

### Community 53 - "TestFiveFailuresFiveComments"
Cohesion: 0.18
Nodes (5): has_comments_relationship(), Return ordered list of (text, has_ins, [commentRangeStart ids]) for every…, The combined 'Results and Discussion' fixture has no standalone Discussion…, Canonical order check., TestFiveFailuresFiveComments

### Community 54 - "build_edited_document"
Cohesion: 0.06
Nodes (59): _apply_abstract_plan(), _style_fix_pass(), _apply_citation_plan(), _apply_editorial_review_comment_plan(), _apply_heading_2_title_case(), _apply_heading_keep_next(), _apply_intro_page_break(), _apply_keywords_plan() (+51 more)

### Community 55 - "pytest"
Cohesion: 0.19
Nodes (13): io, pytest, _client(), _poll_until_final(), Tests for the upload guardrails added to app.main: 1. Whole-document word-count…, A pipeline that stalls without ever calling progress still flips the session to…, Poll /api/results until it returns a non-202 (final) response., A pipeline that keeps calling progress past the deadline is aborted at the next… (+5 more)

### Community 56 - "test_references_block_corrections.py"
Cohesion: 0.10
Nodes (37): check_references_page_break(), APA010: the References block starts on a new page., _add_heading1_style(), _doc_with_references(), _drop_heading1_style(), parametrize, C-25 evidence tests: the References block reaches its APA-12 form. Covers the…, A numeric style id ("3") named "heading 1" still counts as Heading 1. (+29 more)

### Community 57 - "apply_reference_order_comments"
Cohesion: 0.17
Nodes (20): _anchor_comment_on_paragraph(), apply_reference_order_comments(), _build_comment(), _find_references_heading(), _first_inversion(), _passthrough(), _Element, Comment on a reference list that is not alphabetically ordered. Comment-only —… (+12 more)

### Community 58 - "test_acronym_api.py"
Cohesion: 0.10
Nodes (9): importlib, client(), gated_client(), fixture, Smoke tests for the acronym admin HTTP endpoints. Skipped when Flask isn't…, Read-only access stays open so the pipeline can still load the list., Boot the Flask app with auth disabled and the store pointed at tmp., Boot the app with the editor-password gate enabled. (+1 more)

### Community 59 - "test_reference_indent_corrections.py"
Cohesion: 0.14
Nodes (21): _already_correct(), apply_reference_indent_corrections(), _is_heading(), _resolved_name(), _build_style_hanging_map(), _resolve(), _build_style_name_map(), _Element (+13 more)

### Community 60 - "run_editorial_review"
Cohesion: 0.10
Nodes (33): EditorialNote, EditorialReviewResult, LLM verdict on a single deterministic structural check result., StructuralValidation, Run LLM-based editorial review on a JUTLP manuscript. Pipeline: 1. Parse DOCX…, run_editorial_review(), _strip_internal_markers(), build_editorial_review_comment_plan() (+25 more)

### Community 61 - "test_abstract_length_rule.py"
Cohesion: 0.17
Nodes (18): check_abstract(), _fp008(), _parsed(), APA-08 abstract length rule: at most 250 words. The JUTLP companion rule — "the…, The body (after Introduction) must not be swallowed into the abstract., C-26 removed the JUTLP front-page line region. These keys must not return — a…, C-26 removed Practitioner Notes (APA-20)., Regression guard for the retired line-region rule: a short abstract padded with… (+10 more)

### Community 62 - "_make_textbox_wrap_around_text"
Cohesion: 0.33
Nodes (13): _make_textbox_wrap_around_text(), Make a front-page floating textbox use *square* text-wrapping so the…, 2. `tests/test_front_page_textbox_wrap.py` — 6 tests, 84 lines, _anchor_para(), _Element, The front-page editorial textbox must wrap text around it, not overlay it. The…, Schema order: the wrap element must precede docPr in the anchor., test_behinddoc_is_cleared() (+5 more)

### Community 63 - "reference_type_checker.py"
Cohesion: 0.19
Nodes (18): _check_book(), _check_book_chapter(), _check_conference(), _check_dataset(), _check_journal(), _check_podcast(), check_reference_type_style(), _check_report() (+10 more)

### Community 64 - "test_abstract_keywords_formatting.py"
Cohesion: 0.12
Nodes (33): apply_abstract_keywords_formatting(), _is_bold(), Apply APA-08 (abstract) and APA-09 (keywords) formatting. Returns…, Return ``styleId -> lowercased style name``., _styles_index(), _add_front_matter_styles(), _doc(), _find() (+25 more)

### Community 65 - "apa7_validator.py"
Cohesion: 0.24
Nodes (19): check_references_hanging_indent(), APA012: every reference entry carries a 0.5in hanging indent., build_report(), check_abstract(), check_discussion_subsections(), check_front_page(), check_keywords(), check_method_subsections() (+11 more)

### Community 67 - "test_reference_checker.py"
Cohesion: 0.23
Nodes (9): check_text_dois(), DOIT: Validate every DOI-shaped substring found in the plain text of each…, _cr_item(), Return a fake ``_lookup_doi`` that resolves DOIs from a dict. ``None`` value…, A reference that quotes the same DOI twice (bare + URL form) should only hit…, _stub_lookup(), TestCheckTextDOIs, _spy() (+1 more)

### Community 68 - "abstract_keywords_formatting.py"
Cohesion: 0.09
Nodes (45): _available_style_ids(), APA-08 / APA-09 abstract and keywords formatting (C-26). Abstract: heading bold…, Return the styleId whose declared name is ``wanted`` (case-insensitive)., _style_id_for(), Return the wrong typefaces a style/defaults ``w:rFonts`` declares. Dry-run of…, _style_rfonts_would_change(), find_canonical_heading(), get_or_add_ppr() (+37 more)

### Community 69 - "abstractFound"
Cohesion: 0.07
Nodes (32): abstractFormatCheck(), abstractFound(), _build_front_page_affiliations_dump(), _build_missing_abstract_components_message(), _check_abstract_components_with_llm(), _find_affiliations_end_pos(), _find_affiliations_end_pos_with_llm(), _is_abstract_body_end_marker() (+24 more)

### Community 70 - "_read_doc_root"
Cohesion: 0.15
Nodes (13): Five problematic acronyms still produce exactly one Word comment., Allow-listed acronyms still need a first-use introduction in the body. A…, First body use is rewritten as 'full term (ACRO)', not just 'full term'., The single comment range wraps the first issue's location., Acronyms in the manuscript title produce NO issue at all — no bullet in the…, Crucially, ignoring the title must NOT cause the title's acronym to pre-…, _read_doc_root(), test_allow_listed_acronym_in_body_flagged_when_not_introduced() (+5 more)

### Community 71 - "_find_target_para_index"
Cohesion: 0.11
Nodes (31): _find_after(), _find_first_heading(), _find_first_non_empty_para(), _find_front_matter_anchor(), _find_front_matter_rule_anchor(), _find_front_style(), _find_front_text(), _find_heading() (+23 more)

### Community 73 - "_iter_paren_citations"
Cohesion: 0.20
Nodes (7): _iter_paren_citations(), Yield ``(surname, year)`` tuples for every parenthetical citation. Handles…, Coverage for the multi-citation parenthesis parser., The reported bug: a four-citation paren block produced ZERO matches because the…, APA disambiguators like ``2020a`` must survive., A `(see ...)` aside without a Surname,Year pair must yield nothing — even…, TestParenCitationIterator

### Community 74 - "_llm_edits_for_paragraph"
Cohesion: 0.16
Nodes (13): _dedupe_edits(), _fix_au_spellings(), _llm_edits_for_paragraph(), Replace any US spellings in text with AU equivalents., patch, test_body_edit_plan_propagates_accepted_exact_repeat(), test_dedupe_edits_drops_duplicates(), test_llm_edits_for_paragraph_caps_edits() (+5 more)

### Community 75 - "_apply_tracked_style_change"
Cohesion: 0.25
Nodes (14): _apply_style_if_needed(), _apply_tracked_style_change(), Remove direct formatting that would override a heading style. A paragraph that…, _strip_conflicting_direct_format_for_heading(), _body_para(), _ppr(), A body paragraph restyled to a heading must shed its body formatting. When the…, Only size/spacing are stripped — bold stays (headings are bold anyway). (+6 more)

### Community 76 - "test_reporting_ownership.py"
Cohesion: 0.17
Nodes (8): app_domain, glob, _all_emitted_rule_ids(), _family(), Contract tests for reporting ownership (D-01 remediation, Phase 1). Every…, TestFamilyVerdictsCoverEverything, TestSamFixedIdsAreReal, TestSingleSource

### Community 77 - "find_quote_spans"
Cohesion: 0.15
Nodes (8): find_quote_spans(), is_in_quote(), Return True when the half-open range ``[start, end)`` overlaps any quotation…, Return a list of ``(start, end)`` half-open intervals locating every paired-…, Tests for the inline-quotation detection helper. The helper underpins JUTLP's…, Single quote marks are ambiguous (apostrophes!) so the helper deliberately…, TestFindQuoteSpans, TestIsInQuote

### Community 78 - "_normalise_surname"
Cohesion: 0.27
Nodes (5): _normalise_surname(), Lowercase, strip accents, punctuation, and possessive 's for fuzzy match.…, Return ``(normalised_surname, display_surname)`` for a reference entry, or None…, _sort_key_and_label(), TestNormaliseSurname

### Community 79 - "_read_comments_root"
Cohesion: 0.22
Nodes (11): _comment_visible_text(), _Element, Concatenate every ``<w:t>`` text under the comments root., When the author DID introduce the acronym in the body, no issue fires., Allow-listed acronyms in the abstract are silent — no flagging., When a track change is proposed, the bullet mentions it so the editor knows…, _read_comments_root(), test_abstract_allow_listed_silent() (+3 more)

### Community 80 - "docx"
Cohesion: 0.24
Nodes (17): build_output_filename(), build_output_filename_from_author_line(), _first_author_last_name(), _get_author_line_and_markers(), _get_document_year(), _remove_superscript_runs_from_author_line(), _unique_output_filename(), datetime (+9 more)

### Community 81 - "fixture"
Cohesion: 0.17
Nodes (4): fixture, TestCrefPassIsNotCommented, TestReferenceVisualIndicators, TestValidDocNoComments

### Community 82 - "test_acronym_corrections.py"
Cohesion: 0.17
Nodes (15): _format_author_query_text(), _matches_definition(), Attempt to align ``letters`` against the leading section of ``words``. Walks…, If `words` contain a valid full form for `acro`, return the phrase. Walks the…, _try_match_definition(), Tests for acronym detection + consolidated comment + tracked-change rewrites., Conversely, text inside ``<w:del>`` represents tracked deletions — content the…, If the docx already has comments from earlier passes, the new one gets the next… (+7 more)

### Community 83 - "count_comments_in_docx"
Cohesion: 0.22
Nodes (3): count_comments_in_docx(), has_comments_content_type(), TestOneFailureOneComment

### Community 84 - "test_language_corrections.py"
Cohesion: 0.21
Nodes (11): Return one summary entry per repeated spelling correction. The tracked-change…, summarize_spelling_correction_repeats(), _docx_xml(), An unquoted US spelling in the same paragraph as a quoted one must still be…, A US-spelled word INSIDE quoted text must NOT be rewritten — direct quotations…, test_generalizability_is_changed_to_australian_spelling(), test_repeated_spelling_fix_gets_one_author_query_comment(), test_spelling_summary_groups_case_variants_of_same_fix() (+3 more)

### Community 85 - "test_body_llm_edits.py"
Cohesion: 0.08
Nodes (39): _validate_edit(), _apply_body_and_reference_style_fixes(), Apply tracked style changes for body and reference paragraphs: - Required body…, Regression: `Evidences-Based → evidencesbased` slipped past a case-sensitive…, An edit that keeps the hyphen and fixes a real typo must still pass., JUTLP policy: text inside `"..."` retains the source's spelling., Same paragraph, unquoted region: a meaning-preserving edit must still be…, The LLM may not strip a hyphen from a compound word. (+31 more)

### Community 86 - "_extract_ref_author_part"
Cohesion: 0.17
Nodes (6): _extract_ref_author_part(), _normalise_text(), Return the author/group-author portion of a reference entry. Slices everything…, Replace curly quotes with their straight ASCII equivalents., TestCitationRegexes, TestExtractRefAuthorPart

### Community 87 - "TestPresentUnstyledDiscussionNoStub"
Cohesion: 0.27
Nodes (4): A Discussion section that is present but not yet Heading-1 styled (the author…, No tracked-inserted 'Discussion' heading paragraph should exist., The Discussion-subsection comment must anchor on the original (non-inserted)…, TestPresentUnstyledDiscussionNoStub

### Community 88 - "_is_appendix_heading"
Cohesion: 0.38
Nodes (5): _extract_ref_hyperlinks(), _is_appendix_heading(), Return (entry_num, ref_text, url) for reference entries that already have a…, parametrize, TestIsAppendixHeading

### Community 89 - "_apply_inline_keywords_split"
Cohesion: 0.14
Nodes (20): _append_plain_text_run(), _append_plain_text_run_with_size(), _append_text_with_line_breaks(), _append_text_with_superscript_markers(), _append_tracked_replace(), _apply_inline_keywords_split(), _apply_table_paragraph_style(), _apply_title_text_tracked_changes() (+12 more)

### Community 90 - "_ref_surname_keys"
Cohesion: 0.36
Nodes (4): Return every normalised surname-key a reference can plausibly match. For person…, _ref_surname_keys(), Person refs (with a comma) must NOT have an acronym alias generated — otherwise…, TestRefSurnameKeys

### Community 91 - "appendix_removal.py"
Cohesion: 0.23
Nodes (13): _anchor_comment_on_paragraph(), apply_appendix_removal(), _find_appendix_start(), _is_heading_paragraph(), _paragraph_has_image(), _passthrough(), _Element, Flag content that appears AFTER the reference list (appendices). JUTLP house… (+5 more)

### Community 92 - "inspect_abstract.py"
Cohesion: 0.29
Nodes (5): get_comment_anchors(), get_ref_entries(), Inspect the processed output vs the original to find comment placement issues., Map comment id -> paragraph text snippet where the anchor sits., Return numbered reference entries from the document.

### Community 93 - "test_jutlp_validator.py"
Cohesion: 0.12
Nodes (11): docx_oxml, docx_oxml_ns, _make_numbered(), Method/Discussion subheadings that aren't in the template's expected set are…, results_by_rule(), test_combined_findings_discussion_reports_long_policy_comment(), test_dot_points_flagged_everywhere(), test_required_literature_and_method_messages_include_expected_location() (+3 more)

### Community 95 - "Gurman — Sprint 2 Wiring Tasks (Frontend ↔ Backend Reference)"
Cohesion: 0.13
Nodes (16): ProcessingCancelled, ProcessingTimeout, Exception, _run(), _pipeline(), _update_progress(), Artifacts, Backend truth (verified against `app/main.py`, `app/static/script.js`) (+8 more)

### Community 96 - "Path"
Cohesion: 0.29
Nodes (7): _build_docx(), _build_docx_with_inserted_run(), Path, The scanner must read text inside ``<w:ins>`` runs — that's what upstream…, Build a minimal docx with one paragraph per supplied text., Build a docx where each entry is ``(style, text, inside_ins)``. When…, test_acronyms_inside_inserted_runs_are_detected()

### Community 97 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 98 - "session_manager.py"
Cohesion: 0.17
Nodes (20): create_app(), Background thread that prunes expired session files every 5 minutes (D-06/D-07)., start_session_sweeper(), _sweep_loop(), start_session_sweeper(), _sweep_loop(), delete_session(), _delete_session_unlocked() (+12 more)

### Community 99 - "timestamps.py"
Cohesion: 0.19
Nodes (13): now_sydney_iso(), Shared timestamp helper for Word comments and tracked changes. Word stores the…, Return the current time as an ISO-8601 string with the Sydney offset. Example:…, _sydney_tz(), Tests for the shared Sydney-time stamp helper. Word comments and tracked…, Sydney is UTC+10 (standard) or UTC+11 (daylight saving). If the tz database is…, Second precision only — keeps the stamp tidy and matches the previous format's…, Regression: the old format ended in 'Z' (UTC). The new one must not. (+5 more)

### Community 101 - "permission"
Cohesion: 0.08
Nodes (24): git diff *, git log *, git status *, pip install *, pytest *, python *, python3 *, ruff check * (+16 more)

### Community 102 - "os"
Cohesion: 0.05
Nodes (69): Deterministic abbreviation / journal-style fixes emitted as tracked changes.…, _make_comment_element(), _patch_content_types(), _patch_rels(), Replace the run with (before | comment-anchored content | after). When…, _split_run_for_action(), _anchor_paragraph_comment(), _build_comment() (+61 more)

### Community 107 - "_canonical_insert_index"
Cohesion: 0.24
Nodes (9): _canonical_insert_index(), Return the pStyle val used by existing Heading-1 paragraphs. Documents vary:…, Return the index within ``all_paras`` to insert the stub for ``section``. Place…, _resolve_h1_style_id(), _h1_para(), Build a Heading-1 lxml <w:p> for insert-index tests., test_canonical_insert_index_after_present_predecessor(), test_canonical_insert_index_before_successor_when_no_predecessor() (+1 more)

### Community 108 - "Gurman — Data / Endpoint Tasks (Source of Truth)"
Cohesion: 0.15
Nodes (12): Backend truth (current codebase), G-01 — Endpoint inventory + contract doc (P0, unblocks H-01/H-02), G-02 — Upload + validation error-code map (P0, pairs H-02), G-03 — Processing poll/state machine + Cancel/timeout + carousel (P0, pairs H-03), G-04 — Results payload shape (P1, pairs H-04), G-05 — Download + retry semantics (P1, pairs H-05 — answers Humaid's open question), G-06 — Support/error passthrough (P2, pairs H-07), G-07 — Handoff: frontend data layer + open-questions log (P2, pairs H-01/Z-09) (+4 more)

### Community 110 - "test_reference_justification.py"
Cohesion: 0.24
Nodes (7): docx_enum_text, docx_shared, Reference entries must be justified (w:jc=both), not left-aligned. Two layers…, Return the w:jc value of the APA 7 reference style, or None., _ref_style_jc(), test_left_aligned_author_reference_style_is_replaced_with_justified(), test_template_reference_style_is_justified()

### Community 111 - "test_output_generation.py"
Cohesion: 0.14
Nodes (14): _format_author_query_text(), Return the canonical section a fail-rule belongs to, or None. SEC001-008 map…, True if a Heading-1 paragraph is the section itself (exact / 'name:' prefix),…, _section_for_rule(), _section_heading_present(), Minimal ParagraphRecord-like stub for heading-presence checks., _rec(), test_author_query_comment_text_is_not_double_prefixed() (+6 more)

### Community 113 - "2. Amendment spec"
Cohesion: 0.33
Nodes (6): 2.1 MUST — add three paragraph styles to `word/styles.xml`, 2.2 MUST — rewrite `Title` to APA shape, 2.3 MUST — de-colour `Heading1`–`Heading5` (this is also a C-23 defect), 2.4 MUST — de-colour the linked character styles, 2.5 MUST — delete `word/stylesWithEffects.xml`, 2. Amendment spec

### Community 115 - "vercel.json"
Cohesion: 0.50
Nodes (3): builds, routes, version

### Community 116 - "Research — APA 7 Base Template styles inventory"
Cohesion: 0.22
Nodes (8): 2. The model student title page in `word/document.xml`, 3. Title / author / affiliation style surface, 5. Reference styles, 6. Table / figure styles, 7. Other paragraph styles (remaining), 8. Defaults and latent styles, 9. Media / textbox verification (the decisive check), Research — APA 7 Base Template styles inventory

### Community 118 - "body_llm_edits.py"
Cohesion: 0.15
Nodes (15): _body_paragraphs(), build_body_edit_plan(), _is_skippable_paragraph(), _propagate_repeated_edits(), LLM-generated surgical copy-edits for the document body. Produces tracked-…, Return the symmetric token difference between ``find`` and ``replace``. Tokens…, Return True when the LLM reason is specific enough for display., Apply accepted exact edits to repeated matching body text. The LLM reviews each… (+7 more)

### Community 119 - "test_blinded_citation_comments.py"
Cohesion: 0.39
Nodes (11): apply_blinded_citation_comments(), Comment on blinded / placeholder citations and self-references. Comment-only,…, _comment_texts(), _doc(), Tests for the blinded / placeholder citation comment pass., Unbracketed 'anonymous'/'anonymised' prose must NOT trigger., test_anonymised_prose_is_not_flagged(), test_author_under_review_citation_is_flagged() (+3 more)

### Community 120 - "test_body_font_enforcement.py"
Cohesion: 0.27
Nodes (10): _ensure_normal_style_body_rpr(), _passthrough_copy(), Pin the body font + size on the Normal style's run properties. The template's…, 2.6 OPTIONAL — tighten `w:docDefaults`, _doc_with_normal(), _normal_rpr(), Tests for body-font enforcement: the Normal style must carry Calibri 11pt so…, A docx whose Normal style is a non-template font/size. (+2 more)

### Community 121 - "apply_table_section_boundary_comments"
Cohesion: 0.17
Nodes (24): apply_table_section_boundary_comments(), Comment on sections that open and/or close directly with a table. Returns…, docx_enum_style, create_base_doc(), get_or_add_style(), _body_paragraphs(), _make_student_doc(), _paragraph_text() (+16 more)

### Community 122 - "Gurman — Wrong File Type + Cancel + Solo Demo"
Cohesion: 0.20
Nodes (9): Dev Tasks — OpenEditor Demo (Frontend Only), G1 · Wrong file type error (`08-blocked` variant), G2 · Cancel button (`03-processing`), G3 · Solo demo to Joey and Michael, Gurman — Wrong File Type + Cancel + Solo Demo, H1 · Upload (`01-upload`, `1:10`), H2 · Checking + Processing (`02-checking` `2:2` · `03-processing` `2:28`), H3 · Results, Upgrade, Download (`04-results` `2:42` · `05-upgrade` `2:73` · `06-download` `2:94`) (+1 more)

### Community 123 - "zac-ux-tasks.md"
Cohesion: 0.20
Nodes (9): DONT DO (  Archived coz im not sure), Z-01 -- Lock Concept A IA: 4 screens + states map, Z-02 -- Upload page: validation + error states, Z-03 — Processing screen: status + carousel + Cancel/timeout, Z-04 — Results screen: issues vs. no-issues + track changes context, Z-05 — Download + process-another guard, Z-06 — MemberPress access states, Z-08 — Copy + plain-language + accessibility/responsive pass (+1 more)

### Community 124 - "_fake_llm"
Cohesion: 0.25
Nodes (3): _fake_llm(), Return a _llm_check_reference stub that embeds a distinctive marker., TestLLMVerificationConstraints

### Community 125 - "api.js"
Cohesion: 0.36
Nodes (7): CAROUSEL_ENABLED, _mapUploadErrorCode(), pollResults(), pollUntilDone(), STAGE_TO_STEP, stageToStep(), uploadManuscript()

### Community 126 - "startProcessing"
Cohesion: 0.29
Nodes (8): cancelJob(), fetchCarouselArticles(), confirmCancel(), fetchJutlpArticles(), nextJutlpArticle(), startJutlpRotation(), startProcessing(), stopJutlpRotation()

### Community 127 - "_strip_heading_direct_jc"
Cohesion: 0.18
Nodes (10): Drop a direct ``w:jc`` from Heading 1-5 paragraphs. > C-23 / APA-11: paragraph-…, _strip_heading_direct_jc(), Commit order, Implementation Plan — C-25 / C-26 / C-27 (single batch), Ordering risks, Phase 1 — C-27 font sweep (FIRST, in isolation), Test surface, Regression guard for C-22: only heading paragraphs are stripped. (+2 more)

### Community 128 - "applyFile"
Cohesion: 0.50
Nodes (4): applyFile(), checkReadable(), onFileDropped(), onFileSelected()

### Community 129 - "resetToUpload"
Cohesion: 0.50
Nodes (4): continueWithoutDownloading(), requestProcessAnother(), resetToUpload(), retryProcessing()

### Community 130 - "number_word_corrections.py"
Cohesion: 0.21
Nodes (13): _apply_corrections_to_para(), _bracket_spans(), _in_any_span(), _is_sentence_start(), _para_plain_text(), _Element, Spell out whole numbers 0-9 in running prose as tracked changes. Most academic…, Return character spans (start, end) covered by paren/bracket/brace pairs.… (+5 more)

### Community 131 - "document_zones.py"
Cohesion: 0.08
Nodes (41): _needs_apa7_split(), Flag figure/table captions that aren't split into APA 7 paragraphs. APA 7…, Return True when the paragraph holds a full single-paragraph figure/table…, apply_decimal_corrections(), Run both decimal checks over ``input_path`` and write to ``output_path``.…, get_style_name(), is_in_table(), is_list_item() (+33 more)

### Community 132 - "downloadUrl"
Cohesion: 0.67
Nodes (3): downloadUrl(), downloadFirst(), downloadManuscript()

### Community 133 - "_apply_apa_heading_styles"
Cohesion: 0.40
Nodes (5): _apply_apa_heading_styles(), Copy the APA base Heading 1-5 styles into the output and clear overrides. Two…, 4. Heading styles, Idempotence: a second run must not rewrite what is already correct., test_heading_styles_pass_is_no_op_when_already_apa()

### Community 136 - "Research — APA base template amendment plan (viability for C-24a)"
Cohesion: 0.25
Nodes (7): Repack the docx zip replacing only word/styles.xml; all other entries are…, _save_styles_xml_to_zip(), 0. Verdict, 4. Execution method, 5. Verification, 6. Sequencing, Research — APA base template amendment plan (viability for C-24a)

### Community 144 - "_llm_notes_to_results"
Cohesion: 0.50
Nodes (4): _extract_field(), _llm_notes_to_results(), Read a field from dict/object safely with a default., Normalize LLM editorial notes into validator-like result dictionaries.

### Community 145 - "_apply_intra_paragraph_tracked_replace"
Cohesion: 0.33
Nodes (7): _apply_body_edit_plan(), _apply_intra_paragraph_tracked_replace(), _paragraph_with_runs(), test_body_edit_plan_applies_all_repeated_occurrences_in_paragraph(), test_body_edit_plan_skips_repeated_occurrence_inside_direct_quote(), test_intra_paragraph_tracked_replace_reports_false_when_missing(), test_intra_paragraph_tracked_replace_single_run()

### Community 146 - "synthetic_doc"
Cohesion: 0.67
Nodes (3): fixture, A docx carrying Word's *default* Heading 1-5 definitions. Word's defaults are…, synthetic_doc()

### Community 147 - "_italicise_keyword_label"
Cohesion: 0.40
Nodes (5): _ensure_run_flag(), _is_italic(), _italicise_keyword_label(), Add a run property (``w:b`` / ``w:i``) if absent. True when written., Italicise the keywords LABEL (never the terms). Prefers the ``Keywords Label``…

### Community 148 - "read_docx"
Cohesion: 0.67
Nodes (3): read_docx(), Document, Path

### Community 149 - "test_not_sam_fixed"
Cohesion: 0.67
Nodes (3): parametrize, FP004, FP007, TAB002 have no demonstrated Sam fix — they must stay comment-only…, test_not_sam_fixed()

## Knowledge Gaps
- **101 isolated node(s):** `11. Comment / style conventions to honour`, `1. Branch / commit history`, `9. C-24b mode plumbing — what exists today`, `10. Open point to confirm before starting`, `1. Context` (+96 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1104 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_paragraphs()` connect `load_paragraphs` to `jutlp_validator.py`, `test_front_page_style_fixes.py`, `output_generation.py`, `test_sentence_coherence_corrections.py`, `main.py`, `document_analysis_services.py`, `output_generation_samfix.py`, `test_heading_corrections.py`, `generate_commented_docx`, `test_spell_checker.py`, `test_grammar_corrections.py`, `keywordsFound`, `titleFound`, `build_prompts`, `reference_checker.py`, `document_styling_fixes.py`, `extract_references`, `build_edited_document`, `run_editorial_review`, `test_abstract_length_rule.py`, `test_abstract_keywords_formatting.py`, `apa7_validator.py`, `test_reference_checker.py`, `abstractFound`, `docx`, `os`, `body_llm_edits.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `doc_analysis_pipeline()` connect `feedback_gen_pipeline.py` to `document_zones.py`, `output_generation.py`, `main.py`, `test_document_normalisation.py`, `test_abbreviation_corrections.py`, `apply_caption_apa7_comments`, `test_heading_corrections.py`, `generate_commented_docx`, `acronym_corrections.py`, `read_docx`, `short_paragraph_comments.py`, `reference_format_corrections.py`, `apply_number_word_corrections`, `cli_copybot.py`, `test_table_keep_together.py`, `table_page_breaks.py`, `test_font_sweep.py`, `test_copyeditor_comment_regressions.py`, `pathlib`, `table_n_notation_comments.py`, `build_edited_document`, `apply_reference_order_comments`, `test_reference_indent_corrections.py`, `run_editorial_review`, `apa7_validator.py`, `appendix_removal.py`, `Gurman — Sprint 2 Wiring Tasks (Frontend ↔ Backend Reference)`, `os`, `test_blinded_citation_comments.py`, `apply_table_section_boundary_comments`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `build_edited_document()` connect `build_edited_document` to `8. Dead-code reachability after C-24a`, `test_front_page_style_fixes.py`, `_apply_apa_heading_styles`, `main.py`, `output_generation_samfix.py`, `test_heading_corrections.py`, `_apply_intra_paragraph_tracked_replace`, `lxml`, `keywordsFound`, `titleFound`, `cli_copybot.py`, `test_font_sweep.py`, `results`, `test_copyeditor_comment_regressions.py`, `feedback_gen_pipeline.py`, `pathlib`, `run_editorial_review`, `test_abstract_keywords_formatting.py`, `abstract_keywords_formatting.py`, `abstractFound`, `docx`, `test_body_llm_edits.py`, `body_llm_edits.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `build_edited_document()` (e.g. with `4. Relevant functions in `output_generation_samfix.py`` and `Every other test in the file — none assert on banner/textbox insertion`) actually correct?**
  _`build_edited_document()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `11. Comment / style conventions to honour`, `1. Branch / commit history`, `9. C-24b mode plumbing — what exists today` to the rest of the system?**
  _101 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `8. Dead-code reachability after C-24a` be split into smaller, more focused modules?**
  _Cohesion score 0.06004543979227524 - nodes in this community are weakly interconnected._
- **Should `_build_zoned_docx` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._