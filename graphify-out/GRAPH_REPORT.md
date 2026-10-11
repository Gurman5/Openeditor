# Graph Report - Openeditor  (2026-10-11)

## Corpus Check
- 162 files · ~193,824 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 3, .css 2, .example 1)

## Summary
- 3061 nodes · 7204 edges · 132 communities (118 shown, 14 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 102 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `951bd549`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- output_generation_samfix.py
- apply_acronym_corrections
- validate
- test_front_page_style_fixes.py
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
- gen_apa7_base_template.py
- _insert_front_page_banner_from_template
- test_heading_corrections.py
- test_output_generation.py
- apply_caption_apa7_comments
- rules
- acronym_corrections.py
- test_access_validation.py
- openeditor.js
- _apply_author_plan
- test_spell_checker.py
- blinded_citation_comments.py
- test_appendix_removal.py
- build_edited_document
- keywordsFound
- Frontend-Backend API Contract
- feedback_gen_pipeline.py
- test_decimal_corrections.py
- reference_format_corrections.py
- script.js
- load_acronyms
- call_llm_json
- build_prompts
- apply_number_word_corrections
- output_generation.py
- narrative_citation_corrections.py
- reference_checker.py
- test_table_keep_together.py
- test_sam_fixes_validator_rules.py
- table_page_breaks.py
- jutlp_articles.py
- test_grammar_corrections.py
- _Element
- document_styling_fixes.py
- test_copyeditor_comment_regressions.py
- _to_title_case_title
- extract_references
- cli_copybot.py
- apply_table_n_notation_comments
- TestFiveFailuresFiveComments
- body_llm_edits.py
- test_upload_guardrails.py
- test_short_paragraph_comments.py
- apply_reference_order_comments
- test_acronym_api.py
- _apply_phrase_correction
- run_editorial_review
- test_abstract_length_rule.py
- _normalise_heading_text
- reference_type_checker.py
- run_font_corrections.py
- get_front_page
- abstractFound
- test_reference_checker.py
- document_zones.py
- now_sydney_iso
- test_acronym_corrections.py
- _canonical_insert_index
- check_references
- _iter_paren_citations
- apply_table_section_boundary_comments
- _apply_tracked_style_change
- find_quote_spans
- _make_textbox_wrap_around_text
- _normalise_surname
- _read_comments_root
- authorFormatCheck
- _group_pending_comments
- LLMError
- table_keep_together.py
- TestSubsectionAliasMatch
- test_body_font_enforcement.py
- _extract_ref_author_part
- TestPresentUnstyledDiscussionNoStub
- check_submitted_hyperlinks
- results
- _ref_surname_keys
- _collect_discussion_subheading_issues
- inspect_abstract.py
- test_intro_page_break.py
- TestValidDoc
- Gurman — Sprint 2 Wiring Tasks (Frontend ↔ Backend Reference)
- Path
- graphify.js
- _split_run_for_track_change_only
- inspect_original_refs.py
- setup.sh
- permission
- session_manager.py
- copybot
- test_reporting_ownership.py
- Gurman — Data / Endpoint Tasks (Source of Truth)
- _llm_resolve_mismatch
- docx
- _find_word_anchor
- _llm_notes_to_results
- _find_next_action
- _make_comment_element
- vercel.json
- read_docx
- deployment.md
- Gurman — Wrong File Type + Cancel + Solo Demo
- zac-ux-tasks.md
- _fake_llm
- api.js
- startProcessing
- number_word_corrections.py
- applyFile
- resetToUpload
- downloadUrl
- apa7_template.py
- acronym_store.py

## God Nodes (most connected - your core abstractions)
1. `load_paragraphs()` - 91 edges
2. `validate()` - 64 edges
3. `build_edited_document()` - 56 edges
4. `doc_analysis_pipeline()` - 41 edges
5. `generate_commented_docx()` - 41 edges
6. `apply_acronym_corrections()` - 41 edges
7. `ParagraphRecord` - 39 edges
8. `documentBodyFormatCheck()` - 36 edges
9. `documentBodyFound()` - 29 edges
10. `_apply_author_plan()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `Results Status Mapping` --semantically_similar_to--> `Four-Stage Manuscript Workflow`  [INFERRED] [semantically similar]
  docs/api-contract.md → app/templates/writer.html
- `G-03 — Cancel job (cooperative)` --references--> `ProcessingCancelled`  [INFERRED]
  docs/gurman-sprint2-tasks.md → app/main.py
- `Client-Side Manuscript Validation` --semantically_similar_to--> `Upload Limit Mismatch`  [INFERRED] [semantically similar]
  app/templates/writer.html → docs/api-contract.md
- `test_remove_bold_italic_only_changes_normal_body_paragraphs()` --calls--> `_remove_bold_italic_from_normal_body_paragraphs()`  [EXTRACTED]
  tests/test_body_llm_edits.py → app/services/output_generation_samfix.py
- `TestUserPrompt` --uses--> `ParagraphRecord`  [INFERRED]
  tests/test_prompt_builder.py → app/domain/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Canonical API Screen Flow** — app_templates_writer_four_stage_manuscript_workflow, docs_api_contract_processing_state_machine, docs_api_contract_results_status_mapping, docs_api_contract_idempotent_download [EXTRACTED 1.00]
- **Deterministic Validation Stack** — jutlp_validator_checklist_deterministic_jutlp_validation, jutlp_validator_checklist_paragraph_row_model, jutlp_validator_checklist_required_section_checks, jutlp_validator_checklist_front_page_checks, jutlp_validator_checklist_rule_report_format [EXTRACTED 1.00]
- **Manuscript Review Pipeline** — readme_open_editor_bot, readme_jutlp_manuscript_review, readme_openai_editorial_review, readme_flask_document_processing_pipeline [EXTRACTED 1.00]

## Communities (132 total, 14 thin omitted)

### Community 0 - "output_generation_samfix.py"
Cohesion: 0.04
Nodes (86): _append_author_query_runs(), _apply_apa_section_margins(), _apply_body_run_format(), _apply_table_caption_formatting(), _apply_table_paragraph_style(), _apply_tracked_body_format_fixes(), _apply_tracked_body_paragraph_format(), _apply_tracked_body_run_format() (+78 more)

### Community 1 - "apply_acronym_corrections"
Cohesion: 0.07
Nodes (38): apply_acronym_corrections(), Run the full acronym pass against ``input_path``, writing to ``output_path``.…, _build_zoned_docx(), An introduction in the abstract does NOT satisfy the body's first-use rule., Truly unknown acronyms in the abstract (no allow-list, no inline def anywhere)…, Conversely, text inside ``<w:del>`` represents tracked deletions — content the…, Block-listed tokens (USA, OK, NASA, iOS, …) never produce issues even when bare…, If the editor adds a well-known org (e.g. NASA) to the allow-list, the block-… (+30 more)

### Community 2 - "validate"
Cohesion: 0.06
Nodes (62): build_report(), check_abstract_single_paragraph(), check_block_quote_style(), check_body_paragraph_styles(), check_combined_results_discussion(), check_conclusion_length(), check_discussion_subsections(), check_dot_points() (+54 more)

### Community 3 - "test_front_page_style_fixes.py"
Cohesion: 0.06
Nodes (64): _append_body_comment(), _apply_document_body_plan(), _apply_front_page_asset_plan(), _apply_heading_1_text_normalization(), _apply_heading_2_title_case(), _apply_normal_style_fix(), _canonical_heading_1_text(), _collect_dot_point_issues() (+56 more)

### Community 4 - "language_corrections.py"
Cohesion: 0.08
Nodes (45): apply_citation_formatting_corrections(), _apply_corrections_to_para(), _Element, Insert missing space after p. / pp. in in-text page references. APA style…, Add a space after p./pp. before page numbers as tracked changes. Returns…, _apply_corrections_to_para(), apply_et_al_corrections(), _corrected_bracket() (+37 more)

### Community 5 - "test_body_llm_edits.py"
Cohesion: 0.07
Nodes (44): _propagate_repeated_edits(), Apply accepted exact edits to repeated matching body text. The LLM reviews each…, _validate_edit(), _apply_body_and_reference_style_fixes(), _apply_body_edit_plan(), _apply_intra_paragraph_tracked_replace(), Apply tracked style changes for body and reference paragraphs: - Required body…, _paragraph_with_runs() (+36 more)

### Community 6 - "test_sentence_coherence_corrections.py"
Cohesion: 0.11
Nodes (36): apply_sentence_coherence_corrections(), get_sentence_coherence_flags(), _is_usable_reason(), Call the LLM and return a list of ``{original, reason}`` dicts.…, Anchor a comment at every coherence flag for ``input_path``. ``flags`` may be…, True if ``reason`` is a real explanation, not a degenerate verdict. Guards…, _make_doc(), parametrize (+28 more)

### Community 7 - "load_paragraphs"
Cohesion: 0.08
Nodes (47): detect_heading_level_1(), extract_main_sections(), extract_subsections(), load_paragraphs(), Scan a .docx file and return its Heading 1 section text and positions., _add_inserted_paragraph(), _add_paragraph_with_deletion(), _add_paragraph_with_textbox() (+39 more)

### Community 8 - "main.py"
Cohesion: 0.07
Nodes (46): _acronym_admin_active(), _acronym_admin_authed(), acronyms_admin_login(), acronyms_admin_logout(), acronyms_admin_page(), add_acronym_api(), analyse_cli(), _body_edit_items() (+38 more)

### Community 9 - "document_analysis_services.py"
Cohesion: 0.08
Nodes (49): Few-shot editorial examples extracted from real JUTLP editor decisions. These…, JUTLP editorial guidelines extracted from 'JUTLP Template 2026.docx'. Last…, ParagraphRecord, _build_system_prompt(), _build_user_prompt(), _canonical_section_for(), _extract_front_page_content(), _find_sections_by_text() (+41 more)

### Community 10 - "test_document_normalisation.py"
Cohesion: 0.10
Nodes (45): _accept_tracked_changes(), _ancestor_paragraph_index(), _delete_guidance_paragraphs(), _is_paragraph_blank(), NormalisationReport, normalise_docx(), _Element, Path (+37 more)

### Community 11 - "test_abbreviation_corrections.py"
Cohesion: 0.08
Nodes (49): apply_abbreviation_corrections(), _find_first_match(), _iter_text_runs(), _overlaps_quote(), _process_paragraph(), _Element, Return the earliest rule-match in ``text`` as ``(start, end, replacement,…, Apply every matching rule in ``para_el``, returning updated ``next_change_id``.… (+41 more)

### Community 12 - "reference_reconstructor.py"
Cohesion: 0.09
Nodes (46): build_apa7_from_crossref(), _build_book(), _build_book_chapter(), _build_dataset(), _build_dissertation(), _build_edited_book(), _build_journal_article(), _build_preprint() (+38 more)

### Community 13 - "doc_analysis_pipeline"
Cohesion: 0.12
Nodes (15): doc_analysis_pipeline(), _hyperlink_plain_urls_in_refs(), _inject_crossref_doi_links(), _max_revision_id(), _normalise(), _patch_settings_show_markup(), Path, Remove Sam's comments (id > our_max_id) that duplicate our validator output.… (+7 more)

### Community 14 - "gen_apa7_base_template.py"
Cohesion: 0.07
Nodes (49): _already_correct(), apply_reference_indent_corrections(), _is_heading(), _resolved_name(), _build_style_hanging_map(), _resolve(), _build_style_name_map(), _Element (+41 more)

### Community 15 - "_insert_front_page_banner_from_template"
Cohesion: 0.10
Nodes (30): _apply_apa_body_geometry(), _collect_image_rel_ids(), _doc_has_first_page_header_picture(), _ensure_first_footer(), _ensure_first_header(), _ensure_header_reference(), _ensure_image_content_types(), _find_first_footer_ref() (+22 more)

### Community 16 - "test_heading_corrections.py"
Cohesion: 0.06
Nodes (52): _build_section_rename_map(), _merges_two_sections(), _normalise_subsection(), Remove a leading heading number from ``text`` (e.g. "2. Literature" ->…, Lower-case, collapse whitespace, strip a leading heading number and any…, Return the canonical main section a heading fragment names, or None. Matches…, True when ``alias`` merges two *distinct* canonical sections (e.g. "Results and…, ``normalised alias -> canonical label`` for safe heading renames. Built from… (+44 more)

### Community 17 - "test_output_generation.py"
Cohesion: 0.08
Nodes (34): _format_author_query_text(), generate_commented_docx(), Generate a reviewed `.docx` with inline comments and a validation summary page., Return the canonical section a fail-rule belongs to, or None. SEC001-008 map…, True if a Heading-1 paragraph is the section itself (exact / 'name:' prefix),…, _section_for_rule(), _section_heading_present(), count_comments_in_docx() (+26 more)

### Community 18 - "apply_caption_apa7_comments"
Cohesion: 0.18
Nodes (22): apply_caption_apa7_comments(), _iter_text_runs(), _needs_apa7_split(), _Element, Emit one APA 7 caption-split comment per offending paragraph. Returns…, Yield (run_el, text) for runs we may safely anchor a comment on., Return True when the paragraph holds a full single-paragraph figure/table…, _build_docx() (+14 more)

### Community 19 - "rules"
Cohesion: 0.07
Nodes (8): fixture, rules(), TestDeidentifiedWithAuthorLeak, TestFrontPageIssues, TestMissingMethodSubsection, TestStructureAndEndmatterIssues, TestValidDeidentified, TestValidIdentified

### Community 20 - "acronym_corrections.py"
Cohesion: 0.12
Nodes (30): _append_author_query_runs(), _author_query_parts(), _bracketed_spans(), _build_zone_map(), _collect_inline_definitions(), _find_run_at_offset(), _find_title_paragraph_indices(), _format_author_query_text() (+22 more)

### Community 21 - "test_access_validation.py"
Cohesion: 0.13
Nodes (26): _require_access(), AccessResult, AccessStatus, check_access(), check_local_bypass(), Access validation service — G-07. Defines the authentication contract for…, Single entry point the Flask gate calls. Tries, in order: 1. Local SKIP_AUTH…, SKIP_AUTH must be explicitly 'true' (case-insensitive) — any other value,… (+18 more)

### Community 23 - "_apply_author_plan"
Cohesion: 0.08
Nodes (40): _append_affiliation_before_notes(), _append_plain_text_run(), _append_plain_text_run_with_size(), _append_text_with_line_breaks(), _append_text_with_superscript_markers(), _append_tracked_replace(), _apply_author_plan(), _apply_style_if_needed() (+32 more)

### Community 24 - "test_spell_checker.py"
Cohesion: 0.10
Nodes (37): _build_word_counts(), _classify_word(), _freq_ratio(), get_spell_corrections(), _levenshtein(), Return ``(verdict, candidate)`` for a single suspect word. Verdict is one of: *…, Cheap Levenshtein implementation — we only ever compare short words so the…, Ratio of dictionary frequency between candidate and source word. Both… (+29 more)

### Community 25 - "blinded_citation_comments.py"
Cohesion: 0.17
Nodes (21): _anchor_paragraph_comment(), apply_blinded_citation_comments(), _build_comment(), _classify(), _distinct(), _own_text_runs(), _Element, Flag blinded / placeholder citations and self-references. For peer review… (+13 more)

### Community 26 - "test_appendix_removal.py"
Cohesion: 0.12
Nodes (36): _anchor_comment_on_paragraph(), apply_appendix_removal(), _find_appendix_start(), _is_appendix_heading(), _is_heading_paragraph(), _paragraph_has_image(), _passthrough(), _Element (+28 more)

### Community 27 - "build_edited_document"
Cohesion: 0.08
Nodes (38): _flush(), _apply_citation_plan(), _apply_heading_center_alignment(), _apply_heading_keep_next(), _apply_intro_page_break(), _apply_keywords_plan(), _apply_tracked_style_fixes(), build_edited_document() (+30 more)

### Community 28 - "keywordsFound"
Cohesion: 0.06
Nodes (37): _apply_missing_keywords_stub(), citationFound(), _count_abstract_lines(), _count_title_lines(), _extract_keywords_list(), _find_abstract_heading_in_front(), _find_blank_line_after_index(), _find_citation_heading_in_front() (+29 more)

### Community 29 - "Frontend-Backend API Contract"
Cohesion: 0.07
Nodes (32): Graphify Knowledge Graph, OAPA Brand Mark, Acronym Management UI, Editor Admin Authentication, Persistent Acronym Storage, Editorial Access Gate, Shared Password Authentication, Client-Side Manuscript Validation (+24 more)

### Community 30 - "feedback_gen_pipeline.py"
Cohesion: 0.08
Nodes (50): Deterministic abbreviation / journal-style fixes emitted as tracked changes.…, _make_comment_element(), _patch_content_types(), _patch_rels(), Replace the run with (before | comment-anchored content | after). When…, _split_run_for_action(), Flag content that appears AFTER the reference list (appendices). JUTLP house…, Flag figure/table captions that aren't split into APA 7 paragraphs. APA 7… (+42 more)

### Community 31 - "test_decimal_corrections.py"
Cohesion: 0.09
Nodes (26): _build_docx(), _Element, Path, Tests for the decimal-precision and comma-as-decimal checks., The classic example: thousand separators and comma-decimals together., The example from the client's brief, end-to-end., A `0.1234` inside `"..."` retains the source's precision., Unquoted comma-decimal in the same paragraph as a quoted one must still be… (+18 more)

### Community 32 - "reference_format_corrections.py"
Cohesion: 0.16
Nodes (17): normalise_heading(), Lower-case, strip numeric prefix and trailing colon-suffix., _apply_del_ins(), apply_reference_format_corrections(), _build_style_name_map(), _collect_ref_paragraphs(), _is_comment_ref_run(), _para_plain_text() (+9 more)

### Community 33 - "script.js"
Cohesion: 0.10
Nodes (28): _activateStep(), _clearPollDelay(), clearUploadError(), displayFile(), fetchJutlpArticles(), finishStepAnimation(), groupItems(), JUTLP_FALLBACK_ARTICLE (+20 more)

### Community 34 - "load_acronyms"
Cohesion: 0.10
Nodes (28): list_acronyms_api(), add_acronym(), _ensure_file_exists(), load_acronyms(), _load_seed(), Path, Restore the on-disk store to the bundled seed. Used by tests., Return the bundled seed JSON as a fresh dict. (+20 more)

### Community 35 - "call_llm_json"
Cohesion: 0.12
Nodes (27): call_llm_json(), _build_user_prompt(), _clean_one(), _dedupe_case_insensitive(), generate_keywords(), _is_acceptable(), LLM-driven keyword generation for manuscripts missing a Keywords section.…, Strip surrounding whitespace and quotes; collapse internal whitespace. (+19 more)

### Community 36 - "build_prompts"
Cohesion: 0.17
Nodes (11): build_prompts(), Build (system_prompt, user_prompt) from parsed document data., _make_paragraphs(), _make_parsed_structure(), Build a minimal set of ParagraphRecord objects for testing., The prompt instructs the LLM to use specific severity labels. Originally…, Regression: sections headed by an ALIAS ("Methodology", "Findings", "Literature…, A titled heading ("Introduction: Background") maps to its canonical section so… (+3 more)

### Community 37 - "apply_number_word_corrections"
Cohesion: 0.08
Nodes (50): _has_reference_issue_summary_comment(), _insert_suspicious_ref_comments(), Add Word comments for reference issues: - CONS001/CONS002 citation-consistency…, Document, Path, read_docx(), apply_number_word_corrections(), Scan body paragraphs and emit tracked-change replacements for digits 0-9.… (+42 more)

### Community 38 - "output_generation.py"
Cohesion: 0.09
Nodes (43): _append_validation_summary(), _dedupe_pending_comments(), _find_after(), _find_first_heading(), _find_first_non_empty_para(), _find_front_matter_anchor(), _find_front_matter_rule_anchor(), _find_front_style() (+35 more)

### Community 39 - "narrative_citation_corrections.py"
Cohesion: 0.18
Nodes (23): _apply_corrections_to_para(), apply_narrative_citation_corrections(), _bracket_spans(), _in_any_span(), _plain_text(), _Element, Fix APA narrative citation ampersands as Word tracked changes. APA narrative…, Replace narrative-citation ampersands in one paragraph. (+15 more)

### Community 40 - "reference_checker.py"
Cohesion: 0.10
Nodes (31): _build_structured_reference(), _cache_get(), _cache_set(), check_duplicate_references(), check_orphan_citations(), check_reference_citations(), check_references(), check_references_section() (+23 more)

### Community 41 - "test_table_keep_together.py"
Cohesion: 0.28
Nodes (15): apply_table_keep_together(), Set cantSplit / tblHeader / caption keepNext on every table. Returns one action…, _basic_table_doc(), _has(), Tests for the table keep-together pass., cantSplit must precede tblHeader, and trPr must be tr's first child., Running twice produces no second set of changes and no duplicate props., _rows() (+7 more)

### Community 42 - "test_sam_fixes_validator_rules.py"
Cohesion: 0.11
Nodes (30): app_services, _add_style(), parametrize, D-01 Phase 2 evidence tests: one test per validator rule id, proving the…, FP006 fixed by S._apply_missing_keywords_stub (tracked change)., FP011 fixed by S._apply_abstract_plan (tracked change)., STY003 fixed by S._apply_body_and_reference_style_fixes (tracked style change)., STY004 fixed by S._apply_body_and_reference_style_fixes (tracked style change). (+22 more)

### Community 43 - "table_page_breaks.py"
Cohesion: 0.20
Nodes (26): apply_table_page_breaks(), _cell_text(), _make_page_break_paragraph(), _page_break_anchor(), _para_has_page_break(), _para_style(), _para_text(), _preceded_by_page_break() (+18 more)

### Community 44 - "jutlp_articles.py"
Cohesion: 0.18
Nodes (25): _abstract_candidates(), _article_details_url(), _clean_abstract_candidate(), _clean_text(), _extract_abstract(), _extract_article_urls(), _extract_author(), _extract_title() (+17 more)

### Community 45 - "test_grammar_corrections.py"
Cohesion: 0.11
Nodes (30): apply_contingent_grammar_comments(), _contingent_sva_comment(), _fix_au_spellings(), get_grammar_corrections(), _has_au_us_suffix_swap(), _is_au_to_us_replacement(), _is_proper_noun_correction(), Return True if original looks like a proper noun, surname, acronym, or tech… (+22 more)

### Community 46 - "_Element"
Cohesion: 0.16
Nodes (17): _build_comment_ref_run(), _find_span(), _inject_comment_markers(), _inject_comment_markers_for_phrase(), _make_inserted_heading_paragraph(), _Element, Fallback comment anchor: wrap the whole paragraph. We only use this when…, Build `<w:r><w:commentReference .../></w:r>` for the inline comment mark. (+9 more)

### Community 47 - "document_styling_fixes.py"
Cohesion: 0.17
Nodes (19): get_section_bounds(), _heading_matches(), True if heading_text exactly matches query, or starts with 'query:'. Handles…, _canonical_index(), _collect_until(), compare_document_styles(), compare_template_and_document(), extract_headings() (+11 more)

### Community 48 - "test_copyeditor_comment_regressions.py"
Cohesion: 0.09
Nodes (42): Renumber visible Author Query labels after every comment pass has run., _renumber_final_author_queries(), apply_au_spelling_corrections(), Scan every eligible paragraph and apply AU spelling tracked changes. Returns…, Return one summary entry per repeated spelling correction. The tracked-change…, summarize_spelling_correction_repeats(), _apply_editorial_review_comment_plan(), _comment_ids_in_document_order() (+34 more)

### Community 49 - "_to_title_case_title"
Cohesion: 0.07
Nodes (32): authorFound(), _collect_quote_formatting_issues(), _count_title_words(), _extract_quoted_segments(), _find_anchor_above(), _find_content_authors(), _fix_au_spellings_in_text(), _has_known_title() (+24 more)

### Community 50 - "extract_references"
Cohesion: 0.14
Nodes (13): extract_references(), _get_style_name(), Return ``(start_index, end_index)`` bounding the References section. ``start``…, Two-tier reference selection used by BOTH extraction and comment anchoring so…, _references_window(), _select_reference_entries(), _build_docx_with_sections(), A paper with reference-styled paragraphs but NO References heading still has… (+5 more)

### Community 51 - "cli_copybot.py"
Cohesion: 0.18
Nodes (20): _heading_level_1_sections(), _is_generic_copyedit_output(), main(), _print_heading_normalization_summary(), Path, _rename_generic_copyedit_output(), _show_heading_level_1_sections(), _status() (+12 more)

### Community 52 - "apply_table_n_notation_comments"
Cohesion: 0.16
Nodes (20): apply_table_n_notation_comments(), _is_capital_n_header(), _iter_text_runs(), _Element, Yield (run_el, text) for runs we may safely anchor a comment on., True when the paragraph is a table cell whose only content is "N"., Emit one comment per table column header that is a bare capital "N". Returns…, _comment_texts() (+12 more)

### Community 53 - "TestFiveFailuresFiveComments"
Cohesion: 0.10
Nodes (8): has_comments_content_type(), has_comments_relationship(), Return ordered list of (text, has_ins, [commentRangeStart ids]) for every…, The combined 'Results and Discussion' fixture has no standalone Discussion…, SEC005 + DIS001-003 comments anchor inside the inserted Discussion stub, NOT on…, The inserted Discussion stub sits after Results and before References in…, TestFiveFailuresFiveComments, TestOneFailureOneComment

### Community 54 - "body_llm_edits.py"
Cohesion: 0.12
Nodes (20): _body_paragraphs(), build_body_edit_plan(), _dedupe_edits(), _fix_au_spellings(), _is_skippable_paragraph(), _llm_edits_for_paragraph(), LLM-generated surgical copy-edits for the document body. Produces tracked-…, Return the symmetric token difference between ``find`` and ``replace``. Tokens… (+12 more)

### Community 55 - "test_upload_guardrails.py"
Cohesion: 0.15
Nodes (16): _document_word_count(), Total word count across every paragraph (whole-document count)., io, pytest, _client(), _poll_until_final(), Tests for the upload guardrails added to app.main: 1. Whole-document word-count…, A pipeline that stalls without ever calling progress still flips the session to… (+8 more)

### Community 56 - "test_short_paragraph_comments.py"
Cohesion: 0.44
Nodes (8): _build_zoned_docx(), _comment_texts(), _Element, Path, _read_comments_root(), test_adds_comments_for_paragraphs_with_under_three_sentences(), test_no_changes_when_every_paragraph_has_three_or_more_sentences(), test_skips_title_heading_and_outside_zone()

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
Nodes (36): EditorialNote, EditorialReviewResult, LLM verdict on a single deterministic structural check result., StructuralValidation, Run LLM-based editorial review on a JUTLP manuscript. Pipeline: 1. Parse DOCX…, run_editorial_review(), _strip_internal_markers(), build_editorial_review_comment_plan() (+28 more)

### Community 61 - "test_abstract_length_rule.py"
Cohesion: 0.20
Nodes (17): check_abstract(), _fp008(), _long_abstract_doc(), _parsed(), Tests for the JUTLP abstract length rule: the abstract must fit lines 7–23 of…, The body (after Introduction) must not be swallowed into the abstract., The length flag must be its OWN comment (not folded into the merge/style…, Regression: an abstract that is NOT styled 'Front Page Text' (authors routinely… (+9 more)

### Community 62 - "_normalise_heading_text"
Cohesion: 0.11
Nodes (23): build_front_page_asset_check_plan(), _collect_relationship_ids(), _collect_required_section_issues(), _element_has_textbox(), _find_combined_results_discussion_index(), _find_first_non_empty_index(), _find_heading1_index(), _front_page_body_paras() (+15 more)

### Community 63 - "reference_type_checker.py"
Cohesion: 0.19
Nodes (18): _check_book(), _check_book_chapter(), _check_conference(), _check_dataset(), _check_journal(), _check_podcast(), check_reference_type_style(), _check_report() (+10 more)

### Community 64 - "run_font_corrections.py"
Cohesion: 0.14
Nodes (23): apply_run_font_corrections(), _apply_tracked_run_font(), _current_font(), _current_sz(), _direct_text_runs(), _is_inside_insertion(), _para_style_val(), _Element (+15 more)

### Community 65 - "get_front_page"
Cohesion: 0.26
Nodes (16): get_front_page(), build_output_filename(), build_output_filename_from_author_line(), _first_author_last_name(), _get_author_line_and_markers(), _get_document_year(), _remove_superscript_runs_from_author_line(), _unique_output_filename() (+8 more)

### Community 66 - "abstractFound"
Cohesion: 0.10
Nodes (23): abstractFormatCheck(), abstractFound(), _apply_abstract_plan(), _apply_missing_practitioner_stub(), _build_missing_abstract_components_message(), _check_abstract_components_with_llm(), _ensure_template_styles_available(), _is_abstract_body_end_marker() (+15 more)

### Community 67 - "test_reference_checker.py"
Cohesion: 0.16
Nodes (11): check_entry_author(), check_text_dois(), DOIT: Validate every DOI-shaped substring found in the plain text of each…, _cr_item(), Return a fake ``_lookup_doi`` that resolves DOIs from a dict. ``None`` value…, A reference that quotes the same DOI twice (bare + URL form) should only hit…, _stub_lookup(), TestCheckTextDOIs (+3 more)

### Community 68 - "document_zones.py"
Cohesion: 0.09
Nodes (44): apply_decimal_corrections(), Run both decimal checks over ``input_path`` and write to ``output_path``.…, get_style_name(), heading_zone_transition(), initial_zone(), is_in_table(), is_list_item(), iter_paragraphs_with_zone() (+36 more)

### Community 69 - "now_sydney_iso"
Cohesion: 0.18
Nodes (14): now_sydney_iso(), Shared timestamp helper for Word comments and tracked changes. Word stores the…, Return the current time as an ISO-8601 string with the Sydney offset. Example:…, _sydney_tz(), datetime, Tests for the shared Sydney-time stamp helper. Word comments and tracked…, Sydney is UTC+10 (standard) or UTC+11 (daylight saving). If the tz database is…, Second precision only — keeps the stamp tidy and matches the previous format's… (+6 more)

### Community 70 - "test_acronym_corrections.py"
Cohesion: 0.13
Nodes (22): _matches_definition(), Attempt to align ``letters`` against the leading section of ``words``. Walks…, If `words` contain a valid full form for `acro`, return the phrase. Walks the…, _try_match_definition(), Tests for acronym detection + consolidated comment + tracked-change rewrites., Five problematic acronyms still produce exactly one Word comment., Allow-listed acronyms still need a first-use introduction in the body. A…, First body use is rewritten as 'full term (ACRO)', not just 'full term'. (+14 more)

### Community 71 - "_canonical_insert_index"
Cohesion: 0.15
Nodes (16): True if ``text`` is exactly a JUTLP main-section name or alias. Matching is…, _text_matches_main_section(), _canonical_insert_index(), _next_h1_after(), _heading_para_index(), _para_style_val(), _para_text(), Return the pStyle val used by existing Heading-1 paragraphs. Documents vary:… (+8 more)

### Community 73 - "_iter_paren_citations"
Cohesion: 0.20
Nodes (7): _iter_paren_citations(), Yield ``(surname, year)`` tuples for every parenthetical citation. Handles…, Coverage for the multi-citation parenthesis parser., The reported bug: a four-citation paren block produced ZERO matches because the…, APA disambiguators like ``2020a`` must survive., A `(see ...)` aside without a Surname,Year pair must yield nothing — even…, TestParenCitationIterator

### Community 74 - "apply_table_section_boundary_comments"
Cohesion: 0.22
Nodes (20): apply_table_section_boundary_comments(), _iter_text_runs(), First meaningful block: a table (skipping leading caption/blank) → it, prose →…, Last meaningful block: a table (skipping trailing note/blank) → it, prose →…, Comment on sections that open and/or close directly with a table. Returns…, Yield (run_el, text) for runs we may safely anchor a comment on., _section_closer(), _section_opener() (+12 more)

### Community 75 - "_apply_tracked_style_change"
Cohesion: 0.27
Nodes (13): _apply_tracked_style_change(), Remove direct formatting that would override a heading style. A paragraph that…, _strip_conflicting_direct_format_for_heading(), _body_para(), _ppr(), A body paragraph restyled to a heading must shed its body formatting. When the…, Only size/spacing are stripped — bold stays (headings are bold anyway)., Restyling to the reference style must NOT strip the run size — only heading… (+5 more)

### Community 76 - "find_quote_spans"
Cohesion: 0.15
Nodes (8): find_quote_spans(), is_in_quote(), Return True when the half-open range ``[start, end)`` overlaps any quotation…, Return a list of ``(start, end)`` half-open intervals locating every paired-…, Tests for the inline-quotation detection helper. The helper underpins JUTLP's…, Single quote marks are ambiguous (apostrophes!) so the helper deliberately…, TestFindQuoteSpans, TestIsInQuote

### Community 77 - "_make_textbox_wrap_around_text"
Cohesion: 0.29
Nodes (12): _make_textbox_wrap_around_text(), Make a front-page floating textbox use *square* text-wrapping so the…, _anchor_para(), _Element, The front-page editorial textbox must wrap text around it, not overlay it. The…, Schema order: the wrap element must precede docPr in the anchor., test_behinddoc_is_cleared(), test_breathing_margins_added() (+4 more)

### Community 78 - "_normalise_surname"
Cohesion: 0.27
Nodes (5): _normalise_surname(), Lowercase, strip accents, punctuation, and possessive 's for fuzzy match.…, Return ``(normalised_surname, display_surname)`` for a reference entry, or None…, _sort_key_and_label(), TestNormaliseSurname

### Community 79 - "_read_comments_root"
Cohesion: 0.22
Nodes (11): _comment_visible_text(), _Element, Concatenate every ``<w:t>`` text under the comments root., When the author DID introduce the acronym in the body, no issue fires., Allow-listed acronyms in the abstract are silent — no flagging., When a track change is proposed, the bullet mentions it so the editor knows…, _read_comments_root(), test_abstract_allow_listed_silent() (+3 more)

### Community 80 - "authorFormatCheck"
Cohesion: 0.13
Nodes (20): _author_affiliation_marker_count(), _author_naming_pattern_valid(), authorFormatCheck(), _authors_with_multiple_affiliation_markers(), _build_affiliation_mismatch_message(), _build_author_naming_query(), _default_affiliations_text_for_authors(), _default_authors_line_for_markers() (+12 more)

### Community 81 - "_group_pending_comments"
Cohesion: 0.40
Nodes (5): _comment_group_key(), _group_pending_comments(), _grouped_comment_message(), Return a family key for high-volume, same-kind comment groups., Reduce high-volume same-family findings to one Word comment each.

### Community 82 - "LLMError"
Cohesion: 0.17
Nodes (15): call_llm(), get_client(), LLMError, Exception, Raised when the LLM call fails after retries., Create an OpenAI client., Send a structured-output request to the OpenAI Chat Completions API. Returns…, dotenv (+7 more)

### Community 83 - "table_keep_together.py"
Cohesion: 0.26
Nodes (12): _apply_caption_keep_next(), _ensure_keep_next(), _ensure_trpr(), _ensure_trpr_child(), _para_style(), _para_text(), _Element, Keep tables (and their headers) from splitting awkwardly across pages. A common… (+4 more)

### Community 85 - "test_body_font_enforcement.py"
Cohesion: 0.31
Nodes (9): _ensure_normal_style_body_rpr(), _passthrough_copy(), Pin the body font + size on the Normal style's run properties. The template's…, _doc_with_normal(), _normal_rpr(), Tests for body-font enforcement: the Normal style must carry Arial 11pt so…, A docx whose Normal style is a non-template font/size., test_already_correct_normal_style_no_change() (+1 more)

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

### Community 91 - "_collect_discussion_subheading_issues"
Cohesion: 0.23
Nodes (12): _ack_contains(), _all_alias_norms(), _collect_acknowledgements_issues(), _collect_discussion_subheading_issues(), _collect_method_subheading_issues(), _collect_results_reference_issues(), _find_next_heading1_index(), _matches_required_subsection() (+4 more)

### Community 92 - "inspect_abstract.py"
Cohesion: 0.29
Nodes (5): get_comment_anchors(), get_ref_entries(), Inspect the processed output vs the original to find comment placement issues., Map comment id -> paragraph text snippet where the anchor sits., Return numbered reference entries from the document.

### Community 93 - "test_intro_page_break.py"
Cohesion: 0.48
Nodes (6): _doc(), _intro_has_page_break(), Tests for the front-page / body page break before the Introduction., Regression: a numbered "1. Introduction" heading must still get the front-…, test_page_break_inserted_before_numbered_introduction(), test_page_break_inserted_before_plain_introduction()

### Community 95 - "Gurman — Sprint 2 Wiring Tasks (Frontend ↔ Backend Reference)"
Cohesion: 0.13
Nodes (16): ProcessingCancelled, ProcessingTimeout, Exception, _run(), _pipeline(), _update_progress(), Artifacts, Backend truth (verified against `app/main.py`, `app/static/script.js`) (+8 more)

### Community 96 - "Path"
Cohesion: 0.29
Nodes (7): _build_docx(), _build_docx_with_inserted_run(), Path, The scanner must read text inside ``<w:ins>`` runs — that's what upstream…, Build a minimal docx with one paragraph per supplied text., Build a docx where each entry is ``(style, text, inside_ins)``. When…, test_acronyms_inside_inserted_runs_are_detected()

### Community 97 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 98 - "_split_run_for_track_change_only"
Cohesion: 0.22
Nodes (8): _apply_mutations(), _build_bullet(), _build_replacement(), Replace `run_el` with (before | <w:del> | <w:ins> | after). Like…, Return the introduction text ``full term (ACRO)`` for a track change., Render one issue as a single bullet line for the consolidated comment. Title…, Apply tracked-change rewrites and the comment-range anchor. Mutations are…, _split_run_for_track_change_only()

### Community 99 - "inspect_original_refs.py"
Cohesion: 0.25
Nodes (7): find_refs_section(), get_all_para_info(), Compare reference entry detection between original and output documents.…, Return info on every paragraph: (index, style, text[:120]), Find start index of References section and return (start, end) para indices., Mirror _select_reference_entries: prefer styled, fallback to heuristic., select_ref_entries()

### Community 101 - "permission"
Cohesion: 0.08
Nodes (24): git diff *, git log *, git status *, pip install *, pytest *, python *, python3 *, ruff check * (+16 more)

### Community 102 - "session_manager.py"
Cohesion: 0.20
Nodes (18): create_app(), Background thread that prunes expired session files every 5 minutes (D-06/D-07)., start_session_sweeper(), _sweep_loop(), start_session_sweeper(), _sweep_loop(), delete_session(), _delete_session_unlocked() (+10 more)

### Community 107 - "test_reporting_ownership.py"
Cohesion: 0.17
Nodes (8): app_domain, glob, _all_emitted_rule_ids(), _family(), Contract tests for reporting ownership (D-01 remediation, Phase 1). Every…, TestFamilyVerdictsCoverEverything, TestSamFixedIdsAreReal, TestSingleSource

### Community 108 - "Gurman — Data / Endpoint Tasks (Source of Truth)"
Cohesion: 0.15
Nodes (12): Backend truth (current codebase), G-01 — Endpoint inventory + contract doc (P0, unblocks H-01/H-02), G-02 — Upload + validation error-code map (P0, pairs H-02), G-03 — Processing poll/state machine + Cancel/timeout + carousel (P0, pairs H-03), G-04 — Results payload shape (P1, pairs H-04), G-05 — Download + retry semantics (P1, pairs H-05 — answers Humaid's open question), G-06 — Support/error passthrough (P2, pairs H-07), G-07 — Handoff: frontend data layer + open-questions log (P2, pairs H-01/Z-09) (+4 more)

### Community 109 - "_llm_resolve_mismatch"
Cohesion: 0.33
Nodes (6): _cr_item_summary(), _llm_check_reference(), _llm_resolve_mismatch(), Format the most identifying fields of a CrossRef record for an LLM prompt., Ask the LLM whether the CrossRef title/journal confirms the same paper despite…, Use the LLM to assess a reference that CrossRef could not verify. Returns…

### Community 110 - "docx"
Cohesion: 0.22
Nodes (10): docx, docx_enum_style, create_base_doc(), get_or_add_style(), Verify the generated APA7 Base Template.docx (C-47 acceptance). Checks:…, Reference entries must be justified (w:jc=both), not left-aligned. Two layers…, Return the w:jc value of the APA 7 reference style, or None., _ref_style_jc() (+2 more)

### Community 111 - "_find_word_anchor"
Cohesion: 0.50
Nodes (5): _find_word_anchor(), _iter_text_runs(), _Element, Yield (run, text) for body runs not inside tracked-change wrappers., Locate the first occurrence of ``word`` (case-sensitive, word-bounded) in the…

### Community 112 - "_llm_notes_to_results"
Cohesion: 0.50
Nodes (4): _extract_field(), _llm_notes_to_results(), Read a field from dict/object safely with a default., Normalize LLM editorial notes into validator-like result dictionaries.

### Community 113 - "_find_next_action"
Cohesion: 0.28
Nodes (8): _find_next_action(), _get_style_name(), _has_corrected_form_in_tracked_ins(), _iter_text_runs(), _Element, Return True if a sibling ``<w:ins>`` already supplies ``comma_value`` with the…, Return ``(run_el, start, end, check_kind, message, value)`` for the earliest…, Yield (run_element, text) for body-text runs we may safely modify. Skips runs…

### Community 114 - "_make_comment_element"
Cohesion: 0.16
Nodes (14): add_document_summary_comment(), add_paragraph_comment(), _append_author_query_runs(), _author_query_parts(), _make_comment_element(), _patch_content_types(), _patch_rels(), Ensure `document.xml.rels` contains the comments relationship. (+6 more)

### Community 115 - "vercel.json"
Cohesion: 0.50
Nodes (3): builds, routes, version

### Community 116 - "read_docx"
Cohesion: 0.67
Nodes (3): Document, Path, read_docx()

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

### Community 127 - "number_word_corrections.py"
Cohesion: 0.21
Nodes (13): _apply_corrections_to_para(), _bracket_spans(), _in_any_span(), _is_sentence_start(), _para_plain_text(), _Element, Spell out whole numbers 0-9 in running prose as tracked changes. Most academic…, Return character spans (start, end) covered by paren/bracket/brace pairs.… (+5 more)

### Community 128 - "applyFile"
Cohesion: 0.50
Nodes (4): applyFile(), checkReadable(), onFileDropped(), onFileSelected()

### Community 129 - "resetToUpload"
Cohesion: 0.50
Nodes (4): continueWithoutDownloading(), requestProcessAnother(), resetToUpload(), retryProcessing()

### Community 132 - "downloadUrl"
Cohesion: 0.67
Nodes (3): downloadUrl(), downloadFirst(), downloadManuscript()

### Community 136 - "acronym_store.py"
Cohesion: 0.15
Nodes (10): Persistent store for the editor-managed acronym allow-list. The list lives as a…, jutlp_validator_validator, C-22 direct-formatting path test. The 01_valid_identified fixture carries no…, # TODO: Delete script after completion of Track C, Runs build_edited_document on the 01_valid_identified.docx fixture and asserts…, # TODO: Delete script after completion of Track C, Runs build_edited_document on the 01_valid_identified.docx fixture, then…, shutil (+2 more)

## Knowledge Gaps
- **76 isolated node(s):** `setup.sh script`, `git diff *`, `git log *`, `git status *`, `pip install *` (+71 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 972 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_paragraphs()` connect `load_paragraphs` to `output_generation_samfix.py`, `validate`, `test_front_page_style_fixes.py`, `test_sentence_coherence_corrections.py`, `main.py`, `document_analysis_services.py`, `test_heading_corrections.py`, `test_output_generation.py`, `_apply_author_plan`, `test_spell_checker.py`, `keywordsFound`, `feedback_gen_pipeline.py`, `call_llm_json`, `build_prompts`, `output_generation.py`, `reference_checker.py`, `test_grammar_corrections.py`, `document_styling_fixes.py`, `_to_title_case_title`, `extract_references`, `body_llm_edits.py`, `test_upload_guardrails.py`, `run_editorial_review`, `test_abstract_length_rule.py`, `get_front_page`, `abstractFound`, `test_reference_checker.py`, `authorFormatCheck`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `LLMError` connect `LLMError` to `call_llm_json`, `test_sentence_coherence_corrections.py`, `reference_checker.py`, `test_grammar_corrections.py`, `_llm_resolve_mismatch`, `body_llm_edits.py`, `feedback_gen_pipeline.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `doc_analysis_pipeline()` connect `doc_analysis_pipeline` to `apply_acronym_corrections`, `validate`, `test_sentence_coherence_corrections.py`, `main.py`, `test_document_normalisation.py`, `test_abbreviation_corrections.py`, `gen_apa7_base_template.py`, `test_heading_corrections.py`, `test_output_generation.py`, `apply_caption_apa7_comments`, `blinded_citation_comments.py`, `test_appendix_removal.py`, `build_edited_document`, `feedback_gen_pipeline.py`, `reference_format_corrections.py`, `apply_number_word_corrections`, `test_table_keep_together.py`, `table_page_breaks.py`, `test_grammar_corrections.py`, `test_copyeditor_comment_regressions.py`, `cli_copybot.py`, `apply_table_n_notation_comments`, `apply_reference_order_comments`, `run_editorial_review`, `run_font_corrections.py`, `document_zones.py`, `apply_table_section_boundary_comments`, `Gurman — Sprint 2 Wiring Tasks (Frontend ↔ Backend Reference)`, `_make_comment_element`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **What connects `setup.sh script`, `git diff *`, `git log *` to the rest of the system?**
  _76 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `output_generation_samfix.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0431960049937578 - nodes in this community are weakly interconnected._
- **Should `apply_acronym_corrections` be split into smaller, more focused modules?**
  _Cohesion score 0.07254623044096728 - nodes in this community are weakly interconnected._
- **Should `validate` be split into smaller, more focused modules?**
  _Cohesion score 0.0635814889336016 - nodes in this community are weakly interconnected._