# Graph Report - Openeditor  (2026-10-10)

## Corpus Check
- 166 files · ~215,042 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 4, .css 2, .example 1)

## Summary
- 2925 nodes · 7005 edges · 119 communities (105 shown, 14 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 184 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0f10ac62`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- output_generation_samfix.py
- apply_acronym_corrections
- jutlp_validator.py
- grammar_corrections.py
- lxml
- reference_format_corrections.py
- test_sentence_coherence_corrections.py
- load_paragraphs
- main.py
- document_analysis_services.py
- normalise_docx
- test_abbreviation_corrections.py
- reference_reconstructor.py
- feedback_gen_pipeline.py
- apply_run_font_corrections
- test_front_page_style_fixes.py
- test_heading_corrections.py
- get_comment_anchor_texts
- pathlib
- rules
- acronym_corrections.py
- test_access_validation.py
- openeditor.js
- _apply_missing_practitioner_stub
- test_spell_checker.py
- blinded_citation_comments.py
- LLMError
- _make_comment_element
- keywordsFound
- Frontend-Backend API Contract
- _find_next_action
- test_decimal_corrections.py
- test_appendix_removal.py
- script.js
- acronym_store.py
- _insert_front_page_banner_from_template
- ParagraphRecord
- apply_number_word_corrections
- _find_target_para_index
- test_body_llm_edits.py
- reference_checker.py
- test_table_keep_together.py
- TRACK K — Evaluation Corpus + Conformance Harness · DEV TASK BACKLOG
- table_page_breaks.py
- jutlp_articles.py
- call_llm
- _apply_tracked_table_formatting
- document_styling_fixes.py
- test_copyeditor_comment_regressions.py
- _to_title_case_title
- extract_references
- cli_copybot.py
- table_n_notation_comments.py
- TestFiveFailuresFiveComments
- body_llm_edits.py
- document_normalisation_services.py
- 2. Revised Pipeline (`app/pipelines/feedback_gen_pipeline.py`)
- reference_order_comments.py
- test_acronym_api.py
- test_grammar_corrections.py
- run_editorial_review
- test_abstract_length_rule.py
- build_edited_document
- reference_type_checker.py
- _ensure_template_styles_available
- output_filename.py
- _build_zoned_docx
- test_reference_checker.py
- test_document_zones.py
- now_sydney_iso
- _read_doc_root
- test_output_generation.py
- check_references
- _iter_paren_citations
- apply_table_section_boundary_comments
- _apply_tracked_style_change
- results
- _make_textbox_wrap_around_text
- _normalise_surname
- _read_comments_root
- test_acronym_corrections.py
- output_generation.py
- 0. STAGE 0 — SEED SET + MINIMAL HARNESS + BASELINE (do this first)
- test_suspicious_ref_comments.py
- strip_leading_section_number
- test_body_font_enforcement.py
- _extract_ref_author_part
- TestPresentUnstyledDiscussionNoStub
- _is_appendix_heading
- NormalisationReport
- _ref_surname_keys
- test_reference_justification.py
- inspect_abstract.py
- _apply_intro_page_break
- TestValidDoc
- _update_progress
- Path
- graphify.js
- inspect_original_refs.py
- number_word_corrections.py
- setup.sh
- opencode.json
- app/__init__.py
- copybot
- check_entry_author
- APA 7 Rework Plan — OpenEditor (planning-only audit)
- Curated Reference Point.md
- test_allow_list_takes_precedence_over_block_list
- DEV TASK BACKLOG — TRACK C (APA‑7 deterministic/output layer)
- test_bare_use_before_inline_def_still_flagged
- _make_comment_element
- test_skips_heading_paragraphs
- vercel.json
- deployment.md
- _is_au_to_us_replacement
- _is_deidentified_manuscript

## God Nodes (most connected - your core abstractions)
1. `load_paragraphs()` - 91 edges
2. `build_edited_document()` - 60 edges
3. `validate()` - 57 edges
4. `generate_commented_docx()` - 45 edges
5. `doc_analysis_pipeline()` - 43 edges
6. `apply_acronym_corrections()` - 41 edges
7. `ParagraphRecord` - 39 edges
8. `documentBodyFormatCheck()` - 36 edges
9. `_apply_author_plan()` - 29 edges
10. `documentBodyFound()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `K-0.3 Minimal harness (3-5 checks) + accepted-changes view` --references--> `normalise_docx()`  [INFERRED]
  docs/apa7-backlog-K.md → app/services/document_normalisation_services.py
- `K-0.5a Baseline capture (in-process pipeline; LLM-off)` --references--> `validate()`  [INFERRED]
  docs/apa7-backlog-K.md → app/services/jutlp_validator.py
- `K-Inject — defect-injection tooling` --references--> `doc_analysis_pipeline()`  [INFERRED]
  docs/apa7-backlog-K.md → app/pipelines/feedback_gen_pipeline.py
- `Stage B — Phase 0: Normalisation` --references--> `normalise_docx()`  [INFERRED]
  docs/developer-handbook-revised.md → app/services/document_normalisation_services.py
- `E. Evaluation plan` --references--> `_max_revision_id()`  [INFERRED]
  docs/apa7-rework-plan.md → app/pipelines/feedback_gen_pipeline.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Canonical API Screen Flow** — app_templates_writer_four_stage_manuscript_workflow, docs_api_contract_processing_state_machine, docs_api_contract_results_status_mapping, docs_api_contract_idempotent_download [EXTRACTED 1.00]
- **Deterministic Validation Stack** — jutlp_validator_checklist_deterministic_jutlp_validation, jutlp_validator_checklist_paragraph_row_model, jutlp_validator_checklist_required_section_checks, jutlp_validator_checklist_front_page_checks, jutlp_validator_checklist_rule_report_format [EXTRACTED 1.00]
- **Manuscript Review Pipeline** — readme_open_editor_bot, readme_jutlp_manuscript_review, readme_openai_editorial_review, readme_flask_document_processing_pipeline [EXTRACTED 1.00]

## Communities (119 total, 14 thin omitted)

### Community 0 - "output_generation_samfix.py"
Cohesion: 0.04
Nodes (102): _ack_contains(), _all_alias_norms(), _append_author_query_runs(), _author_affiliation_marker_count(), _author_naming_pattern_valid(), _author_query_parts(), authorFormatCheck(), _authors_with_multiple_affiliation_markers() (+94 more)

### Community 1 - "apply_acronym_corrections"
Cohesion: 0.12
Nodes (16): apply_acronym_corrections(), Run the full acronym pass against ``input_path``, writing to ``output_path``.…, An introduction in the abstract does NOT satisfy the body's first-use rule., Conversely, text inside ``<w:del>`` represents tracked deletions — content the…, Block-listed tokens (USA, OK, NASA, iOS, …) never produce issues even when bare…, A novel acronym sitting next to block-listed tokens still fires., The abstract is an independent zone and needs its OWN introduction. An acronym…, If the docx already has comments from earlier passes, the new one gets the next… (+8 more)

### Community 2 - "jutlp_validator.py"
Cohesion: 0.06
Nodes (63): build_report(), check_abstract_single_paragraph(), check_block_quote_style(), check_body_paragraph_styles(), check_combined_results_discussion(), check_conclusion_length(), check_discussion_subsections(), check_dot_points() (+55 more)

### Community 3 - "grammar_corrections.py"
Cohesion: 0.06
Nodes (64): Deterministic abbreviation / journal-style fixes emitted as tracked changes.…, _make_comment_element(), _patch_content_types(), _patch_rels(), Replace the run with (before | comment-anchored content | after). When…, _split_run_for_action(), Flag content that appears AFTER the reference list (appendices). JUTLP house…, _needs_apa7_split() (+56 more)

### Community 4 - "lxml"
Cohesion: 0.06
Nodes (58): apply_citation_formatting_corrections(), _apply_corrections_to_para(), _Element, Insert missing space after p. / pp. in in-text page references. APA style…, Add a space after p./pp. before page numbers as tracked changes. Returns…, _apply_corrections_to_para(), apply_et_al_corrections(), _corrected_bracket() (+50 more)

### Community 5 - "reference_format_corrections.py"
Cohesion: 0.10
Nodes (29): heading_zone_transition(), initial_zone(), normalise_heading(), Lower-case, strip numeric prefix and trailing colon-suffix., Return the new zone given a heading paragraph's style and text. A real Heading…, Determine the starting zone for the very first paragraph. If the document has…, _apply_del_ins(), apply_reference_format_corrections() (+21 more)

### Community 6 - "test_sentence_coherence_corrections.py"
Cohesion: 0.07
Nodes (48): _build_user_prompt(), get_sentence_coherence_flags(), _is_usable_reason(), Call the LLM and return a list of ``{original, reason}`` dicts.…, True if ``reason`` is a real explanation, not a degenerate verdict. Guards…, io, pytest, _make_doc() (+40 more)

### Community 7 - "load_paragraphs"
Cohesion: 0.08
Nodes (49): detect_heading_level_1(), extract_heading_level_1_sections(), extract_main_sections(), extract_subsections(), load_paragraphs(), parse_docx_structure(), Return all non-empty Heading 1 sections in document order. `position` is the…, Scan a .docx file and return its Heading 1 section text and positions. (+41 more)

### Community 8 - "main.py"
Cohesion: 0.06
Nodes (53): _acronym_admin_active(), _acronym_admin_authed(), acronyms_admin_login(), acronyms_admin_logout(), acronyms_admin_page(), add_acronym_api(), analyse_cli(), _body_edit_items() (+45 more)

### Community 9 - "document_analysis_services.py"
Cohesion: 0.07
Nodes (38): _accepted_paragraph_text(), count_styles(), find_all_by_style(), find_all_heading1(), find_all_heading2(), front_page_summary(), _generic_sections(), get_front_page() (+30 more)

### Community 10 - "normalise_docx"
Cohesion: 0.32
Nodes (20): normalise_docx(), Write a normalised copy of `input_path` to `output_path` and return a report.…, _build_docx(), _Element, Path, Tests for the input-normalisation pass. Fixtures are built programmatically…, _read_document_xml(), test_accepts_tracked_insertions_and_deletions() (+12 more)

### Community 11 - "test_abbreviation_corrections.py"
Cohesion: 0.08
Nodes (49): apply_abbreviation_corrections(), _find_first_match(), _iter_text_runs(), _overlaps_quote(), _process_paragraph(), _Element, Return the earliest rule-match in ``text`` as ``(start, end, replacement,…, Apply every matching rule in ``para_el``, returning updated ``next_change_id``.… (+41 more)

### Community 12 - "reference_reconstructor.py"
Cohesion: 0.09
Nodes (46): build_apa7_from_crossref(), _build_book(), _build_book_chapter(), _build_dataset(), _build_dissertation(), _build_edited_book(), _build_journal_article(), _build_preprint() (+38 more)

### Community 13 - "feedback_gen_pipeline.py"
Cohesion: 0.09
Nodes (27): doc_analysis_pipeline(), _hyperlink_plain_urls_in_refs(), _inject_crossref_doi_links(), _normalise(), _patch_settings_show_markup(), Path, Remove Sam's comments (id > our_max_id) that duplicate our validator output.…, Append CrossRef-verified DOI hyperlinks as tracked insertions to reference… (+19 more)

### Community 14 - "apply_run_font_corrections"
Cohesion: 0.06
Nodes (44): _already_correct(), apply_reference_indent_corrections(), _is_heading(), _resolved_name(), _build_style_hanging_map(), _resolve(), _build_style_name_map(), _Element (+36 more)

### Community 15 - "test_front_page_style_fixes.py"
Cohesion: 0.06
Nodes (74): abstractFormatCheck(), abstractFound(), _append_affiliation_before_notes(), _append_body_comment(), _apply_author_plan(), _apply_document_body_plan(), _apply_front_page_asset_plan(), authorFound() (+66 more)

### Community 16 - "test_heading_corrections.py"
Cohesion: 0.08
Nodes (41): apply_heading_corrections(), _apply_tracked_edit(), _build_style_level_map(), _corrected_heading(), _direct_text_runs(), _heading_level(), _level_from_name(), _norm() (+33 more)

### Community 17 - "get_comment_anchor_texts"
Cohesion: 0.08
Nodes (33): _format_author_query_text(), generate_commented_docx(), Generate a reviewed `.docx` with inline comments and a validation summary page., Return the canonical section a fail-rule belongs to, or None. SEC001-008 map…, True if a Heading-1 paragraph is the section itself (exact / 'name:' prefix),…, _section_for_rule(), _section_heading_present(), count_comments_in_docx() (+25 more)

### Community 18 - "pathlib"
Cohesion: 0.08
Nodes (47): apply_caption_apa7_comments(), _iter_text_runs(), _Element, Emit one APA 7 caption-split comment per offending paragraph. Returns…, Yield (run_el, text) for runs we may safely anchor a comment on., Document, Path, read_docx() (+39 more)

### Community 19 - "rules"
Cohesion: 0.07
Nodes (8): fixture, rules(), TestDeidentifiedWithAuthorLeak, TestFrontPageIssues, TestMissingMethodSubsection, TestStructureAndEndmatterIssues, TestValidDeidentified, TestValidIdentified

### Community 20 - "acronym_corrections.py"
Cohesion: 0.10
Nodes (36): _append_author_query_runs(), _apply_mutations(), _author_query_parts(), _bracketed_spans(), _build_bullet(), _build_replacement(), _build_zone_map(), _collect_inline_definitions() (+28 more)

### Community 21 - "test_access_validation.py"
Cohesion: 0.13
Nodes (26): _require_access(), AccessResult, AccessStatus, check_access(), check_local_bypass(), Access validation service — G-07. Defines the authentication contract for…, Single entry point the Flask gate calls. Tries, in order: 1. Local SKIP_AUTH…, SKIP_AUTH must be explicitly 'true' (case-insensitive) — any other value,… (+18 more)

### Community 22 - "openeditor.js"
Cohesion: 0.09
Nodes (26): cancelJob(), CAROUSEL_ENABLED, downloadUrl(), fetchCarouselArticles(), _mapUploadErrorCode(), pollResults(), pollUntilDone(), STAGE_TO_STEP (+18 more)

### Community 23 - "_apply_missing_practitioner_stub"
Cohesion: 0.05
Nodes (44): _append_plain_text_run_with_size(), _apply_abstract_plan(), _flush(), _style_fix_pass(), _apply_heading_center_alignment(), _apply_heading_keep_next(), _apply_inline_keywords_split(), _apply_missing_keywords_stub() (+36 more)

### Community 24 - "test_spell_checker.py"
Cohesion: 0.06
Nodes (45): find_quote_spans(), is_in_quote(), Return True when the half-open range ``[start, end)`` overlaps any quotation…, Return a list of ``(start, end)`` half-open intervals locating every paired-…, _build_word_counts(), _classify_word(), _freq_ratio(), get_spell_corrections() (+37 more)

### Community 25 - "blinded_citation_comments.py"
Cohesion: 0.17
Nodes (21): _anchor_paragraph_comment(), apply_blinded_citation_comments(), _build_comment(), _classify(), _distinct(), _own_text_runs(), _Element, Flag blinded / placeholder citations and self-references. For peer review… (+13 more)

### Community 26 - "LLMError"
Cohesion: 0.10
Nodes (34): call_llm_json(), get_client(), LLMError, Exception, Raised when the LLM call fails after retries., Create an OpenAI client., _build_user_prompt(), _clean_one() (+26 more)

### Community 27 - "_make_comment_element"
Cohesion: 0.16
Nodes (17): _build_comment_ref_run(), _find_span(), _inject_comment_markers(), _inject_comment_markers_for_phrase(), _make_inserted_heading_paragraph(), _Element, Fallback comment anchor: wrap the whole paragraph. We only use this when…, Build `<w:r><w:commentReference .../></w:r>` for the inline comment mark. (+9 more)

### Community 28 - "keywordsFound"
Cohesion: 0.07
Nodes (36): _apply_keywords_plan(), citationFound(), _extract_keywords_list(), _find_abstract_heading_in_front(), _find_blank_line_after_index(), _find_citation_heading_in_front(), _find_introduction_heading_in_front(), _find_keywords_heading_in_front() (+28 more)

### Community 29 - "Frontend-Backend API Contract"
Cohesion: 0.07
Nodes (32): Graphify Knowledge Graph, OAPA Brand Mark, Acronym Management UI, Editor Admin Authentication, Persistent Acronym Storage, Editorial Access Gate, Shared Password Authentication, Client-Side Manuscript Validation (+24 more)

### Community 30 - "_find_next_action"
Cohesion: 0.24
Nodes (10): _find_next_action(), _get_style_name(), _has_corrected_form_in_tracked_ins(), _iter_text_runs(), _process_paragraph(), _Element, Return True if a sibling ``<w:ins>`` already supplies ``comma_value`` with the…, Return ``(run_el, start, end, check_kind, message, value)`` for the earliest… (+2 more)

### Community 31 - "test_decimal_corrections.py"
Cohesion: 0.11
Nodes (28): apply_decimal_corrections(), Run both decimal checks over ``input_path`` and write to ``output_path``.…, _build_docx(), _Element, Path, Tests for the decimal-precision and comma-as-decimal checks., The classic example: thousand separators and comma-decimals together., The example from the client's brief, end-to-end. (+20 more)

### Community 32 - "test_appendix_removal.py"
Cohesion: 0.12
Nodes (36): _anchor_comment_on_paragraph(), apply_appendix_removal(), _find_appendix_start(), _is_appendix_heading(), _is_heading_paragraph(), _paragraph_has_image(), _passthrough(), _Element (+28 more)

### Community 33 - "script.js"
Cohesion: 0.10
Nodes (28): _activateStep(), _clearPollDelay(), clearUploadError(), displayFile(), fetchJutlpArticles(), finishStepAnimation(), groupItems(), JUTLP_FALLBACK_ARTICLE (+20 more)

### Community 34 - "acronym_store.py"
Cohesion: 0.12
Nodes (27): add_acronym(), _ensure_file_exists(), load_acronyms(), _load_seed(), Path, Persistent store for the editor-managed acronym allow-list. The list lives as a…, Restore the on-disk store to the bundled seed. Used by tests., Return the bundled seed JSON as a fresh dict. (+19 more)

### Community 35 - "_insert_front_page_banner_from_template"
Cohesion: 0.12
Nodes (23): _collect_image_rel_ids(), _doc_has_first_page_header_picture(), _ensure_first_footer(), _ensure_first_header(), _ensure_image_content_types(), _find_first_footer_ref(), _find_first_header_ref(), _find_first_picture_paragraph() (+15 more)

### Community 36 - "ParagraphRecord"
Cohesion: 0.10
Nodes (30): Few-shot editorial examples extracted from real JUTLP editor decisions. These…, JUTLP editorial guidelines extracted from 'JUTLP Template 2026.docx'. Last…, ParagraphRecord, build_prompts(), _build_system_prompt(), _build_user_prompt(), _canonical_section_for(), _extract_front_page_content() (+22 more)

### Community 37 - "apply_number_word_corrections"
Cohesion: 0.16
Nodes (30): apply_number_word_corrections(), Scan body paragraphs and emit tracked-change replacements for digits 0-9.…, _build_docx_with_paragraph(), _count_changes(), Path, Tests for digit-to-word tracked-change corrections. These tests build minimal…, A digit INSIDE quoted text retains the source's form., Unquoted digit in a paragraph that also has a quoted digit must still be… (+22 more)

### Community 38 - "_find_target_para_index"
Cohesion: 0.11
Nodes (31): _find_after(), _find_first_heading(), _find_first_non_empty_para(), _find_front_matter_anchor(), _find_front_matter_rule_anchor(), _find_front_style(), _find_front_text(), _find_heading() (+23 more)

### Community 39 - "test_body_llm_edits.py"
Cohesion: 0.06
Nodes (51): _propagate_repeated_edits(), Apply accepted exact edits to repeated matching body text. The LLM reviews each…, _validate_edit(), _apply_body_and_reference_style_fixes(), _apply_body_edit_plan(), _apply_intra_paragraph_tracked_replace(), Apply tracked style changes for body and reference paragraphs: - Required body…, _paragraph_with_runs() (+43 more)

### Community 40 - "reference_checker.py"
Cohesion: 0.08
Nodes (40): build_reference_report(), _cache_get(), _cache_set(), check_and_report(), check_duplicate_references(), check_orphan_citations(), check_reference_citations(), check_references() (+32 more)

### Community 41 - "test_table_keep_together.py"
Cohesion: 0.14
Nodes (26): _apply_caption_keep_next(), apply_table_keep_together(), _ensure_keep_next(), _ensure_trpr(), _ensure_trpr_child(), _para_style(), _para_text(), _Element (+18 more)

### Community 42 - "TRACK K — Evaluation Corpus + Conformance Harness · DEV TASK BACKLOG"
Cohesion: 0.11
Nodes (18): _max_revision_id(), Return the largest ``w:id`` on any tracked-change element in the doc. Tracked-…, 1. TICKETS BY GROUP, 2. STAGE GATES & DEMO ARTEFACTS, 3. DEPENDENCY GRAPH & CRITICAL PATH, 4. PARALLELISATION INSIDE K (2 people), 5. CROSS-TRACK REQUESTS, 6. RISKS, OPEN DECISIONS, OUT-OF-SCOPE (+10 more)

### Community 43 - "table_page_breaks.py"
Cohesion: 0.20
Nodes (26): apply_table_page_breaks(), _cell_text(), _make_page_break_paragraph(), _page_break_anchor(), _para_has_page_break(), _para_style(), _para_text(), _preceded_by_page_break() (+18 more)

### Community 44 - "jutlp_articles.py"
Cohesion: 0.17
Nodes (26): _abstract_candidates(), _article_details_url(), _clean_abstract_candidate(), _clean_text(), _extract_abstract(), _extract_article_urls(), _extract_author(), _extract_title() (+18 more)

### Community 45 - "call_llm"
Cohesion: 0.29
Nodes (7): call_llm(), Send a structured-output request to the OpenAI Chat Completions API. Returns…, _mock_response(), patch, Build a mock ChatCompletion response., TestCallLlm, TestGetClient

### Community 46 - "_apply_tracked_table_formatting"
Cohesion: 0.18
Nodes (19): _apply_body_run_format(), _apply_tracked_body_format_fixes(), _apply_tracked_body_paragraph_format(), _apply_tracked_body_run_format(), _apply_tracked_table_cell_borders(), _apply_tracked_table_formatting(), _apply_tracked_table_properties(), _apply_tracked_table_run_format() (+11 more)

### Community 47 - "document_styling_fixes.py"
Cohesion: 0.33
Nodes (11): _canonical_index(), _collect_until(), compare_document_styles(), compare_template_and_document(), extract_headings(), extract_template_styles(), _find_first_text(), _front_page_limit() (+3 more)

### Community 48 - "test_copyeditor_comment_regressions.py"
Cohesion: 0.08
Nodes (44): Renumber visible Author Query labels after every comment pass has run., _renumber_final_author_queries(), apply_au_spelling_corrections(), Build one Word comment for all AU spelling replacements., Scan every eligible paragraph and apply AU spelling tracked changes. Returns…, Return one summary entry per repeated spelling correction. The tracked-change…, _spelling_comment_text(), _spelling_summary_comment_text() (+36 more)

### Community 49 - "_to_title_case_title"
Cohesion: 0.07
Nodes (38): _append_plain_text_run(), _append_text_with_line_breaks(), _append_text_with_superscript_markers(), _append_tracked_replace(), _apply_heading_2_title_case(), _apply_table_caption_formatting(), _apply_table_paragraph_style(), _apply_title_plan() (+30 more)

### Community 50 - "extract_references"
Cohesion: 0.16
Nodes (12): extract_references(), Return ``(start_index, end_index)`` bounding the References section. ``start``…, Two-tier reference selection used by BOTH extraction and comment anchoring so…, _references_window(), _select_reference_entries(), _build_docx_with_sections(), A paper with reference-styled paragraphs but NO References heading still has…, Build a docx from a list of (kind, text) blocks. kind: "h1" → Heading 1, "ref"… (+4 more)

### Community 51 - "cli_copybot.py"
Cohesion: 0.23
Nodes (17): _heading_level_1_sections(), _is_generic_copyedit_output(), main(), _print_heading_normalization_summary(), Path, _rename_generic_copyedit_output(), _show_heading_level_1_sections(), _status() (+9 more)

### Community 52 - "table_n_notation_comments.py"
Cohesion: 0.15
Nodes (21): apply_table_n_notation_comments(), _is_capital_n_header(), _iter_text_runs(), _Element, Flag capital "N" used as a table column header. In statistical reporting the…, Yield (run_el, text) for runs we may safely anchor a comment on., True when the paragraph is a table cell whose only content is "N"., Emit one comment per table column header that is a bare capital "N". Returns… (+13 more)

### Community 53 - "TestFiveFailuresFiveComments"
Cohesion: 0.10
Nodes (8): has_comments_content_type(), has_comments_relationship(), Return ordered list of (text, has_ins, [commentRangeStart ids]) for every…, The combined 'Results and Discussion' fixture has no standalone Discussion…, SEC005 + DIS001-003 comments anchor inside the inserted Discussion stub, NOT on…, The inserted Discussion stub sits after Results and before References in…, TestFiveFailuresFiveComments, TestOneFailureOneComment

### Community 54 - "body_llm_edits.py"
Cohesion: 0.12
Nodes (21): _body_paragraphs(), build_body_edit_plan(), _dedupe_edits(), _fix_au_spellings(), _is_skippable_paragraph(), _llm_edits_for_paragraph(), LLM-generated surgical copy-edits for the document body. Produces tracked-…, Return the symmetric token difference between ``find`` and ``replace``. Tokens… (+13 more)

### Community 55 - "document_normalisation_services.py"
Cohesion: 0.17
Nodes (18): _accept_tracked_changes(), _ancestor_paragraph_index(), _delete_guidance_paragraphs(), _is_paragraph_blank(), _Element, Strip author-supplied formatting noise from incoming .docx files. Authors…, Replace `element` with its children in the parent., Resolve all tracked-change wrappers as if 'Accept All Changes' was clicked. -… (+10 more)

### Community 56 - "2. Revised Pipeline (`app/pipelines/feedback_gen_pipeline.py`)"
Cohesion: 0.12
Nodes (16): 1. What Changed vs. CopyBot, 2. Revised Pipeline (`app/pipelines/feedback_gen_pipeline.py`), 3. Track C / Track D Work Plan (condensed), 4. Service Inventory (disposition), 5. Risks & Open Questions, 6. Flowchart (revised), OpenEditor — Developer Handbook (Proposed Revision), Stage A — Upload & guards (`app/main.py`) (+8 more)

### Community 57 - "reference_order_comments.py"
Cohesion: 0.17
Nodes (21): _anchor_comment_on_paragraph(), apply_reference_order_comments(), _build_comment(), _find_references_heading(), _first_inversion(), _passthrough(), _Element, Flag a reference list that is not in alphabetical order. APA 7 (which JUTLP… (+13 more)

### Community 58 - "test_acronym_api.py"
Cohesion: 0.10
Nodes (9): importlib, client(), gated_client(), fixture, Smoke tests for the acronym admin HTTP endpoints. Skipped when Flask isn't…, Read-only access stays open so the pipeline can still load the list., Boot the Flask app with auth disabled and the store pointed at tmp., Boot the app with the editor-password gate enabled. (+1 more)

### Community 59 - "test_grammar_corrections.py"
Cohesion: 0.11
Nodes (27): app_services, _build_user_prompt(), _fix_au_spellings(), get_grammar_corrections(), _is_proper_noun_correction(), Remove parenthetical citations and URLs before sending to LLM., Return True if original looks like a proper noun, surname, acronym, or tech…, Replace any US spellings in text with AU equivalents using AU_CORRECTIONS. (+19 more)

### Community 60 - "run_editorial_review"
Cohesion: 0.06
Nodes (51): EditorialNote, EditorialReviewResult, LLM verdict on a single deterministic structural check result., StructuralValidation, Run LLM-based editorial review on a JUTLP manuscript. Pipeline: 1. Parse DOCX…, run_editorial_review(), _strip_internal_markers(), build_editorial_review_comment_plan() (+43 more)

### Community 61 - "test_abstract_length_rule.py"
Cohesion: 0.16
Nodes (22): estimate_line_count(), extract_abstract(), _is_abstract_boundary(), Estimate how many rendered lines ``text`` occupies. Takes the larger of the…, word_count(), check_abstract(), _fp008(), _long_abstract_doc() (+14 more)

### Community 62 - "build_edited_document"
Cohesion: 0.10
Nodes (34): _apply_citation_plan(), _apply_editorial_review_comment_plan(), _apply_heading_1_text_normalization(), _apply_intro_page_break(), build_edited_document(), build_front_page_asset_check_plan(), _canonical_heading_1_text(), citationFormatCheck() (+26 more)

### Community 63 - "reference_type_checker.py"
Cohesion: 0.19
Nodes (18): _check_book(), _check_book_chapter(), _check_conference(), _check_dataset(), _check_journal(), _check_podcast(), check_reference_type_style(), _check_report() (+10 more)

### Community 64 - "_ensure_template_styles_available"
Cohesion: 0.25
Nodes (9): _apply_normal_style_fix(), _ensure_template_styles_available(), _load_template_style_names(), Repack the docx zip replacing only word/styles.xml; all other entries are…, _resolve_style_id(), _resolve_style_name(), _save_styles_xml_to_zip(), _style_matches_template() (+1 more)

### Community 65 - "output_filename.py"
Cohesion: 0.25
Nodes (16): build_output_filename(), build_output_filename_from_author_line(), _first_author_last_name(), _get_author_line_and_markers(), _get_document_year(), _remove_superscript_runs_from_author_line(), _unique_output_filename(), datetime (+8 more)

### Community 66 - "_build_zoned_docx"
Cohesion: 0.12
Nodes (16): _build_zoned_docx(), Truly unknown acronyms in the abstract (no allow-list, no inline def anywhere)…, OECD and UNESCO are on the client's approved-acronyms list — bare body use…, Regression: an introduction WITHIN the abstract silences later abstract uses…, Anything from Acknowledgements onwards is outside the bot's scope., Build a docx where each entry is (style or None, text). A ``None`` style…, Once introduced in the body, later body uses are correct journal style., Acronyms inside `(...)` are definitions or citations — never flag. (+8 more)

### Community 67 - "test_reference_checker.py"
Cohesion: 0.23
Nodes (9): check_text_dois(), DOIT: Validate every DOI-shaped substring found in the plain text of each…, _cr_item(), Return a fake ``_lookup_doi`` that resolves DOIs from a dict. ``None`` value…, A reference that quotes the same DOI twice (bare + URL form) should only hit…, _stub_lookup(), TestCheckTextDOIs, _spy() (+1 more)

### Community 68 - "test_document_zones.py"
Cohesion: 0.54
Nodes (7): _make_doc(), test_body_sentence_mentioning_references_is_not_boundary(), test_decimal_checks_skip_unstyled_acknowledgements_and_refs(), test_number_words_skip_unstyled_references_section(), test_unstyled_intro_and_reference_aliases_set_zones(), test_unstyled_references_without_intro_starts_as_body_then_exits(), _zones()

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
Cohesion: 0.16
Nodes (28): para_plain_text(), Concatenate every visible ``w:t`` text node inside the paragraph., _anchor_paragraph(), apply_table_section_boundary_comments(), _classify(), _iter_text_runs(), _Element, Flag sections that open or close directly with a table. JUTLP/APA style expects… (+20 more)

### Community 75 - "_apply_tracked_style_change"
Cohesion: 0.25
Nodes (14): _apply_style_if_needed(), _apply_tracked_style_change(), Remove direct formatting that would override a heading style. A paragraph that…, _strip_conflicting_direct_format_for_heading(), _body_para(), _ppr(), A body paragraph restyled to a heading must shed its body formatting. When the…, Only size/spacing are stripped — bold stays (headings are bold anyway). (+6 more)

### Community 76 - "results"
Cohesion: 0.17
Nodes (9): _build_summary(), _dedup_sam_issues(), _llm_notes_to_results(), Convert Sam's build_edited_document plan into frontend issue dicts., Remove Sam's issues that duplicate existing ones (3+ significant word overlap)., Poll for analysis results. --- tags: - Results parameters: - in: path name:…, results(), _sam_plan_to_issues() (+1 more)

### Community 77 - "_make_textbox_wrap_around_text"
Cohesion: 0.29
Nodes (12): _make_textbox_wrap_around_text(), Make a front-page floating textbox use *square* text-wrapping so the…, _anchor_para(), _Element, The front-page editorial textbox must wrap text around it, not overlay it. The…, Schema order: the wrap element must precede docPr in the anchor., test_behinddoc_is_cleared(), test_breathing_margins_added() (+4 more)

### Community 78 - "_normalise_surname"
Cohesion: 0.36
Nodes (3): _normalise_surname(), Lowercase, strip accents, punctuation, and possessive 's for fuzzy match.…, TestNormaliseSurname

### Community 79 - "_read_comments_root"
Cohesion: 0.22
Nodes (11): _comment_visible_text(), _Element, Concatenate every ``<w:t>`` text under the comments root., When the author DID introduce the acronym in the body, no issue fires., Allow-listed acronyms in the abstract are silent — no flagging., When a track change is proposed, the bullet mentions it so the editor knows…, _read_comments_root(), test_abstract_allow_listed_silent() (+3 more)

### Community 80 - "test_acronym_corrections.py"
Cohesion: 0.24
Nodes (11): _format_author_query_text(), _matches_definition(), Attempt to align ``letters`` against the leading section of ``words``. Walks…, If `words` contain a valid full form for `acro`, return the phrase. Walks the…, _try_match_definition(), Tests for acronym detection + consolidated comment + tracked-change rewrites., test_acronym_author_query_comment_text_is_numbered(), test_matches_definition_rejects_non_initialism() (+3 more)

### Community 81 - "output_generation.py"
Cohesion: 0.11
Nodes (23): _append_author_query_runs(), _append_validation_summary(), _author_query_parts(), _comment_group_key(), _dedupe_pending_comments(), _extract_field(), _format_summary_line(), _group_pending_comments() (+15 more)

### Community 82 - "0. STAGE 0 — SEED SET + MINIMAL HARNESS + BASELINE (do this first)"
Cohesion: 0.18
Nodes (11): 0. STAGE 0 — SEED SET + MINIMAL HARNESS + BASELINE (do this first), K-0.0 Scaffolding, K-0.1 Seed corpus (exactly 4 web-sourced APA-7 docs), K-0.2 Upload-gate test, K-0.3 Minimal harness (3-5 checks) + accepted-changes view, K-0.3a Synthetic known-good fixture (python-docx), K-0.4 Effective-format resolver (style inheritance through basedOn + docDefaults + theme), K-0.5 BASELINE RUN of unmodified engine (capture + score) (+3 more)

### Community 83 - "test_suspicious_ref_comments.py"
Cohesion: 0.22
Nodes (15): _has_reference_issue_summary_comment(), _insert_suspicious_ref_comments(), Add Word comments for reference issues: - CONS001/CONS002 citation-consistency…, _build_docx(), _comment_anchor_texts(), _comment_texts(), Path, Regression test for the suspicious-reference comment pass. This pass… (+7 more)

### Community 84 - "strip_leading_section_number"
Cohesion: 0.13
Nodes (17): _build_section_rename_map(), _merges_two_sections(), _normalise_subsection(), Remove a leading heading number from ``text`` (e.g. "2. Literature" ->…, Lower-case, collapse whitespace, strip a leading heading number and any…, Return the canonical main section a heading fragment names, or None. Matches…, True when ``alias`` merges two *distinct* canonical sections (e.g. "Results and…, ``normalised alias -> canonical label`` for safe heading renames. Built from… (+9 more)

### Community 85 - "test_body_font_enforcement.py"
Cohesion: 0.31
Nodes (9): _ensure_normal_style_body_rpr(), _passthrough_copy(), Pin the body font + size on the Normal style's run properties. The template's…, _doc_with_normal(), _normal_rpr(), Tests for body-font enforcement: the Normal style must carry Arial 11pt so…, A docx whose Normal style is a non-template font/size., test_already_correct_normal_style_no_change() (+1 more)

### Community 86 - "_extract_ref_author_part"
Cohesion: 0.15
Nodes (8): _extract_ref_author_part(), _normalise_text(), Return the author/group-author portion of a reference entry. Slices everything…, Replace curly quotes with their straight ASCII equivalents., Return ``(normalised_surname, display_surname)`` for a reference entry, or None…, _sort_key_and_label(), TestCitationRegexes, TestExtractRefAuthorPart

### Community 87 - "TestPresentUnstyledDiscussionNoStub"
Cohesion: 0.31
Nodes (4): A Discussion section that is present but not yet Heading-1 styled (the author…, No tracked-inserted 'Discussion' heading paragraph should exist., The Discussion-subsection comment must anchor on the original (non-inserted)…, TestPresentUnstyledDiscussionNoStub

### Community 88 - "_is_appendix_heading"
Cohesion: 0.38
Nodes (5): _extract_ref_hyperlinks(), _is_appendix_heading(), Return (entry_num, ref_text, url) for reference entries that already have a…, parametrize, TestIsAppendixHeading

### Community 89 - "NormalisationReport"
Cohesion: 0.20
Nodes (7): NormalisationReport, Path, Counts of what was changed during normalisation. Aggregate counts feed the…, Human-readable single-line summary for the document comment., Write an audit JSON next to ``docx_path`` listing every strip. Returns the path…, test_blank_paragraph_count_in_summary(), test_summary_text_is_human_readable()

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

### Community 98 - "inspect_original_refs.py"
Cohesion: 0.25
Nodes (7): find_refs_section(), get_all_para_info(), Compare reference entry detection between original and output documents.…, Return info on every paragraph: (index, style, text[:120]), Find start index of References section and return (start, end) para indices., Mirror _select_reference_entries: prefer styled, fallback to heuristic., select_ref_entries()

### Community 99 - "number_word_corrections.py"
Cohesion: 0.21
Nodes (13): _apply_corrections_to_para(), _bracket_spans(), _in_any_span(), _is_sentence_start(), _para_plain_text(), _Element, Spell out whole numbers 0-9 in running prose as tracked changes. Most academic…, Return character spans (start, end) covered by paren/bracket/brace pairs.… (+5 more)

### Community 108 - "APA 7 Rework Plan — OpenEditor (planning-only audit)"
Cohesion: 0.33
Nodes (5): A. APA 7 rule matrix (from apastyle.apa.org primary sources), APA 7 Rework Plan — OpenEditor (planning-only audit), C. Architecture recommendation, D. Prioritised work breakdown — stages, not weeks, E. Evaluation plan

### Community 111 - "DEV TASK BACKLOG — TRACK C (APA‑7 deterministic/output layer)"
Cohesion: 0.15
Nodes (12): 0. STAGE 0 — SAFETY NET, 2. STAGE 3 — PLUMBING, TESTS, SHIP, 2. STAGE GATES (runnable), 3. DEPENDENCY GRAPH + CRITICAL PATH, 4. PARALLELISATION INSIDE C (3–4 people) + HOT FILES, 5. CROSS-TRACK REQUESTS, 6. RISKS / OPEN DECISIONS / OUT OF SCOPE, C‑Plumbing (+4 more)

### Community 113 - "_make_comment_element"
Cohesion: 0.20
Nodes (12): add_document_summary_comment(), add_paragraph_comment(), _make_comment_element(), _patch_content_types(), _patch_rels(), Ensure `document.xml.rels` contains the comments relationship., Ensure `[Content_Types].xml` declares `word/comments.xml`., Attach a single document-level Word comment to the first body paragraph. Used… (+4 more)

### Community 115 - "vercel.json"
Cohesion: 0.50
Nodes (3): builds, routes, version

### Community 119 - "_is_au_to_us_replacement"
Cohesion: 0.17
Nodes (11): _has_au_us_suffix_swap(), _is_au_to_us_replacement(), Return True if the correction would flip Australian English to American English., Stage 2 — Passes + safety, Create, Delete, Track C — Deterministic / Output, Track C & Track D — Comprehensive Checklists (+3 more)

### Community 120 - "_is_deidentified_manuscript"
Cohesion: 0.19
Nodes (14): _front_page_paragraphs_for_deid(), _is_deidentified_manuscript(), Read up to the first ~15 front-page paragraphs of ``docxpath``. Used by the…, Return True if the manuscript was deliberately stripped of identity. Three…, _make_deid_state(), Minimal abstract_state stub — the deidentified check only reads docxpath., Plain `[Authors removed for blind review]` placeholder anywhere in the front-…, The placeholder regex covers the 'Affiliations removed' phrasing too. (+6 more)

## Knowledge Gaps
- **72 isolated node(s):** `Curated Refernce point`, `K-0.0 Scaffolding`, `K-0.1 Seed corpus (exactly 4 web-sourced APA-7 docs)`, `K-0.2 Upload-gate test`, `K-0.3a Synthetic known-good fixture (python-docx)` (+67 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 889 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_paragraphs()` connect `load_paragraphs` to `output_generation_samfix.py`, `jutlp_validator.py`, `grammar_corrections.py`, `test_sentence_coherence_corrections.py`, `main.py`, `document_analysis_services.py`, `feedback_gen_pipeline.py`, `test_front_page_style_fixes.py`, `test_heading_corrections.py`, `get_comment_anchor_texts`, `_apply_missing_practitioner_stub`, `test_spell_checker.py`, `keywordsFound`, `ParagraphRecord`, `reference_checker.py`, `document_styling_fixes.py`, `extract_references`, `body_llm_edits.py`, `test_grammar_corrections.py`, `run_editorial_review`, `test_abstract_length_rule.py`, `output_filename.py`, `test_reference_checker.py`, `output_generation.py`, `_is_deidentified_manuscript`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `doc_analysis_pipeline()` connect `feedback_gen_pipeline.py` to `apply_acronym_corrections`, `grammar_corrections.py`, `reference_format_corrections.py`, `main.py`, `normalise_docx`, `test_abbreviation_corrections.py`, `apply_run_font_corrections`, `test_heading_corrections.py`, `get_comment_anchor_texts`, `pathlib`, `blinded_citation_comments.py`, `test_decimal_corrections.py`, `test_appendix_removal.py`, `apply_number_word_corrections`, `reference_checker.py`, `test_table_keep_together.py`, `TRACK K — Evaluation Corpus + Conformance Harness · DEV TASK BACKLOG`, `table_page_breaks.py`, `test_copyeditor_comment_regressions.py`, `table_n_notation_comments.py`, `reference_order_comments.py`, `run_editorial_review`, `build_edited_document`, `apply_table_section_boundary_comments`, `test_suspicious_ref_comments.py`, `_update_progress`, `DEV TASK BACKLOG — TRACK C (APA‑7 deterministic/output layer)`, `_make_comment_element`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `load_acronyms()` connect `acronym_store.py` to `output_generation_samfix.py`, `apply_acronym_corrections`, `main.py`, `_to_title_case_title`, `acronym_corrections.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `build_edited_document()` (e.g. with `4. PARALLELISATION INSIDE C (3–4 people) + HOT FILES` and `Key verifications / plan-vs-code contradictions`) actually correct?**
  _`build_edited_document()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `validate()` (e.g. with `C‑Validator` and `Key verifications / plan-vs-code contradictions`) actually correct?**
  _`validate()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Curated Refernce point`, `K-0.0 Scaffolding`, `K-0.1 Seed corpus (exactly 4 web-sourced APA-7 docs)` to the rest of the system?**
  _72 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `output_generation_samfix.py` be split into smaller, more focused modules?**
  _Cohesion score 0.036344755970924195 - nodes in this community are weakly interconnected._