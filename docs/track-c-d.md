# Track C & Track D — Comprehensive Checklists

Goal: OpenEditor produces APA 7-aligned output (title page, headings, fonts/spacing, in-text citations, references, tables/figures) with a fully APA-oriented LLM review path. Track C is the deterministic pipeline; Track D is the LLM injection/prompt layer.

---

## Track C — Deterministic / Output

### Delete
- [ ] `app/domain/canonical_jultp_template.py` — delete after porting needed constants to `apa7_template.py`
- [ ] `app/domain/jutlp_guidelines.py`, `app/domain/jutlp_editorial_examples.py` — delete; consumers moved to APA files
- [ ] `app/domain/jutlp_template_style_map.json` — delete once APA base .docx exists
- [ ] `app/services/jutlp_articles.py` + `GET /api/jutlp-articles` in `app/main.py` + carousel in `app/templates/writer.html`, `app/static/openeditor.js`, `app/static/api.js`
- [ ] `app/services/appendix_removal.py`, `app/services/short_paragraph_comments.py`, `app/services/blinded_citation_comments.py`

### Create
- [ ] `app/domain/apa7_template.py` — `CANONICAL_STRUCTURE_APA7`: student/professional front page, abstract ≤250, Method/Results/Discussion as expected (not renamed), References, appendices allowed, figure/table expectations
- [ ] `app/domain/apa7_guidelines.py` — `APA7_GUIDELINES` markdown (margins, fonts, double spacing, headings 1–5, citations, references, tables/figures, student vs professional front matter)
- [ ] `app/domain/apa7_editorial_examples.py` — `APA7_EDITORIAL_EXAMPLES` few-shots (APA-appropriate flag/keep cases)
- [ ] `app/domain/apa_base_template.docx` — built from the setup guide; supplies clean Normal/Heading styles

### Edit
- [ ] `app/config.py` — APA-only defaults: `ALLOWED_FONTS`, `DEFAULT_FONT` (client pick), `DEFAULT_MODE` student/professional, no profile enum
- [ ] `app/services/jutlp_validator.py` → `app/services/apa7_validator.py`: drop SEC/MET/DIS/FP/CON/AFF/ANDOR/ETC/DOTPT/SPE001–3; keep STY/TAB/FIG/SPE004/REF family; add APA001–APA012 (margins, spacing, font, align, indent, page number, title page, abstract, keywords, intro heading, heading levels, references block)
- [ ] `app/services/output_generation_samfix.py` — delete JUTLP steps (`_insert_front_page_banner_from_template`, `_insert_front_page_text_box_from_template`, `_move_body_citation_to_footer`, `_apply_missing_practitioner_stub`, `_apply_missing_keywords_stub`, `_apply_heading_1_text_normalization`, `_apply_intro_page_break`, `CENTER_ALIGNED_HEADING_TEXTS` policy); add APA passes (margins/spacing/indent/align, heading-level styles, title-page rebuild, page break before References, hanging indent, allowed-font sweep); fix `_to_title_case_title` replacement bug; retarget `_TEMPLATE_PATH` to APA base docx
- [ ] `app/services/output_generation.py` — replace JUTLP anchor table (`_CANONICAL_ORDER`, `"Article Title"`, `"Practitioner Notes"`) with APA section anchors; de-JUTLP `_REF_ENTRY_STYLE`
- [ ] `app/services/heading_corrections.py` — drop `SECTION_RENAME_MAP`→JUTLP; keep number-stripping; enforce APA heading *levels* instead of JUTLP names
- [ ] `app/services/document_zones.py` — zone boundaries from `CANONICAL_STRUCTURE_APA7`; remove `"Practitioner Notes"` skips
- [ ] `app/services/document_analysis_services.py` — `get_front_page`/`extract_abstract`/`extract_keywords` boundaries to APA; delete `extract_practitioner_notes`
- [ ] `app/services/document_normalisation_services.py` — `GUIDANCE_NOTES_STYLE` deletion → generic template-junk list
- [ ] `app/services/document_styling_fixes.py` — compare against `apa7_template` styles, APA base docx default
- [ ] `app/services/keywords_generation.py` — drop JUTLP 5-cap and JUTLP system prompt; accept APA keywords conventions
- [ ] `app/services/run_font_corrections.py` — `_TARGET_FONT` → APA-allowed default; same for reference runs
- [ ] `app/services/decimal_corrections.py`, `app/services/language_corrections.py`, `app/services/spell_checker.py` — de-JUTLP messages; spelling variant per client decision
- [ ] `app/services/reference_format_corrections.py`, `reference_indent_corrections.py`, `reference_order_comments.py`, `reference_type_checker.py`, `reference_reconstructor.py` — verify rules are APA-generic; keep
- [ ] `app/services/table_keep_together.py`, `table_n_notation_comments.py`, `table_page_breaks.py`, `table_section_boundary_comments.py`, `caption_apa7_check.py`, `quotation_utils.py`, `et_al_corrections.py`, `narrative_citation_corrections.py`, `citation_formatting_corrections.py`, `abbreviation_corrections.py` (e.g./i.e. part), `number_word_corrections.py`, `acronym_corrections.py` — keep; sweep for JUTLP-specific strings
- [ ] `app/pipelines/feedback_gen_pipeline.py` — remove deleted-service imports/calls; point `validate`/`generate_commented_docx`/`build_edited_document` at APA modules; drop `appendix_removal`/`blinded_citation_comments`/`short_paragraph_comments` rows
- [ ] `app/main.py` — remove `/api/jutlp-articles`; update docstrings/copy; keep session/cancel/timeout
- [ ] `app/services/output_filename.py` — naming scheme without `_JUTLP_`
- [ ] `app/templates/writer.html`, `app/static/openeditor.js`, `app/static/api.js` — remove carousel + JUTLP copy

---

## Track D — LLM Layer

- [ ] `app/services/ai/prompt_builder.py` — system prompt: "APA 7 copy editor" not "JUTLP activist sub-editor"; inject `APA7_GUIDELINES`/`APA7_EDITORIAL_EXAMPLES`; new `VALID_CATEGORIES` (title_quality, abstract_quality, introduction_quality, method_quality, results_quality, discussion_quality, conclusion_quality, apa_style, references_quality, tables_figures_quality, general); remove `JUTLP_TITLE_WORD_LIMIT`; `SECTION_NAME_VARIANTS` generalised (Method/Methods/Methodology, Literature Review, Findings, Theoretical Framework); `_extract_front_page_content` drops practitioner notes; duplication guard now consumes `apa7_validator` results
- [ ] `app/services/ai/editorial_review_service.py` — de-JUTLP framing line; marker-stripping kept
- [ ] `app/services/ai/llm_client.py` — `EDITORIAL_RESPONSE_SCHEMA`: `category` → enum of new categories; `structural_validations.verdict` → add `"needs_review"`; keep notes shape
- [ ] `app/services/body_llm_edits.py` — prompt: "JUTLP house style" → APA spelling decision; keep all guards (`_is_au_to_us_replacement`, quote protection, hyphen/plural/tense guards)
- [ ] `app/services/grammar_corrections.py` — prompt: "accepted for publication in JUTLP" → APA 7; keep AU/US guards
- [ ] `app/services/sentence_coherence_corrections.py` — prompt already generic; de-JUTLP any skip-style mentions
- [ ] `app/services/keywords_generation.py` — system prompt de-JUTLP; 5-keyword cap relaxed
- [ ] Smoke test: run one doc, assert `notes[]` has no "JUTLP"/"Practitioner Notes" strings, `structural_validations` parse, categories within enum

---

## Verification gates between tracks
- After C-delete: `python -m pytest` green (fix import/fixture breakage, incl. `test_jutlp_validator.py`).
- After C-create/edit: `validate` returns APA rule IDs only; no JUTLP strings in results payload.
- After D: LLM notes contain zero JUTLP references; schema enums tight.
- After C3+D3: 5-paper demo batch — no banner/textbox/practitioner/footer-citation; double spacing; heading levels; references hanging indent.
