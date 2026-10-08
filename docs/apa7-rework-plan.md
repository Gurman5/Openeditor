# APA 7 Rework Plan — OpenEditor (planning-only audit)

## A. APA 7 rule matrix (from apastyle.apa.org primary sources)

| ID | Rule | Source | Mode | Deterministic? | Auto-fix vs comment |
|---|---|---|---|---|---|
| APA-00 | 1-in margins all sides | Student Paper Setup Guide /§1.21 | both | Y | tracked fix (sectPr) |
| APA-01 | Double spacing entire paper, incl. block quotes + refs; no blank lines before/after headings | Setup Guide /§1.20 | both | Y | tracked fix |
| APA-02 | Font: one of 11pt Calibri / 11pt Arial / 12pt TNR / 11pt Georgia / 10pt Lucida Sans Unicode | Setup Guide /§1.18 | both | Y | tracked fix (Normal style + runs) |
| APA-03 | Left-align, ragged right, NO full justification | Setup Guide §alignment | both | Y | tracked fix — CONFLICTS with current JUTLP `BODY_REQUIRED_...` / justified "APA 7 Reference List Entry" |
| APA-04 | First-line paragraph indent 0.5 in | Setup Guide /§1.23 | both | Y | tracked fix |
| APA-05 | Page number top-right every page incl. title page | Setup Guide /§1.17 | both | Y | tracked fix |
| APA-06 | No running head (student); ALL-CAPS ≤50-char running head left of page number (professional) | Student Title Page Guide / pro guide | mode-dependent | Y | fix/warning |
| APA-07 | Title page: title bold centered upper half (3–4 lines down), author names, affiliation, course+number, instructor, due date (student); title/author/affiliation, no course, author note (professional) | Student Title Page Guide | student/pro | Y (layout) | fix + comments |
| APA-08 | Abstract ≤250 words, one unindented paragraph, "Abstract" bold centered | Concise Guide §abstract | both | Y | comment (length), fix (heading style) |
| APA-09 | Keywords: italic "Keywords:" label, indented, lowercase unless proper nouns, ≤1 line | Concise Guide | both | Y | fix + comment |
| APA-10 | Intro: repeat bold centered title, NO "Introduction" heading | Concise Guide /§1.11 | both | Y | fix headings |
| APA-11 | Heading levels 1–5: L1 centered bold, L2 flush-left bold, L3 flush-left bold italic, L4 indented bold, L5 indented bold italic; title case; no paragraph break after heading | Heading Templates (student/professional) | both | Y | tracked fix on styles |
| APA-12 | References start new page, bold centered "References", hanging indent 0.5 in, double-spaced, alphabetical | Concise Guide / ref checklist | both | Y | order=comment, indent=fix, hanging indent exists (`reference_indent_corrections.py`) |
| APA-13 | In-text citation: (Author & Author, Year) parenthetical; Author and Author (Year) narrative | ref guide | both | Y — code passes exist: `narrative_citation_corrections.py`, `citation_formatting_corrections.py`, `et_al_corrections.py` | tracked fix |
| APA-14 | Block quote ≥40 words: new line, indented 0.5, no quotation marks, citation after final period | ref guide | both | Y — partially (`SPE004`, `quotation_utils`, Quote style) | fix + comment |
| APA-15 | Table number bold ("Table 1"), italic title title case, Note. below (TABLE_* exists) | ref guide / table setup | both | Y — existing `table_*` passes + `TABLE_*_STYLE_ID` | fix + comment |
| APA-16 | Figure number bold ("Figure 1"), italic title, sans-serif image | ref guide | both | Y — existing `FIG001/002`, `caption_apa7_check` | fix + comment |
| APA-17 | Numbers: spell out <10 in prose, numerals for stats/units/ages (existing `number_word_corrections`); two decimals policy is JUTLP (`decimal_corrections` says "This Journal...") | ref guide | both | Y | fix + comment — **message text needs de-JUTLP-ing** |
| APA-18 | DOI as https://doi.org/... ; don't add URLs to DB homepage | ref checklist | both | Y — `reference_format_corrections.py` likely; VERIFY | fix |
| APA-19 | Appendices allowed after references, "Appendix A" labels | ref guide | both | Y — **CONFLICTS with `appendix_removal.py` (JUTLP bans appendices)** | REMOVE for APA mode |
| APA-20 | Do not use "Practitioner Notes", banner, text box, CRediT block, AI-disclosure mandate, combined Results+Discussion ban | — | APA mode must not emit | client decision | remove |

**Hard conflicts with current engine (must flip for APA):** justified text→left; 1.15 spacing→double; Arial-11 pin→selectable; centered H1 stays (L1 is centered — JUTLP H2 title-case/centered differs); JUTLP section names→APA section expectations (Method→"Method", References fine); "no appendices"→appendices allowed; Practitioner Notes/keywords-5-limit/abstract-250-in-line-region → APA variants; 3-sentence paragraph minimum (`short_paragraph_comments`) → JUTLP house rule, REMOVE/DEFER; AU spelling → client decision (US likely for APA); blinded-in-final mandate → JUTLP-specific (APA equivalent: title page author note/anonymized); dot-point ban message references "academic journal…Practitioner Notes" → REMOVE.

## B. Component inventory

| Module | APA-mode verdict | Evidence |
|---|---|---|
| `domain/canonical_jultp_template.py` | DELETE (JUTLP moved to another application); replaced by `apa7_template.py` | `CANONICAL_STRUCTURE` hardcodes front_page, practitioner notes, Method subs |
| `domain/jutlp_guidelines.py` | DELETE, replaced by `apa7_guidelines.py` (APA-generic, mode-neutral) | `JUTLP_GUIDELINES` injected into prompt |
| `domain/jutlp_editorial_examples.py` | DELETE, replaced by `apa7_editorial_examples.py` (15-word JUTLP title limit, CRediT examples) | `EDITORIAL_EXAMPLES` |
| `domain/reporting_ownership.py` | ADAPT | `SAM_FIXED_RULE_IDS`, `FAMILY_VERDICTS` keyed to JUTLP families |
| `domain/models.py`, `domain/editorial_feedback.py` | KEEP | generic |
| `domain/jutlp_template_style_map.json` | DEFER/REMOVE for APA — styles come from JUTLP .docx | maps "Normal","Heading 1" (Arial 14 centered) |
| `services/jutlp_validator.py` | ADAPT — keep engine, swap rule set; JUTLP-only families SEC/MET/DIS/FP/SPE001–3/CON/AFF/ANDOR/ETC/DOTPT disabled in APA mode | `validate()` aggregates per-family `check_*` |
| `services/output_generation_samfix.py` | HEAVIEST. Build a new APA `build_edited_document`; reuse helpers (`_write_single_comment_docx`, heading keepNext, table formatting, normal-style fix) | `_TEMPLATE_PATH`=JUTLP docx, `_insert_front_page_banner_from_template`, `_insert_front_page_text_box_from_template`, `_move_body_citation_to_footer`, `_apply_intro_page_break`, `_apply_heading_1_text_normalization`, `PRACTITIONER_*`, `CENTER_ALIGNED_HEADING_TEXTS`, Arial/1.15 constants |
| `services/output_generation.py` | ADAPT — comment anchors/labels JUTLP (`_CANONICAL_ORDER`, `"Article Title"`, `"Practitioner Notes"`) | `generate_commented_docx`, `_REF_ENTRY_STYLE` |
| `services/heading_corrections.py` | ADAPT — strip numbers OK; rename map JUTLP | `SECTION_RENAME_MAP` |
| `services/editorial_review_comments.py` | ADAPT | `SECTION_TEXT_ALIASES`, `CATEGORY_TO_SECTION_KEY` include practitioner notes/keywords |
| `services/keywords_generation.py` | ADAPT (5-max JUTLP) | `_MAX_KEYWORDS=5`, system prompt says "JUTLP" |
| `services/document_styling_fixes.py`, `document_normalisation_services.py`, `document_zones.py`, `document_analysis_services.py` | ADAPT — zones/style anchors reference "Practitioner Notes","APA 7 Reference List Entry","Guidance Notes" | `SKIP_STYLES`, `GUIDANCE_NOTES_STYLE`, `_ABSTRACT_BOUNDARY_TEXTS` |
| `services/ai/prompt_builder.py` | ADAPT — swap guideline source + category list | `## JUTLP Editorial Guidelines` block, `JUTLP_TITLE_WORD_LIMIT=15` |
| `services/ai/editorial_review_service.py` | KEEP (thin wrapper) | strips markers only |
| `services/ai/llm_client.py` | KEEP | JSON-schema generic |
| `services/body_llm_edits.py`, `grammar_corrections.py` | KEEP logic, ADAPT spelling direction (US/AU decision) | `_fix_au_spellings`, `AU_CORRECTIONS`, prompt "JUTLP house style" |
| `services/language_corrections.py` | DECIDE: invert to US for APA (client) | `AU_CORRECTIONS` ~900 entries US→AU |
| `services/spell_checker.py` | ADAPT — AU whitelist + no US-ize autofix | `_ACADEMIC_WHITELIST`, `_US_IZE_SUFFIX_RE` |
| `services/acronym_corrections.py` + `app/data/acronyms.json` | KEEP (JUTLP-coloured intro comment) | `_CONSOLIDATED_INTRO` |
| `services/number_word_corrections.py`, `decimal_corrections.py`, `abbreviation_corrections.py`, `et_al_corrections.py`, `citation_formatting_corrections.py`, `narrative_citation_corrections.py` | KEEP; `decimal_corrections` comment text de-JUTLP | regexes APA |
| `services/short_paragraph_comments.py` | REMOVE for APA (3-sentence rule is JUTLP) | message text |
| `services/appendix_removal.py` | REMOVE for APA — APA allows appendices | `_COMMENT_TEXT` "JUTLP does not accept appendices" |
| `services/blinded_citation_comments.py` | REMOVE for APA or retarget | "JUTLP publishes identified…" |
| `services/caption_apa7_check.py`, `table_*` passes, `run_font_corrections.py`, `quotation_utils.py`, `reference_*` (checker/type/indent/order/format/reconstructor/hyperlink) | KEEP logic; ADAPT constants (`_TARGET_FONT="Arial"` → APA-allowed default) | as named |
| `services/jutlp_articles.py`, `/api/jutlp-articles`, carousel in `openeditor.js`/`api.js` | REMOVE/HIDE for APA default | main.py:583, writer.html:100 |
| `services/access_validation.py` | KEEP disabled; nothing in this plan calls it | `skip_auth_enabled`, `verify_memberpress` stub |
| `main.py` (results payload, `/api/upload`, timeouts) | KEEP; no profile field needed | per api-contract.md |

**Validator rule families in APA mode:** survive — STY (style sanity, retargeted), TAB001/002, FIG001/002, SPE004 (40-word quotes), REF/CREF/HREF/CONS, REFE; **disable** — SEC*/MET*/DIS*/FP*/SPE001–3/CON001/AFF001/ANDOR/ETC/DOTPT/STY003(body=Normal kept), STY002.

## C. Architecture recommendation

**Recommend: full JUTLP removal, APA 7-only codebase, staged rollout.**

There is no live JUTLP service to protect (JUTLP lives in a different application), so no profile switch is needed. OpenEditor is APA-7-only.

- Delete / replace the JUTLP domain and service layer rather than guarding it: remove `canonical_jultp_template.py`, `jutlp_guidelines.py`, `jutlp_editorial_examples.py`, `jutlp_template_style_map.json`, `jutlp_validator.py`'s JUTLP rule families (SEC/MET/DIS/FP/CON/AFF/ANDOR/ETC/DOTPT/SPE001–3), `output_generation_samfix.py`'s JUTLP steps (banner, text box, citation-to-footer, practitioner/keywords stubs, intro page-break, heading-name normalisation, Arial-11/1.15/justified pinning), `appendix_removal.py`, `short_paragraph_comments.py`, `blinded_citation_comments.py`, `jutlp_articles.py` + `/api/jutlp-articles` + the carousel in `openeditor.js`.
- Introduce `app/domain/apa7_template.py` (`CANONICAL_STRUCTURE_APA7`: student/professional front page, abstract ≤250, Method/Results/Discussion as *expected* sections, appendices allowed), `apa7_guidelines.py`, `apa7_editorial_examples.py`.
- `config.py` is APA-7-only: no `EditorialProfile`. Single constants module for APA 7 defaults (font set, double spacing, 0.5" indent, margins).
- Pipeline stays one path: `validate(docx)` → `run_editorial_review(...)` → `build_edited_document(...)`, all APA-7. Threaded parameter is the manuscript doc, not a profile.
- Replace the JUTLP base .docx (`JUTLP Template 2026.docx`) and `jutlp_template_style_map.json` with an APA base template before APA styling can be considered correct.

No fork: there is nothing to preserve on this side. The valuable shared machinery (tracked-change builder, reference passes, table passes, LLM client, pipeline orchestration) survives the JUTLP deletion intact.

## D. Prioritised work breakdown — stages, not weeks

**Stage 1 — Cut JUTLP out (everything must still import + tests green):**
1. Delete JUTLP service files listed in C; strip their imports/calls from `feedback_gen_pipeline.py`, `main.py`, `editorial_review_service.py`, `document_zones.py`, `document_analysis_services.py`, `output_generation.py`, `heading_corrections.py`, `editorial_review_comments.py` — S.
2. Create `apa7_template.py` / `apa7_guidelines.py` / `apa7_editorial_examples.py` and point `prompt_builder.py` at them — S.
3. Remove JUTLP carousel from `writer.html` / `openeditor.js` / `api.js` and delete `/api/jutlp-articles` — S.
4. De-JUTLP user-facing strings in kept passes (`decimal_corrections._PRECISION_COMMENT`, appendix text, short-paragraph message, output filename, results summary) — S.

**Stage 2 — APA 7 structural correctness (visible in demo output):**
5. APA body formatting pass: double spacing, left-align, first-line 0.5", no space before/after headings, margins 1", page number top-right — M.
6. APA heading levels 1–5 style fix (L1 centered bold / L2 flush-left bold / L3 flush-left bold-italic / L4–5 indented) — M.
7. Title-page normalisation to student default (bold centered title, affiliations, course, instructor, due date) — M.
8. References: new page, bold centered "References", hanging indent, alphabetical comment, DOI form — M.
9. Abstract/keywords bounds per APA (no 250-in-line-region JUTLP logic; "Abstract"/"Keywords:" labels) — M.

**Stage 3 — Consistency + ship:**
10. Title-case bug: fix `_to_title_case_title` so replacement words re-cap correctly (e.g. "Task One" not lowercase) — S.
11. Replace base template .docx with an APA one; re-pin Normal/Heading styles to APA — M.
12. US-vs-AU spelling decision implemented as `SPELLING_VARIANT` (default per client) — M.
13. Batch evaluation harness from §E + baseline vs final conformance score — M.
14. Defer: clean-vs-tracked toggle, references[].title gap, D-01/D-02 verification.

## E. Evaluation plan

1. **Corpus assembly:** 15–30 .docx — mix student/professional, with/without abstract, tables, figures, appendices, ≥1 intentional-error doc per rule family (bad title page, no double spacing, justified text, missing hanging indent, comma decimals, 3+ author inline missing "et al.", >40-word quote inline, appendix removed-by-JUTLP, blinded placeholders). Source from sample-paper hub + team-collected real papers (week-1 demo set).
2. **Checklist harness:** Python script opens each output .docx with python-docx + zip XML; assert per-row checks from matrix A (spacing=480 twips, alignment left, margins 1440, font ∈ allowed set, heading levels correct, References page break + hanging indent, no Practitioner Notes/banner, appendices preserved, abstract ≤250, citations format, table/figure numbering).
3. **Tracked-change diff:** for each output, `git`-style diff of `<w:del>/<w:ins>` text vs input; count insertions/deletions per pass family; ensure no pass regresses another (id collisions: assert `w:id` monotonic via `_max_revision_id`).
4. **Baseline before/after:** run CURRENT engine on the same corpus first, record score; run after APA cleanup; report conformance delta per rule row.
5. **LLM conformance:** for 5 docs, have reviewer eyeball `notes[]` — must contain no JUTLP references ("Practitioner Notes", "JUTLP limit") in APA mode.

Report: table of (doc, rule, pass/fail, #tracked changes) + aggregate APA-7 conformance %.

## F. Risks & open questions

**Client decisions needed:**
1. Student vs professional default? (recommend auto-detect with manual override)
2. US vs AU spelling for APA output?
3. Keep editorial LLM commentary in APA mode? (currently generic enough; keep but de-JUTLP framing in `editorial_review_service`)
4. What happens to JUTLP-only checks (Practitioner Notes, CRediT, AI-disclosure)? (recommend: delete with the JUTLP layer — they live in the other application)
5. Which fonts are acceptable to pin (client picks default, e.g. 11pt Calibri)?
6. Carousel: remove or rebrand to APA resources?

**Technical risks:**
- Tracked-change `w:id` collisions across passes — pipeline already re-seeds via `_max_revision_id` after samfix; any new APA passes must take `next_lang_id` (risk if bypassed).
- Pass-ordering dependencies in `feedback_gen_pipeline.py`: `_fix_au_spellings` post-passes, spell_checker must run after AU map, heading corrections before editorial anchors.
- Style fragmentation: output styles are copied from `JUTLP Template 2026.docx` / `jutlp_template_style_map.json` — APA output will still carry JUTLP style names/ids ("Article Title", "Practitioner Notes") until a clean APA base .docx exists. **Need an APA base template .docx from client or built from setup guide.**
- `canonical_jultp_template.py` is imported in ~15 places; deleting it means a single sweep fixing every import — do it in one commit so the tree never half-imports.
- `references[ ].title` always null (known gap); 2 failing tests in `test_jutlp_validator.py` unrelated to APA work — do not let them block.

**First 5 actions for tomorrow (exact files to open):**
1. `app/config.py` — make it APA-7-only: single constants module for APA 7 defaults (allowed fonts, double spacing, 0.5" indent, 1" margins); no `EditorialProfile` enum.
2. Create `app/domain/apa7_template.py`, `apa7_guidelines.py`, `apa7_editorial_examples.py`.
3. `app/pipelines/feedback_gen_pipeline.py` lines ~700–1080 — strip JUTLP imports/calls, point `validate` / `run_editorial_review` / `build_edited_document` at the APA modules.
4. `app/services/output_generation_samfix.py` — delete JUTLP-only steps in `build_edited_document` (banner/textbox/citation-footer/practitioner/keywords/heading-normalisation/intro-page-break); open `_to_title_case_title` at line 479 to fix the capitalisation-after-replacement bug.
5. `app/services/ai/prompt_builder.py` — switch `JUTLP_GUIDELINES`/`EDITORIAL_EXAMPLES` import to the APA constants; verify `VALID_CATEGORIES` still covers APA.
