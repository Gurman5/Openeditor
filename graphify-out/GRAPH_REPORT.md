# Graph Report - Openeditor  (2026-09-29)

## Corpus Check
- 142 files · ~173,049 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 3, .css 2, .example 1)

## Summary
- 2836 nodes · 6838 edges · 119 communities (108 shown, 11 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 95 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c9aba5a0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- output_generation_samfix.py
- apply_acronym_corrections
- jutlp_validator.py
- documentBodyFormatCheck
- language_corrections.py
- test_body_llm_edits.py
- test_sentence_coherence_corrections.py
- load_paragraphs
- main.py
- document_analysis_services.py
- test_document_normalisation.py
- test_abbreviation_corrections.py
- reference_reconstructor.py
- doc_analysis_pipeline
- run_font_corrections.py
- test_front_page_style_fixes.py
- build_edited_document
- get_comment_anchor_texts
- apply_caption_apa7_comments
- rules
- _Element
- test_access_validation.py
- openeditor.js
- _apply_missing_practitioner_stub
- test_spell_checker.py
- _anchor_paragraph_comment
- test_appendix_removal.py
- _make_comment_element
- keywordsFound
- Frontend-Backend API Contract
- feedback_gen_pipeline.py
- test_decimal_corrections.py
- document_zones.py
- script.js
- acronym_store.py
- narrative_citation_corrections.py
- build_prompts
- apply_number_word_corrections
- _find_target_para_index
- _validate_edit
- reference_checker.py
- test_table_keep_together.py
- generate_commented_docx
- table_page_breaks.py
- jutlp_articles.py
- LLMError
- _apply_tracked_table_formatting
- strip_leading_section_number
- test_copyeditor_comment_regressions.py
- _to_title_case_title
- extract_references
- cli_copybot.py
- apply_table_n_notation_comments
- TestFiveFailuresFiveComments
- _llm_edits_for_paragraph
- test_upload_guardrails.py
- apply_short_paragraph_comments
- apply_reference_order_comments
- test_acronym_api.py
- grammar_corrections.py
- run_editorial_review
- test_abstract_length_rule.py
- _normalise_heading_text
- reference_type_checker.py
- test_acronym_corrections.py
- docx
- body_llm_edits.py
- test_reference_checker.py
- number_word_corrections.py
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
- TestOneFailureOneComment
- output_generation.py
- inspect_original_refs.py
- _heading_para_index
- subsection_alias_match
- test_body_font_enforcement.py
- _normalise_text
- TestPresentUnstyledDiscussionNoStub
- _is_appendix_heading
- _extract_ref_author_part
- _ref_surname_keys
- test_reference_justification.py
- inspect_abstract.py
- _apply_intro_page_break
- TestValidDoc
- upload
- Path
- graphify.js
- _apply_mutations
- _llm_notes_to_results
- setup.sh
- opencode.json
- app/__init__.py
- copybot
- _find_appendix_start
- _apply_tracked_edit
- check_entry_author
- _anchor_flag
- _find_word_anchor
- _accepted_paragraph_text
- _corrected_heading
- TestNonTemplateSubheadingComment
- vercel.json
- read_docx
- deployment.md
- test_discussion_required_section_passes_when_unstyled

## God Nodes (most connected - your core abstractions)
1. `load_paragraphs()` - 91 edges
2. `build_edited_document()` - 53 edges
3. `validate()` - 49 edges
4. `apply_acronym_corrections()` - 41 edges
5. `generate_commented_docx()` - 41 edges
6. `doc_analysis_pipeline()` - 40 edges
7. `ParagraphRecord` - 39 edges
8. `documentBodyFormatCheck()` - 36 edges
9. `iter_paragraphs_with_zone()` - 29 edges
10. `apply_number_word_corrections()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `Results Status Mapping` --semantically_similar_to--> `Four-Stage Manuscript Workflow`  [INFERRED] [semantically similar]
  docs/api-contract.md → app/templates/writer.html
- `Client-Side Manuscript Validation` --semantically_similar_to--> `Upload Limit Mismatch`  [INFERRED] [semantically similar]
  app/templates/writer.html → docs/api-contract.md
- `test_strip_leading_number_variants()` --calls--> `strip_leading_section_number()`  [EXTRACTED]
  tests/test_heading_corrections.py → app/domain/canonical_jultp_template.py
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

## Communities (119 total, 11 thin omitted)

### Community 0 - "output_generation_samfix.py"
Cohesion: 0.04
Nodes (95): _append_author_query_runs(), _apply_citation_plan(), _author_query_parts(), authorFormatCheck(), _body_alignment_ok(), _body_font_ok(), _body_indent_ok(), _body_line_spacing_ok() (+87 more)

### Community 1 - "apply_acronym_corrections"
Cohesion: 0.08
Nodes (36): apply_acronym_corrections(), Run the full acronym pass against ``input_path``, writing to ``output_path``.…, _build_zoned_docx(), An introduction in the abstract does NOT satisfy the body's first-use rule., Truly unknown acronyms in the abstract (no allow-list, no inline def anywhere)…, Block-listed tokens (USA, OK, NASA, iOS, …) never produce issues even when bare…, If the editor adds a well-known org (e.g. NASA) to the allow-list, the block-…, OECD and UNESCO are on the client's approved-acronyms list — bare body use… (+28 more)

### Community 2 - "jutlp_validator.py"
Cohesion: 0.06
Nodes (62): build_report(), check_abstract_single_paragraph(), check_block_quote_style(), check_body_paragraph_styles(), check_combined_results_discussion(), check_conclusion_length(), check_discussion_subsections(), check_dot_points() (+54 more)

### Community 3 - "documentBodyFormatCheck"
Cohesion: 0.09
Nodes (33): _append_body_comment(), _apply_document_body_plan(), _collect_dot_point_issues(), _collect_numbered_author_placeholder_issues(), _collect_required_section_issues(), _collect_table_figure_labels(), documentBodyFormatCheck(), documentBodyFound() (+25 more)

### Community 4 - "language_corrections.py"
Cohesion: 0.08
Nodes (45): apply_citation_formatting_corrections(), _apply_corrections_to_para(), _Element, Insert missing space after p. / pp. in in-text page references. APA style…, Add a space after p./pp. before page numbers as tracked changes. Returns…, _apply_corrections_to_para(), apply_et_al_corrections(), _corrected_bracket() (+37 more)

### Community 5 - "test_body_llm_edits.py"
Cohesion: 0.16
Nodes (19): _apply_body_and_reference_style_fixes(), _apply_body_edit_plan(), _apply_intra_paragraph_tracked_replace(), Apply tracked style changes for body and reference paragraphs: - Required body…, docx_oxml, _paragraph_with_runs(), test_body_edit_plan_applies_all_repeated_occurrences_in_paragraph(), test_body_edit_plan_skips_repeated_occurrence_inside_direct_quote() (+11 more)

### Community 6 - "test_sentence_coherence_corrections.py"
Cohesion: 0.06
Nodes (44): find_quote_spans(), is_in_quote(), Return True when the half-open range ``[start, end)`` overlaps any quotation…, Return a list of ``(start, end)`` half-open intervals locating every paired-…, apply_sentence_coherence_corrections(), get_sentence_coherence_flags(), _is_usable_reason(), Call the LLM and return a list of ``{original, reason}`` dicts.… (+36 more)

### Community 7 - "load_paragraphs"
Cohesion: 0.06
Nodes (55): detect_heading_level_1(), extract_main_sections(), extract_subsections(), load_paragraphs(), Scan a .docx file and return its Heading 1 section text and positions., authorFound(), _find_existing_affiliations_for_missing_authors(), _front_page_paragraphs_for_deid() (+47 more)

### Community 8 - "main.py"
Cohesion: 0.05
Nodes (54): _acronym_admin_active(), _acronym_admin_authed(), acronyms_admin_login(), acronyms_admin_logout(), acronyms_admin_page(), add_acronym_api(), analyse_cli(), _body_edit_items() (+46 more)

### Community 9 - "document_analysis_services.py"
Cohesion: 0.08
Nodes (49): Few-shot editorial examples extracted from real JUTLP editor decisions. These…, JUTLP editorial guidelines extracted from 'JUTLP Template 2026.docx'. Last…, ParagraphRecord, _build_system_prompt(), _build_user_prompt(), _canonical_section_for(), _extract_front_page_content(), _find_sections_by_text() (+41 more)

### Community 10 - "test_document_normalisation.py"
Cohesion: 0.08
Nodes (50): Document, Path, read_docx(), _accept_tracked_changes(), _ancestor_paragraph_index(), _delete_guidance_paragraphs(), _is_paragraph_blank(), NormalisationReport (+42 more)

### Community 11 - "test_abbreviation_corrections.py"
Cohesion: 0.08
Nodes (49): apply_abbreviation_corrections(), _find_first_match(), _iter_text_runs(), _overlaps_quote(), _process_paragraph(), _Element, Return the earliest rule-match in ``text`` as ``(start, end, replacement,…, Apply every matching rule in ``para_el``, returning updated ``next_change_id``.… (+41 more)

### Community 12 - "reference_reconstructor.py"
Cohesion: 0.08
Nodes (48): build_apa7_from_crossref(), _build_book(), _build_book_chapter(), _build_dataset(), _build_dissertation(), _build_edited_book(), _build_journal_article(), _build_preprint() (+40 more)

### Community 13 - "doc_analysis_pipeline"
Cohesion: 0.07
Nodes (41): doc_analysis_pipeline(), _has_reference_issue_summary_comment(), _hyperlink_plain_urls_in_refs(), _inject_crossref_doi_links(), _insert_suspicious_ref_comments(), _max_revision_id(), _normalise(), _patch_settings_show_markup() (+33 more)

### Community 14 - "run_font_corrections.py"
Cohesion: 0.07
Nodes (45): _already_correct(), apply_reference_indent_corrections(), _is_heading(), _resolved_name(), _build_style_hanging_map(), _resolve(), _build_style_name_map(), _Element (+37 more)

### Community 15 - "test_front_page_style_fixes.py"
Cohesion: 0.06
Nodes (71): abstractFormatCheck(), abstractFound(), _append_affiliation_before_notes(), _apply_author_plan(), _apply_front_page_asset_plan(), _apply_heading_1_text_normalization(), _apply_heading_2_title_case(), _apply_normal_style_fix() (+63 more)

### Community 16 - "build_edited_document"
Cohesion: 0.11
Nodes (34): apply_heading_corrections(), _build_style_level_map(), _heading_level(), _level_from_name(), Return 1/2/… for a Heading style, or None for non-heading styles. Resolves both…, Strip heading numbers and rename non-canonical section names (tracked). Returns…, Heading level from a style NAME/ID ("Heading 1", "heading1", "Heading")., Map ``styleId -> heading level`` from ``styles.xml``. Documents converted from… (+26 more)

### Community 17 - "get_comment_anchor_texts"
Cohesion: 0.11
Nodes (16): count_comments_in_docx(), get_comment_anchor_texts(), A `DOIT005`-style result should drop a Word comment anchored at reference entry…, `DOIT002_2` (the second DOI inside reference 2) must anchor at the same…, Regression: the pre-existing `HREF***` rule (hyperlink-DOI check) previously…, test_andor_occurrences_are_grouped_into_one_comment(), test_cref_comments_anchor_to_unstyled_reference_entries(), test_doit_comment_anchors_at_correct_reference_entry() (+8 more)

### Community 18 - "apply_caption_apa7_comments"
Cohesion: 0.20
Nodes (20): apply_caption_apa7_comments(), _iter_text_runs(), _Element, Emit one APA 7 caption-split comment per offending paragraph. Returns…, Yield (run_el, text) for runs we may safely anchor a comment on., _build_docx(), Path, Tests for the APA 7 caption-split recommendation pass. A figure or table… (+12 more)

### Community 19 - "rules"
Cohesion: 0.07
Nodes (8): fixture, rules(), TestDeidentifiedWithAuthorLeak, TestFrontPageIssues, TestMissingMethodSubsection, TestStructureAndEndmatterIssues, TestValidDeidentified, TestValidIdentified

### Community 20 - "_Element"
Cohesion: 0.13
Nodes (23): _bracketed_spans(), _build_zone_map(), _collect_inline_definitions(), _find_run_at_offset(), _find_title_paragraph_indices(), _get_style_name(), _in_any_span(), _is_cc_licence_paragraph() (+15 more)

### Community 21 - "test_access_validation.py"
Cohesion: 0.13
Nodes (26): _require_access(), AccessResult, AccessStatus, check_access(), check_local_bypass(), Access validation service — G-07. Defines the authentication contract for…, Single entry point the Flask gate calls. Tries, in order: 1. Local SKIP_AUTH…, SKIP_AUTH must be explicitly 'true' (case-insensitive) — any other value,… (+18 more)

### Community 22 - "openeditor.js"
Cohesion: 0.09
Nodes (26): cancelJob(), CAROUSEL_ENABLED, downloadUrl(), fetchCarouselArticles(), _mapUploadErrorCode(), pollResults(), pollUntilDone(), STAGE_TO_STEP (+18 more)

### Community 23 - "_apply_missing_practitioner_stub"
Cohesion: 0.06
Nodes (43): _append_plain_text_run(), _append_plain_text_run_with_size(), _append_text_with_line_breaks(), _append_text_with_superscript_markers(), _append_tracked_replace(), _apply_abstract_plan(), _apply_style_if_needed(), _flush() (+35 more)

### Community 24 - "test_spell_checker.py"
Cohesion: 0.05
Nodes (65): app_services, _fix_au_spellings(), get_grammar_corrections(), _has_au_us_suffix_swap(), _is_au_to_us_replacement(), _is_proper_noun_correction(), Return True if original looks like a proper noun, surname, acronym, or tech…, Return True if the correction would flip Australian English to American English. (+57 more)

### Community 25 - "_anchor_paragraph_comment"
Cohesion: 0.25
Nodes (9): _anchor_paragraph_comment(), _build_comment(), _classify(), _distinct(), _own_text_runs(), _Element, Detect placeholders in ``para_el`` and, if any, anchor one comment. Returns…, inst' for institution/affiliation placeholders, else 'author'. (+1 more)

### Community 26 - "test_appendix_removal.py"
Cohesion: 0.17
Nodes (24): _is_appendix_heading(), _build_docx(), _comment_texts(), _del_texts(), _p(), _Element, Path, Tests for the appendix-comment pass. JUTLP does not accept appendices: the… (+16 more)

### Community 27 - "_make_comment_element"
Cohesion: 0.12
Nodes (21): _append_author_query_runs(), _author_query_parts(), _build_comment_ref_run(), _find_span(), _inject_comment_markers_for_phrase(), _make_comment_element(), _make_inserted_heading_paragraph(), _Element (+13 more)

### Community 28 - "keywordsFound"
Cohesion: 0.06
Nodes (37): _apply_keywords_plan(), _apply_missing_keywords_stub(), citationFound(), _extract_keywords_list(), _find_abstract_heading_in_front(), _find_blank_line_after_index(), _find_citation_heading_in_front(), _find_introduction_heading_in_front() (+29 more)

### Community 29 - "Frontend-Backend API Contract"
Cohesion: 0.06
Nodes (36): Graphify Knowledge Graph, OAPA Brand Mark, Acronym Management UI, Editor Admin Authentication, Persistent Acronym Storage, Editorial Results Dashboard, JUTLP Article Carousel, Manuscript Upload Workflow (+28 more)

### Community 30 - "feedback_gen_pipeline.py"
Cohesion: 0.08
Nodes (48): # TODO: remove once sections D-G replace these downstream references, Deterministic abbreviation / journal-style fixes emitted as tracked changes.…, _append_author_query_runs(), _author_query_parts(), _make_comment_element(), _patch_content_types(), _patch_rels(), Detect acronym usage problems and emit one consolidated Word comment. Journal… (+40 more)

### Community 31 - "test_decimal_corrections.py"
Cohesion: 0.11
Nodes (28): apply_decimal_corrections(), Run both decimal checks over ``input_path`` and write to ``output_path``.…, _build_docx(), _Element, Path, Tests for the decimal-precision and comma-as-decimal checks., The classic example: thousand separators and comma-decimals together., The example from the client's brief, end-to-end. (+20 more)

### Community 32 - "document_zones.py"
Cohesion: 0.07
Nodes (49): _heading_zone_transition(), Compatibility shim — the shared helper has no ``intro_seen`` arg. The acronym…, _needs_apa7_split(), Return True when the paragraph holds a full single-paragraph figure/table…, get_style_name(), heading_zone_transition(), initial_zone(), is_in_table() (+41 more)

### Community 33 - "script.js"
Cohesion: 0.10
Nodes (28): _activateStep(), _clearPollDelay(), clearUploadError(), displayFile(), fetchJutlpArticles(), finishStepAnimation(), groupItems(), JUTLP_FALLBACK_ARTICLE (+20 more)

### Community 34 - "acronym_store.py"
Cohesion: 0.09
Nodes (32): list_acronyms_api(), add_acronym(), _ensure_file_exists(), load_acronyms(), _load_seed(), Path, Persistent store for the editor-managed acronym allow-list. The list lives as a…, Restore the on-disk store to the bundled seed. Used by tests. (+24 more)

### Community 35 - "narrative_citation_corrections.py"
Cohesion: 0.18
Nodes (23): _apply_corrections_to_para(), apply_narrative_citation_corrections(), _bracket_spans(), _in_any_span(), _plain_text(), _Element, Fix APA narrative citation ampersands as Word tracked changes. APA narrative…, Replace narrative-citation ampersands in one paragraph. (+15 more)

### Community 36 - "build_prompts"
Cohesion: 0.19
Nodes (10): build_prompts(), Build (system_prompt, user_prompt) from parsed document data., _make_paragraphs(), _make_parsed_structure(), Build a minimal set of ParagraphRecord objects for testing., The prompt instructs the LLM to use specific severity labels. Originally…, Regression: sections headed by an ALIAS ("Methodology", "Findings", "Literature…, A titled heading ("Introduction: Background") maps to its canonical section so… (+2 more)

### Community 37 - "apply_number_word_corrections"
Cohesion: 0.12
Nodes (37): _apply_corrections_to_para(), apply_number_word_corrections(), _bracket_spans(), _para_plain_text(), _Element, Return character spans (start, end) covered by paren/bracket/brace pairs.…, Concatenate the run text of `para_el` excluding tracked-change wrappers., Apply digit→word tracked changes to one paragraph, run-by-run. (+29 more)

### Community 38 - "_find_target_para_index"
Cohesion: 0.11
Nodes (31): _find_after(), _find_first_heading(), _find_first_non_empty_para(), _find_front_matter_anchor(), _find_front_matter_rule_anchor(), _find_front_style(), _find_front_text(), _find_heading() (+23 more)

### Community 39 - "_validate_edit"
Cohesion: 0.10
Nodes (21): _validate_edit(), Regression: `Evidences-Based → evidencesbased` slipped past a case-sensitive…, An edit that keeps the hyphen and fixes a real typo must still pass., JUTLP policy: text inside `"..."` retains the source's spelling., Same paragraph, unquoted region: a meaning-preserving edit must still be…, The LLM may not strip a hyphen from a compound word., test_validate_edit_accepts_edits_outside_quotation(), test_validate_edit_accepts_legitimate_hyphen_keeping_edit() (+13 more)

### Community 40 - "reference_checker.py"
Cohesion: 0.13
Nodes (21): call_llm_json(), _check_citation_components_with_llm(), build_reference_report(), _cache_get(), _cache_set(), check_and_report(), _cr_item_summary(), _get_apa_via_content_negotiation() (+13 more)

### Community 41 - "test_table_keep_together.py"
Cohesion: 0.14
Nodes (26): _apply_caption_keep_next(), apply_table_keep_together(), _ensure_keep_next(), _ensure_trpr(), _ensure_trpr_child(), _para_style(), _para_text(), _Element (+18 more)

### Community 42 - "generate_commented_docx"
Cohesion: 0.16
Nodes (10): _dedupe_pending_comments(), generate_commented_docx(), _infer_target_phrase(), _patch_hyperlink_color_styles(), Collapse exact duplicate comments for the same document anchor., Set the Hyperlink character style to black via raw lxml (no python-docx)., Generate a reviewed `.docx` with inline comments and a validation summary page., Guess which phrase inside a paragraph should receive the comment. This gives… (+2 more)

### Community 43 - "table_page_breaks.py"
Cohesion: 0.20
Nodes (26): apply_table_page_breaks(), _cell_text(), _make_page_break_paragraph(), _page_break_anchor(), _para_has_page_break(), _para_style(), _para_text(), _preceded_by_page_break() (+18 more)

### Community 44 - "jutlp_articles.py"
Cohesion: 0.17
Nodes (26): _abstract_candidates(), _article_details_url(), _clean_abstract_candidate(), _clean_text(), _extract_abstract(), _extract_article_urls(), _extract_author(), _extract_title() (+18 more)

### Community 45 - "LLMError"
Cohesion: 0.08
Nodes (39): call_llm(), get_client(), LLMError, Exception, Raised when the LLM call fails after retries., Create an OpenAI client., Send a structured-output request to the OpenAI Chat Completions API. Returns…, _build_user_prompt() (+31 more)

### Community 46 - "_apply_tracked_table_formatting"
Cohesion: 0.07
Nodes (45): _apply_body_run_format(), _apply_heading_center_alignment(), _apply_heading_keep_next(), _apply_table_caption_formatting(), _apply_table_paragraph_style(), _apply_tracked_body_format_fixes(), _apply_tracked_body_paragraph_format(), _apply_tracked_body_run_format() (+37 more)

### Community 47 - "strip_leading_section_number"
Cohesion: 0.16
Nodes (21): _build_section_rename_map(), _merges_two_sections(), _normalise_subsection(), Remove a leading heading number from ``text`` (e.g. "2. Literature" ->…, Lower-case, collapse whitespace, strip a leading heading number and any…, Return the canonical main section a heading fragment names, or None. Matches…, True when ``alias`` merges two *distinct* canonical sections (e.g. "Results and…, ``normalised alias -> canonical label`` for safe heading renames. Built from… (+13 more)

### Community 48 - "test_copyeditor_comment_regressions.py"
Cohesion: 0.09
Nodes (42): Renumber visible Author Query labels after every comment pass has run., _renumber_final_author_queries(), apply_au_spelling_corrections(), Scan every eligible paragraph and apply AU spelling tracked changes. Returns…, Return one summary entry per repeated spelling correction. The tracked-change…, summarize_spelling_correction_repeats(), _apply_editorial_review_comment_plan(), _comment_ids_in_document_order() (+34 more)

### Community 49 - "_to_title_case_title"
Cohesion: 0.07
Nodes (31): _collect_quote_formatting_issues(), _count_title_words(), _extract_quoted_segments(), _find_anchor_above(), _find_content_authors(), _fix_au_spellings_in_text(), _has_known_title(), _has_long_quote() (+23 more)

### Community 50 - "extract_references"
Cohesion: 0.16
Nodes (12): extract_references(), Return ``(start_index, end_index)`` bounding the References section. ``start``…, Two-tier reference selection used by BOTH extraction and comment anchoring so…, _references_window(), _select_reference_entries(), _build_docx_with_sections(), A paper with reference-styled paragraphs but NO References heading still has…, Build a docx from a list of (kind, text) blocks. kind: "h1" → Heading 1, "ref"… (+4 more)

### Community 51 - "cli_copybot.py"
Cohesion: 0.23
Nodes (17): _heading_level_1_sections(), _is_generic_copyedit_output(), main(), _print_heading_normalization_summary(), Path, _rename_generic_copyedit_output(), _show_heading_level_1_sections(), _status() (+9 more)

### Community 52 - "apply_table_n_notation_comments"
Cohesion: 0.16
Nodes (20): apply_table_n_notation_comments(), _is_capital_n_header(), _iter_text_runs(), _Element, Yield (run_el, text) for runs we may safely anchor a comment on., True when the paragraph is a table cell whose only content is "N"., Emit one comment per table column header that is a bare capital "N". Returns…, _comment_texts() (+12 more)

### Community 53 - "TestFiveFailuresFiveComments"
Cohesion: 0.19
Nodes (5): Return ordered list of (text, has_ins, [commentRangeStart ids]) for every…, The combined 'Results and Discussion' fixture has no standalone Discussion…, SEC005 + DIS001-003 comments anchor inside the inserted Discussion stub, NOT on…, The inserted Discussion stub sits after Results and before References in…, TestFiveFailuresFiveComments

### Community 54 - "_llm_edits_for_paragraph"
Cohesion: 0.16
Nodes (12): _dedupe_edits(), _fix_au_spellings(), _llm_edits_for_paragraph(), Replace any US spellings in text with AU equivalents., Return True when the LLM reason is specific enough for display., _reason_identifies_change(), patch, test_body_edit_plan_propagates_accepted_exact_repeat() (+4 more)

### Community 55 - "test_upload_guardrails.py"
Cohesion: 0.21
Nodes (12): io, _client(), _poll_until_final(), Tests for the upload guardrails added to app.main: 1. Whole-document word-count…, A pipeline that stalls without ever calling progress still flips the session to…, Poll /api/results until it returns a non-202 (final) response., A pipeline that keeps calling progress past the deadline is aborted at the next…, test_cooperative_timeout_via_progress_callback() (+4 more)

### Community 56 - "apply_short_paragraph_comments"
Cohesion: 0.20
Nodes (17): apply_short_paragraph_comments(), _first_token_span(), _iter_text_runs(), _paragraph_text(), _Element, Yield editable visible text runs from ``para_el``. Runs inside tracked-change…, Count sentence-like spans in ``text``. A sentence is any non-empty chunk after…, Add comments to paragraphs with fewer than three sentences. Returns… (+9 more)

### Community 57 - "apply_reference_order_comments"
Cohesion: 0.17
Nodes (20): _anchor_comment_on_paragraph(), apply_reference_order_comments(), _build_comment(), _find_references_heading(), _first_inversion(), _passthrough(), _Element, Comment on a reference list that is not alphabetically ordered. Comment-only —… (+12 more)

### Community 58 - "test_acronym_api.py"
Cohesion: 0.10
Nodes (8): client(), gated_client(), fixture, Smoke tests for the acronym admin HTTP endpoints. Skipped when Flask isn't…, Read-only access stays open so the pipeline can still load the list., Boot the Flask app with auth disabled and the store pointed at tmp., Boot the app with the editor-password gate enabled., test_gated_get_still_open_when_not_authed()

### Community 59 - "grammar_corrections.py"
Cohesion: 0.11
Nodes (23): Return True if a prose-mutating pass should ignore this paragraph. Skips when:…, should_skip_paragraph(), _anchor_visible_span(), apply_contingent_grammar_comments(), apply_grammar_corrections(), _apply_phrase_correction(), _build_user_prompt(), _contingent_sva_comment() (+15 more)

### Community 60 - "run_editorial_review"
Cohesion: 0.09
Nodes (37): EditorialNote, EditorialReviewResult, LLM verdict on a single deterministic structural check result., StructuralValidation, Run LLM-based editorial review on a JUTLP manuscript. Pipeline: 1. Parse DOCX…, run_editorial_review(), _strip_internal_markers(), build_editorial_review_comment_plan() (+29 more)

### Community 61 - "test_abstract_length_rule.py"
Cohesion: 0.18
Nodes (19): estimate_line_count(), Estimate how many rendered lines ``text`` occupies. Takes the larger of the…, check_abstract(), _fp008(), _long_abstract_doc(), _parsed(), Tests for the JUTLP abstract length rule: the abstract must fit lines 7–23 of…, The body (after Introduction) must not be swallowed into the abstract. (+11 more)

### Community 62 - "_normalise_heading_text"
Cohesion: 0.10
Nodes (30): _ack_contains(), _all_alias_norms(), build_front_page_asset_check_plan(), _collect_acknowledgements_issues(), _collect_discussion_subheading_issues(), _collect_method_subheading_issues(), _collect_relationship_ids(), _collect_results_reference_issues() (+22 more)

### Community 63 - "reference_type_checker.py"
Cohesion: 0.19
Nodes (18): _check_book(), _check_book_chapter(), _check_conference(), _check_dataset(), _check_journal(), _check_podcast(), check_reference_type_style(), _check_report() (+10 more)

### Community 64 - "test_acronym_corrections.py"
Cohesion: 0.20
Nodes (13): _format_author_query_text(), _matches_definition(), Attempt to align ``letters`` against the leading section of ``words``. Walks…, If `words` contain a valid full form for `acro`, return the phrase. Walks the…, _try_match_definition(), Tests for acronym detection + consolidated comment + tracked-change rewrites., Conversely, text inside ``<w:del>`` represents tracked deletions — content the…, test_acronym_author_query_comment_text_is_numbered() (+5 more)

### Community 65 - "docx"
Cohesion: 0.25
Nodes (16): build_output_filename(), build_output_filename_from_author_line(), _first_author_last_name(), _get_author_line_and_markers(), _get_document_year(), _remove_superscript_runs_from_author_line(), _unique_output_filename(), docx (+8 more)

### Community 66 - "body_llm_edits.py"
Cohesion: 0.18
Nodes (13): _body_paragraphs(), build_body_edit_plan(), _is_skippable_paragraph(), _propagate_repeated_edits(), LLM-generated surgical copy-edits for the document body. Produces tracked-…, Return the symmetric token difference between ``find`` and ``replace``. Tokens…, Apply accepted exact edits to repeated matching body text. The LLM reviews each…, Normalise curly quotes/apostrophes to ASCII for comparison only. (+5 more)

### Community 67 - "test_reference_checker.py"
Cohesion: 0.23
Nodes (9): check_text_dois(), DOIT: Validate every DOI-shaped substring found in the plain text of each…, _cr_item(), Return a fake ``_lookup_doi`` that resolves DOIs from a dict. ``None`` value…, A reference that quotes the same DOI twice (bare + URL form) should only hit…, _stub_lookup(), TestCheckTextDOIs, _spy() (+1 more)

### Community 68 - "number_word_corrections.py"
Cohesion: 0.23
Nodes (13): _in_any_span(), _is_sentence_start(), Spell out whole numbers 0-9 in running prose as tracked changes. Most academic…, True if position is at the start of a sentence. "Start of sentence" = beginning…, Apply the deny-list of contexts. Return True only when safe to replace., _should_replace(), _make_doc(), test_body_sentence_mentioning_references_is_not_boundary() (+5 more)

### Community 69 - "now_sydney_iso"
Cohesion: 0.18
Nodes (14): now_sydney_iso(), Shared timestamp helper for Word comments and tracked changes. Word stores the…, Return the current time as an ISO-8601 string with the Sydney offset. Example:…, _sydney_tz(), datetime, Tests for the shared Sydney-time stamp helper. Word comments and tracked…, Sydney is UTC+10 (standard) or UTC+11 (daylight saving). If the tz database is…, Second precision only — keeps the stamp tidy and matches the previous format's… (+6 more)

### Community 70 - "_read_doc_root"
Cohesion: 0.15
Nodes (13): Five problematic acronyms still produce exactly one Word comment., Allow-listed acronyms still need a first-use introduction in the body. A…, First body use is rewritten as 'full term (ACRO)', not just 'full term'., The single comment range wraps the first issue's location., Acronyms in the manuscript title produce NO issue at all — no bullet in the…, Crucially, ignoring the title must NOT cause the title's acronym to pre-…, _read_doc_root(), test_allow_listed_acronym_in_body_flagged_when_not_introduced() (+5 more)

### Community 71 - "test_output_generation.py"
Cohesion: 0.14
Nodes (19): _canonical_insert_index(), _format_author_query_text(), Return the canonical section a fail-rule belongs to, or None. SEC001-008 map…, True if a Heading-1 paragraph is the section itself (exact / 'name:' prefix),…, Return the index within ``all_paras`` to insert the stub for ``section``. Place…, _section_for_rule(), _section_heading_present(), _h1_para() (+11 more)

### Community 72 - "check_references"
Cohesion: 0.15
Nodes (15): check_duplicate_references(), check_entry_year(), check_orphan_citations(), check_reference_citations(), check_references(), check_references_section(), _extract_body_citation_keys(), _extract_body_citations() (+7 more)

### Community 73 - "_iter_paren_citations"
Cohesion: 0.20
Nodes (7): _iter_paren_citations(), Yield ``(surname, year)`` tuples for every parenthetical citation. Handles…, Coverage for the multi-citation parenthesis parser., The reported bug: a four-citation paren block produced ZERO matches because the…, APA disambiguators like ``2020a`` must survive., A `(see ...)` aside without a Surname,Year pair must yield nothing — even…, TestParenCitationIterator

### Community 74 - "apply_table_section_boundary_comments"
Cohesion: 0.17
Nodes (25): _anchor_paragraph(), apply_table_section_boundary_comments(), _classify(), _iter_text_runs(), _Element, First meaningful block: a table (skipping leading caption/blank) → it, prose →…, Last meaningful block: a table (skipping trailing note/blank) → it, prose →…, Return a paragraph to anchor the comment on: the nearest non-empty caption… (+17 more)

### Community 75 - "_apply_tracked_style_change"
Cohesion: 0.27
Nodes (13): _apply_tracked_style_change(), Remove direct formatting that would override a heading style. A paragraph that…, _strip_conflicting_direct_format_for_heading(), _body_para(), _ppr(), A body paragraph restyled to a heading must shed its body formatting. When the…, Only size/spacing are stripped — bold stays (headings are bold anyway)., Restyling to the reference style must NOT strip the run size — only heading… (+5 more)

### Community 76 - "_find_next_action"
Cohesion: 0.28
Nodes (8): _find_next_action(), _get_style_name(), _has_corrected_form_in_tracked_ins(), _iter_text_runs(), _Element, Return True if a sibling ``<w:ins>`` already supplies ``comma_value`` with the…, Return ``(run_el, start, end, check_kind, message, value)`` for the earliest…, Yield (run_element, text) for body-text runs we may safely modify. Skips runs…

### Community 77 - "_make_textbox_wrap_around_text"
Cohesion: 0.29
Nodes (12): _make_textbox_wrap_around_text(), Make a front-page floating textbox use *square* text-wrapping so the…, _anchor_para(), _Element, The front-page editorial textbox must wrap text around it, not overlay it. The…, Schema order: the wrap element must precede docPr in the anchor., test_behinddoc_is_cleared(), test_breathing_margins_added() (+4 more)

### Community 78 - "_normalise_surname"
Cohesion: 0.22
Nodes (7): check_submitted_hyperlinks(), _lookup_doi(), _normalise_surname(), Lowercase, strip accents, punctuation, and possessive 's for fuzzy match.…, Query CrossRef by DOI and return the work item, or None on failure., HREF: Verify that user-submitted hyperlinks point to the cited work. For each…, TestNormaliseSurname

### Community 79 - "_read_comments_root"
Cohesion: 0.22
Nodes (11): _comment_visible_text(), _Element, Concatenate every ``<w:t>`` text under the comments root., When the author DID introduce the acronym in the body, no issue fires., Allow-listed acronyms in the abstract are silent — no flagging., When a track change is proposed, the bullet mentions it so the editor knows…, _read_comments_root(), test_abstract_allow_listed_silent() (+3 more)

### Community 80 - "TestOneFailureOneComment"
Cohesion: 0.20
Nodes (3): has_comments_content_type(), has_comments_relationship(), TestOneFailureOneComment

### Community 81 - "output_generation.py"
Cohesion: 0.13
Nodes (22): add_document_summary_comment(), add_paragraph_comment(), _append_validation_summary(), _comment_group_key(), _format_summary_line(), _group_pending_comments(), _grouped_comment_message(), _inject_comment_markers() (+14 more)

### Community 82 - "inspect_original_refs.py"
Cohesion: 0.25
Nodes (7): find_refs_section(), get_all_para_info(), Compare reference entry detection between original and output documents.…, Return info on every paragraph: (index, style, text[:120]), Find start index of References section and return (start, end) para indices., Mirror _select_reference_entries: prefer styled, fallback to heuristic., select_ref_entries()

### Community 83 - "_heading_para_index"
Cohesion: 0.29
Nodes (7): _next_h1_after(), _heading_para_index(), _para_style_val(), _para_text(), Return the pStyle val used by existing Heading-1 paragraphs. Documents vary:…, Index within ``all_paras`` of the Heading-1 paragraph that IS ``section``…, _resolve_h1_style_id()

### Community 84 - "subsection_alias_match"
Cohesion: 0.31
Nodes (4): Return True when ``canonical_label`` is satisfied by ``found_subs``.…, subsection_alias_match(), Direct tests of the alias matcher — no docx fixture needed., TestSubsectionAliasMatch

### Community 85 - "test_body_font_enforcement.py"
Cohesion: 0.31
Nodes (9): _ensure_normal_style_body_rpr(), _passthrough_copy(), Pin the body font + size on the Normal style's run properties. The template's…, _doc_with_normal(), _normal_rpr(), Tests for body-font enforcement: the Normal style must carry Arial 11pt so…, A docx whose Normal style is a non-template font/size., test_already_correct_normal_style_no_change() (+1 more)

### Community 86 - "_normalise_text"
Cohesion: 0.22
Nodes (5): _fingerprint_ref(), _normalise_text(), Collapse a reference to a normalised fingerprint for duplicate detection., Replace curly quotes with their straight ASCII equivalents., TestCitationRegexes

### Community 87 - "TestPresentUnstyledDiscussionNoStub"
Cohesion: 0.31
Nodes (4): A Discussion section that is present but not yet Heading-1 styled (the author…, No tracked-inserted 'Discussion' heading paragraph should exist., The Discussion-subsection comment must anchor on the original (non-inserted)…, TestPresentUnstyledDiscussionNoStub

### Community 88 - "_is_appendix_heading"
Cohesion: 0.38
Nodes (5): _extract_ref_hyperlinks(), _is_appendix_heading(), Return (entry_num, ref_text, url) for reference entries that already have a…, parametrize, TestIsAppendixHeading

### Community 89 - "_extract_ref_author_part"
Cohesion: 0.31
Nodes (5): _extract_ref_author_part(), Return the author/group-author portion of a reference entry. Slices everything…, Return ``(normalised_surname, display_surname)`` for a reference entry, or None…, _sort_key_and_label(), TestExtractRefAuthorPart

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
Cohesion: 0.33
Nodes (9): _apply_intro_page_break(), citationFormatCheck(), test_body_citation_moves_to_footer_and_intro_gets_page_break(), _doc(), _intro_has_page_break(), Tests for the front-page / body page break before the Introduction., Regression: a numbered "1. Introduction" heading must still get the front-…, test_page_break_inserted_before_numbered_introduction() (+1 more)

### Community 94 - "TestValidDoc"
Cohesion: 0.31
Nodes (3): fixture, rules(), TestValidDoc

### Community 95 - "upload"
Cohesion: 0.22
Nodes (11): _document_word_count(), ProcessingCancelled, ProcessingTimeout, Exception, Total word count across every paragraph (whole-document count)., Upload a .docx manuscript for editorial analysis. --- tags: - Analysis…, upload(), _run() (+3 more)

### Community 96 - "Path"
Cohesion: 0.29
Nodes (7): _build_docx(), _build_docx_with_inserted_run(), Path, The scanner must read text inside ``<w:ins>`` runs — that's what upstream…, Build a minimal docx with one paragraph per supplied text., Build a docx where each entry is ``(style, text, inside_ins)``. When…, test_acronyms_inside_inserted_runs_are_detected()

### Community 97 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 98 - "_apply_mutations"
Cohesion: 0.33
Nodes (6): _apply_mutations(), _build_bullet(), _build_replacement(), Return the introduction text ``full term (ACRO)`` for a track change., Render one issue as a single bullet line for the consolidated comment. Title…, Apply tracked-change rewrites and the comment-range anchor. Mutations are…

### Community 99 - "_llm_notes_to_results"
Cohesion: 0.50
Nodes (4): _extract_field(), _llm_notes_to_results(), Read a field from dict/object safely with a default., Normalize LLM editorial notes into validator-like result dictionaries.

### Community 107 - "_find_appendix_start"
Cohesion: 0.47
Nodes (6): _find_appendix_start(), _is_heading_paragraph(), _paragraph_has_image(), _Element, Return True if the paragraph contains a drawing / picture / embedded object…, Return the index (within ``body``'s ``<w:p>`` children list) of the first…

### Community 108 - "_apply_tracked_edit"
Cohesion: 0.40
Nodes (5): _apply_tracked_edit(), _direct_text_runs(), _Element, Direct-child ``<w:r>`` of the paragraph that carry a ``<w:t>``. Runs already…, Replace the paragraph's direct text runs with a del(old)/ins(new) pair.

### Community 110 - "_anchor_flag"
Cohesion: 0.50
Nodes (5): _anchor_flag(), _iter_text_runs(), _Element, Yield (run_element, text) for body-text runs we may safely modify. Mirrors the…, Locate ``original`` inside ``para_el`` and wrap it in a comment range. Returns…

### Community 111 - "_find_word_anchor"
Cohesion: 0.50
Nodes (5): _find_word_anchor(), _iter_text_runs(), _Element, Yield (run, text) for body runs not inside tracked-change wrappers., Locate the first occurrence of ``word`` (case-sensitive, word-bounded) in the…

### Community 112 - "_accepted_paragraph_text"
Cohesion: 0.50
Nodes (4): _accepted_paragraph_text(), True if ``run_el`` should NOT contribute to ``para_p``'s text. Walks up to the…, Return a paragraph's *own* text as if all tracked changes were accepted.…, _run_skipped()

### Community 113 - "_corrected_heading"
Cohesion: 0.50
Nodes (4): _corrected_heading(), _norm(), Return the corrected heading text, or None if no change is needed., Lower-case, collapse whitespace, drop trailing colon/period/semicolon. Matches…

### Community 115 - "vercel.json"
Cohesion: 0.50
Nodes (3): builds, routes, version

### Community 116 - "read_docx"
Cohesion: 0.67
Nodes (3): Document, Path, read_docx()

## Knowledge Gaps
- **24 isolated node(s):** `$schema`, `plugin`, `STAGE_TO_STEP`, `PROC_STEPS`, `JUTLP_FALLBACK_ARTICLE` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 836 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_paragraphs()` connect `load_paragraphs` to `output_generation_samfix.py`, `jutlp_validator.py`, `documentBodyFormatCheck`, `test_sentence_coherence_corrections.py`, `main.py`, `document_analysis_services.py`, `test_front_page_style_fixes.py`, `build_edited_document`, `_apply_missing_practitioner_stub`, `test_spell_checker.py`, `keywordsFound`, `feedback_gen_pipeline.py`, `reference_checker.py`, `generate_commented_docx`, `strip_leading_section_number`, `_to_title_case_title`, `extract_references`, `grammar_corrections.py`, `run_editorial_review`, `test_abstract_length_rule.py`, `docx`, `body_llm_edits.py`, `test_reference_checker.py`, `check_references`, `output_generation.py`, `upload`, `_accepted_paragraph_text`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `find_quote_spans()` connect `test_sentence_coherence_corrections.py` to `output_generation_samfix.py`, `language_corrections.py`, `number_word_corrections.py`, `apply_number_word_corrections`, `test_body_llm_edits.py`, `test_abbreviation_corrections.py`, `_find_next_action`, `test_spell_checker.py`, `feedback_gen_pipeline.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `run_editorial_review()` connect `run_editorial_review` to `build_prompts`, `load_paragraphs`, `document_analysis_services.py`, `LLMError`, `doc_analysis_pipeline`, `feedback_gen_pipeline.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **What connects `$schema`, `plugin`, `STAGE_TO_STEP` to the rest of the system?**
  _24 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `output_generation_samfix.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0393733250876108 - nodes in this community are weakly interconnected._
- **Should `apply_acronym_corrections` be split into smaller, more focused modules?**
  _Cohesion score 0.07777777777777778 - nodes in this community are weakly interconnected._
- **Should `jutlp_validator.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0635814889336016 - nodes in this community are weakly interconnected._