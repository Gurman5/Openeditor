# Graph Report - Openeditor  (2026-10-19)

## Corpus Check
- 253 files · ~280,159 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 14 file(s) not represented in the graph (top: (none) 8, .css 2, .example 1)

## Summary
- 3684 nodes · 8627 edges · 156 communities (140 shown, 16 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 189 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `18f0410b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _insert_front_page_banner_from_template
- _build_zoned_docx
- validate
- test_front_page_style_fixes.py
- language_corrections.py
- apa7_formatting_checks.py
- test_sentence_coherence_corrections.py
- load_paragraphs
- main.py
- document_analysis_services.py
- normalise_docx
- test_abbreviation_corrections.py
- reference_reconstructor.py
- apply_caption_apa7_comments
- gen_apa7_base_template.py
- output_generation_samfix.py
- test_heading_corrections.py
- generate_commented_docx
- test_heading_style_apa11.py
- rules
- apply_acronym_corrections
- test_access_validation.py
- openeditor.js
- test_intro_page_break.py
- test_spell_checker.py
- shutil
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
- _find_target_para_index
- cli_copybot.py
- reference_checker.py
- test_table_keep_together.py
- generate_keywords
- table_page_breaks.py
- jutlp_articles.py
- test_font_sweep.py
- results
- canonical_jultp_template.py
- test_copyeditor_comment_regressions.py
- doc_analysis_pipeline
- test_reference_checker.py
- test_suspicious_ref_comments.py
- apply_table_n_notation_comments
- TestFiveFailuresFiveComments
- _apply_author_plan
- pytest
- test_references_block_corrections.py
- apply_reference_order_comments
- test_acronym_api.py
- apply_reference_indent_corrections
- editorial_review_comments.py
- test_abstract_length_rule.py
- _make_textbox_wrap_around_text
- reference_type_checker.py
- test_abstract_keywords_formatting.py
- apa7_validator.py
- abstractFound
- check_text_dois
- abstract_keywords_formatting.py
- _to_title_case_title
- _read_doc_root
- _find_target_para_index
- check_entry_author
- _iter_paren_citations
- body_llm_edits.py
- _apply_tracked_style_change
- test_reporting_ownership.py
- _normalise_heading_text
- _normalise_surname
- _read_comments_root
- output_filename.py
- output_generation.py
- test_acronym_corrections.py
- LLMError
- canonical_jultp_template.py
- test_body_llm_edits.py
- _normalise_text
- TestPresentUnstyledDiscussionNoStub
- check_submitted_hyperlinks
- subsection_alias_match
- _extract_ref_author_part
- TRACK K — Evaluation Corpus + Conformance Harness · DEV TASK BACKLOG
- inspect_abstract.py
- DEV TASK BACKLOG — TRACK D (LLM layer)
- TestValidDoc
- _update_progress
- Path
- graphify.js
- session_manager.py
- now_sydney_iso
- setup.sh
- opencode.json
- lxml
- copybot
- _apply_apa_title_page
- docx
- run_editorial_review
- docx
- test_output_generation.py
- test_block_list_does_not_swallow_real_acronyms
- add_document_summary_comment
- _Element
- vercel.json
- _find_front_matter_rule_anchor
- deployment.md
- _is_deidentified_manuscript
- apply_blinded_citation_comments
- test_body_font_enforcement.py
- apply_table_section_boundary_comments
- test_abstract_stops_at_introduction_heading
- test_normal_styled_abstract_is_measured
- _fake_llm
- api.js
- startProcessing
- editorial_review_service.py
- applyFile
- resetToUpload
- _get
- document_zones.py
- downloadUrl
- test_run_font_corrections.py
- test_abstract_silent_when_introduced_in_abstract
- _apply_phrase_correction
- build_edited_document
- DEV TASK BACKLOG — TRACK C (APA‑7 deterministic/output layer)
- test_acronym_inside_parentheses_is_skipped
- test_zone_transition_handles_numbered_heading_prefix
- blinded_citation_comments.py
- _llm_notes_to_results
- _find_next_action
- _sam_plan_to_issues
- test_apa7_title_page.py
- read_docx
- Track C — Deterministic / Output
- test_numbered_section_detection.py
- _accepted_paragraph_text
- _try_match_definition
- _front_page_paragraphs_for_deid
- Curated Refernce point (1).md
- test_allow_list_takes_precedence_over_block_list

## God Nodes (most connected - your core abstractions)
1. `load_paragraphs()` - 100 edges
2. `build_edited_document()` - 70 edges
3. `validate()` - 65 edges
4. `generate_commented_docx()` - 45 edges
5. `doc_analysis_pipeline()` - 43 edges
6. `apply_acronym_corrections()` - 42 edges
7. `ParagraphRecord` - 39 edges
8. `documentBodyFormatCheck()` - 37 edges
9. `apply_run_font_corrections()` - 36 edges
10. `documentBodyFound()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `validate()` --references--> `C‑Validator`  [INFERRED]
  app/services/jutlp_validator.py → docs/apa7-backlog-C.md
- `validate()` --references--> `Verification gates between tracks`  [INFERRED]
  app/services/jutlp_validator.py → docs/track-c-d.md
- `build_edited_document()` --references--> `4. PARALLELISATION INSIDE C (3–4 people) + HOT FILES`  [INFERRED]
  app/services/output_generation_samfix.py → docs/apa7-backlog-C.md
- `extract_template_styles()` --references--> `C‑Tests + base template`  [INFERRED]
  app/services/document_styling_fixes.py → docs/apa7-backlog-C.md
- `_llm_edits_for_paragraph()` --references--> `0.1 LLM call sites (verified via grep — no site missed)`  [INFERRED]
  app/services/body_llm_edits.py → docs/apa7-backlog-D.md

## Import Cycles
- None detected.

## Communities (156 total, 16 thin omitted)

### Community 0 - "_insert_front_page_banner_from_template"
Cohesion: 0.11
Nodes (28): _apply_apa_body_geometry(), _doc_has_first_page_header_picture(), _ensure_first_footer(), _ensure_first_header(), _ensure_header_reference(), _ensure_image_content_types(), _find_first_footer_ref(), _find_first_header_ref() (+20 more)

### Community 1 - "_build_zoned_docx"
Cohesion: 0.09
Nodes (22): _build_zoned_docx(), An introduction in the abstract does NOT satisfy the body's first-use rule., Truly unknown acronyms in the abstract (no allow-list, no inline def anywhere)…, Block-listed tokens (USA, OK, NASA, iOS, …) never produce issues even when bare…, OECD and UNESCO are on the client's approved-acronyms list — bare body use…, The abstract is an independent zone and needs its OWN introduction. An acronym…, Anything from Acknowledgements onwards is outside the bot's scope., Build a docx where each entry is (style or None, text). A ``None`` style… (+14 more)

### Community 2 - "validate"
Cohesion: 0.05
Nodes (72): build_report(), check_abstract_single_paragraph(), check_block_quote_style(), check_body_paragraph_styles(), check_combined_results_discussion(), check_conclusion_length(), check_discussion_subsections(), check_dot_points() (+64 more)

### Community 3 - "test_front_page_style_fixes.py"
Cohesion: 0.07
Nodes (59): _append_body_comment(), _apply_document_body_plan(), _apply_front_page_asset_plan(), _apply_heading_2_title_case(), build_author_check_plan(), _collect_dot_point_issues(), _collect_numbered_author_placeholder_issues(), _collect_table_figure_labels() (+51 more)

### Community 4 - "language_corrections.py"
Cohesion: 0.06
Nodes (54): apply_citation_formatting_corrections(), _apply_corrections_to_para(), _Element, Insert missing space after p. / pp. in in-text page references. APA style…, Add a space after p./pp. before page numbers as tracked changes. Returns…, _apply_corrections_to_para(), apply_et_al_corrections(), _corrected_bracket() (+46 more)

### Community 5 - "apa7_formatting_checks.py"
Cohesion: 0.14
Nodes (24): _find_keywords_paragraph(), Return the Keywords paragraph — either a heading or the inline label., check_abstract_format(), check_keywords_format(), check_references_heading_format(), check_references_page_break(), _first_effective_ind(), _front_matter_paras() (+16 more)

### Community 6 - "test_sentence_coherence_corrections.py"
Cohesion: 0.11
Nodes (34): get_sentence_coherence_flags(), _is_usable_reason(), Call the LLM and return a list of ``{original, reason}`` dicts.…, True if ``reason`` is a real explanation, not a degenerate verdict. Guards…, _make_doc(), parametrize, Path, Tests for the sentence-coherence LLM pass. We stub the LLM call so the tests… (+26 more)

### Community 7 - "load_paragraphs"
Cohesion: 0.07
Nodes (53): detect_heading_level_1(), extract_main_sections(), extract_subsections(), load_paragraphs(), parse_docx_structure(), Scan a .docx file and return its Heading 1 section text and positions., _maybe_generate_keywords_for_missing_section(), check_references_section() (+45 more)

### Community 8 - "main.py"
Cohesion: 0.07
Nodes (41): _acronym_admin_active(), _acronym_admin_authed(), acronyms_admin_login(), acronyms_admin_logout(), add_acronym_api(), analyse_cli(), _body_edit_items(), _build_cli_frontend_payload() (+33 more)

### Community 9 - "document_analysis_services.py"
Cohesion: 0.08
Nodes (53): Few-shot editorial examples extracted from real JUTLP editor decisions. These…, JUTLP editorial guidelines extracted from 'JUTLP Template 2026.docx'. Last…, ParagraphRecord, _build_system_prompt(), _build_user_prompt(), _canonical_section_for(), _extract_front_page_content(), _find_sections_by_text() (+45 more)

### Community 10 - "normalise_docx"
Cohesion: 0.06
Nodes (60): _accept_tracked_changes(), _ancestor_paragraph_index(), _delete_guidance_paragraphs(), _is_paragraph_blank(), NormalisationReport, normalise_docx(), _Element, Path (+52 more)

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
Cohesion: 0.11
Nodes (41): docx_enum_text, docx_oxml, docx_shared, add_first_page_banner(), apply_caption_styles(), apply_front_matter_styles(), apply_heading_style(), apply_normal_style() (+33 more)

### Community 15 - "output_generation_samfix.py"
Cohesion: 0.04
Nodes (97): _append_author_query_runs(), _apply_apa_section_margins(), _apply_body_run_format(), _apply_tracked_body_format_fixes(), _apply_tracked_body_paragraph_format(), _apply_tracked_body_run_format(), _apply_tracked_table_cell_borders(), _apply_tracked_table_properties() (+89 more)

### Community 16 - "test_heading_corrections.py"
Cohesion: 0.09
Nodes (38): apply_heading_corrections(), _apply_tracked_edit(), _build_style_level_map(), _corrected_heading(), _direct_text_runs(), _heading_level(), _level_from_name(), _norm() (+30 more)

### Community 17 - "generate_commented_docx"
Cohesion: 0.09
Nodes (24): generate_commented_docx(), Generate a reviewed `.docx` with inline comments and a validation summary page., Generate a reviewed `.docx` with inline comments and a validation summary page., count_comments_in_docx(), get_comment_anchor_texts(), fixture, A `DOIT005`-style result should drop a Word comment anchored at reference entry…, A `DOIT005`-style result should drop a Word comment anchored at reference entry… (+16 more)

### Community 18 - "test_heading_style_apa11.py"
Cohesion: 0.08
Nodes (42): _apply_apa_heading_styles(), Drop a direct ``w:jc`` from Heading 1-5 paragraphs. > C-23 / APA-11: paragraph-…, Copy the APA base Heading 1-5 styles into the output and clear overrides. Two…, _strip_heading_direct_jc(), check_headings, fixture, parametrize, _article_title_texts() (+34 more)

### Community 19 - "rules"
Cohesion: 0.07
Nodes (8): fixture, rules(), TestDeidentifiedWithAuthorLeak, TestFrontPageIssues, TestMissingMethodSubsection, TestStructureAndEndmatterIssues, TestValidDeidentified, TestValidIdentified

### Community 20 - "apply_acronym_corrections"
Cohesion: 0.05
Nodes (50): apply_acronym_corrections(), _apply_mutations(), _bracketed_spans(), _build_bullet(), _build_replacement(), _build_zone_map(), _collect_inline_definitions(), _find_run_at_offset() (+42 more)

### Community 21 - "test_access_validation.py"
Cohesion: 0.13
Nodes (26): _require_access(), AccessResult, AccessStatus, check_access(), check_local_bypass(), Access validation service — G-07. Defines the authentication contract for…, Single entry point the Flask gate calls. Tries, in order: 1. Local SKIP_AUTH…, SKIP_AUTH must be explicitly 'true' (case-insensitive) — any other value,… (+18 more)

### Community 23 - "test_intro_page_break.py"
Cohesion: 0.48
Nodes (6): _doc(), _intro_has_page_break(), Tests for the front-page / body page break before the Introduction., Regression: a numbered "1. Introduction" heading must still get the front-…, test_page_break_inserted_before_numbered_introduction(), test_page_break_inserted_before_plain_introduction()

### Community 24 - "test_spell_checker.py"
Cohesion: 0.06
Nodes (45): find_quote_spans(), is_in_quote(), Return True when the half-open range ``[start, end)`` overlaps any quotation…, Return a list of ``(start, end)`` half-open intervals locating every paired-…, _build_word_counts(), _classify_word(), _freq_ratio(), get_spell_corrections() (+37 more)

### Community 25 - "shutil"
Cohesion: 0.07
Nodes (19): jutlp_validator_validator, C-22 direct-formatting path test. The 01_valid_identified fixture carries no…, # TODO: Delete script after completion of Track C, Runs build_edited_document on the 01_valid_identified.docx fixture and asserts…, # TODO: Delete script after completion of Track C, Runs build_edited_document on the 01_valid_identified.docx fixture and asserts…, # TODO: Delete script after completion of Track C, C-25 References-block verification: runs build_edited_document on the… (+11 more)

### Community 26 - "test_appendix_removal.py"
Cohesion: 0.17
Nodes (24): _is_appendix_heading(), _build_docx(), _comment_texts(), _del_texts(), _p(), _Element, Path, Tests for the appendix-comment pass. JUTLP does not accept appendices: the… (+16 more)

### Community 27 - "test_grammar_corrections.py"
Cohesion: 0.14
Nodes (23): _fix_au_spellings(), get_grammar_corrections(), _is_proper_noun_correction(), Return True if original looks like a proper noun, surname, acronym, or tech…, Replace any US spellings in text with AU equivalents using AU_CORRECTIONS., Call LLM and return a list of {original, replacement, reason} dicts., _build_min_docx(), _comments_text() (+15 more)

### Community 28 - "keywordsFound"
Cohesion: 0.05
Nodes (44): _apply_missing_keywords_stub(), citationFound(), _extract_keywords_list(), _find_abstract_heading_in_front(), _find_blank_line_after_index(), _find_citation_heading_in_front(), _find_introduction_heading_in_front(), _find_keywords_heading_in_front() (+36 more)

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
Cohesion: 0.11
Nodes (26): heading_zone_transition(), Return the new zone given a heading paragraph's style and text. A real Heading…, Return the new zone given a heading paragraph's style and text. A real Heading…, _apply_del_ins(), apply_reference_format_corrections(), _build_style_name_map(), _collect_ref_paragraphs(), _is_comment_ref_run() (+18 more)

### Community 33 - "script.js"
Cohesion: 0.10
Nodes (28): _activateStep(), _clearPollDelay(), clearUploadError(), displayFile(), fetchJutlpArticles(), finishStepAnimation(), groupItems(), JUTLP_FALLBACK_ARTICLE (+20 more)

### Community 34 - "acronym_store.py"
Cohesion: 0.11
Nodes (29): add_acronym(), _ensure_file_exists(), load_acronyms(), _load_seed(), Path, Persistent store for the editor-managed acronym allow-list. The list lives as a…, Restore the on-disk store to the bundled seed. Used by tests., Return the bundled seed JSON as a fresh dict. (+21 more)

### Community 35 - "titleFound"
Cohesion: 0.11
Nodes (25): authorFound(), build_apa_title_page_plan(), _collect_quote_formatting_issues(), _count_title_words(), _extract_quoted_segments(), _find_anchor_above(), _find_content_authors(), _has_known_title() (+17 more)

### Community 36 - "build_prompts"
Cohesion: 0.16
Nodes (13): build_prompts(), Build (system_prompt, user_prompt) from parsed document data., _make_paragraphs(), _make_parsed_structure(), Build a minimal set of ParagraphRecord objects for testing., The prompt instructs the LLM to use specific severity labels. Originally…, Regression: sections headed by an ALIAS ("Methodology", "Findings", "Literature…, Regression: sections headed by an ALIAS ("Methodology", "Findings", "Literature… (+5 more)

### Community 37 - "apply_number_word_corrections"
Cohesion: 0.09
Nodes (49): Document, Path, read_docx(), apply_narrative_citation_corrections(), Apply tracked "&" -> "and" fixes for APA narrative citations., apply_number_word_corrections(), Scan body paragraphs and emit tracked-change replacements for digits 0-9.…, hashlib (+41 more)

### Community 38 - "_find_target_para_index"
Cohesion: 0.12
Nodes (29): app_services, _add_style(), parametrize, D-01 Phase 2 evidence tests: one test per validator rule id, proving the…, FP006 fixed by S._apply_missing_keywords_stub (tracked change)., FP011 fixed by S._apply_abstract_plan (tracked change)., STY003 fixed by S._apply_body_and_reference_style_fixes (tracked style change)., STY004 fixed by S._apply_body_and_reference_style_fixes (tracked style change). (+21 more)

### Community 39 - "cli_copybot.py"
Cohesion: 0.23
Nodes (17): _heading_level_1_sections(), _is_generic_copyedit_output(), main(), _print_heading_normalization_summary(), Path, _rename_generic_copyedit_output(), _show_heading_level_1_sections(), _status() (+9 more)

### Community 40 - "reference_checker.py"
Cohesion: 0.07
Nodes (41): build_reference_report(), _build_structured_reference(), _cache_get(), _cache_set(), check_and_report(), check_duplicate_references(), check_orphan_citations(), check_reference_citations() (+33 more)

### Community 41 - "test_table_keep_together.py"
Cohesion: 0.14
Nodes (26): _apply_caption_keep_next(), apply_table_keep_together(), _ensure_keep_next(), _ensure_trpr(), _ensure_trpr_child(), _para_style(), _para_text(), _Element (+18 more)

### Community 42 - "generate_keywords"
Cohesion: 0.14
Nodes (24): _build_user_prompt(), _clean_one(), _dedupe_case_insensitive(), generate_keywords(), _is_acceptable(), LLM-driven keyword generation for manuscripts missing a Keywords section. APA…, Strip surrounding whitespace and quotes; collapse internal whitespace., Return up to ``_MAX_KEYWORDS`` keyword candidates for the manuscript. Best-… (+16 more)

### Community 43 - "table_page_breaks.py"
Cohesion: 0.20
Nodes (26): apply_table_page_breaks(), _cell_text(), _make_page_break_paragraph(), _page_break_anchor(), _para_has_page_break(), _para_style(), _para_text(), _preceded_by_page_break() (+18 more)

### Community 44 - "jutlp_articles.py"
Cohesion: 0.17
Nodes (26): _abstract_candidates(), _article_details_url(), _clean_abstract_candidate(), _clean_text(), _extract_abstract(), _extract_article_urls(), _extract_author(), _extract_title() (+18 more)

### Community 45 - "test_font_sweep.py"
Cohesion: 0.06
Nodes (60): check_fonts(), Return the wrong typefaces a style/defaults ``w:rFonts`` declares. Dry-run of…, APA002: every typeface resolves to the APA default (Calibri). Inspects text…, _style_rfonts_would_change(), is_symbol_font(), Pin every non-symbol Latin slot to ``target``; True when changed. Slots already…, True for typefaces that must never be normalised (equations, symbols). Mirrors…, Return the explicit ``{attr: typeface}`` map of a ``w:rFonts`` element. (+52 more)

### Community 46 - "results"
Cohesion: 0.14
Nodes (13): is_sam_fixed(), Reporting ownership: which layer reports each validation finding. A finding…, True when Sam's builder fixes this validator rule, so no other layer should…, _build_summary(), _dedup_sam_issues(), _llm_notes_to_results(), Poll for analysis results. --- tags: - Results parameters: - in: path name:…, Remove Sam's issues that duplicate existing ones (3+ significant word overlap). (+5 more)

### Community 47 - "canonical_jultp_template.py"
Cohesion: 0.11
Nodes (28): APA-7 Template Definitions and Formatting Constants. Locked Decisions: Calibri…, _build_section_rename_map(), _merges_two_sections(), _normalise_subsection(), Remove a leading heading number from ``text`` (e.g. "2. Literature" ->…, Lower-case, collapse whitespace, strip a leading heading number and any…, Return the canonical main section a heading fragment names, or None. Matches…, Return the canonical main section a heading fragment names, or None. Matches… (+20 more)

### Community 48 - "test_copyeditor_comment_regressions.py"
Cohesion: 0.15
Nodes (28): Renumber visible Author Query labels after every comment pass has run., Renumber visible Author Query labels after every comment pass has run., _renumber_final_author_queries(), apply_au_spelling_corrections(), Scan every eligible paragraph and apply AU spelling tracked changes. Returns…, _inject_comment_markers(), _make_comment_element(), _patch_content_types() (+20 more)

### Community 49 - "doc_analysis_pipeline"
Cohesion: 0.10
Nodes (18): doc_analysis_pipeline(), _hyperlink_plain_urls_in_refs(), _inject_crossref_doi_links(), _normalise(), _patch_settings_show_markup(), Path, Remove Sam's comments (id > our_max_id) that duplicate our validator output.…, Remove Sam's comments (id > our_max_id) that duplicate our validator output.… (+10 more)

### Community 50 - "test_reference_checker.py"
Cohesion: 0.12
Nodes (17): extract_references(), _get_style_name(), _is_appendix_heading(), Return ``(start_index, end_index)`` bounding the References section. ``start``…, Return ``(start_index, end_index)`` bounding the References section. ``start``…, Two-tier reference selection used by BOTH extraction and comment anchoring so…, _references_window(), _select_reference_entries() (+9 more)

### Community 51 - "test_suspicious_ref_comments.py"
Cohesion: 0.20
Nodes (16): _has_reference_issue_summary_comment(), _insert_suspicious_ref_comments(), Add Word comments for reference issues: - CONS001/CONS002 citation-consistency…, Add Word comments for reference issues: - CONS001/CONS002 citation-consistency…, _build_docx(), _comment_anchor_texts(), _comment_texts(), Path (+8 more)

### Community 52 - "apply_table_n_notation_comments"
Cohesion: 0.18
Nodes (18): apply_table_n_notation_comments(), _iter_text_runs(), _Element, Yield (run_el, text) for runs we may safely anchor a comment on., Emit one comment per table column header that is a bare capital "N". Returns…, _comment_texts(), Tests for the capital-N table-header notation comment., Comment-only pass must return the change id it was given. (+10 more)

### Community 53 - "TestFiveFailuresFiveComments"
Cohesion: 0.08
Nodes (13): has_comments_content_type(), has_comments_relationship(), Return ordered list of (text, has_ins, [commentRangeStart ids]) for every…, Return ordered list of (text, has_ins, [commentRangeStart ids]) for every…, The combined 'Results and Discussion' fixture has no standalone Discussion…, The combined 'Results and Discussion' fixture has no standalone Discussion…, SEC005 + DIS001-003 comments anchor inside the inserted Discussion stub, NOT on…, Canonical order check. (+5 more)

### Community 54 - "_apply_author_plan"
Cohesion: 0.05
Nodes (68): _append_affiliation_before_notes(), _append_plain_text_run(), _append_plain_text_run_with_size(), _append_text_with_line_breaks(), _append_text_with_superscript_markers(), _append_tracked_replace(), _apply_author_plan(), _apply_style_if_needed() (+60 more)

### Community 55 - "pytest"
Cohesion: 0.14
Nodes (17): _document_word_count(), Total word count across every paragraph (whole-document count)., Total word count across every paragraph (whole-document count)., io, pytest, _client(), _poll_until_final(), Tests for the upload guardrails added to app.main: 1. Whole-document word-count… (+9 more)

### Community 56 - "test_references_block_corrections.py"
Cohesion: 0.11
Nodes (34): check_references_hanging_indent(), APA012: every reference entry carries a 0.5in hanging indent., _add_heading1_style(), _doc_with_references(), _drop_heading1_style(), parametrize, C-25 evidence tests: the References block reaches its APA-12 form. Covers the…, A numeric style id ("3") named "heading 1" still counts as Heading 1. (+26 more)

### Community 57 - "apply_reference_order_comments"
Cohesion: 0.17
Nodes (20): _anchor_comment_on_paragraph(), apply_reference_order_comments(), _build_comment(), _find_references_heading(), _first_inversion(), _passthrough(), _Element, Comment on a reference list that is not alphabetically ordered. Comment-only —… (+12 more)

### Community 58 - "test_acronym_api.py"
Cohesion: 0.10
Nodes (8): client(), gated_client(), fixture, Smoke tests for the acronym admin HTTP endpoints. Skipped when Flask isn't…, Read-only access stays open so the pipeline can still load the list., Boot the Flask app with auth disabled and the store pointed at tmp., Boot the app with the editor-password gate enabled., test_gated_get_still_open_when_not_authed()

### Community 59 - "apply_reference_indent_corrections"
Cohesion: 0.14
Nodes (21): _already_correct(), apply_reference_indent_corrections(), _is_heading(), _resolved_name(), _build_style_hanging_map(), _resolve(), _build_style_name_map(), _Element (+13 more)

### Community 60 - "editorial_review_comments.py"
Cohesion: 0.20
Nodes (18): build_editorial_review_comment_plan(), _build_section_anchor_map(), _comment_family(), _format_comment(), _group_similar_comments(), _is_body_prose(), _is_paragraph_length_note(), _is_table_or_figure_text() (+10 more)

### Community 61 - "test_abstract_length_rule.py"
Cohesion: 0.12
Nodes (28): estimate_line_count(), Estimate how many rendered lines ``text`` occupies. Takes the larger of the…, Estimate how many rendered lines ``text`` occupies. Takes the larger of the…, check_abstract(), _fp008(), _parsed(), APA-08 abstract length rule: at most 250 words. The JUTLP companion rule — "the…, The body (after Introduction) must not be swallowed into the abstract. (+20 more)

### Community 62 - "_make_textbox_wrap_around_text"
Cohesion: 0.26
Nodes (13): _make_textbox_wrap_around_text(), Make a front-page floating textbox use *square* text-wrapping so the…, Make a front-page floating textbox use *square* text-wrapping so the…, _anchor_para(), _Element, The front-page editorial textbox must wrap text around it, not overlay it. The…, Schema order: the wrap element must precede docPr in the anchor., test_behinddoc_is_cleared() (+5 more)

### Community 63 - "reference_type_checker.py"
Cohesion: 0.19
Nodes (18): _check_book(), _check_book_chapter(), _check_conference(), _check_dataset(), _check_journal(), _check_podcast(), check_reference_type_style(), _check_report() (+10 more)

### Community 64 - "test_abstract_keywords_formatting.py"
Cohesion: 0.12
Nodes (33): apply_abstract_keywords_formatting(), _is_bold(), Apply APA-08 (abstract) and APA-09 (keywords) formatting. Returns…, Return ``styleId -> lowercased style name``., _styles_index(), _add_front_matter_styles(), _doc(), _find() (+25 more)

### Community 65 - "apa7_validator.py"
Cohesion: 0.24
Nodes (18): build_report(), check_abstract(), check_discussion_subsections(), check_front_page(), check_keywords(), check_method_subsections(), check_required_sections(), check_section_order() (+10 more)

### Community 66 - "abstractFound"
Cohesion: 0.09
Nodes (29): abstractFormatCheck(), abstractFound(), _apply_abstract_plan(), _apply_missing_practitioner_stub(), _build_missing_abstract_components_message(), _check_abstract_components_with_llm(), _count_abstract_lines(), _count_title_lines() (+21 more)

### Community 67 - "check_text_dois"
Cohesion: 0.21
Nodes (10): check_text_dois(), DOIT: Validate every DOI-shaped substring found in the plain text of each…, DOIT: Validate every DOI-shaped substring found in the plain text of each…, _cr_item(), Return a fake ``_lookup_doi`` that resolves DOIs from a dict. ``None`` value…, A reference that quotes the same DOI twice (bare + URL form) should only hit…, _stub_lookup(), TestCheckTextDOIs (+2 more)

### Community 68 - "abstract_keywords_formatting.py"
Cohesion: 0.08
Nodes (50): _abstract_body_paragraphs(), _available_style_ids(), _ensure_run_flag(), _is_italic(), _italicise_keyword_label(), _keywords_text_paragraph(), _Element, APA-08 / APA-09 abstract and keywords formatting (C-26). Abstract: heading bold… (+42 more)

### Community 69 - "_to_title_case_title"
Cohesion: 0.08
Nodes (28): _max_revision_id(), Return the largest ``w:id`` on any tracked-change element in the doc. Tracked-…, Return the largest ``w:id`` on any tracked-change element in the doc. Tracked-…, Return ``text`` rewritten in academic title case. Rules applied (APA 7 /…, Return ``text`` rewritten in academic title case. Rules applied (APA 7 /…, _to_title_case_title(), A. APA 7 rule matrix (from apastyle.apa.org primary sources), APA 7 Rework Plan — OpenEditor (planning-only audit) (+20 more)

### Community 70 - "_read_doc_root"
Cohesion: 0.15
Nodes (13): Five problematic acronyms still produce exactly one Word comment., Allow-listed acronyms still need a first-use introduction in the body. A…, First body use is rewritten as 'full term (ACRO)', not just 'full term'., The single comment range wraps the first issue's location., Acronyms in the manuscript title produce NO issue at all — no bullet in the…, Crucially, ignoring the title must NOT cause the title's acronym to pre-…, _read_doc_root(), test_allow_listed_acronym_in_body_flagged_when_not_introduced() (+5 more)

### Community 71 - "_find_target_para_index"
Cohesion: 0.11
Nodes (28): _find_first_heading(), _find_first_non_empty_para(), _find_front_matter_anchor(), _find_heading(), _find_missing_section_anchor(), _find_para_by_section(), _find_preceding_section(), _find_reference_entry_indexes() (+20 more)

### Community 72 - "check_entry_author"
Cohesion: 0.24
Nodes (4): check_entry_author(), check_entry_year(), TestEntryAuthorCheck, TestEntryYearCheck

### Community 73 - "_iter_paren_citations"
Cohesion: 0.18
Nodes (8): _iter_paren_citations(), Yield ``(surname, year)`` tuples for every parenthetical citation. Handles…, Yield ``(surname, year)`` tuples for every parenthetical citation. Handles…, Coverage for the multi-citation parenthesis parser., The reported bug: a four-citation paren block produced ZERO matches because the…, APA disambiguators like ``2020a`` must survive., A `(see ...)` aside without a Surname,Year pair must yield nothing — even…, TestParenCitationIterator

### Community 74 - "body_llm_edits.py"
Cohesion: 0.12
Nodes (20): _body_paragraphs(), build_body_edit_plan(), _dedupe_edits(), _fix_au_spellings(), _is_skippable_paragraph(), _llm_edits_for_paragraph(), LLM-generated surgical copy-edits for the document body. Produces tracked-…, Return the symmetric token difference between ``find`` and ``replace``. Tokens… (+12 more)

### Community 75 - "_apply_tracked_style_change"
Cohesion: 0.25
Nodes (14): _apply_tracked_style_change(), Remove direct formatting that would override a heading style. A paragraph that…, Remove direct formatting that would override a heading style. A paragraph that…, _strip_conflicting_direct_format_for_heading(), _body_para(), _ppr(), A body paragraph restyled to a heading must shed its body formatting. When the…, Only size/spacing are stripped — bold stays (headings are bold anyway). (+6 more)

### Community 76 - "test_reporting_ownership.py"
Cohesion: 0.17
Nodes (8): app_domain, glob, _all_emitted_rule_ids(), _family(), Contract tests for reporting ownership (D-01 remediation, Phase 1). Every…, TestFamilyVerdictsCoverEverything, TestSamFixedIdsAreReal, TestSingleSource

### Community 77 - "_normalise_heading_text"
Cohesion: 0.09
Nodes (29): _ack_contains(), _all_alias_norms(), _apply_heading_center_alignment(), _collect_acknowledgements_issues(), _collect_discussion_subheading_issues(), _collect_method_subheading_issues(), _collect_results_reference_issues(), _find_heading1_index() (+21 more)

### Community 78 - "_normalise_surname"
Cohesion: 0.24
Nodes (6): _normalise_surname(), Lowercase, strip accents, punctuation, and possessive 's for fuzzy match.…, Lowercase, strip accents, punctuation, and possessive 's for fuzzy match.…, Return ``(normalised_surname, display_surname)`` for a reference entry, or None…, _sort_key_and_label(), TestNormaliseSurname

### Community 79 - "_read_comments_root"
Cohesion: 0.22
Nodes (11): _comment_visible_text(), _Element, Concatenate every ``<w:t>`` text under the comments root., When the author DID introduce the acronym in the body, no issue fires., Allow-listed acronyms in the abstract are silent — no flagging., When a track change is proposed, the bullet mentions it so the editor knows…, _read_comments_root(), test_abstract_allow_listed_silent() (+3 more)

### Community 80 - "output_filename.py"
Cohesion: 0.27
Nodes (15): build_output_filename(), build_output_filename_from_author_line(), _first_author_last_name(), _get_author_line_and_markers(), _get_document_year(), _remove_superscript_runs_from_author_line(), _unique_output_filename(), test_corrected_author_line_uses_doc_affiliation_markers() (+7 more)

### Community 81 - "output_generation.py"
Cohesion: 0.08
Nodes (30): _append_validation_summary(), _next_h1_after(), _comment_group_key(), _dedupe_pending_comments(), _format_summary_line(), _group_pending_comments(), _grouped_comment_message(), _heading_para_index() (+22 more)

### Community 82 - "test_acronym_corrections.py"
Cohesion: 0.18
Nodes (14): _format_author_query_text(), _matches_definition(), If `words` contain a valid full form for `acro`, return the phrase. Walks the…, If `words` contain a valid full form for `acro`, return the phrase. Walks the…, Tests for acronym detection + consolidated comment + tracked-change rewrites., Conversely, text inside ``<w:del>`` represents tracked deletions — content the…, If the docx already has comments from earlier passes, the new one gets the next…, test_acronym_author_query_comment_text_is_numbered() (+6 more)

### Community 83 - "LLMError"
Cohesion: 0.18
Nodes (15): call_llm(), call_llm_json(), get_client(), LLMError, Exception, Raised when the LLM call fails after retries., Create an OpenAI client., Send a structured-output request to the OpenAI Chat Completions API. Returns… (+7 more)

### Community 84 - "canonical_jultp_template.py"
Cohesion: 0.21
Nodes (11): Return one summary entry per repeated spelling correction. The tracked-change…, summarize_spelling_correction_repeats(), _docx_xml(), An unquoted US spelling in the same paragraph as a quoted one must still be…, A US-spelled word INSIDE quoted text must NOT be rewritten — direct quotations…, test_generalizability_is_changed_to_australian_spelling(), test_repeated_spelling_fix_gets_one_author_query_comment(), test_spelling_summary_groups_case_variants_of_same_fix() (+3 more)

### Community 85 - "test_body_llm_edits.py"
Cohesion: 0.06
Nodes (51): _propagate_repeated_edits(), Apply accepted exact edits to repeated matching body text. The LLM reviews each…, _validate_edit(), _apply_body_and_reference_style_fixes(), _apply_body_edit_plan(), _apply_intra_paragraph_tracked_replace(), Apply tracked style changes for body and reference paragraphs: - Required body…, Apply tracked style changes for body and reference paragraphs: - Required body… (+43 more)

### Community 86 - "_normalise_text"
Cohesion: 0.18
Nodes (7): _fingerprint_ref(), _normalise_text(), Collapse a reference to a normalised fingerprint for duplicate detection., Collapse a reference to a normalised fingerprint for duplicate detection., Replace curly quotes with their straight ASCII equivalents., Replace curly quotes with their straight ASCII equivalents., TestCitationRegexes

### Community 87 - "TestPresentUnstyledDiscussionNoStub"
Cohesion: 0.19
Nodes (7): A Discussion section that is present but not yet Heading-1 styled (the author…, A Discussion section that is present but not yet Heading-1 styled (the author…, No tracked-inserted 'Discussion' heading paragraph should exist., No tracked-inserted 'Discussion' heading paragraph should exist., The Discussion-subsection comment must anchor on the original (non-inserted)…, The Discussion-subsection comment must anchor on the original (non-inserted)…, TestPresentUnstyledDiscussionNoStub

### Community 88 - "check_submitted_hyperlinks"
Cohesion: 0.13
Nodes (15): check_submitted_hyperlinks(), _cr_item_summary(), _extract_ref_hyperlinks(), _llm_resolve_mismatch(), _lookup_doi(), Format the most identifying fields of a CrossRef record for an LLM prompt., Format the most identifying fields of a CrossRef record for an LLM prompt., Ask the LLM whether the CrossRef title/journal confirms the same paper despite… (+7 more)

### Community 89 - "subsection_alias_match"
Cohesion: 0.15
Nodes (11): Return True when ``canonical_label`` is satisfied by ``found_subs``.…, subsection_alias_match(), _extra_subheadings(), _looks_like_subheading(), True if ``text`` is plausibly a subheading, not a mis-styled body line. Mirrors…, True if ``text`` is plausibly a subheading, not a mis-styled body line. Mirrors…, Return heading-like found subheadings that match no required subsection (or…, Return heading-like found subheadings that match no required subsection (or… (+3 more)

### Community 90 - "_extract_ref_author_part"
Cohesion: 0.16
Nodes (9): _extract_ref_author_part(), Return the author/group-author portion of a reference entry. Slices everything…, Return the author/group-author portion of a reference entry. Slices everything…, Return every normalised surname-key a reference can plausibly match. For person…, Return every normalised surname-key a reference can plausibly match. For person…, _ref_surname_keys(), Person refs (with a comma) must NOT have an acronym alias generated — otherwise…, TestExtractRefAuthorPart (+1 more)

### Community 91 - "TRACK K — Evaluation Corpus + Conformance Harness · DEV TASK BACKLOG"
Cohesion: 0.09
Nodes (22): 0. STAGE 0 — SEED SET + MINIMAL HARNESS + BASELINE (do this first), 1. TICKETS BY GROUP, 2. STAGE GATES & DEMO ARTEFACTS, 3. DEPENDENCY GRAPH & CRITICAL PATH, 4. PARALLELISATION INSIDE K (2 people), 5. CROSS-TRACK REQUESTS, 6. RISKS, OPEN DECISIONS, OUT-OF-SCOPE, END — Required outputs (+14 more)

### Community 92 - "inspect_abstract.py"
Cohesion: 0.29
Nodes (5): get_comment_anchors(), get_ref_entries(), Inspect the processed output vs the original to find comment placement issues., Map comment id -> paragraph text snippet where the anchor sits., Return numbered reference entries from the document.

### Community 93 - "DEV TASK BACKLOG — TRACK D (LLM layer)"
Cohesion: 0.10
Nodes (19): _has_au_us_suffix_swap(), _is_au_to_us_replacement(), Return True if the correction would flip Australian English to American English., 0.1 LLM call sites (verified via grep — no site missed), 0.2 Baseline artefacts, 0.3 Plan-vs-code contradictions found, 0. Stage 0 — Inventory & baseline (do first), CROSS-TRACK REQUESTS (+11 more)

### Community 94 - "TestValidDoc"
Cohesion: 0.31
Nodes (3): fixture, rules(), TestValidDoc

### Community 95 - "_update_progress"
Cohesion: 0.13
Nodes (16): ProcessingCancelled, ProcessingTimeout, Exception, _run(), _pipeline(), _update_progress(), Artifacts, Backend truth (verified against `app/main.py`, `app/static/script.js`) (+8 more)

### Community 96 - "Path"
Cohesion: 0.29
Nodes (7): _build_docx(), _build_docx_with_inserted_run(), Path, The scanner must read text inside ``<w:ins>`` runs — that's what upstream…, Build a minimal docx with one paragraph per supplied text., Build a docx where each entry is ``(style, text, inside_ins)``. When…, test_acronyms_inside_inserted_runs_are_detected()

### Community 97 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 98 - "session_manager.py"
Cohesion: 0.19
Nodes (19): create_app(), CopyEditor AI application package., Background thread that prunes expired session files every 5 minutes (D-06/D-07)., start_session_sweeper(), _sweep_loop(), start_session_sweeper(), _sweep_loop(), delete_session() (+11 more)

### Community 99 - "now_sydney_iso"
Cohesion: 0.18
Nodes (14): now_sydney_iso(), Shared timestamp helper for Word comments and tracked changes. Word stores the…, Return the current time as an ISO-8601 string with the Sydney offset. Example:…, _sydney_tz(), datetime, Tests for the shared Sydney-time stamp helper. Word comments and tracked…, Sydney is UTC+10 (standard) or UTC+11 (daylight saving). If the tz database is…, Second precision only — keeps the stamp tidy and matches the previous format's… (+6 more)

### Community 101 - "opencode.json"
Cohesion: 0.08
Nodes (24): git diff *, git log *, git status *, pip install *, pytest *, python *, python3 *, ruff check * (+16 more)

### Community 102 - "lxml"
Cohesion: 0.06
Nodes (69): # TODO: remove once sections D-G replace these downstream references, Deterministic abbreviation / journal-style fixes emitted as tracked changes.…, _append_author_query_runs(), _author_query_parts(), _make_comment_element(), _patch_content_types(), _patch_rels(), Detect acronym usage problems and emit one consolidated Word comment. Journal… (+61 more)

### Community 107 - "_apply_apa_title_page"
Cohesion: 0.17
Nodes (19): _apply_apa_title_page(), _apply_apa_title_page_headers(), build_front_page_asset_check_plan(), _collect_image_rel_ids(), _collect_relationship_ids(), _derive_running_head(), _element_has_textbox(), _front_page_body_paras() (+11 more)

### Community 108 - "docx"
Cohesion: 0.15
Nodes (12): Backend truth (current codebase), G-01 — Endpoint inventory + contract doc (P0, unblocks H-01/H-02), G-02 — Upload + validation error-code map (P0, pairs H-02), G-03 — Processing poll/state machine + Cancel/timeout + carousel (P0, pairs H-03), G-04 — Results payload shape (P1, pairs H-04), G-05 — Download + retry semantics (P1, pairs H-05 — answers Humaid's open question), G-06 — Support/error passthrough (P2, pairs H-07), G-07 — Handoff: frontend data layer + open-questions log (P2, pairs H-01/Z-09) (+4 more)

### Community 109 - "run_editorial_review"
Cohesion: 0.20
Nodes (9): Run LLM-based editorial review on a JUTLP manuscript. Pipeline: 1. Parse DOCX…, run_editorial_review(), _strip_internal_markers(), main(), Demo script for JUTLP Copy-Editor AI — LLM Editorial Review. Usage: python…, patch, The LLM occasionally quotes our '[Subheading]' or '###' markers verbatim in its…, TestEditorialReviewService (+1 more)

### Community 110 - "docx"
Cohesion: 0.25
Nodes (9): docx, docx_enum_style, create_base_doc(), get_or_add_style(), Reference entries must be justified (w:jc=both), not left-aligned. Two layers…, Return the w:jc value of the APA 7 reference style, or None., _ref_style_jc(), test_left_aligned_author_reference_style_is_replaced_with_justified() (+1 more)

### Community 111 - "test_output_generation.py"
Cohesion: 0.09
Nodes (30): _append_author_query_runs(), _author_query_parts(), _canonical_insert_index(), _format_author_query_text(), _make_comment_element(), Create one `<w:comment>` node for `word/comments.xml`., Return the canonical section a fail-rule belongs to, or None. SEC001-008 map…, True if a Heading-1 paragraph is the section itself (exact / 'name:' prefix),… (+22 more)

### Community 113 - "add_document_summary_comment"
Cohesion: 0.18
Nodes (12): add_document_summary_comment(), add_paragraph_comment(), _patch_content_types(), _patch_rels(), Ensure `document.xml.rels` contains the comments relationship., Ensure `[Content_Types].xml` declares `word/comments.xml`., Ensure `document.xml.rels` contains the comments relationship., Ensure `[Content_Types].xml` declares `word/comments.xml`. (+4 more)

### Community 114 - "_Element"
Cohesion: 0.14
Nodes (19): _build_comment_ref_run(), _find_span(), _inject_comment_markers(), _inject_comment_markers_for_phrase(), _make_inserted_heading_paragraph(), _Element, Fallback comment anchor: wrap the whole paragraph. We only use this when…, Build `<w:r><w:commentReference .../></w:r>` for the inline comment mark. (+11 more)

### Community 115 - "vercel.json"
Cohesion: 0.50
Nodes (3): builds, routes, version

### Community 116 - "_find_front_matter_rule_anchor"
Cohesion: 0.13
Nodes (18): _find_after(), _find_front_matter_rule_anchor(), _find_front_style(), _find_front_text(), _find_last_front_non_empty(), _front_matter_end(), Return the paragraph index where front matter ends., Return the paragraph index where front matter ends. (+10 more)

### Community 118 - "_is_deidentified_manuscript"
Cohesion: 0.15
Nodes (17): _is_deidentified_manuscript(), Return True if the manuscript was deliberately stripped of identity. Three…, Return True if the manuscript was deliberately stripped of identity. Three…, _make_deid_state(), Minimal abstract_state stub — the deidentified check only reads docxpath., Plain `[Authors removed for blind review]` placeholder anywhere in the front-…, The placeholder regex covers the 'Affiliations removed' phrasing too., A manuscript that genuinely lacks affiliations (but has authors and no… (+9 more)

### Community 119 - "apply_blinded_citation_comments"
Cohesion: 0.39
Nodes (11): apply_blinded_citation_comments(), Comment on blinded / placeholder citations and self-references. Comment-only,…, _comment_texts(), _doc(), Tests for the blinded / placeholder citation comment pass., Unbracketed 'anonymous'/'anonymised' prose must NOT trigger., test_anonymised_prose_is_not_flagged(), test_author_under_review_citation_is_flagged() (+3 more)

### Community 120 - "test_body_font_enforcement.py"
Cohesion: 0.29
Nodes (11): _ensure_normal_style_body_rpr(), _passthrough_copy(), Pin the body font + size on the Normal style's run properties. The template's…, Pin the body font + size on the Normal style's run properties. The template's…, _doc_with_normal(), _normal_rpr(), Tests for body-font enforcement: the Normal style must carry Calibri 11pt so…, A docx whose Normal style is a non-template font/size. (+3 more)

### Community 121 - "apply_table_section_boundary_comments"
Cohesion: 0.22
Nodes (20): apply_table_section_boundary_comments(), _iter_text_runs(), First meaningful block: a table (skipping leading caption/blank) → it, prose →…, Last meaningful block: a table (skipping trailing note/blank) → it, prose →…, Comment on sections that open and/or close directly with a table. Returns…, Yield (run_el, text) for runs we may safely anchor a comment on., _section_closer(), _section_opener() (+12 more)

### Community 122 - "test_abstract_stops_at_introduction_heading"
Cohesion: 0.20
Nodes (9): Dev Tasks — OpenEditor Demo (Frontend Only), G1 · Wrong file type error (`08-blocked` variant), G2 · Cancel button (`03-processing`), G3 · Solo demo to Joey and Michael, Gurman — Wrong File Type + Cancel + Solo Demo, H1 · Upload (`01-upload`, `1:10`), H2 · Checking + Processing (`02-checking` `2:2` · `03-processing` `2:28`), H3 · Results, Upgrade, Download (`04-results` `2:42` · `05-upgrade` `2:73` · `06-download` `2:94`) (+1 more)

### Community 123 - "test_normal_styled_abstract_is_measured"
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

### Community 127 - "editorial_review_service.py"
Cohesion: 0.31
Nodes (11): EditorialNote, EditorialReviewResult, LLM verdict on a single deterministic structural check result., StructuralValidation, _length_note(), _plan(), test_non_paragraph_notes_still_fall_back_to_section_heading(), test_paragraph_length_comments_anchor_only_to_body_prose() (+3 more)

### Community 128 - "applyFile"
Cohesion: 0.50
Nodes (4): applyFile(), checkReadable(), onFileDropped(), onFileSelected()

### Community 129 - "resetToUpload"
Cohesion: 0.50
Nodes (4): continueWithoutDownloading(), requestProcessAnother(), resetToUpload(), retryProcessing()

### Community 130 - "_get"
Cohesion: 0.20
Nodes (14): acronyms_admin_page(), download(), health(), jutlp_articles_api(), list_acronyms_api(), login_form(), logout(), openeditor() (+6 more)

### Community 131 - "document_zones.py"
Cohesion: 0.05
Nodes (69): _find_appendix_start(), _is_heading_paragraph(), _paragraph_has_image(), _Element, Return True if the paragraph contains a drawing / picture / embedded object…, Return the index (within ``body``'s ``<w:p>`` children list) of the first…, _needs_apa7_split(), Return True when the paragraph holds a full single-paragraph figure/table… (+61 more)

### Community 132 - "downloadUrl"
Cohesion: 0.67
Nodes (3): downloadUrl(), downloadFirst(), downloadManuscript()

### Community 133 - "test_run_font_corrections.py"
Cohesion: 0.23
Nodes (13): _current_fonts_and_sizes(), _find_or_make(), Tests for run-level font normalisation (Calibri; references at 11pt)., A reconstructed reference run (inside <w:ins>, as the APA-7 format pass emits)…, A reconstructed reference run (inside <w:ins>, as the APA-7 format pass emits)…, Return per-run (font, sz) from the *current* rPr (ignoring rPrChange)., _set_run_font(), test_direct_times_run_becomes_arial() (+5 more)

### Community 135 - "_apply_phrase_correction"
Cohesion: 0.18
Nodes (11): apply_grammar_corrections(), _apply_phrase_correction(), _find_phrase_in_runs(), _Element, Return (run_el, text) for every plain run (not inside del/ins)., Locate *phrase* in the concatenated run texts. Returns (run_start_idx,…, Replace *original* phrase in para_el with del+ins tracked changes. Returns the…, Apply grammar corrections as tracked changes. Returns (next_id, applied). (+3 more)

### Community 136 - "build_edited_document"
Cohesion: 0.10
Nodes (28): _apply_citation_plan(), _apply_editorial_review_comment_plan(), _apply_heading_1_text_normalization(), _apply_intro_page_break(), _apply_normal_style_fix(), build_edited_document(), _canonical_heading_1_text(), citationFormatCheck() (+20 more)

### Community 137 - "DEV TASK BACKLOG — TRACK C (APA‑7 deterministic/output layer)"
Cohesion: 0.15
Nodes (12): 0. STAGE 0 — SAFETY NET, 2. STAGE 3 — PLUMBING, TESTS, SHIP, 2. STAGE GATES (runnable), 3. DEPENDENCY GRAPH + CRITICAL PATH, 4. PARALLELISATION INSIDE C (3–4 people) + HOT FILES, 5. CROSS-TRACK REQUESTS, 6. RISKS / OPEN DECISIONS / OUT OF SCOPE, C‑Plumbing (+4 more)

### Community 143 - "blinded_citation_comments.py"
Cohesion: 0.27
Nodes (10): _anchor_paragraph_comment(), _build_comment(), _classify(), _distinct(), _own_text_runs(), _Element, Flag blinded / placeholder citations and self-references. For peer review…, Detect placeholders in ``para_el`` and, if any, anchor one comment. Returns… (+2 more)

### Community 144 - "_llm_notes_to_results"
Cohesion: 0.33
Nodes (6): _extract_field(), _llm_notes_to_results(), Read a field from dict/object safely with a default., Normalize LLM editorial notes into validator-like result dictionaries., Read a field from dict/object safely with a default., Normalize LLM editorial notes into validator-like result dictionaries.

### Community 145 - "_find_next_action"
Cohesion: 0.24
Nodes (10): _find_next_action(), _get_style_name(), _has_corrected_form_in_tracked_ins(), _iter_text_runs(), _process_paragraph(), _Element, Return True if a sibling ``<w:ins>`` already supplies ``comma_value`` with the…, Return ``(run_el, start, end, check_kind, message, value)`` for the earliest… (+2 more)

### Community 146 - "_sam_plan_to_issues"
Cohesion: 0.25
Nodes (7): _build_changes_made(), _count_sam_changes(), Convert Sam's build_edited_document plan into frontend issue dicts., Convert Sam's build_edited_document plan into frontend issue dicts., Aggregate every tracked-change correction into the three 'changes made' groups.…, Count Sam's tracked changes via the same plan→issue conversion the results…, _sam_plan_to_issues()

### Community 147 - "test_apa7_title_page.py"
Cohesion: 0.50
Nodes (7): _body_paragraphs(), _make_student_doc(), _paragraph_text(), _run_title_page_pass(), test_mode_override_beats_auto_detection(), test_professional_mode_adds_running_head_and_removes_student_metadata(), test_student_title_page_is_centered_and_has_no_banner_or_textbox()

### Community 148 - "read_docx"
Cohesion: 0.40
Nodes (5): Document, Path, read_docx(), Document, Path

### Community 149 - "Track C — Deterministic / Output"
Cohesion: 0.29
Nodes (6): Create, Delete, Track C — Deterministic / Output, Track C & Track D — Comprehensive Checklists, Track D — LLM Layer, Verification gates between tracks

### Community 150 - "test_numbered_section_detection.py"
Cohesion: 0.53
Nodes (5): _doc(), Regression tests for section/subsection detection on numbered or aliased…, test_present_subsection_not_flagged_missing(), test_section_bounds_match_numbered_alias_heading(), test_subsections_found_under_numbered_section()

### Community 151 - "_accepted_paragraph_text"
Cohesion: 0.50
Nodes (4): _accepted_paragraph_text(), True if ``run_el`` should NOT contribute to ``para_p``'s text. Walks up to the…, Return a paragraph's *own* text as if all tracked changes were accepted.…, _run_skipped()

### Community 152 - "_try_match_definition"
Cohesion: 0.67
Nodes (3): Attempt to align ``letters`` against the leading section of ``words``. Walks…, Attempt to align ``letters`` against the leading section of ``words``. Walks…, _try_match_definition()

### Community 153 - "_front_page_paragraphs_for_deid"
Cohesion: 0.67
Nodes (3): _front_page_paragraphs_for_deid(), Read up to the first ~15 front-page paragraphs of ``docxpath``. Used by the…, Read up to the first ~15 front-page paragraphs of ``docxpath``. Used by the…

## Knowledge Gaps
- **126 isolated node(s):** `1. What Changed vs. CopyBot`, `3. Track C / Track D Work Plan (condensed)`, `4. Service Inventory (disposition)`, `5. Risks & Open Questions`, `6. Flowchart (revised)` (+121 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1322 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_paragraphs()` connect `load_paragraphs` to `validate`, `test_front_page_style_fixes.py`, `test_sentence_coherence_corrections.py`, `main.py`, `document_analysis_services.py`, `output_generation_samfix.py`, `generate_commented_docx`, `test_numbered_section_detection.py`, `_accepted_paragraph_text`, `test_spell_checker.py`, `_front_page_paragraphs_for_deid`, `test_grammar_corrections.py`, `keywordsFound`, `titleFound`, `build_prompts`, `reference_checker.py`, `canonical_jultp_template.py`, `test_reference_checker.py`, `pytest`, `editorial_review_comments.py`, `test_abstract_length_rule.py`, `test_abstract_keywords_formatting.py`, `apa7_validator.py`, `abstractFound`, `body_llm_edits.py`, `output_filename.py`, `output_generation.py`, `lxml`, `run_editorial_review`, `editorial_review_service.py`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `run_editorial_review()` connect `run_editorial_review` to `build_prompts`, `_to_title_case_title`, `lxml`, `load_paragraphs`, `doc_analysis_pipeline`, `LLMError`, `editorial_review_comments.py`, `DEV TASK BACKLOG — TRACK D (LLM layer)`, `editorial_review_service.py`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Why does `build_edited_document()` connect `build_edited_document` to `_insert_front_page_banner_from_template`, `test_front_page_style_fixes.py`, `main.py`, `DEV TASK BACKLOG — TRACK C (APA‑7 deterministic/output layer)`, `normalise_docx`, `output_generation_samfix.py`, `test_heading_corrections.py`, `test_heading_style_apa11.py`, `shutil`, `keywordsFound`, `titleFound`, `apply_number_word_corrections`, `cli_copybot.py`, `test_font_sweep.py`, `doc_analysis_pipeline`, `_apply_author_plan`, `editorial_review_comments.py`, `test_abstract_keywords_formatting.py`, `abstractFound`, `abstract_keywords_formatting.py`, `_to_title_case_title`, `body_llm_edits.py`, `_normalise_heading_text`, `output_filename.py`, `test_body_llm_edits.py`, `lxml`, `_apply_apa_title_page`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `build_edited_document()` (e.g. with `4. PARALLELISATION INSIDE C (3–4 people) + HOT FILES` and `Key verifications / plan-vs-code contradictions`) actually correct?**
  _`build_edited_document()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `validate()` (e.g. with `C‑Validator` and `Key verifications / plan-vs-code contradictions`) actually correct?**
  _`validate()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `1. What Changed vs. CopyBot`, `3. Track C / Track D Work Plan (condensed)`, `4. Service Inventory (disposition)` to the rest of the system?**
  _126 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `_insert_front_page_banner_from_template` be split into smaller, more focused modules?**
  _Cohesion score 0.10846560846560846 - nodes in this community are weakly interconnected._