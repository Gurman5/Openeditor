# Feedback Generation Pipeline Pass-Order Ledger (C-01)

This ledger documents the exact execution order, pass type, identifier source, and terminal state of all processing steps within `feedback_gen_pipeline.py`.

| Order | Pass Name / Service Module | Pass Type (Comment / Tracked Change) | Identifier Source | Terminal State / Action |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Document Normalization** (`document_normalisation_services.py`) | Structural Clean / Tracked Change | Hardcoded / Seeded (`1`) | Standardizes document zones, front-matter layout, and root element hierarchy. |
| 2 | **Heading Corrections** (`heading_corrections.py`) | Tracked Change / Hierarchy Adjustment | Pipeline `next_lang_id` | Aligns H1-H5 heading levels with APA-7 structural requirements and corrects numbering/spacing. |
| 3 | **Document Styling Fixes** (`document_styling_fixes.py`) | Tracked Change | Pipeline `next_lang_id` | Enforces font family (Calibri), size (11pt), line spacing, and paragraph indents. |
| 4 | **Reference Checker** (`reference_checker.py`) | Comment / Validation | Matrix ID / Validator | Scans bibliography entries, cross-references citations, and appends comment tags for missing DOIs or malformed entries. |
| 5 | **Samfix Output Generation** (`output_generation_samfix.py`) | Tracked Change / Final Layout Fixes | Pipeline `next_lang_id` | Applies table keep-together rules, section boundaries, and page break adjustments prior to final export. |

## Revision ID Management & Safety
- **Dynamic Reseeding**: To prevent revision identifier collisions across passes, the pipeline evaluates `next_lang_id = _max_revision_id(...) + 1` dynamically at major phase boundaries.
- **Firewall Rule**: Passes utilizing `output_generation_samfix.py` strictly adhere to Track C dependency locks and execute only after prerequisite import sweeps are verified.