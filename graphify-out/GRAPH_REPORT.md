# Graph Report - Openeditor  (2026-10-10)

## Corpus Check
- 155 files · ~186,359 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 3, .css 2, .example 1)

## Summary
- 3000 nodes · 7072 edges · 143 communities (122 shown, 21 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 101 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2d6474b5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- output_generation_samfix.py
- _build_zoned_docx
- validate
- test_front_page_style_fixes.py
- _split_run_at_match
- _apply_body_and_reference_style_fixes
- test_sentence_coherence_corrections.py
- load_paragraphs
- main.py
- document_analysis_services.py
- test_document_normalisation.py
- test_abbreviation_corrections.py
- reference_reconstructor.py
- doc_analysis_pipeline
- run_font_corrections.py
- _apply_author_plan
- test_heading_corrections.py
- get_comment_anchor_texts
- pathlib
- rules
- _Element
- test_access_validation.py
- openeditor.js
- _apply_tracked_table_formatting
- test_spell_checker.py
- _anchor_paragraph_comment
- test_appendix_removal.py
- _make_comment_element
- keywordsFound
- Frontend-Backend API Contract
- feedback_gen_pipeline.py
- test_decimal_corrections.py
- reference_format_corrections.py
- script.js
- acronym_store.py
- test_grammar_corrections.py
- build_prompts
- apply_number_word_corrections
- _find_target_para_index
- test_body_llm_edits.py
- reference_checker.py
- test_table_keep_together.py
- test_sam_fixes_validator_rules.py
- table_page_breaks.py
- jutlp_articles.py
- LLMError
- _remove_tracked_property_change
- strip_leading_section_number
- test_copyeditor_comment_regressions.py
- _to_title_case_title
- extract_references
- cli_copybot.py
- apply_table_n_notation_comments
- TestFiveFailuresFiveComments
- body_llm_edits.py
- test_upload_guardrails.py
- _make_comment_element
- apply_reference_order_comments
- test_acronym_api.py
- _apply_phrase_correction
- run_editorial_review
- test_abstract_length_rule.py
- _normalise_heading_text
- reference_type_checker.py
- test_acronym_corrections.py
- docx
- abstractFound
- test_reference_checker.py
- apply_decimal_corrections
- now_sydney_iso
- _read_doc_root
- test_output_generation.py
- check_references
- _iter_paren_citations
- apply_table_section_boundary_comments
- _apply_tracked_style_change
- _find_next_action
- _make_textbox_wrap_around_text
- _normalise_surname
- _read_comments_root
- generate_keywords
- output_generation.py
- find_refs_section
- reference_indent_corrections.py
- TestSubsectionAliasMatch
- docx
- _extract_ref_author_part
- TestPresentUnstyledDiscussionNoStub
- check_submitted_hyperlinks
- results
- _ref_surname_keys
- check_method_subsections
- inspect_abstract.py
- _ensure_template_styles_available
- TestValidDoc
- Gurman — Sprint 2 Wiring Tasks (Frontend ↔ Backend Reference)
- Path
- graphify.js
- apply_acronym_corrections
- test_jutlp_validator.py
- setup.sh
- permission
- session_manager.py
- copybot
- test_reporting_ownership.py
- Gurman — Data / Endpoint Tasks (Source of Truth)
- check_entry_author
- _split_run_for_action
- _find_word_anchor
- _accepted_paragraph_text
- test_language_corrections.py
- _make_comment_element
- vercel.json
- read_docx
- deployment.md
- _collect_discussion_subheading_issues
- _is_deidentified_manuscript
- get_section_bounds
- parse_docx
- Gurman — Wrong File Type + Cancel + Solo Demo
- zac-ux-tasks.md
- _fake_llm
- api.js
- startProcessing
- _should_replace
- applyFile
- resetToUpload
- _iter_text_runs
- _spelling_summary_comment_text
- downloadUrl
- test_paragraph_below_min_length_skipped
- apa7_template.py
- get_all_para_info
- select_ref_entries
- test_allow_list_takes_precedence_over_block_list
- test_bare_use_before_inline_def_still_flagged
- test_skips_heading_paragraphs

## God Nodes (most connected - your core abstractions)
1. `load_paragraphs()` - 92 edges
2. `validate()` - 64 edges
3. `build_edited_document()` - 53 edges
4. `doc_analysis_pipeline()` - 41 edges
5. `apply_acronym_corrections()` - 41 edges
6. `generate_commented_docx()` - 41 edges
7. `ParagraphRecord` - 39 edges
8. `documentBodyFormatCheck()` - 36 edges
9. `iter_paragraphs_with_zone()` - 29 edges
10. `apply_number_word_corrections()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `Results Status Mapping` --semantically_similar_to--> `Four-Stage Manuscript Workflow`  [INFERRED] [semantically similar]
  docs/api-contract.md → app/templates/writer.html
- `G-03 — Cancel job (cooperative)` --references--> `ProcessingCancelled`  [INFERRED]
  docs/gurman-sprint2-tasks.md → app/main.py
- `Client-Side Manuscript Validation` --semantically_similar_to--> `Upload Limit Mismatch`  [INFERRED] [semantically similar]
  app/templates/writer.html → docs/api-contract.md
- `TestUserPrompt` --uses--> `ParagraphRecord`  [INFERRED]
  tests/test_prompt_builder.py → app/domain/models.py
- `test_llm_edits_for_paragraph_handles_llm_error()` --calls--> `LLMError`  [INFERRED]
  tests/test_body_llm_edits.py → app/services/ai/llm_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Canonical API Screen Flow** — app_templates_writer_four_stage_manuscript_workflow, docs_api_contract_processing_state_machine, docs_api_contract_results_status_mapping, docs_api_contract_idempotent_download [EXTRACTED 1.00]
- **Deterministic Validation Stack** — jutlp_validator_checklist_deterministic_jutlp_validation, jutlp_validator_checklist_paragraph_row_model, jutlp_validator_checklist_required_section_checks, jutlp_validator_checklist_front_page_checks, jutlp_validator_checklist_rule_report_format [EXTRACTED 1.00]
- **Manuscript Review Pipeline** — readme_open_editor_bot, readme_jutlp_manuscript_review, readme_openai_editorial_review, readme_flask_document_processing_pipeline [EXTRACTED 1.00]

## Communities (143 total, 21 thin omitted)

### Community 0 - "output_generation_samfix.py"
Cohesion: 0.04
Nodes (95): _append_author_query_runs(), _apply_tracked_table_run_format(), _author_affiliation_marker_count(), _author_naming_pattern_valid(), _author_query_parts(), authorFormatCheck(), _authors_with_multiple_affiliation_markers(), _body_alignment_ok() (+87 more)

### Community 1 - "_build_zoned_docx"
Cohesion: 0.12
Nodes (16): _build_zoned_docx(), Truly unknown acronyms in the abstract (no allow-list, no inline def anywhere)…, OECD and UNESCO are on the client's approved-acronyms list — bare body use…, Regression: an introduction WITHIN the abstract silences later abstract uses…, Anything from Acknowledgements onwards is outside the bot's scope., Build a docx where each entry is (style or None, text). A ``None`` style…, Once introduced in the body, later body uses are correct journal style., Acronyms inside `(...)` are definitions or citations — never flag. (+8 more)

### Community 2 - "validate"
Cohesion: 0.10
Nodes (39): build_report(), check_abstract_single_paragraph(), check_block_quote_style(), check_body_paragraph_styles(), check_conclusion_length(), check_figure_table_structure(), check_forbidden_styles(), check_front_page() (+31 more)

### Community 3 - "test_front_page_style_fixes.py"
Cohesion: 0.07
Nodes (64): _append_body_comment(), _apply_document_body_plan(), _apply_editorial_review_comment_plan(), _apply_front_page_asset_plan(), _apply_heading_1_text_normalization(), _apply_heading_2_title_case(), _apply_keywords_plan(), _apply_normal_style_fix() (+56 more)

### Community 4 - "_split_run_at_match"
Cohesion: 0.05
Nodes (67): apply_citation_formatting_corrections(), _apply_corrections_to_para(), _Element, Insert missing space after p. / pp. in in-text page references. APA style…, Add a space after p./pp. before page numbers as tracked changes. Returns…, _apply_corrections_to_para(), apply_et_al_corrections(), _corrected_bracket() (+59 more)

### Community 5 - "_apply_body_and_reference_style_fixes"
Cohesion: 0.10
Nodes (18): _apply_body_and_reference_style_fixes(), Apply tracked style changes for body and reference paragraphs: - Required body…, docx_enum_text, docx_shared, test_body_style_fix_changes_bold_body_subheading_to_heading2(), test_body_style_fix_changes_long_quote_to_quote_style(), test_body_style_fix_changes_required_body_styles(), test_body_style_fix_does_not_change_bold_sentence_to_heading2() (+10 more)

### Community 6 - "test_sentence_coherence_corrections.py"
Cohesion: 0.12
Nodes (32): get_sentence_coherence_flags(), _is_usable_reason(), Call the LLM and return a list of ``{original, reason}`` dicts.…, True if ``reason`` is a real explanation, not a degenerate verdict. Guards…, _make_doc(), parametrize, Path, Tests for the sentence-coherence LLM pass. We stub the LLM call so the tests… (+24 more)

### Community 7 - "load_paragraphs"
Cohesion: 0.08
Nodes (48): detect_heading_level_1(), extract_heading_level_1_sections(), extract_main_sections(), extract_subsections(), load_paragraphs(), parse_docx_structure(), Return all non-empty Heading 1 sections in document order. `position` is the…, Scan a .docx file and return its Heading 1 section text and positions. (+40 more)

### Community 8 - "main.py"
Cohesion: 0.06
Nodes (50): _acronym_admin_active(), _acronym_admin_authed(), acronyms_admin_login(), acronyms_admin_logout(), acronyms_admin_page(), add_acronym_api(), analyse_cli(), _body_edit_items() (+42 more)

### Community 9 - "document_analysis_services.py"
Cohesion: 0.11
Nodes (37): Few-shot editorial examples extracted from real JUTLP editor decisions. These…, app_domain_jutlp_guidelines, ParagraphRecord, _build_system_prompt(), _build_user_prompt(), _canonical_section_for(), _extract_front_page_content(), _find_sections_by_text() (+29 more)

### Community 10 - "test_document_normalisation.py"
Cohesion: 0.10
Nodes (45): _accept_tracked_changes(), _ancestor_paragraph_index(), _delete_guidance_paragraphs(), _is_paragraph_blank(), NormalisationReport, normalise_docx(), _Element, Path (+37 more)

### Community 11 - "test_abbreviation_corrections.py"
Cohesion: 0.08
Nodes (49): apply_abbreviation_corrections(), _find_first_match(), _iter_text_runs(), _overlaps_quote(), _process_paragraph(), _Element, Return the earliest rule-match in ``text`` as ``(start, end, replacement,…, Apply every matching rule in ``para_el``, returning updated ``next_change_id``.… (+41 more)

### Community 12 - "reference_reconstructor.py"
Cohesion: 0.09
Nodes (47): build_apa7_from_crossref(), _build_book(), _build_book_chapter(), _build_dataset(), _build_dissertation(), _build_edited_book(), _build_journal_article(), _build_preprint() (+39 more)

### Community 13 - "doc_analysis_pipeline"
Cohesion: 0.12
Nodes (15): doc_analysis_pipeline(), _hyperlink_plain_urls_in_refs(), _inject_crossref_doi_links(), _max_revision_id(), _normalise(), _patch_settings_show_markup(), Path, Remove Sam's comments (id > our_max_id) that duplicate our validator output.… (+7 more)

### Community 14 - "run_font_corrections.py"
Cohesion: 0.14
Nodes (23): apply_run_font_corrections(), _apply_tracked_run_font(), _current_font(), _current_sz(), _direct_text_runs(), _is_inside_insertion(), _para_style_val(), _Element (+15 more)

### Community 15 - "_apply_author_plan"
Cohesion: 0.14
Nodes (21): _append_affiliation_before_notes(), _apply_author_plan(), _apply_style_if_needed(), _style_fix_pass(), build_author_check_plan(), _build_authors_tracked_change_comment(), _insert_paragraph_at_index(), _remove_blank_paragraph_at_index() (+13 more)

### Community 16 - "test_heading_corrections.py"
Cohesion: 0.09
Nodes (41): app_domain_canonical_jultp_template, apply_heading_corrections(), _apply_tracked_edit(), _build_style_level_map(), _corrected_heading(), _direct_text_runs(), _heading_level(), _level_from_name() (+33 more)

### Community 17 - "get_comment_anchor_texts"
Cohesion: 0.08
Nodes (33): _format_author_query_text(), generate_commented_docx(), Generate a reviewed `.docx` with inline comments and a validation summary page., Return the canonical section a fail-rule belongs to, or None. SEC001-008 map…, True if a Heading-1 paragraph is the section itself (exact / 'name:' prefix),…, _section_for_rule(), _section_heading_present(), count_comments_in_docx() (+25 more)

### Community 18 - "pathlib"
Cohesion: 0.09
Nodes (37): _has_reference_issue_summary_comment(), _insert_suspicious_ref_comments(), Add Word comments for reference issues: - CONS001/CONS002 citation-consistency…, apply_caption_apa7_comments(), Emit one APA 7 caption-split comment per offending paragraph. Returns…, Document, Path, read_docx() (+29 more)

### Community 19 - "rules"
Cohesion: 0.07
Nodes (8): fixture, rules(), TestDeidentifiedWithAuthorLeak, TestFrontPageIssues, TestMissingMethodSubsection, TestStructureAndEndmatterIssues, TestValidDeidentified, TestValidIdentified

### Community 20 - "_Element"
Cohesion: 0.10
Nodes (36): _append_author_query_runs(), _apply_mutations(), _author_query_parts(), _bracketed_spans(), _build_bullet(), _build_replacement(), _build_zone_map(), _collect_inline_definitions() (+28 more)

### Community 21 - "test_access_validation.py"
Cohesion: 0.13
Nodes (26): _require_access(), AccessResult, AccessStatus, check_access(), check_local_bypass(), Access validation service — G-07. Defines the authentication contract for…, Single entry point the Flask gate calls. Tries, in order: 1. Local SKIP_AUTH…, SKIP_AUTH must be explicitly 'true' (case-insensitive) — any other value,… (+18 more)

### Community 23 - "_apply_tracked_table_formatting"
Cohesion: 0.08
Nodes (43): _append_plain_text_run(), _append_plain_text_run_with_size(), _append_text_with_line_breaks(), _append_text_with_superscript_markers(), _append_tracked_replace(), _flush(), _apply_heading_keep_next(), _apply_inline_keywords_split() (+35 more)

### Community 24 - "test_spell_checker.py"
Cohesion: 0.06
Nodes (45): find_quote_spans(), is_in_quote(), Return True when the half-open range ``[start, end)`` overlaps any quotation…, Return a list of ``(start, end)`` half-open intervals locating every paired-…, _build_word_counts(), _classify_word(), _freq_ratio(), get_spell_corrections() (+37 more)

### Community 25 - "_anchor_paragraph_comment"
Cohesion: 0.17
Nodes (21): _anchor_paragraph_comment(), apply_blinded_citation_comments(), _build_comment(), _classify(), _distinct(), _own_text_runs(), _Element, Flag blinded / placeholder citations and self-references. For peer review… (+13 more)

### Community 26 - "test_appendix_removal.py"
Cohesion: 0.12
Nodes (36): _anchor_comment_on_paragraph(), apply_appendix_removal(), _find_appendix_start(), _is_appendix_heading(), _is_heading_paragraph(), _paragraph_has_image(), _passthrough(), _Element (+28 more)

### Community 27 - "_make_comment_element"
Cohesion: 0.16
Nodes (17): _build_comment_ref_run(), _find_span(), _inject_comment_markers(), _inject_comment_markers_for_phrase(), _make_inserted_heading_paragraph(), _Element, Fallback comment anchor: wrap the whole paragraph. We only use this when…, Build `<w:r><w:commentReference .../></w:r>` for the inline comment mark. (+9 more)

### Community 28 - "keywordsFound"
Cohesion: 0.06
Nodes (37): _apply_missing_keywords_stub(), citationFound(), _count_abstract_lines(), _count_title_lines(), _extract_keywords_list(), _find_abstract_heading_in_front(), _find_blank_line_after_index(), _find_citation_heading_in_front() (+29 more)

### Community 29 - "Frontend-Backend API Contract"
Cohesion: 0.07
Nodes (32): Graphify Knowledge Graph, OAPA Brand Mark, Acronym Management UI, Editor Admin Authentication, Persistent Acronym Storage, Editorial Access Gate, Shared Password Authentication, Client-Side Manuscript Validation (+24 more)

### Community 30 - "feedback_gen_pipeline.py"
Cohesion: 0.09
Nodes (49): Deterministic abbreviation / journal-style fixes emitted as tracked changes.…, _patch_content_types(), _patch_rels(), Flag content that appears AFTER the reference list (appendices). JUTLP house…, _needs_apa7_split(), Flag figure/table captions that aren't split into APA 7 paragraphs. APA 7…, Return True when the paragraph holds a full single-paragraph figure/table…, Two journal-style decimal checks emitted as Word comments. 1. **Excess… (+41 more)

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
Cohesion: 0.10
Nodes (31): list_acronyms_api(), add_acronym(), _ensure_file_exists(), load_acronyms(), _load_seed(), Path, Persistent store for the editor-managed acronym allow-list. The list lives as a…, Restore the on-disk store to the bundled seed. Used by tests. (+23 more)

### Community 35 - "test_grammar_corrections.py"
Cohesion: 0.10
Nodes (31): _build_user_prompt(), _fix_au_spellings(), get_grammar_corrections(), _has_au_us_suffix_swap(), _is_au_to_us_replacement(), _is_proper_noun_correction(), Remove parenthetical citations and URLs before sending to LLM., Return True if original looks like a proper noun, surname, acronym, or tech… (+23 more)

### Community 36 - "build_prompts"
Cohesion: 0.17
Nodes (11): build_prompts(), Build (system_prompt, user_prompt) from parsed document data., _make_paragraphs(), _make_parsed_structure(), Build a minimal set of ParagraphRecord objects for testing., The prompt instructs the LLM to use specific severity labels. Originally…, Regression: sections headed by an ALIAS ("Methodology", "Findings", "Literature…, A titled heading ("Introduction: Background") maps to its canonical section so… (+3 more)

### Community 37 - "apply_number_word_corrections"
Cohesion: 0.16
Nodes (30): apply_number_word_corrections(), Scan body paragraphs and emit tracked-change replacements for digits 0-9.…, _build_docx_with_paragraph(), _count_changes(), Path, Tests for digit-to-word tracked-change corrections. These tests build minimal…, A digit INSIDE quoted text retains the source's form., Unquoted digit in a paragraph that also has a quoted digit must still be… (+22 more)

### Community 38 - "_find_target_para_index"
Cohesion: 0.11
Nodes (31): _find_after(), _find_first_heading(), _find_first_non_empty_para(), _find_front_matter_anchor(), _find_front_matter_rule_anchor(), _find_front_style(), _find_front_text(), _find_heading() (+23 more)

### Community 39 - "test_body_llm_edits.py"
Cohesion: 0.08
Nodes (40): _propagate_repeated_edits(), Apply accepted exact edits to repeated matching body text. The LLM reviews each…, _validate_edit(), _apply_body_edit_plan(), _apply_intra_paragraph_tracked_replace(), _paragraph_with_runs(), Regression: `Evidences-Based → evidencesbased` slipped past a case-sensitive…, An edit that keeps the hyphen and fixes a real typo must still pass. (+32 more)

### Community 40 - "reference_checker.py"
Cohesion: 0.08
Nodes (38): build_reference_report(), _build_structured_reference(), _cache_get(), _cache_set(), check_and_report(), check_duplicate_references(), check_orphan_citations(), check_reference_citations() (+30 more)

### Community 41 - "test_table_keep_together.py"
Cohesion: 0.12
Nodes (30): _apply_caption_keep_next(), apply_table_keep_together(), _ensure_keep_next(), _ensure_trpr(), _ensure_trpr_child(), _para_style(), _para_text(), _Element (+22 more)

### Community 42 - "test_sam_fixes_validator_rules.py"
Cohesion: 0.12
Nodes (29): app_services, _add_style(), parametrize, D-01 Phase 2 evidence tests: one test per validator rule id, proving the…, FP006 fixed by S._apply_missing_keywords_stub (tracked change)., FP011 fixed by S._apply_abstract_plan (tracked change)., STY003 fixed by S._apply_body_and_reference_style_fixes (tracked style change)., STY004 fixed by S._apply_body_and_reference_style_fixes (tracked style change). (+21 more)

### Community 43 - "table_page_breaks.py"
Cohesion: 0.20
Nodes (26): apply_table_page_breaks(), _cell_text(), _make_page_break_paragraph(), _page_break_anchor(), _para_has_page_break(), _para_style(), _para_text(), _preceded_by_page_break() (+18 more)

### Community 44 - "jutlp_articles.py"
Cohesion: 0.18
Nodes (25): _abstract_candidates(), _article_details_url(), _clean_abstract_candidate(), _clean_text(), _extract_abstract(), _extract_article_urls(), _extract_author(), _extract_title() (+17 more)

### Community 45 - "LLMError"
Cohesion: 0.14
Nodes (19): call_llm(), call_llm_json(), get_client(), LLMError, Exception, Raised when the LLM call fails after retries., Create an OpenAI client., Send a structured-output request to the OpenAI Chat Completions API. Returns… (+11 more)

### Community 46 - "_remove_tracked_property_change"
Cohesion: 0.30
Nodes (12): _apply_body_run_format(), _apply_tracked_body_format_fixes(), _apply_tracked_body_paragraph_format(), _apply_tracked_body_run_format(), _apply_tracked_table_cell_borders(), _apply_tracked_table_properties(), _copy_properties_without_change(), _find_or_make_child() (+4 more)

### Community 47 - "strip_leading_section_number"
Cohesion: 0.33
Nodes (11): _canonical_index(), _collect_until(), compare_document_styles(), compare_template_and_document(), extract_headings(), extract_template_styles(), _find_first_text(), _front_page_limit() (+3 more)

### Community 48 - "test_copyeditor_comment_regressions.py"
Cohesion: 0.20
Nodes (21): Renumber visible Author Query labels after every comment pass has run., _renumber_final_author_queries(), apply_au_spelling_corrections(), Scan every eligible paragraph and apply AU spelling tracked changes. Returns…, _make_comment_element(), _accepted_visible_text(), _assert_no_visible_timestamp(), _comment_text() (+13 more)

### Community 49 - "_to_title_case_title"
Cohesion: 0.07
Nodes (32): authorFound(), _collect_quote_formatting_issues(), _count_title_words(), _extract_quoted_segments(), _find_anchor_above(), _find_content_authors(), _fix_au_spellings_in_text(), _has_known_title() (+24 more)

### Community 50 - "extract_references"
Cohesion: 0.15
Nodes (13): extract_references(), _get_style_name(), Return ``(start_index, end_index)`` bounding the References section. ``start``…, Two-tier reference selection used by BOTH extraction and comment anchoring so…, _references_window(), _select_reference_entries(), _build_docx_with_sections(), A paper with reference-styled paragraphs but NO References heading still has… (+5 more)

### Community 51 - "cli_copybot.py"
Cohesion: 0.23
Nodes (17): _heading_level_1_sections(), _is_generic_copyedit_output(), main(), _print_heading_normalization_summary(), Path, _rename_generic_copyedit_output(), _show_heading_level_1_sections(), _status() (+9 more)

### Community 52 - "apply_table_n_notation_comments"
Cohesion: 0.16
Nodes (20): apply_table_n_notation_comments(), _is_capital_n_header(), _iter_text_runs(), _Element, Yield (run_el, text) for runs we may safely anchor a comment on., True when the paragraph is a table cell whose only content is "N"., Emit one comment per table column header that is a bare capital "N". Returns…, _comment_texts() (+12 more)

### Community 53 - "TestFiveFailuresFiveComments"
Cohesion: 0.10
Nodes (8): has_comments_content_type(), has_comments_relationship(), Return ordered list of (text, has_ins, [commentRangeStart ids]) for every…, The combined 'Results and Discussion' fixture has no standalone Discussion…, SEC005 + DIS001-003 comments anchor inside the inserted Discussion stub, NOT on…, The inserted Discussion stub sits after Results and before References in…, TestFiveFailuresFiveComments, TestOneFailureOneComment

### Community 54 - "body_llm_edits.py"
Cohesion: 0.10
Nodes (24): _body_paragraphs(), build_body_edit_plan(), _dedupe_edits(), _fix_au_spellings(), _is_skippable_paragraph(), _llm_edits_for_paragraph(), LLM-generated surgical copy-edits for the document body. Produces tracked-…, Return the symmetric token difference between ``find`` and ``replace``. Tokens… (+16 more)

### Community 55 - "test_upload_guardrails.py"
Cohesion: 0.19
Nodes (13): io, pytest, _client(), _poll_until_final(), Tests for the upload guardrails added to app.main: 1. Whole-document word-count…, A pipeline that stalls without ever calling progress still flips the session to…, Poll /api/results until it returns a non-202 (final) response., A pipeline that keeps calling progress past the deadline is aborted at the next… (+5 more)

### Community 56 - "_make_comment_element"
Cohesion: 0.13
Nodes (26): _make_comment_element(), is_in_table(), is_list_item(), _Element, Return True if ``para_el`` has a ``<w:tbl>`` ancestor. Used by prose-…, Return True if ``para_el`` carries a list-numbering reference. Word marks…, Return True when a prose-development check should ignore this paragraph.…, should_skip_prose_paragraph() (+18 more)

### Community 57 - "apply_reference_order_comments"
Cohesion: 0.17
Nodes (20): _anchor_comment_on_paragraph(), apply_reference_order_comments(), _build_comment(), _find_references_heading(), _first_inversion(), _passthrough(), _Element, Comment on a reference list that is not alphabetically ordered. Comment-only —… (+12 more)

### Community 58 - "test_acronym_api.py"
Cohesion: 0.10
Nodes (8): client(), gated_client(), fixture, Smoke tests for the acronym admin HTTP endpoints. Skipped when Flask isn't…, Read-only access stays open so the pipeline can still load the list., Boot the Flask app with auth disabled and the store pointed at tmp., Boot the app with the editor-password gate enabled., test_gated_get_still_open_when_not_authed()

### Community 59 - "_apply_phrase_correction"
Cohesion: 0.15
Nodes (13): _anchor_visible_span(), apply_grammar_corrections(), _apply_phrase_correction(), _find_phrase_in_runs(), _Element, Return (run_el, text) for every plain run (not inside del/ins)., Locate *phrase* in the concatenated run texts. Returns (run_start_idx,…, Replace *original* phrase in para_el with del+ins tracked changes. Returns the… (+5 more)

### Community 60 - "run_editorial_review"
Cohesion: 0.09
Nodes (35): EditorialNote, EditorialReviewResult, LLM verdict on a single deterministic structural check result., StructuralValidation, Run LLM-based editorial review on a JUTLP manuscript. Pipeline: 1. Parse DOCX…, run_editorial_review(), _strip_internal_markers(), build_editorial_review_comment_plan() (+27 more)

### Community 61 - "test_abstract_length_rule.py"
Cohesion: 0.18
Nodes (19): estimate_line_count(), Estimate how many rendered lines ``text`` occupies. Takes the larger of the…, check_abstract(), _fp008(), _long_abstract_doc(), _parsed(), Tests for the JUTLP abstract length rule: the abstract must fit lines 7–23 of…, The body (after Introduction) must not be swallowed into the abstract. (+11 more)

### Community 62 - "_normalise_heading_text"
Cohesion: 0.08
Nodes (29): _apply_heading_center_alignment(), build_front_page_asset_check_plan(), _collect_relationship_ids(), _collect_required_section_issues(), _element_has_textbox(), _find_combined_results_discussion_index(), _find_first_non_empty_index(), _find_heading1_index() (+21 more)

### Community 63 - "reference_type_checker.py"
Cohesion: 0.19
Nodes (18): _check_book(), _check_book_chapter(), _check_conference(), _check_dataset(), _check_journal(), _check_podcast(), check_reference_type_style(), _check_report() (+10 more)

### Community 64 - "test_acronym_corrections.py"
Cohesion: 0.24
Nodes (11): _format_author_query_text(), _matches_definition(), Attempt to align ``letters`` against the leading section of ``words``. Walks…, If `words` contain a valid full form for `acro`, return the phrase. Walks the…, _try_match_definition(), Tests for acronym detection + consolidated comment + tracked-change rewrites., test_acronym_author_query_comment_text_is_numbered(), test_matches_definition_rejects_non_initialism() (+3 more)

### Community 65 - "docx"
Cohesion: 0.25
Nodes (16): build_output_filename(), build_output_filename_from_author_line(), _first_author_last_name(), _get_author_line_and_markers(), _get_document_year(), _remove_superscript_runs_from_author_line(), _unique_output_filename(), datetime (+8 more)

### Community 66 - "abstractFound"
Cohesion: 0.10
Nodes (23): abstractFormatCheck(), abstractFound(), _apply_abstract_plan(), _apply_missing_practitioner_stub(), _apply_tracked_style_fixes(), _build_missing_abstract_components_message(), _check_abstract_components_with_llm(), _direct_space_after_is_zero() (+15 more)

### Community 67 - "test_reference_checker.py"
Cohesion: 0.23
Nodes (9): check_text_dois(), DOIT: Validate every DOI-shaped substring found in the plain text of each…, _cr_item(), Return a fake ``_lookup_doi`` that resolves DOIs from a dict. ``None`` value…, A reference that quotes the same DOI twice (bare + URL form) should only hit…, _stub_lookup(), TestCheckTextDOIs, _spy() (+1 more)

### Community 68 - "apply_decimal_corrections"
Cohesion: 0.40
Nodes (9): apply_decimal_corrections(), Run both decimal checks over ``input_path`` and write to ``output_path``.…, _make_doc(), test_body_sentence_mentioning_references_is_not_boundary(), test_decimal_checks_skip_unstyled_acknowledgements_and_refs(), test_number_words_skip_unstyled_references_section(), test_unstyled_intro_and_reference_aliases_set_zones(), test_unstyled_references_without_intro_starts_as_body_then_exits() (+1 more)

### Community 69 - "now_sydney_iso"
Cohesion: 0.19
Nodes (13): now_sydney_iso(), Shared timestamp helper for Word comments and tracked changes. Word stores the…, Return the current time as an ISO-8601 string with the Sydney offset. Example:…, _sydney_tz(), Tests for the shared Sydney-time stamp helper. Word comments and tracked…, Sydney is UTC+10 (standard) or UTC+11 (daylight saving). If the tz database is…, Second precision only — keeps the stamp tidy and matches the previous format's…, Regression: the old format ended in 'Z' (UTC). The new one must not. (+5 more)

### Community 70 - "_read_doc_root"
Cohesion: 0.15
Nodes (13): Five problematic acronyms still produce exactly one Word comment., Allow-listed acronyms still need a first-use introduction in the body. A…, First body use is rewritten as 'full term (ACRO)', not just 'full term'., The single comment range wraps the first issue's location., Acronyms in the manuscript title produce NO issue at all — no bullet in the…, Crucially, ignoring the title must NOT cause the title's acronym to pre-…, _read_doc_root(), test_allow_listed_acronym_in_body_flagged_when_not_introduced() (+5 more)

### Community 71 - "test_output_generation.py"
Cohesion: 0.17
Nodes (14): _canonical_insert_index(), _next_h1_after(), _heading_para_index(), _para_style_val(), _para_text(), Return the pStyle val used by existing Heading-1 paragraphs. Documents vary:…, Index within ``all_paras`` of the Heading-1 paragraph that IS ``section``…, Return the index within ``all_paras`` to insert the stub for ``section``. Place… (+6 more)

### Community 73 - "_iter_paren_citations"
Cohesion: 0.20
Nodes (7): _iter_paren_citations(), Yield ``(surname, year)`` tuples for every parenthetical citation. Handles…, Coverage for the multi-citation parenthesis parser., The reported bug: a four-citation paren block produced ZERO matches because the…, APA disambiguators like ``2020a`` must survive., A `(see ...)` aside without a Surname,Year pair must yield nothing — even…, TestParenCitationIterator

### Community 74 - "apply_table_section_boundary_comments"
Cohesion: 0.22
Nodes (21): apply_table_section_boundary_comments(), _iter_text_runs(), _Element, First meaningful block: a table (skipping leading caption/blank) → it, prose →…, Last meaningful block: a table (skipping trailing note/blank) → it, prose →…, Comment on sections that open and/or close directly with a table. Returns…, Yield (run_el, text) for runs we may safely anchor a comment on., _section_closer() (+13 more)

### Community 75 - "_apply_tracked_style_change"
Cohesion: 0.27
Nodes (13): _apply_tracked_style_change(), Remove direct formatting that would override a heading style. A paragraph that…, _strip_conflicting_direct_format_for_heading(), _body_para(), _ppr(), A body paragraph restyled to a heading must shed its body formatting. When the…, Only size/spacing are stripped — bold stays (headings are bold anyway)., Restyling to the reference style must NOT strip the run size — only heading… (+5 more)

### Community 76 - "_find_next_action"
Cohesion: 0.24
Nodes (10): _find_next_action(), _get_style_name(), _has_corrected_form_in_tracked_ins(), _iter_text_runs(), _process_paragraph(), _Element, Return True if a sibling ``<w:ins>`` already supplies ``comma_value`` with the…, Return ``(run_el, start, end, check_kind, message, value)`` for the earliest… (+2 more)

### Community 77 - "_make_textbox_wrap_around_text"
Cohesion: 0.29
Nodes (12): _make_textbox_wrap_around_text(), Make a front-page floating textbox use *square* text-wrapping so the…, _anchor_para(), _Element, The front-page editorial textbox must wrap text around it, not overlay it. The…, Schema order: the wrap element must precede docPr in the anchor., test_behinddoc_is_cleared(), test_breathing_margins_added() (+4 more)

### Community 78 - "_normalise_surname"
Cohesion: 0.27
Nodes (5): _normalise_surname(), Lowercase, strip accents, punctuation, and possessive 's for fuzzy match.…, Return ``(normalised_surname, display_surname)`` for a reference entry, or None…, _sort_key_and_label(), TestNormaliseSurname

### Community 79 - "_read_comments_root"
Cohesion: 0.22
Nodes (11): _comment_visible_text(), _Element, Concatenate every ``<w:t>`` text under the comments root., When the author DID introduce the acronym in the body, no issue fires., Allow-listed acronyms in the abstract are silent — no flagging., When a track change is proposed, the bullet mentions it so the editor knows…, _read_comments_root(), test_abstract_allow_listed_silent() (+3 more)

### Community 80 - "generate_keywords"
Cohesion: 0.14
Nodes (24): _build_user_prompt(), _clean_one(), _dedupe_case_insensitive(), generate_keywords(), _is_acceptable(), LLM-driven keyword generation for manuscripts missing a Keywords section.…, Strip surrounding whitespace and quotes; collapse internal whitespace., Return up to ``_MAX_KEYWORDS`` keyword candidates for the manuscript. Best-… (+16 more)

### Community 81 - "output_generation.py"
Cohesion: 0.11
Nodes (23): _append_author_query_runs(), _append_validation_summary(), _author_query_parts(), _comment_group_key(), _dedupe_pending_comments(), _extract_field(), _format_summary_line(), _group_pending_comments() (+15 more)

### Community 83 - "reference_indent_corrections.py"
Cohesion: 0.13
Nodes (23): _already_correct(), apply_reference_indent_corrections(), _is_heading(), _resolved_name(), _build_style_hanging_map(), _resolve(), _build_style_name_map(), _Element (+15 more)

### Community 85 - "docx"
Cohesion: 0.27
Nodes (10): _ensure_normal_style_body_rpr(), _passthrough_copy(), Pin the body font + size on the Normal style's run properties. The template's…, docx, _doc_with_normal(), _normal_rpr(), Tests for body-font enforcement: the Normal style must carry Arial 11pt so…, A docx whose Normal style is a non-template font/size. (+2 more)

### Community 86 - "_extract_ref_author_part"
Cohesion: 0.17
Nodes (6): _extract_ref_author_part(), _normalise_text(), Return the author/group-author portion of a reference entry. Slices everything…, Replace curly quotes with their straight ASCII equivalents., TestCitationRegexes, TestExtractRefAuthorPart

### Community 87 - "TestPresentUnstyledDiscussionNoStub"
Cohesion: 0.31
Nodes (4): A Discussion section that is present but not yet Heading-1 styled (the author…, No tracked-inserted 'Discussion' heading paragraph should exist., The Discussion-subsection comment must anchor on the original (non-inserted)…, TestPresentUnstyledDiscussionNoStub

### Community 88 - "check_submitted_hyperlinks"
Cohesion: 0.22
Nodes (9): check_submitted_hyperlinks(), _extract_ref_hyperlinks(), _is_appendix_heading(), _lookup_doi(), Return (entry_num, ref_text, url) for reference entries that already have a…, Query CrossRef by DOI and return the work item, or None on failure., HREF: Verify that user-submitted hyperlinks point to the cited work. For each…, parametrize (+1 more)

### Community 89 - "results"
Cohesion: 0.11
Nodes (17): is_sam_fixed(), Reporting ownership: which layer reports each validation finding. A finding…, True when Sam's builder fixes this validator rule, so no other layer should…, _build_changes_made(), _build_summary(), _count_sam_changes(), _dedup_sam_issues(), _llm_notes_to_results() (+9 more)

### Community 90 - "_ref_surname_keys"
Cohesion: 0.36
Nodes (4): Return every normalised surname-key a reference can plausibly match. For person…, _ref_surname_keys(), Person refs (with a comma) must NOT have an acronym alias generated — otherwise…, TestRefSurnameKeys

### Community 91 - "check_method_subsections"
Cohesion: 0.15
Nodes (10): check_discussion_subsections(), check_method_subsections(), _extra_subheadings(), _looks_like_subheading(), True if ``text`` is plausibly a subheading, not a mis-styled body line. Mirrors…, Return heading-like found subheadings that match no required subsection (or…, Method/Discussion subheadings that aren't in the template's expected set are…, TestDiscussionSubsectionsWithAliases (+2 more)

### Community 92 - "inspect_abstract.py"
Cohesion: 0.29
Nodes (5): get_comment_anchors(), get_ref_entries(), Inspect the processed output vs the original to find comment placement issues., Map comment id -> paragraph text snippet where the anchor sits., Return numbered reference entries from the document.

### Community 93 - "_ensure_template_styles_available"
Cohesion: 0.12
Nodes (21): _apply_citation_plan(), _apply_intro_page_break(), citationFormatCheck(), _ensure_template_styles_available(), _load_template_style_names(), _make_footer_citation_paragraph(), _move_body_citation_to_footer(), _patch_footer_content_type() (+13 more)

### Community 94 - "TestValidDoc"
Cohesion: 0.31
Nodes (3): fixture, rules(), TestValidDoc

### Community 95 - "Gurman — Sprint 2 Wiring Tasks (Frontend ↔ Backend Reference)"
Cohesion: 0.13
Nodes (16): ProcessingCancelled, ProcessingTimeout, Exception, _run(), _pipeline(), _update_progress(), Artifacts, Backend truth (verified against `app/main.py`, `app/static/script.js`) (+8 more)

### Community 96 - "Path"
Cohesion: 0.29
Nodes (7): _build_docx(), _build_docx_with_inserted_run(), Path, The scanner must read text inside ``<w:ins>`` runs — that's what upstream…, Build a minimal docx with one paragraph per supplied text., Build a docx where each entry is ``(style, text, inside_ins)``. When…, test_acronyms_inside_inserted_runs_are_detected()

### Community 97 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 98 - "apply_acronym_corrections"
Cohesion: 0.12
Nodes (16): apply_acronym_corrections(), Run the full acronym pass against ``input_path``, writing to ``output_path``.…, An introduction in the abstract does NOT satisfy the body's first-use rule., Conversely, text inside ``<w:del>`` represents tracked deletions — content the…, Block-listed tokens (USA, OK, NASA, iOS, …) never produce issues even when bare…, A novel acronym sitting next to block-listed tokens still fires., The abstract is an independent zone and needs its OWN introduction. An acronym…, If the docx already has comments from earlier passes, the new one gets the next… (+8 more)

### Community 99 - "test_jutlp_validator.py"
Cohesion: 0.17
Nodes (15): check_combined_results_discussion(), check_dot_points(), check_section_order(), canonical_index(), _matches_section(), True if heading_text matches canonical or any alias, exactly or as a prefix-…, Flag bullet/numbered list paragraphs — continuous prose is expected in JUTLP., docx_oxml (+7 more)

### Community 101 - "permission"
Cohesion: 0.08
Nodes (24): git diff *, git log *, git status *, pip install *, pytest *, python *, python3 *, ruff check * (+16 more)

### Community 102 - "session_manager.py"
Cohesion: 0.23
Nodes (16): create_app(), Background thread that prunes expired session files every 5 minutes (D-06/D-07)., start_session_sweeper(), _sweep_loop(), start_session_sweeper(), _sweep_loop(), delete_session(), _delete_session_unlocked() (+8 more)

### Community 107 - "test_reporting_ownership.py"
Cohesion: 0.17
Nodes (8): app_domain, glob, _all_emitted_rule_ids(), _family(), Contract tests for reporting ownership (D-01 remediation, Phase 1). Every…, TestFamilyVerdictsCoverEverything, TestSamFixedIdsAreReal, TestSingleSource

### Community 108 - "Gurman — Data / Endpoint Tasks (Source of Truth)"
Cohesion: 0.15
Nodes (12): Backend truth (current codebase), G-01 — Endpoint inventory + contract doc (P0, unblocks H-01/H-02), G-02 — Upload + validation error-code map (P0, pairs H-02), G-03 — Processing poll/state machine + Cancel/timeout + carousel (P0, pairs H-03), G-04 — Results payload shape (P1, pairs H-04), G-05 — Download + retry semantics (P1, pairs H-05 — answers Humaid's open question), G-06 — Support/error passthrough (P2, pairs H-07), G-07 — Handoff: frontend data layer + open-questions log (P2, pairs H-01/Z-09) (+4 more)

### Community 110 - "_split_run_for_action"
Cohesion: 0.20
Nodes (10): Replace the run with (before | comment-anchored content | after). When…, _split_run_for_action(), _anchor_flag(), _iter_text_runs(), _Element, Yield (run_element, text) for body-text runs we may safely modify. Mirrors the…, Locate ``original`` inside ``para_el`` and wrap it in a comment range. Returns…, apply_spell_corrections() (+2 more)

### Community 111 - "_find_word_anchor"
Cohesion: 0.50
Nodes (5): _find_word_anchor(), _iter_text_runs(), _Element, Yield (run, text) for body runs not inside tracked-change wrappers., Locate the first occurrence of ``word`` (case-sensitive, word-bounded) in the…

### Community 112 - "_accepted_paragraph_text"
Cohesion: 0.50
Nodes (4): _accepted_paragraph_text(), True if ``run_el`` should NOT contribute to ``para_p``'s text. Walks up to the…, Return a paragraph's *own* text as if all tracked changes were accepted.…, _run_skipped()

### Community 113 - "test_language_corrections.py"
Cohesion: 0.21
Nodes (11): Return one summary entry per repeated spelling correction. The tracked-change…, summarize_spelling_correction_repeats(), _docx_xml(), An unquoted US spelling in the same paragraph as a quoted one must still be…, A US-spelled word INSIDE quoted text must NOT be rewritten — direct quotations…, test_generalizability_is_changed_to_australian_spelling(), test_repeated_spelling_fix_gets_one_author_query_comment(), test_spelling_summary_groups_case_variants_of_same_fix() (+3 more)

### Community 114 - "_make_comment_element"
Cohesion: 0.20
Nodes (12): add_document_summary_comment(), add_paragraph_comment(), _make_comment_element(), _patch_content_types(), _patch_rels(), Ensure `document.xml.rels` contains the comments relationship., Ensure `[Content_Types].xml` declares `word/comments.xml`., Attach a single document-level Word comment to the first body paragraph. Used… (+4 more)

### Community 115 - "vercel.json"
Cohesion: 0.50
Nodes (3): builds, routes, version

### Community 116 - "read_docx"
Cohesion: 0.67
Nodes (3): Document, Path, read_docx()

### Community 118 - "_collect_discussion_subheading_issues"
Cohesion: 0.23
Nodes (12): _ack_contains(), _all_alias_norms(), _collect_acknowledgements_issues(), _collect_discussion_subheading_issues(), _collect_method_subheading_issues(), _collect_results_reference_issues(), _find_next_heading1_index(), _matches_required_subsection() (+4 more)

### Community 119 - "_is_deidentified_manuscript"
Cohesion: 0.23
Nodes (12): _is_deidentified_manuscript(), Return True if the manuscript was deliberately stripped of identity. Three…, _make_deid_state(), Minimal abstract_state stub — the deidentified check only reads docxpath., Plain `[Authors removed for blind review]` placeholder anywhere in the front-…, The placeholder regex covers the 'Affiliations removed' phrasing too., A manuscript that genuinely lacks affiliations (but has authors and no…, test_deidentified_detected_by_affiliations_removed_placeholder() (+4 more)

### Community 120 - "get_section_bounds"
Cohesion: 0.25
Nodes (10): get_section_bounds(), _is_main_section_heading(), True for a real ``Heading 1`` paragraph OR a non-empty paragraph whose text…, True if ``text`` is exactly a JUTLP main-section name or alias. Matching is…, _text_matches_main_section(), _doc(), Regression tests for section/subsection detection on numbered or aliased…, test_present_subsection_not_flagged_missing() (+2 more)

### Community 121 - "parse_docx"
Cohesion: 0.24
Nodes (10): count_styles(), _generic_sections(), _heading_level(), parse_docx(), Return 1/2/3/4 for 'Heading N' styles, else None., Return the heading level used most often in the document to split the document…, Section boundaries based on which heading level is the documents top level — no…, _top_heading_level() (+2 more)

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

### Community 127 - "_should_replace"
Cohesion: 0.40
Nodes (5): _in_any_span(), _is_sentence_start(), True if position is at the start of a sentence. "Start of sentence" = beginning…, Apply the deny-list of contexts. Return True only when safe to replace., _should_replace()

### Community 128 - "applyFile"
Cohesion: 0.50
Nodes (4): applyFile(), checkReadable(), onFileDropped(), onFileSelected()

### Community 129 - "resetToUpload"
Cohesion: 0.50
Nodes (4): continueWithoutDownloading(), requestProcessAnother(), resetToUpload(), retryProcessing()

### Community 130 - "_iter_text_runs"
Cohesion: 0.67
Nodes (3): _iter_text_runs(), _Element, Yield (run_el, text) for runs we may safely anchor a comment on.

### Community 131 - "_spelling_summary_comment_text"
Cohesion: 0.67
Nodes (3): Build one Word comment for all AU spelling replacements., _spelling_comment_text(), _spelling_summary_comment_text()

### Community 132 - "downloadUrl"
Cohesion: 0.67
Nodes (3): downloadUrl(), downloadFirst(), downloadManuscript()

## Knowledge Gaps
- **76 isolated node(s):** `$schema`, `plugin`, `instructions`, `read`, `edit` (+71 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 947 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_paragraphs()` connect `load_paragraphs` to `output_generation_samfix.py`, `validate`, `test_front_page_style_fixes.py`, `test_sentence_coherence_corrections.py`, `main.py`, `document_analysis_services.py`, `_apply_author_plan`, `test_heading_corrections.py`, `get_comment_anchor_texts`, `test_spell_checker.py`, `keywordsFound`, `feedback_gen_pipeline.py`, `test_grammar_corrections.py`, `build_prompts`, `reference_checker.py`, `strip_leading_section_number`, `_to_title_case_title`, `extract_references`, `body_llm_edits.py`, `run_editorial_review`, `test_abstract_length_rule.py`, `docx`, `abstractFound`, `test_reference_checker.py`, `output_generation.py`, `_accepted_paragraph_text`, `get_section_bounds`, `parse_docx`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `validate()` connect `validate` to `test_jutlp_validator.py`, `load_paragraphs`, `test_sam_fixes_validator_rules.py`, `test_reporting_ownership.py`, `doc_analysis_pipeline`, `output_generation.py`, `get_comment_anchor_texts`, `rules`, `TestFiveFailuresFiveComments`, `get_section_bounds`, `check_method_subsections`, `run_editorial_review`, `test_abstract_length_rule.py`, `feedback_gen_pipeline.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `doc_analysis_pipeline()` connect `doc_analysis_pipeline` to `validate`, `test_front_page_style_fixes.py`, `main.py`, `test_document_normalisation.py`, `test_abbreviation_corrections.py`, `run_font_corrections.py`, `test_heading_corrections.py`, `get_comment_anchor_texts`, `pathlib`, `_anchor_paragraph_comment`, `test_appendix_removal.py`, `feedback_gen_pipeline.py`, `reference_format_corrections.py`, `apply_number_word_corrections`, `reference_checker.py`, `test_table_keep_together.py`, `table_page_breaks.py`, `test_copyeditor_comment_regressions.py`, `apply_table_n_notation_comments`, `_make_comment_element`, `apply_reference_order_comments`, `run_editorial_review`, `apply_decimal_corrections`, `apply_table_section_boundary_comments`, `reference_indent_corrections.py`, `Gurman — Sprint 2 Wiring Tasks (Frontend ↔ Backend Reference)`, `apply_acronym_corrections`, `_split_run_for_action`, `_make_comment_element`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **What connects `$schema`, `plugin`, `instructions` to the rest of the system?**
  _76 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `output_generation_samfix.py` be split into smaller, more focused modules?**
  _Cohesion score 0.039991754277468566 - nodes in this community are weakly interconnected._
- **Should `_build_zoned_docx` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._
- **Should `validate` be split into smaller, more focused modules?**
  _Cohesion score 0.10365853658536585 - nodes in this community are weakly interconnected._