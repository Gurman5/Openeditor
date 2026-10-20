# Feedback Generation Pipeline Pass-Order Ledger (C-01)

This ledger documents the exact execution order, pass type, identifier source, and terminal state of all processing steps within `feedback_gen_pipeline.py`.

| Order | Pass Name / Service Module | Pass Type (Comment / Tracked Change) | Identifier Source | Terminal State / Action |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Document Normalization** (`document_normalisation_services.py`) | Structural Clean / Tracked Change | Hardcoded / Seeded (`1`) | Standardizes document zones, front-matter layout, and root element hierarchy. |
| 2 | **Heading Corrections** (`heading_corrections.py`) | Tracked Change / Hierarchy Adjustment | Pipeline `next_lang_id` | Aligns H1-H5 heading levels with APA-7 structural requirements and corrects numbering/spacing. |
| 3 | **Document Styling Fixes** (`document_styling_fixes.py`) | Tracked Change | Pipeline `next_lang_id` | Enforces font family (Calibri), size (11pt), line spacing, and paragraph indents. |
| 4 | **Reference Checker** (`reference_checker.py`) | Comment / Validation | Matrix ID / Validator | Scans bibliography entries, cross-references citations, and appends comment tags for missing DOIs or malformed entries. |
| 5 | **Samfix Output Generation** (`output_generation_samfix.py`) | Tracked Change / Final Layout Fixes | Pipeline `next_lang_id` | Applies table keep-together rules, section boundaries, and page break adjustments prior to final export. |

## C-28 / APA-10 Intro Heading — intra-Samfix ordering

Within `output_generation_samfix.build_edited_document`, the title/heading work runs in this order:

| Step | Function | Rule | Notes |
| :--- | :--- | :--- | :--- |
| a | `_apply_intro_page_break` | SPE002 | Page break before the first body paragraph. |
| b | `_apply_apa_heading_styles` | C-23 / APA-11 | Restyles Heading 1–5 from the APA base. |
| c | `apply_heading_corrections` | — | Tracked strip of leading section numbers / canonical renames. |
| d | `_apply_apa_title_page` | C-24a/b | Settles the front-page title (title-casing + AU respelling). |
| e | `_apply_heading_1_text_normalization` | **C-28 / APA-10** | Runs **last** among the title/heading passes: a literal `"Introduction"` Heading 1 becomes the repeated title (bold, centred). Direct edit — no comment / tracked change. |
| f | `apply_run_font_corrections` | — | Final font sweep. |

**Why C-28 runs after `_apply_apa_title_page`:** it reads the title via `titleFound`, so it must see the *final* front-page title (already title-cased and AU-respelt); otherwise the body copy diverges from the front page.

**Why C-28 runs after `apply_heading_corrections`:** a numbered `"1. Introduction"` is first reduced to `"Introduction"` by the tracked number strip, so C-28 can then match it. Because C-28 runs after that strip, its replacement (the python-docx `paragraph.text` setter) absorbs the strip's `w:del`/`w:ins` — the heading text edit is untracked by design.

Because C-28 runs late, the passes between C-23 and C-28 that key off a literal `"Introduction"` heading — `_apply_body_and_reference_style_fixes`, `_remove_bold_italic_from_normal_body_paragraphs`, `_apply_missing_keywords_stub` — now still see the heading (previously C-28 had already renamed it to the title, silently disabling them).

## Revision ID Management & Safety
- **Dynamic Reseeding**: To prevent revision identifier collisions across passes, the pipeline evaluates `next_lang_id = _max_revision_id(...) + 1` dynamically at major phase boundaries.
- **Firewall Rule**: Passes utilizing `output_generation_samfix.py` strictly adhere to Track C dependency locks and execute only after prerequisite import sweeps are verified.