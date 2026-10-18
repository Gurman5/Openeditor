# C-28 — APA-10 Intro Heading: Implementation Plan

> Repo: `Openeditor` · **Branch: `apa7-rework-v2` (work directly on this branch — no new branch)**
> Working tree: clean except untracked `research/`.
> Backlog: `docs/apa7-backlog-C.md` row C-28 · Rule: APA-10 ("Intro: repeat bold centered title, NO 'Introduction' heading")

## 1. Goal

APA 7 requires the body of the paper to begin by repeating the paper title in **bold, centered**, with **no** "Introduction" heading. C-28 repurposes `_apply_heading_1_text_normalization` to enforce this.

**Acceptance (from backlog):** Output has no `Introduction` H1; the title is repeated (bold, centered).

**Branch:** implement directly on the current `apa7-rework-v2` branch.

## 2. Current state (verified)

- **C-23 done** — `_apply_apa_heading_styles` (`output_generation_samfix.py:8192`) restyles Heading 1–5 from the APA base (L1 centered bold, Calibri, `line=480`, `keepNext`).
- **C-24a/b done** — `_apply_apa_title_page` (`:8541`), **called at `:9899` — i.e. *after* C-28**.
- **C-28 NOT done** — `_apply_heading_1_text_normalization` (`:9680`) still implements the JUTLP alias pass:
  - `HEADING_1_TEXT_NORMALIZATIONS` (`:9669`) built from `SECTION_RENAME_MAP`.
  - `_canonical_heading_1_text` (`:9675`) / `_template_heading_1_name` (`:9657`).
  - Leaves `"Introduction"` as a Heading 1; inserts no repeated title.
- Call order (already correct): `_apply_intro_page_break` `:9768` → `_apply_apa_heading_styles` (C-23) `:9775` → `_apply_heading_1_text_normalization` (C-28) `:9780`. Requirement is only "C-23 before C-28".
- **`_TEMPLATE_PATH` is already the APA base** (`app/domain/APA7 Base Template.docx`, `:294`) — confirms C-47's base is in place.

### Reproduction

Built a student doc with an `"Introduction"` Heading 1, ran the current chain
`_apply_apa_body_geometry` → `_apply_apa_title_page` → `_apply_intro_page_break` → `_apply_apa_heading_styles` → `_apply_heading_1_text_normalization`, then `tools.corpus.checks.headings`:

```
APA-10 fail
  no_introduction_heading: fail  (found paragraph 9)
  title_repeated:          fail  (copies [])
```

Both subchecks broken. The JUTLP corpus (`tests/jutlp_sample_docx_test_pack/01_valid_identified.docx`) all have `"Introduction"` H1 at the body start and **no** repeated title — exactly the case C-28 must fix.

**Known-good target:** `tests/corpus/seed/seed-01.docx` — the body's repeated title is a **Heading 1** paragraph (para 11) equal to the title, centered + bold, with no `"Introduction"` heading.

**Checker semantics** (`tools/corpus/checks/headings.py:164-218`): a paragraph whose `_norm` text equals the title is classified as a *copy* (so a Heading-1-typed title is not flagged as a heading); `title_repeated` needs the copy centered + all visible runs bold; `no_introduction_heading` fails on any heading normalized to `"introduction"`.

## 3. Locked design decisions

| # | Decision | Choice |
|---|---|---|
| D1 | How to handle the `"Introduction"` heading | **Convert its text to the title** (keep Heading 1 → bold/centered via C-23; preserves page break; matches seed-01) |
| D2 | Insert title when no `"Introduction"` heading exists | **No** — only handle the Introduction case (keep C-28 size S) |
| D3 | `_apply_intro_page_break` | **Keep** (page break before the now-title paragraph is desirable) |
| D4 | Change type | **Direct edit** (consistent with the existing silent text-fix; no comments/tracked changes) |
| D5 | Title source | **Backlog-minimal `title_text` only** (not the conditional `corrected_title` rule) — see note below |
| D6 | Implementation idiom | **python-docx `paragraph.text =`** (matches sibling `_apply_heading_2_title_case`; smallest diff) |

**D5 note — superseded by the revision (see §7).** This plan originally read the literal `title_text` because the title-page pass ran *after* C-28. C-28 now runs after `_apply_apa_title_page` and reads the final front-page title via `titleFound` on the already-corrected document, so the body copy matches the front page exactly — including AU respellings.

## 4. Implementation

### 4.1 Rewrite the pass — `output_generation_samfix.py:9680`

Replace `_apply_heading_1_text_normalization` with an APA-10 implementation (backlog-minimal, `title_text` only):

1. `title_state = titleFound(input_path)`; return `False` if `title_found is False` or `title_text.strip() == ""`.
2. `new_title = title_state["title_text"].strip()`.
3. `doc = DocxDocument(input_path)`; match the first Heading 1 whose *accepted-changes* text (via `load_paragraphs`) normalises to `"introduction"`: skip if the text already equals the title; else set `paragraph.text = title`, `changed = True`, **break** (first match only). Numbered intros (`"1. Introduction"`) are handled too, because C-28 now runs **after** `apply_heading_corrections` has stripped the number (see §7).
4. `doc.save(output_path)` only when changed; return `True`/`False`.

> Keep the python-docx idiom (D6). `paragraph.text =` creates a single fresh run that inherits purely from the Heading 1 style — no leftover run `rPr` (italic/non-bold) leaking onto the title copy, and the smallest possible diff. (Raw-XML `_set_paragraph_text_direct` was considered but is unnecessary here.)

### 4.2 Remove dead JUTLP alias code (same change)

- Delete `HEADING_1_TEXT_NORMALIZATIONS` (`:9669`), `_canonical_heading_1_text` (`:9675`), `_template_heading_1_name` (`:9657`).
- Drop the now-unused `SECTION_RENAME_MAP` import (`:17`).
- **Keep** `CANONICAL_STRUCTURE` (used at `:2190`, `:3688`, `:4380`…) and `strip_leading_section_number` (used by C-28 and `_apply_intro_page_break` at `:7617`).
- Pipeline call site at `:9780` unchanged.

### 4.3 Tests

**New** `tests/test_apa7_intro_heading.py`:
- Student doc with an `"Introduction"` H1 → run `_apply_apa_body_geometry` + `_apply_apa_heading_styles` + `_apply_heading_1_text_normalization`, then assert `tools.corpus.checks.headings.check_headings` gives APA-10 `pass`; XML assert no Heading 1 paragraph reads `"Introduction"` and a centered bold run carries the title.
- Doc that already repeats the title and has no `"Introduction"` heading → pass returns `False`, output unchanged, no duplicate title.
- No title page title → returns `False`.

**Update** `tests/test_front_page_style_fixes.py:629-692` — the three JUTLP alias tests become APA-10 tests (or move to the new file); fix imports if `_apply_heading_1_text_normalization` usage changes.

**Update** `tests/test_heading_corrections.py:26-29,229-234` — drop the `HEADING_1_TEXT_NORMALIZATIONS` import; replace `test_sam_silent_rename_uses_the_same_map` with an APA-10 assertion.

**Keep** `tests/test_intro_page_break.py` (pass retained) — should stay green.

### 4.4 Verify (Windows)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_apa7_intro_heading.py tests/test_apa7_title_page.py tests/test_intro_page_break.py tests/test_heading_corrections.py -q

# End-to-end on the two reference docs
.\.venv\Scripts\python.exe -m tools.corpus.checks.headings --docx <chain-output-on-01_valid_identified.docx>   # APA-10 pass
.\.venv\Scripts\python.exe -m tools.corpus.checks.headings --docx <chain-output-on-seed-01.docx>                # APA-10 pass

.\.venv\Scripts\python.exe -m ruff check app/services/output_generation_samfix.py tests/
```

### 4.5 Docs

- Mark the C-28 row done in `docs/apa7-backlog-C.md` (with commit/PR).
- Note in `docs/pass-order-ledger.md` that C-28 runs after C-23.

## 5. Risks / notes

- **Title source (resolved):** C-28 now runs after `_apply_apa_title_page` and reads the final title, so the body copy equals the front-page title exactly (AU respellings included). The earlier `title_text`-only limitation is closed.
- **Numbered intro (resolved):** C-28 now runs after `apply_heading_corrections`, so `"1. Introduction"` has already been reduced to `"Introduction"`. It matches on the *accepted-changes* text (`load_paragraphs`) — after the number strip the text lives in a `w:ins`, and python-docx `paragraph.text` would read it as empty.
- The pass only converts an existing `"Introduction"` H1 and breaks after the first match — it never inserts a second title copy.
- If C-23 didn't run (isolated unit test), the Heading 1 style is whatever the input has; tests must run C-23 first, as the pipeline does.
- `test_heading_corrections.py` already imports from `canonical_jultp_template` (a C-12 delete target) — out of C-28 scope, but the `HEADING_1_TEXT_NORMALIZATIONS` import must go now.

## 6. File touch-list

| File | Change |
|---|---|
| `app/services/output_generation_samfix.py` | rewrite pass `:9680`; delete alias map/helpers `:9657-9677`; drop `SECTION_RENAME_MAP` import `:17` |
| `tests/test_apa7_intro_heading.py` | new |
| `tests/test_front_page_style_fixes.py` | rewrite/remove alias tests `:629-692` |
| `tests/test_heading_corrections.py` | drop import + test `:26-29,229-234` |
| `docs/apa7-backlog-C.md` | mark C-28 done |
| `docs/pass-order-ledger.md` | note C-28 after C-23 |

## 7. Revision — run C-28 late (post-review)

The first implementation ran C-28 immediately after C-23, i.e. *before* `_apply_apa_title_page`, and read `paragraph.text` (so it never saw the tracked number strip). Three problems, all fixed by moving the call to run **after** `_apply_apa_title_page`, immediately before `apply_run_font_corrections`:

1. **Title source** — `titleFound` now sees the already-corrected front-page title, so the body copy matches it exactly (AU respellings included). D5's conditional-`corrected_title` rule is unnecessary.
2. **Numbered intro** — the tracked `apply_heading_corrections` strip runs first, so `"1. Introduction"` is now handled. The heading is matched on the *accepted-changes* text via `load_paragraphs` (`paragraph.text` reads empty once the text sits in `w:ins`).
3. **Downstream anchors** — passes that key off a literal `"Introduction"` heading (`_apply_body_and_reference_style_fixes`, `_remove_bold_italic_from_normal_body_paragraphs`, `_apply_missing_keywords_stub`) run before C-28's new position and now still see the heading; they were silently disabled while C-28 ran earlier.

**Untracked by design:** the replacement uses the python-docx `paragraph.text` setter, which clears every non-`pPr` child — including the number strip's `w:del`/`w:ins`. The heading text edit is a silent, untracked change (consistent with the sibling silent text fixes).

**Knock-on:** `test_sam_fixes_validator_rules.py::test_spe002_intro_page_break` — C-28 absorbs the `"Introduction"` section, so SPE002 stops being emitted (absent, not pass). The test now asserts the page break survives on the heading that absorbed the Introduction.

**Known pre-existing gap (not fixed here):** a full `build_edited_document` run over `tests/corpus/seed/seed-01.docx` fails APA-10 `title_repeated` (`find_headings` sees the title paragraph's text drop out of the accepted view, so the first non-empty paragraph becomes `"Keywords"` and the title has no copies). This reproduces identically on the original commit `3730383` and after the reorder, so it is a pre-existing issue in the title-page pass / seed fixture, not a consequence of moving C-28. §4.4's "seed-01 must still pass" target is therefore not currently met.

See `docs/pass-order-ledger.md` §"C-28 / APA-10 Intro Heading" for the resulting order.
