# Joey's revisions — track-2 amendment plan (JB-02 / JB-04 / JB-08 review)

**Date:** 2026-10-21
**Reviewer:** pipeline dev (Daria)
**Branch reviewed:** `joeys-revisions-track-2` @ `85f3f2b`
**Commits reviewed:** `52d14f4`, `68048df` (JB-02), `d885fff` (JB-04), `85f3f2b` (JB-08) — author `s4027482-ps1nov` (Humaid)
**Criteria source:** `docs/joeys-revisions-execution-plan.md` §4.2 (JB-02), §4.7 (JB-04), §4.8 (JB-08) — note: the doc lives on the `joeys-revisions`/`track-1` line (`a132f87`+), not on this branch's history
**Method:** diff review against the plan's per-ticket criteria, static reachability analysis, targeted empirical runs, full test suite (`1130 passed, 1 skipped`; bare `pytest` is blocked by a pre-existing collection error — see §E), `ruff` on all touched files

This document lists only defects found in review, with concrete amendments. It does not re-litigate ticket scope.

---

## Findings summary

| # | Ticket | Finding | Severity |
|---|---|---|---|
| 1 | JB-02 | `_apply_author_plan` `insert_default_authors` handler arm still live (plan criterion 2 explicitly required it commented out) | **Blocking** |
| 2 | JB-02 | Both missing-authors plan constructions in `authorFormatCheck` were **deleted**, not commented out (criterion: "comment out, do not delete"); the surviving comment falsely claims "commented out, not deleted" | Should |
| 3 | JB-02 | Rationale comments paraphrase rather than carry the plan's quoted block | Should |
| 4 | JB-02 | `llm_calls/25` trace sanity (real authors in 2nd editorial prompt) not evidenced | Should |
| 5 | JB-04 | Professional-mode running head is **re-installed after blanking** — plan listed `_apply_apa_title_page_headers` as a work site; it was not touched | **Blocking** |
| 6 | JB-04 | Word-COM gate assertion (page number top-right) not evidenced | Could |
| 7 | JB-08 | "±table-range" read as above-table only; plan fixture asks for subheading-below case | Should (decision needed) |
| 8 | JB-08 | No explicit spacing-uniformity-inside-tables assertion | Should |
| 9 | JB-08 | Plan-listed files `reference_indent.py` / `references_block_corrections.py` / `abstract_keywords_formatting.py` unverified (likely zone-scoped) | Could |
| 10 | Lint | 2 unused imports in `tests/test_front_page_style_fixes.py` (:5 `WD_SECTION`, :18 `AUTHORS_REQUIRED_STYLE_ID`); missing EOF newline in `tests/test_output_filename.py` | Trivial |
| 11 | Branch | `tests/test_docx_ooxml_validity.py` fails collection (imports `_reconcile_comment_sidecars`, absent from the pipeline since before `51158df`) — **pre-existing, not from these commits** | Out of Joey scope (§E) |

---

## A. JB-02 — placeholder author/affiliation insertion

### A1 (blocking) — comment out the live `insert_default_authors` arm in `_apply_author_plan`

**Site:** `app/services/output_generation_samfix.py:6771-6828` (the whole `if action == "insert_default_authors": … return True` block; the `replace_in_place` arm at `:6830` must stay untouched).

**Defect:** plan §4.2 criterion 2 lists this arm as one of three sites to disable. It is still fully functional — insertion is only inert because no in-tree caller produces the action any more. A hand-built plan (tests, future flag re-enable, another refactor) would still write "First Author^a…" placeholders, comments, and affiliation paragraphs.

**Amendment:** comment out the entire `:6771-6828` block (prefix each line with `#`; do not delete — same "Joey may want this later behind a flag" rationale as the ticket). Prepend the plan's rationale block (see A3). Note for reviewers: the `_append_affiliation_before_notes` call at `:6788` dies with this block; its definition and the `DEFAULT_AUTHORS_LINE` / `DEFAULT_AUTHOR_AFFILIATIONS` / `_default_authors_line_for_markers` / `_default_affiliations_text_for_authors` / `_find_existing_affiliations_for_missing_authors` machinery must **stay** (criterion: keep `SUPERSCRIPT_CHAR_MAP` etc.; the helpers are already unreferenced outside comments except through this arm).

**Acceptance test** (add to `tests/test_front_page_style_fixes.py`):

```python
def test_insert_default_authors_plan_is_inert(tmp_path):
    """Belt-and-braces (JB-02): even a hand-built insert_default_authors
    plan must not write anything — the apply branch is commented out."""
    # doc already has Authors / Author Affiliations styles so nothing else fires
    plan = {"action": "insert_default_authors", "anchor_pos": 0,
            "insert_pos": 1, "corrected_authors_line":
            "First Author^a, Second Author^a, and Third Author^b", ...}
    assert _apply_author_plan(str(input_path), str(output_path), plan) is False
    assert output_path.exists() is False
```

### A2 (should) — restore the deleted code as comments at `authorFormatCheck`

**Site:** `app/services/output_generation_samfix.py:1640-1659`.

**Defect:** the plan said *comment out (do not delete; Joey may want this later behind a flag)*. Humaid replaced the two missing-authors plan constructions with a three-line prose summary whose own header — "Previous behaviour (commented out, not deleted)" — is inaccurate: the literal code was deleted. It is recoverable only from git (`52d14f4^`, blob `1c41adb`). The `abstractFormatCheck` sites (`:2647`, `:2669`) and `_apply_abstract_plan` (`:6974-6997`) **do** comply (properly commented-out code) — only this site does not.

**Amendment:** replace the prose summary (`:1648-1651`) with the following verbatim old code, commented out, under the A3 rationale block:

```python
#     existing_affiliations = _find_existing_affiliations_for_missing_authors(
#         docxpath,
#         author_state["title_idx"],
#     )
#     if existing_affiliations is not None:
#         markers = existing_affiliations["markers"]
#         default_affiliations = ()
#         plan = {
#             "action": "insert_default_authors",
#             "message": "Default author placeholders inserted because authors were not found.",
#             "anchor_pos": author_state["anchor_pos"],
#             "insert_pos": existing_affiliations["first_pos"],
#             "reason": "Authors not found on front page",
#             "corrected_authors_line": _default_authors_line_for_markers(markers),
#             "default_affiliations": default_affiliations,
#             "authors_style_ok": True,
#             "authors_current_style": "",
#         }
#         if len(markers) == 1:
#             plan["append_affiliation_pos"] = existing_affiliations["last_pos"]
#             plan["append_affiliation_text"] = f"{_next_default_marker(markers[0])} Affiliation 2"
#         return plan
#
#     return {
#         "action": "insert_default_authors",
#         "message": "Default author placeholders inserted because authors were not found.",
#         "anchor_pos": author_state["anchor_pos"],
#         "reason": "Authors not found on front page",
#         "corrected_authors_line": DEFAULT_AUTHORS_LINE,
#         "default_affiliations": DEFAULT_AUTHOR_AFFILIATIONS,
#         "authors_style_ok": True,
#         "authors_current_style": "",
#     }
```

The live `return {"action": "none", …}` stays exactly as Humaid wrote it.

### A3 (should) — use the plan's rationale quote at every work site

**Amendment:** at each of the three work sites (`authorFormatCheck:1641`, `abstractFormatCheck:2649` and `:2671`, `_apply_abstract_plan:6974`, plus the new A1 site), lead with the plan's rationale block verbatim:

> Disabled per Joey's reviewer instruction (2026-10): the tool must keep manually
> placed author name and affiliation exactly as authored (e.g. Michael Cowling and
> Joshua Newn, RMIT University) and must not inject "First Author^a…" placeholder
> blocks. Missing author/affiliation is covered by FP002/FP003 comment-only flags.

Existing paraphrases may stay underneath as secondary notes.

### A4 (should) — evidence the `llm_calls/25` trace sanity

Plan criterion: rerun the trace and confirm the second editorial prompt shows the real authors ("Michael Cowling and Joshua Newn"). **Amendment:** run `PIPELINE_TRACE=1 python -m app.pipelines.feedback_gen_pipeline <Cowling-Newn manuscript> --trace`, attach/point to the `llm_calls/*editorial*` request artifacts in the PR, and confirm the author line is real, not placeholder. (Static review found no path that feeds `corrected_authors_line=""` into the editorial prompt, but the plan asks for the run.)

### A5 (could) — single placeholder regex

`app/services/output_filename.py:10-13` introduced `_PLACEHOLDER_AUTHOR_RE` (`First\s+(Author|I\.\s+Last)`) rather than reusing an extraction-side marker regex (criterion: "guard with the same marker regex used for extraction"). Functionally equivalent and covered by tests. Optional: hoist one shared constant used by both extraction and the filename guard so they cannot drift. Low priority.

**Already conforming (no change):** `action:"none"` silent-skip semantics with `corrected_authors_line:""`; `replace_in_place` repairs for malformed-but-present author lines untouched; FP002/FP003 moved to comment-only in `reporting_ownership.py` (correct adaptation for this base, which had them in `SAM_FIXED_RULE_IDS` — locked decision says comment-only); filename fallback guard + test (`Cowling_JUTLP_2026_…`); full-build regression tests via `test_fp002_no_placeholder_authors_inserted` / `test_fp003_no_placeholder_affiliations_inserted`; `SUPERSCRIPT_CHAR_MAP` and helper machinery kept.

---

## B. JB-04 — blank running header, keep only top-right page number

### B1 (blocking) — professional mode re-installs the running head after blanking

**Sites:**
- blanking: `_make_page_number_header` `:7815` (correct in isolation), invoked per header part from `_apply_apa_body_geometry` `:7907-7922` (default + first) — called from `build_edited_document` at **`:9831`**
- the offender: `_apply_apa_title_page_headers` `:8565-8576` → `_ensure_running_head_header` `:8511-8562`, called from `_apply_apa_title_page` at `:8667`, which runs at **`:9936-9941` — after the blanking**

**Defect (empirically verified):** in professional mode (`APA7_TITLE_PAGE_MODE=professional`, or auto when the doc has an Author Note and no student markers — `:8360`) `_ensure_running_head_header` writes a **left-aligned running head + tab + PAGE field** over the already-blanked header. Reproduced: after `geometry → title page` the final header reads `'A STUDY OF … FOR1'` with `jc=left`. JB-04's one-line goal does not hold for professional-mode manuscripts — precisely the journal-submission case. The plan listed `_apply_apa_title_page_headers` **8531-8542** as a work site; it was not touched.

**Amendment (minimal):** in `_apply_apa_title_page_headers`, stop passing a running head — call `_ensure_running_head_header(header_root, None)` (drop the `_derive_running_head` call for the header path). `_ensure_running_head_header` already, for `running_head=None`: rebuilds the PAGE paragraph, strips non-`pPr` children, right-aligns — i.e. it becomes a second blanking pass and the final state is blank + top-right PAGE. Do **not** reorder the build passes (riskier: margins/`sectPrChange` timing). Keep `_derive_running_head` defined (machinery-keep convention) or comment it out with the same rationale as A1.

**Acceptance tests** (extend `tests/test_apa7_title_page.py`):

1. Full-order test: document with pre-existing header text → `_apply_apa_body_geometry` then `_apply_apa_title_page(mode="professional")` → **every** `word/header*.xml` part has exactly one paragraph, no running-head text, `jc=right`, and a PAGE field.
2. Existing header tests stay green.

**Note for PR / Joey confirmation:** APA 7 itself prescribes a running head on professional papers. This amendment follows Joey's explicit "blank header" instruction; add a one-line confirmation question to the PR description so the behaviour change for professional mode is an informed decision, not an accident.

### B2 (could) — Word-COM gate evidence

The plan's Word-COM assertion (page number renders top-right; `word_gate` already opens the output) is runtime evidence, not unit-testable here. **Amendment:** when running the gate / trace with `--trace-word` on a JB-04 fix, note the outcome in the PR. No code change.

**Already conforming:** PAGE paragraph ensured; default + first parts both processed; footers untouched (tested); no track-change markup on header removals (raw XML); `_make_page_field` reuse; stripping of running head sharing the PAGE paragraph (tested).

---

## C. JB-08 — table indent exclusion

### C1 (should, decision needed) — below-table paragraphs ("±table-range")

**Site:** `_table_caption_paragraph_indices` `:8039-8062` excludes (a) caption-labeled paragraphs (`looks_like_caption_paragraph`) and (b) paragraphs whose next body sibling is `w:tbl`. Paragraphs *below* a table are only excluded if they happen to match the caption regex. The plan wording is "inside ±table-range" and its fixture asks for "table 3×3 + heading paragraph above (Normal), **subheading below**"; Humaid's test (`tests/test_body_indent_tables.py:52`) asserts body-below-table **is** indented.

**Amendment — pick one, then lock it in a test:**
- **Recommended (current behaviour):** below-table Normal paragraphs are ordinary body prose and should indent. Keep the code; add `test_subheading_below_table_is_indented` and a 3×3-table fixture matching the plan's shape, with a comment citing this interpretation so the ±range wording is explicitly resolved.
- **Strict ±range:** also skip a Normal-styled paragraph whose previous body sibling is `w:tbl`. Risk: genuine body prose directly after a table would silently lose its indent — only take this if the team confirms the intent.

### C2 (should) — spacing-uniformity assertion inside tables

Plan criterion: "Assert spacing uniformity inside tables remains untouched (spacing pass should skip table paragraphs entirely)." Cell paragraphs are skipped by construction (`_load_body_paras_raw:5543` returns direct `w:p` children only; `_collect_body_formatting_issues` iterates the same list) — but no test asserts it. **Amendment:** extend `tests/test_body_indent_tables.py`: surrounding body paragraphs get spacing/line-spacing fixes; assert cell-paragraph `w:spacing` / `w:ind` XML is byte-identical before/after.

### C3 (could) — verify the remaining plan-listed files

`reference_indent.py`, `references_block_corrections.py`, `abstract_keywords_formatting.py` were listed in the plan but untouched. Static reading suggests all three are zone-scoped (references block / front matter) and cannot reach body table-adjacent paragraphs. **Amendment:** state that verification in the PR description (with the zone entry-points cited); no code change expected.

**Already conforming:** sibling `w:p`/`w:tbl` neighbour scan with no new dependency; reuse of `looks_like_caption_paragraph` from `document_zones`; indent flag flipped without discarding alignment/spacing fixes; caption/heading-above-table/body/cell assertions.

---

## D. Lint debt (trivial, same PR as whichever ticket is amended first)

- `tests/test_front_page_style_fixes.py:5` — remove unused `WD_SECTION` import
- `tests/test_front_page_style_fixes.py:18` — remove unused `AUTHORS_REQUIRED_STYLE_ID` import
- `tests/test_output_filename.py` — restore trailing newline at EOF
- `app/services/output_generation_samfix.py` sits at 5 pre-existing ruff errors (same count as the pre-review base — none introduced by these commits; leave or fix opportunistically, do not block)

---

## E. Out of Joey scope — flag separately, do not fold into these tickets

`tests/test_docx_ooxml_validity.py` fails collection on this branch: it imports `_reconcile_comment_sidecars` from `app.pipelines.feedback_gen_pipeline`, which does not exist at `51158df` or HEAD. The test file arrived via the `e094dba` lineage; the function was dropped in a later merge. This predates all four reviewed commits. It blocks a bare `pytest` run (worked around during review with `--ignore=`). **Options for the owner:** restore the function from its last known commit, or quarantine the module with an `pytest.importorskip`/`skip` marker and open a tracking ticket. Needs a team decision; do not entangle with JB-02/04/08.

---

## F. Definition of done for the amendment PRs

1. A1–A3 applied; inert-plan acceptance test added; existing rewritten tests stay green.
2. B1 applied; full-order professional-mode test added; Joey-confirmation question in PR description.
3. C1 decision recorded + test added; C2 assertion added; C3 verification note in PR description.
4. `python -m pytest --ignore=tests/test_docx_ooxml_validity.py` fully green; `ruff check` clean on every touched file.
5. Trace evidence attached: JB-02 `llm_calls/25` sanity (A4); JB-04 blank header + top-right PAGE in the output snapshot (run with the fix).
6. One commit per ticket amendment (`fix: JB-02 … (review amendments)`, etc.), matching the repo's per-ticket commit style.
