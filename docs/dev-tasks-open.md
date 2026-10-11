# OpenEditor — Dev Task Backlog (Humaid + Gurman)

> Scope: full-stack backlog to take the app from "prototype that demonstrates the
> screens" to "a user can upload a manuscript and receive a correctly formatted
> document, with no manual intervention."
>
> Every claim below was verified against the tree at commit `33ca8f2` (`dev`).
> Line refs are current and will drift — re-verify before acting on an old branch.
>
> Owner labels below are **suggestions, not assignments** — see §0. In short:
> **Gurman** = data contract, endpoints, pipeline internals.
> **Humaid** = markup, screens, state rendering, copy.
> **Zac** = design (`docs/zac-sprint2-3.md` is his source of truth for UX).
> Open questions for Joey/BA are collected in §9 — several block dev work.
>
> Related: `docs/api-contract.md` (G-01, the live contract — its error tables are stale),
> `docs/zac-sprint2-3.md` (Z-07…Z-11), `docs/gurman-sprint2-tasks.md` (Sprint 2 wiring),
> `docs/session-identity-design.md` (session ID + persistence design — supersedes D-07).

---

## 0. How to use this backlog

**Anyone can pick up any ticket.** The owner names are *suggestions, not assignments* —
they indicate where the work has historically sat and who is likely to have the relevant
context, nothing more. They are not a division of labour, not a claim about capacity, and
not a reason to leave something undone because it isn't "yours". If D-07 appeals to you,
take D-07. If you'd rather do the validator than the feed, do the validator. The only real
constraint is **dependency order**: some tickets are genuinely blocked by others, and
those are listed per ticket and in section 8. Everything else is fair game, in any order,
by anyone.

Two things that follow from this:

- **A ticket with an owner is not a ticket with a gatekeeper.** Handing it to someone else
  needs no permission. Conversely, if you complete one, update the checkboxes or say so —
  the point of the ticket list is that the state of the work is discoverable.
- **The "Deps" line is load-bearing; the "Owner" line is not.** Read deps before you start.

Each ticket is self-contained: it states the problem, the current evidence with line
references, what to do, and how to tell when it's done. **You should be able to pick one up
cold, without briefing from whoever wrote it.** If a ticket isn't self-contained, that's a
bug in the ticket — fix it in place rather than asking.

Two conventions worth knowing:

- **Tickets are numbered `D-01`…`D-16`** (correctness, pipeline, data) and
  **`Z-01`…`Z-07`** (the engineering behind Zac's design tickets). The two numbering
  schemes are unrelated; a Z-ticket often depends on a D-ticket.
- **Anything labelled "open question" is a decision, not a task.** Section 9 lists them
  with a default assumption for each — so you can usually proceed unblocked rather than
  waiting, and the default is stated so it's visible if it's the wrong one.

---

## 1. How the pipeline actually works today

Entry point: `POST /api/upload` (`app/main.py:603`) → background thread → `doc_analysis_pipeline`
(`app/pipelines/feedback_gen_pipeline.py:655`). 37 sequential stages, reporting progress
back to the browser via a `progress_callback` checked at each stage, under a 600 s
wall-clock cap (`main.py:69`).

```
normalise_docx                              :698   text/format normalisation
check_and_report                            :709   ← ALL CrossRef work, one blocking call
deterministic_check_results = {"results":[]} :714   ← VALIDATOR DISABLED (placeholder)
run_editorial_review  (LLM #1)              :718   ← no try/except: kills the run
generate_commented_docx                     :737   writes the output file
add_document_summary_comment                :750
build_edited_document  (Sam, ~30 sub-stages) :780   ← THE TRACKED-CHANGES ENGINE
_remove_duplicate_sam_comments              :781
_max_revision_id → seed the rest             :789
apply_heading_corrections                   :798
apply_au_spelling_corrections               :808
apply_number_word_corrections               :818
apply_abbreviation_corrections              :831
apply_spell_corrections                     :845
apply_acronym_corrections                   :859
apply_decimal_corrections                   :870
apply_sentence_coherence_corrections (LLM#2):883
apply_contingent_grammar_comments           :896
apply_caption_apa7_comments                 :909
apply_table_n_notation_comments             :921
apply_table_section_boundary_comments       :933
apply_table_keep_together                   :948
apply_table_page_breaks                     :960
apply_appendix_removal                      :973
apply_blinded_citation_comments             :986
apply_reference_format_corrections          :1006  consumes CREF `reconstructed`
_inject_crossref_doi_links                  :1018  consumes CREF `doi_url`
_max_revision_id → re-seed                   :1026
apply_reference_indent_corrections          :1031
apply_run_font_corrections                  :1043
apply_reference_order_comments              :1055
apply_short_paragraph_comments              :1066
_insert_suspicious_ref_comments             :1075
_hyperlink_plain_urls_in_refs               :1081
_patch_settings_show_markup                 :1088
_renumber_final_author_queries              :1097
```

**Two things are misleading in the source and will mislead the next reader:**

- `feedback_gen_pipeline.py:705` says *"Phase 1: Run all independent analysis tasks in
  parallel."* Nothing runs in parallel. `ThreadPoolExecutor` is imported at line 7 and
  never used. Every stage is sequential.
- `feedback_gen_pipeline.py:706` says *"JUTLP structural validation removed (H-07)."*
  It was not replaced — see **D-01**.

### Where the time goes

Per-reference CrossRef cost: up to 3 HTTP calls (search + content-negotiation + DOI
lookup) plus one LLM call, with a hard-coded `time.sleep(0.5)` between references
(`reference_checker.py:805`). Separately, `build_body_edit_plan` fires **one LLM
round-trip per body paragraph, serially** (`body_llm_edits.py:505-506`), inside Sam's
builder — which runs *after* most progress checkpoints have passed. That is where the
600 s budget actually goes, and it is why `_analysis_timeout_seconds` is a real risk for
long manuscripts rather than a safety net.

---

## 2. Problem-statement traceability

What the project promised, and what the code does today.

| Problem-statement requirement | State | Evidence |
|---|---|---|
| Accept `.docx` input | ✓ | `main.py:635` |
| Async processing + status polling | ✓ | `main.py:835-840` (202) |
| Return corrected document for download | ⚠ | works, but see D-06/D-07 |
| Line spacing **1.15** (not 2.0) | ⚠ | lands, but via an obscure path — see D-04 |
| APA7 formatting applied **deterministically** | ✗ | **validator is off** — D-01 |
| References validated against CrossRef | ⚠ | works, but LLM overrides verdicts — D-03 |
| Confirm or add DOIs | ✓ | `reference_checker.py:608` content negotiation |
| **No generative AI in citation validation** | ✗ | LLM decides CREF pass/fail — D-03 |
| **No hallucinated citations** | ✗ | LLM free text pasted into author comments — D-03 |
| No manual intervention required | ✗ | mock data, so results are fiction — D-02 |
| Temporary file lifecycle management | ✗ | leaks on 4 of 6 paths — D-06 |
| Privacy: no manuscript retention | ✗ | **UI claims deletion that never happens** — D-06 |
| Z-08a: results screen shows real outcome | ✗ | mock data — D-02 / Z-02 |
| Z-08b: empty document ≠ clean document | ✗ | empty doc returns a pass — D-04 / Z-03 |
| Z-09: two download actions, secondary honest | ✗ | not built — Z-05 (frontend stub only) |
| Z-10: per-reference status + clickable DOI | ✗ | no structured payload — Z-06 |
| Z-11: one requirements statement everywhere | ⚠ | 3 of 6 cases missing server-side; wording inconsistent — D-04 / Z-07 |
| Z-07: help page + deterministic/AI disclosure | ✗ | not started; needs spec first — Z-01 |

Seven of eighteen requirements are not met. The four P0s below are what stand between the
current build and the statement; the Z-tickets in section 6 are what stand between it and
Zac's design.

---

## 3. P0 — the app does not currently do what it claims

### D-01 — Make the validator journal-independent, then switch it on
**Owner: Gurman** · Effort: **L** · Deps: none · Blocks: D-02, D-04

`feedback_gen_pipeline.py:714` hard-codes the deterministic validator's output to empty:

```python
#Placeholder so rest of the pipeline doesn't break.
# TODO: remove once sections D-G replace these downstream references
deterministic_check_results={"results":[]}
```

`check_and_report()` at `:709` covers **references only**. So `jutlp_validator.validate()`
— 24 check functions, ~17 rule families (SEC, MET, DIS, FP, SPE, FIG, TAB, CON, STY,
abstract length, keyword counts, page breaks) — **never runs in the pipeline.**

Knock-on effects, all confirmed:
- `main.py:862` reads `report["results"]` → the entire Structure / Front Page / Style
  section of the Results screen is structurally always zero.
- `main.py:885-903` computes those category counts from the same empty list.
- `fp_overrides` (`main.py:868`) is always empty, so the LLM false-positive downgrade
  never fires.
- `feedback_gen_pipeline.py:728-735` — the `_SAM_COVERED = {"FP"}` filter and
  `filtered_report` are a no-op over an empty list. Dead code.

**Do — in this order, and do not skip step 1:**

1. **Extract.** Move the 24 `check_*` functions out of `app/services/jutlp_validator.py`
   (809 lines) into `app/services/validation/`, separating journal-agnostic checks from
   journal-specific ones. The good news: `CANONICAL_STRUCTURE`
   (`app/domain/canonical_jultp_template.py:56`) is already a data dict, so most of the
   profile is already data, not code.
2. **Parameterise.** Make `validate()` take a journal profile. Move the remaining
   hardcoded style literals into that profile — these are the actual blockers:
   - `"APA 7 Reference List Entry"` — `jutlp_validator.py:653`
   - `"Table Number"` — `:698`, and the `_FIGURE_NUMBER_STYLES` set at `:688`
   - the `Heading 1/2/3` literals at `:361,397,632`
   A second journal should then be a new data file, not a code change.
3. **Switch it on** at `feedback_gen_pipeline.py:714`, calling `validate()` and removing
   the placeholder.
4. **Reconcile double-reporting.** Sam's builder already handles `FP*` items as tracked
   changes (`output_generation_samfix.py:9612`). Decide — per rule family, explicitly —
   whether each is reported as a comment, a tracked change, both, or neither. `_SAM_COVERED`
   was the start of this and was never finished. Write the decision down; do not leave it
   as a set literal in the pipeline.
5. **Move the template dependency.** `output_generation_samfix.py:279` and
   `document_styling_fixes.py:485` hardcode `app/domain/JUTLP Template 2026.docx`. That
   path must come from the profile, or a second journal still breaks.

**Why "independent of JUTLP" is the right framing:** the project will not always be
JUTLP-only — `writer.html:36` already markets the tool against "the journal template",
and the front matter is OAPA-branded generally. Building the validator JUTLP-only and
generalising later means paying for it twice.

**Accept:**
- A manuscript with known structural violations produces non-empty Structure/Front
  Page/Style results in the API payload.
- `validate()` accepts a profile argument; the JUTLP profile is data, not code.
- No journal-specific string literal remains in the generic validation modules.
- Each rule family has a written, single answer to "comment, tracked change, both, or
  neither" — no item appears twice, none silently disappears.

### D-02 — Replace the mock Results data; delete the dead frontend
**Owner: Humaid** (markup) + **Gurman** (adapter) · Effort: M · Deps: D-01

`app/static/openeditor.js:30-40` hardcodes what every user sees on the Results screen:

```js
totalCorrections: 34,
freeItems: [ { label: 'Heading hierarchy', status: '12 FIXED' }, … ],
reviewItems: [ { label: '6 references could not be verified' }, … ],
```

`resultsPayload` is assigned at `:165` and **never read again**. All 13 keys of the
carefully-built API payload reach no user. Meanwhile the frontend that *does* consume 8
of those keys (`app/static/script.js`) is **dead code** — no route renders `index.html`
(`main.py:461` serves `writer.html`; `index.html` has been superseded).

The Results screen therefore violates the problem statement's central claim: users get a
"result" that is fiction, with no relation to their manuscript.

**Do:**
- Build an adapter (Gurman) over the real 200 payload mapping
  `sam` → auto-fixed, `validator`/`refs` failures → needs-review, and derive
  `checks_passed`. Reuse the mapping in `docs/gurman-sprint2-tasks.md` G-04.
- Render from it (Humaid), following Zac's Z-08 states: outcome-first, one plain-language
  sentence per group explaining what was checked, download explanation *before* the
  button.
- **Delete `index.html` and `script.js`.** They are a maintenance hazard: they look
  authoritative, they consume 8 payload keys, and they will mislead the next reader.
  Open question for Humaid/Gurman — confirm nothing else depends on them first.
- Wire `downloadFileLabel` (`writer.html:174` references it; it is **not defined** in
  `openeditor.js`, so the download screen's filename currently renders empty).

**Accept:** two different manuscripts produce two different Results screens. No hardcoded
issue counts remain in the served bundle.

### D-03 — Constrain the LLM in citation validation, and document the residual risk
**Owner: Gurman** · Effort: S–M · Deps: none

The problem statement is explicit: references validated against CrossRef *"without the use
of generative AI in order to eliminate any risk of hallucinated citations."*

Today, `reference_checker.py:773` calls `_llm_check_reference` (defined `:212`, LLM call
at `:232`) whenever CrossRef cannot confirm a reference, and the result **determines the
CREF status**, with its free text pasted verbatim into the author's Word comment:

```python
llm = _llm_check_reference(ref, match)
if llm is not None:
    if llm.get("appears_complete"):
        return _result(rule_id, "warn", f"…reference appears complete — {llm.get('reason','')}…")
    return _result(rule_id, "fail", f"…could not verify — {issues_str}: {ref[:80]}")
```

That is precisely the hallucination surface the statement was written to close. Two
related calls can do the same (`:944` HREF, `:1039` DOIT) — neither is reachable from
the pipeline today, but both are exported and tested, so any future wiring re-exposes them.

**Decision: keep the LLM, but constrain it.** The value is real — it distinguishes
"typo in an otherwise real reference" from "reference does not exist", which CrossRef
alone cannot. The risk is that its prose reaches the author as if it were a finding.

**Do:**
1. **Never let it create a citation.** It may only change a verdict, never add a
   reference, author, year, or DOI. Verify no downstream pass treats its output as
   authoritative data.
2. **Never let it flip `fail` → `pass`.** Unverified is unverified. If CrossRef fails and
   the LLM is confident the reference is real, the result is `warn` with a plain-language
   "we could not confirm this automatically" — not a pass.
3. **Strip its free text from author-facing comments.** The Word comment must say what
   was checked and what to do, not quote a model's reasoning. Keep the model's text in a
   log field for internal debugging only.
4. **Never let it override a CrossRef `fail`.** It only runs when CrossRef is silent.
5. **Document the residual risk** in `docs/api-contract.md`: what the LLM influences, what
   it cannot, and the fact that a `warn` is a model opinion, not a verification. Note that
   `prompt_builder.py:128-130` already forbids the *editorial* LLM from touching reference
   data — that guardrail is prompt-level only and should be stated as such.
6. **Fix the negative caching** while you are in the file: `reference_checker.py:598,622,635`
   cache failures as the sentinel `"__none__"`, so a transient network blip becomes a
   permanent "not in CrossRef" verdict for the life of the cache file. Do not cache on
   network/timeout failure, or distinguish those from a genuine 404.
7. Log every LLM citation verdict with the reference index, so a bad run is auditable.

**Accept:** no author-facing comment contains LLM-generated prose. Every `warn`/`fail` is
traceable to a CrossRef response or to a logged, non-citing model opinion. A network
failure does not produce a permanent negative verdict.

### D-04 — Fix the upload error envelope, and unbreak CI
**Owner: Gurman** · Effort: S · Deps: none · **Fixes a red build on `main`**

One endpoint, three conventions. The upload route returns `error_code` + `message`; the
413/429 handlers and every other route return `error`.

| Branch | Line | Keys |
|---|---|---|
| No file | `main.py:632` | `error_code`, `message`, `session_id` |
| Bad extension | `main.py:636` | `error_code`, `message`, `session_id` |
| Over word limit | `main.py:650` | `error_code`, `message`, `session_id`, `word_count`, `max_word_count` |
| Too large | `main.py:217` | `error`, `detail` |
| Rate limited | `main.py:209` | `error`, `detail` |

The frontend reads only `payload.error` (`api.js:49,61,62`), so **every 400 shows the
literal "Upload failed."** and miscodes as `UPLOAD_FAILED`. The real reason — "Only .docx
files are accepted" — never reaches the screen.

This is why `tests/test_upload_guardrails.py:64` fails with `KeyError: 'error'`. That test
has been failing since the codebase import (`6fc1e50`); CI is red on `main`.

**Do:**
1. Add `error` to the three 400 responses. **Additive** — keep `error_code` and `message`
   so nothing else breaks. This alone unbreaks the test.
2. Add a `detail` field carrying the corrective action, and render it. Z-11's acceptance
   criterion ("every rejection explains the corrective action") needs a field that does
   not exist today.
3. Replace `api.js:58-67`'s string-matching with `error_code` reads. It already has
   branches for `CORRUPT` / `PASSWORD_LOCKED` / `FAKE_DOCX` with a comment admitting the
   backend cannot distinguish them — that is now a backend gap, not a frontend guess.
4. Add the missing server-side variants: `EMPTY_FILE`, `CORRUPT`, `PASSWORD_LOCKED`.
   Corrupt and password-protected are one `BadZipFile` case (an encrypted `.docx` is an
   OLE container, not a zip) but warrant distinct messages, matching the client's two
   existing paths (`openeditor.js:88-93`).
5. Reject an empty document. `_document_word_count` (`main.py:261`) returns `0` for an
   empty file, `0 < _max_word_count`, so **an empty document currently returns a passing
   review** — a false positive on the most trust-sensitive output in the product. Gate it
   at the same place as `OVER_WORD_LIMIT` (`main.py:649`).
6. Move `tempfile.mkdtemp()` (`main.py:638`) to *after* the validation gates. It currently
   runs before the word-count check, so **every rejected oversized upload permanently
   strands a temp directory** containing the manuscript. Cheapest leak in the codebase.
7. Stop returning raw exception text to the client (`main.py:843`) — it can leak absolute
   filesystem paths. Log it, return a message + `error_code`.
8. Update the Swagger docstrings: 409, 413, 429, and 504 are all implemented but undocumented.

**Accept:** `pytest tests/` green on `main`. Every rejection returns
`{error_code, error, detail}` and the UI shows the corrective action. No validation failure
creates a temp directory.

---

## 4. P1 — data integrity and failure isolation

### D-05 — Isolate LLM failure so a bad key cannot destroy all output
**Owner: Gurman** · Effort: S · Deps: none

`feedback_gen_pipeline.py:718` (`run_editorial_review`) has **no try/except**.
`call_llm` (`ai/llm_client.py:83`) raises `LLMError` on a missing or exhausted
`OPENAI_API_KEY` (`:79`), on `APIError` (`:118-119`), and on truncated output (`:125-129`).

One missing or exhausted key means the user gets **no document at all** — despite 30
deterministic correction passes downstream. The same applies to
`generate_commented_docx` (`:737`), which writes the output file; if it throws, every
later stage fails on a missing path.

**Do:** wrap both in try/except, record via `_record_stage_error` (`:684`), continue the
deterministic passes, and set the LLM-derived fields to a null-with-reason. Set a severity
on `stage_errors` so "the tracked-changes engine failed" is distinguishable from "the
carousel could not load" — right now both render as the same soft banner
(`script.js:552-570`), which drastically understates a catastrophic failure.

**Accept:** a run with no LLM access still produces a reviewed document containing every
deterministic correction, and says clearly that the AI review was skipped.

### D-06 — Temp file lifecycle, and make the privacy copy true
**Owner: Gurman** · Effort: M · Deps: D-04 (for the rejection-path leak)
**→ The TTL, sweeper and `410` half of this ticket is now specified in
`docs/session-identity-design.md` (D-17). Read that first; it is the design of record.**

`shutil.rmtree` appears **exactly once** in the entire repo: `main.py:792`, on the cancel
path. There is no TTL, no sweeper, no `atexit`, no `after_request`, no periodic job.

| Outcome | Status | `tmp_dir` deleted? |
|---|---|---|
| Success | `done` | **no — forever** |
| Pipeline error | `error` (500) | **no** |
| Timeout | `timeout` (504) | **no** — worker still writing |
| Cancel | `cancelled` (409) | yes (`main.py:792`) |
| Over word limit | 400 | **no** (`main.py:650`, before the gate) |
| `/api/analyse-cli` | 200 | **no — ever** (`main.py:1050`) |

Meanwhile the shipped UI already promises the opposite:

| Copy | Location | Reality |
|---|---|---|
| "Your original file is deleted once you download the result." | `writer.html:36` | nothing runs on download |
| "Your upload has been deleted." (timeout) | `writer.html:129` | **false** — `main.py:845-849` returns without cleanup |
| "Your processed file will not be saved when you leave this page." | `writer.html:189` | **false** — the file persists on disk |

This is a live compliance problem, not just a UX gap: the promise is already in front of
users and is untrue. It also compounds — at 10 uploads/hour (`main.py:100`) the disk grows
monotonically until `file.save()` (`:640`) or `send_file` (`:1105`) starts failing for
**every** user.

**Do — steps 1–2 are now specified in `docs/session-identity-design.md` (D-17):**

1. ~~Background sweeper deleting un-downloaded files after a TTL read from env.~~
   **Superseded by D-17**, which specifies two separate lifetimes (a short one for
   `processing`, a 24 h default for terminal states), a locked daemon-thread sweeper, an
   opportunistic sweep on the upload path, and a signed cookie binding each session to the
   caller. Follow that document.
2. ~~Consume-flag on download; second attempt → `410 Gone`.~~ **Open question** — D-17
   recommends **TTL-only** (unlimited re-downloads within the window) over a consume-flag,
   because a mis-click should not destroy the only copy of someone's manuscript. This
   departs from `gurman-sprint2-tasks.md` G-05 and needs a decision, not a default.
3. Clean up on every terminal state, including error and timeout. For timeout, signal the
   worker first, then remove. **Still to do** — D-17's sweeper handles expiry by TTL, not by
   immediate cleanup on terminal state; the timeout case in particular needs the worker
   signalled before removal.
4. **Reconcile the copy with the implementation.** D-17 makes the TTL and `410` real, which
   makes `writer.html:36` / `:129` true. Note `writer.html:189` still conflates "not saved as
   history" with "deleted from disk" — those are different promises and only one is now
   guaranteed.
5. Note the cancel-path race: `main.py:782-793` sets `status="cancelled"` *before* `rmtree`,
   and `rmtree` may fail silently on Windows if python-docx holds the file open. A
   concurrent poll can therefore tell the user "Your upload has been deleted" while the
   files are still on disk. **Still to do** — D-17's sweeper eventually reclaims them, but
   nothing makes the claim true *at that moment*.

**Accept:** no file survives past its TTL regardless of outcome. `410` once expired. No
privacy claim in the UI that the code does not implement.

### D-07 — Session store: survive restart and scale-out
**Owner: Gurman** · Effort: M · Deps: D-17 · **Deferred — do not build until the trigger fires**

**→ Superseded in part by `docs/session-identity-design.md`.** D-17 fixes three of the five
failures below (unbounded growth, missing ownership, unsynchronised mutation) with no
database. **This ticket is now only the remaining two**, both of which genuinely need a
shared store, and it is **deferred**.

The full schema, the data-hygiene rules that shrink the payload, the database trade-offs, and
the exact trigger for building this are all in `docs/session-identity-design.md` §5 (D-18).
Read that before starting.

**Trigger:** the first time you need `gunicorn --workers N`, deploy to Vercel, or care that
a restart doesn't lose an in-flight client's work. All three are one decision, not three.

The two outstanding failures:

- **Total breakage under `--workers N` or Vercel.** The Procfile pins `--workers 1`, so it
  survives today. Vercel (`vercel.json`) builds `app/main.py` as a serverless function,
  which is horizontally scaled by definition: an upload handled by one instance is
  invisible to the next, and the poll returns 404 forever. **The Vercel deploy is broken
  for this reason, independent of anything else in this doc** — and D-17 does *not* fix it,
  because session *state* is still per-process.
- **Restart loses everything**, orphaning any in-flight manuscript on disk.

**Do:** move session state to the shared store described in D-18. Note that a store
introduces a *new* problem a dict does not have — two workers can now both pick up the same
session, trading a loud 404 for a silent race. It needs a claim/lock with a lease that
expires if a worker dies. **That concurrency work is the real cost of this ticket, not the
schema.**

**Accept:** two workers behind a load balancer can serve one user's poll and download. A
restart mid-run does not lose the client's session.

### D-08 — Unhandled exceptions returning 500 instead of the right status
**Owner: Gurman** · Effort: S · Deps: none

- `download()` (`:1106`) reads `session["output_path"]`, which is only set at `:768` after
  success. Downloading mid-processing raises `KeyError` → unhandled 500, not 409/404.
- `results()` (`:835`) reads `session["status"]`; `/api/analyse-cli` sessions (`:1062-1067`)
  store no `status` → `KeyError` → 500.

Small, but these are reachable by ordinary user action and produce the worst possible
error surface (a stack trace page rather than a message).

### D-09 — Empty `stage_errors` payload fields that make two UI branches unreachable
**Owner: Gurman** · Effort: S · Deps: none

- `main.py:857` reads `llm_error`; **nothing ever writes it**. Always `None`, so the
  "AI review unavailable" branch at `script.js:678` is dead.
- `main.py:765` reads `pipeline_result.get("grammar_corrections")`; the pipeline never
  returns that key (the equivalent is `contingent_grammar_actions`,
  `feedback_gen_pipeline.py:1115`). Always `[]`, so grammar never appears in the
  Language panel.
- `main.py:1004` returns `summary`; **no frontend reads it**. Dead payload.

Either populate these or delete them. Do not leave fields that look meaningful and are
always empty — the next person will trust them.

---

## 5. P1 — feed, limits, contract

### D-10 — Make the article feed honest about failure
**Owner: Gurman** (backend) + **Humaid** (degraded state) · Effort: M

**It is not broken — it is expensive and dishonest.** Measured live:

```
sitemap           HTTP 200, 196,497 bytes
1st call          9.76 s   (cold)
2nd call          0.001 s (in-process cache)
articles          10, all with title + url
abstract lengths  919 – 1,863 chars
```

It is not an RSS feed. There is no feed parser; it is a **scraper**: fetch the sitemap,
regex out article URLs, then fetch **up to 72 pages** (`jutlp_articles.py:99`) to keep at
most 18 (`:64`). With `timeout=8` on the sitemap and 6 s per article, a degraded upstream
means ~440 s worst case, holding a request thread — and the Procfile runs `--threads 8`.

Specific problems:
1. **Silent degradation.** `_normalise_article` (`:173`) drops any article missing a title
   or abstract. If `open-publishing.org` changes its markup, every article fails, and
   every user sees the single hardcoded 2019 fallback article (`:28-42`) with **no error
   surfaced anywhere**. Indistinguishable from success.
2. **Stale-forever cache.** 6 h TTL (`:47`), but on fetch failure the stale cache is
   returned regardless of age (`:74-75`) and `_CACHE_UNTIL` is not refreshed.
3. **Cache stampede.** The lock guards the read/write, not the fetch (`:56` releases
   before `:63`), so N concurrent cold requests all trigger a full crawl.
4. **Per-process cache** — same multi-worker problem as D-07.
5. **No circuit breaker.** Every miss re-crawls immediately.
6. **Three different `limit` defaults:** 30 in `main.py:482`, 10 in the service signature
   (`jutlp_articles.py:50`), hard-capped to 12 at `:54`. The documented 30 silently yields
   at most 12, and the client actually requests 10 (`api.js:165`).
7. **Abstracts are 900–1,900 chars** — they render in full in the carousel. `_trim_text`
   (`:351`) is defined and never called.
8. `CAROUSEL_ENABLED` (`api.js:13`) is a hardcoded JS constant, not the env var
   `api-contract.md:293` describes. It cannot be disabled without a rebuild.
9. `openeditor.js:17-22` initialises `jutlpArticles` to a one-element hardcoded array and
   only overwrites `if (articles.length)`, so a total failure shows a placeholder
   indistinguishable from real content.

**Do:** trim abstracts to a sane length and use `_trim_text`; cap the crawl (fetch
sitemap, sample N candidates, stop early) so cold latency is bounded; add a circuit
breaker; surface a degraded state to the UI rather than silently showing the fallback;
reconcile the three `limit` values to one; make the flag an env var. **Decide whether the
carousel is worth its dependency on a third-party site's markup at all** — it is
decorative, and it is the only part of the app that breaks when someone else's HTML
changes.

**Accept:** a broken upstream degrades visibly and quickly, never silently to one article.
Cold call is bounded. The three limit values agree.

### D-11 — Resolve the upload limits mismatch
**Owner: Gurman** (backend) + **Humaid** (copy) · Effort: S · Deps: BA decision

| Limit | Backend | UI | Client check |
|---|---|---|---|
| Max size | 16 MB (`main.py:59`) | "20 MB MAXIMUM" (`writer.html:62`) | 20 MB (`openeditor.js:83`) |
| Max words | 10,000 (`main.py:64`) | "15,000 words MAXIMUM" | — |

Both mismatches are **over-promises**: the UI invites a 20 MB file the server then
rejects with a 413. `api-contract.md:41` already flags this and assigns it to G-02.

**Do:** render both limits from backend config into the template, so the copy cannot
drift when the env vars change. `writer.html` is already Jinja — pass `max_upload_mb` and
`max_word_count` from the `/` route. Then the *values* decision is a one-line env change
rather than a code edit. Whichever way the BA decision lands, it should not need a UI
change. Note `.doc` is advertised nowhere in the live UI (correct — the backend rejects
it at `main.py:635`), but `index.html:39,45` still advertises it in the dead file.

**Accept:** no limit is stated anywhere in the UI that the server does not enforce —
enforced by a test, not a convention.

### D-12 — Close the contract gaps in `api-contract.md`
**Owner: Gurman** · Effort: S · Deps: D-04, D-07, D-10

The doc is the source of truth both devs build against, and it has drifted:
- Failure tables (`:24-39`) show `error`; the upload route returns `error_code`/`message`.
- `:176` says "the endpoint is currently idempotent… re-calling will succeed again" —
  correct, and now to be fixed by D-06; update it when you do.
- `:293` describes `CAROUSEL_ENABLED` as an env var; it is a JS constant.
- `:466` (Swagger `limit` default) says 30; the service caps at 12.
- `download` and `results` return 409/504/413/429 in code but document only some of them.
- `:130-134` correctly warns the JUTLP scraper can degrade silently — D-10 makes it real.

---

## 6. Z-ticket engineering work (Zac's designs → built product)

Zac's designs live in `docs/zac-sprint2-3.md` (his source of truth) and a **separate Figma
board** he is redrawing against these tickets. Those tickets are **design deliverables**.
This section is the engineering each one implies, split by owner.

**Read this before estimating anything here.** Each Z-ticket is a *coordination* task
first and a build task second: Zac's board is in flux, so the pattern is — agree the
behaviour and states with him, let him redraw, then build against the revised design. Do
not build against the current board, and do not treat the frames that exist there as
authoritative; they predate the redraw. **Where a ticket's substance is data or backend
behaviour rather than markup, the engineering can start now and does not need to wait for
the design** — those are called out per ticket.

**Zac's own words where they diverge from the code — read these before building:**

- **Z-09 reverses the position I took earlier.** I argued against shipping the clean-copy
  button at all. Zac explicitly wants it, visible, as a "Coming soon" secondary, on the
  reasoning that a greyed-out button reads as broken while an inline click-through message
  doesn't. **He is right on the design point**, and it ships as a frontend stub with no
  backend change. His instruction "don't call it 'clean copy'" also stands — accepting all
  changes silently destroys the author's ability to reject individual ones.
- **Z-08b adds a case I had not covered:** a file mislabelled as `.docx`, and a document
  containing code that can't be executed. Both route to the same screen. See **Z-04**.
- **Z-07 is a brainstorm, not a spec** — it reads "make a screen for /about which would
  include infinite scrolling, make a privacy disclosure, further, make a write up of…".
  It needs a requirements pass before it can be estimated. See **Z-01**.

### Z-01 — Z-07 Support & Help: needs a spec before it can be built
**Owner: Zac (spec) → Gurman + Humaid (build)** · Effort: **S for the spec, then M/L** · Deps: Z-11 wording, D-06 retention

Zac's ticket asks for: an `/about` screen with infinite scrolling, a privacy disclosure, a
write-up of deterministic vs non-deterministic output, a support section, a Google Form
link, and a suggested user poll.

**Do first — a 30-minute requirements conversation with Zac, not code.** The ticket
doesn't say what the page *is*. Specific questions to resolve:
- **Infinite scrolling over what?** A static marketing page doesn't need it. If it's a
  documentation/help index, pagination or search is probably better. Infinite scroll also
  conflicts with Z-07's own goal of "without exposing manuscripts" — a long scrollable page
  is harder to link a user to a specific answer in.
- **`/about` or `/help`?** He names `/about`; the ticket title says Support and Help. The
  error-screen links need one canonical URL.
- **Is the Google Form a real destination?** A linked form is the cheapest option and
  keeps manuscript content off our servers. An in-app form means a new POST endpoint and a
  retention policy for what users submit — including possibly attached files. **Recommend
  the linked form**, and note that a form that accepts file attachments would put user
  manuscripts in a Google account, which contradicts the privacy goal.
- **The poll is out of engineering scope.** It's a research activity, not a build. Route it
  to Zac/BA; don't estimate it here.

**Then, the one piece with real engineering substance:**

**The deterministic / non-deterministic write-up.** Zac is asking for the disclosure that
lets a user know which parts of the document they receive were rule-based and which
involved a language model. This is a genuinely good ask and it maps directly onto the
pipeline map in section 1. We already know the answer:

| Deterministic (rule-based) | Model-in-the-loop |
|---|---|
| `check_and_report` — all CrossRef checks (`:709`) | `run_editorial_review` (`:718`) — editorial notes |
| ~28 tracked-change passes (`:798-1097`) | `apply_sentence_coherence_corrections` (`:883`) |
| `normalise_docx` (`:698`) | `build_body_edit_plan` — **one call per body paragraph** (`body_llm_edits.py:505`) |
| line spacing / font / reference format | `_llm_check_reference` (`reference_checker.py:773`) — see D-03 |

**The disclosure must be honest about one thing:** `body_llm_edits` puts model-generated
replacements into the document as tracked changes. That is not "formatting corrections
applied deterministically against APA7" as the problem statement promises — it is the
largest LLM surface in the product, it touches the author's prose, and it is currently
undisclosed. Flag this to Zac: he may want the model-generated edits labelled differently
in the UI, or the write-up may need to name them explicitly. **This is a product decision
with legal weight, not a copy decision.**

**Accept:** the page states plainly which changes are rule-based and which are
model-generated; no manuscript content is submitted to or stored by us; every error screen
links to a specific anchor on the page.

### Z-02 — Z-08a Results screen: coordinate the revised design, then build it
**Owner: Humaid** · Effort: M · Deps: **D-01, D-02** · **First: agree design with Zac**

Zac's screen stacks the two columns rather than splitting them, and leads with the outcome.
Each group carries a one-sentence plain-language explanation; the download explanation sits
**above** the button. The copy is already written in his sketch (`zac-sprint2-3.md:61-80`),
so treat that as settled and coordinate only what he is redrawing.

**Do:** agree the revised layout and states with Zac, then build against it. The group
structure he has settled on (References and citations / Structure and front page / Spelling
and grammar / Needs your decision) is the shape to carry across. **The hard part is D-02** —
this ticket is markup over an adapter that doesn't exist yet, so the backend work can be
agreed in parallel with Zac's redraw but the build cannot finish without it.

**Note for Zac:** his "manual review header that would be a filter for things which can't
be parsed or would amount to some conundrum" maps to the `Needs your decision` group, which
currently mixes two different things — unverified references (a CrossRef limitation) and
unparseable content (a pipeline limitation). Worth separating in the redraw, since they
need different user action. `stage_errors` and the `sam` source both feed that group.

**Accept:** renders real counts and groups from the payload; the download explanation is
visible before the click; no hardcoded strings from **D-02** remain.

### Z-03 — Z-08b No-issues and unreadable screens
**Owner: Humaid** (markup) + **Gurman** (states) · Effort: S · Deps: **D-04 step 5**

Two distinct outcomes that must not be confused: a genuinely clean document, and a document
we could not read.

**The critical half is backend and does not need Zac's design — start now.** It is **D-04
step 5**: an empty document currently returns a *passing review*. Zac's own copy makes the
point — *"This is not the same as an empty file — we read 6,240 words"* — and that is only
truthful once the empty case is rejected at upload. **Do:** reject empty documents
server-side, and surface the word count that proves the document was read. Zac uses it
deliberately and it's a good honesty device: it is the only thing distinguishing "we checked
and found nothing" from "we found nothing to check."

**Then** coordinate both states with Zac and build against the redraw.

**Open question —** Zac's copy for the unreadable state says *"Your file has been deleted —
nothing was saved."* That's only true if **D-06**'s sweeper ships. If retention is
deferred, this copy must change. Flag it to Zac before he finalises the design.

**Accept:** an empty document cannot produce a passing review; the word count is shown;
both states are reachable and honest.

### Z-04 — Z-08b additions: mislabelled and non-executable files
**Owner: Gurman** · Effort: S–M · Deps: D-04 · **Backend only — no Zac dependency**

Zac extends the unreadable screen to two more cases. **Both are pure backend work and
neither needs his design**, so this can be built immediately. The first is a
**security-adjacent gap**:

1. **A file renamed to `.docx` that isn't one.** `main.py:635` checks
   `file.filename.endswith(".docx")` — the **filename only**. No magic-byte or content
   validation server-side. A `.bat`, `.exe`, or `.doc` renamed `.docx` passes, is written
   to disk (`:640`), and is handed to python-docx. The client does check magic bytes
   (`openeditor.js:98-103`) but that is trivially bypassed and cannot be trusted.
   **Do:** validate server-side on the first 4 bytes — `50 4B` (zip/docx) required;
   `D0 CF 11 E0` → password-protected or legacy `.doc`. This is the `FAKE_DOCX` code
   `api-contract.md` already names and no endpoint returns.
2. **A document containing code that cannot execute.** `.docx` cannot carry macros by
   design, but a macro-enabled file renamed `.docx`, or an embedded object/OLE part, can
   reach the parser. **Do:** reject a zip containing `vbaProject.bin` or an unexpected
   `word/embeddings/` payload, with copy that says the file can't be processed rather than
   implying we refused to run it for safety reasons we can't substantiate.

Both route to the same screen per Zac, with "Upload a different file" as the action.

**Accept:** a renamed non-docx is rejected server-side with `FAKE_DOCX`; a
macro-bearing/embedded payload is rejected with its own code; neither reaches the pipeline.

### Z-05 — Z-09 Download choice: the Coming-soon secondary
**Owner: Humaid** (markup + state) · Effort: S · Deps: Z-02, D-06 · **First: agree states with Zac**

Pure frontend. No backend change, per Zac's own dev note — so **this is the one Z-ticket
that can be picked up at any time** without waiting on the design or on D-01/D-02. The
states are already specified in his ticket, so the coordination here is confirmation
rather than invention.

**Three states, per Zac:**
1. **Default:** secondary button styled as available, with a small "Coming soon" tag
   *inside* the button.
2. **After click:** no download; inline message — *"This option isn't available yet. For now,
   download the reviewed document and use Review › Accept All Changes in Word."*
3. **Live (later):** the real action, once the backend exists.

Keep Zac's two prohibitions: do not grey it out, do not let it outweigh the primary. The
tracked-changes explanation from Z-02 stays visible above both.

**Interaction with D-06 to watch:** D-06 adds a consume-flag so a second download 410s. That
flag is per-session, not per-variant, so the stub must not mark the session consumed — only
the real download should.

**When the backend arrives (not this sprint):** accepting all tracked changes and handling
comments is real work in `output_generation_samfix.py`, and the endpoint currently serves one
path (`main.py:1105-1110`). `api-contract.md:176` already logs it as out of scope. Note the
consent problem Zac's own copy raises: a clean copy silently discards the comments, which
are most of the value — his warning text ("You won't be able to accept or reject them one by
one") is doing necessary work.

**Accept:** the secondary is present, honest, and never fails silently; clicking it always
explains what to do instead.

### Z-06 — Z-10 References & DOI screen: backend fields first
**Owner: Gurman** (payload) + **Humaid** (markup) · Effort: **M backend, M frontend** · Deps: D-03, Z-02

**Blocked on backend work that does not exist yet.** This is the one Z-ticket that is
genuinely a full-stack change, and it is the same finding as D-03's file: `ref_verifications`
is `{rule_id, status, message}` where `message` is prose with the DOI buried inside it. Zac
wants author/year, title, status, DOI and source link per row.

**The backend half does not need Zac's design — start it now.** The payload shape is
determined by the data, not the layout, and the frontend cannot proceed without it, so
starting late blocks both.

**Do — backend, first, or the frontend has nothing to render:**
1. Return a structured `references[]` array: `raw_text`, `authors`, `year`, `title`, `doi`,
   `source_url`, `status`. The data exists at check time — `reference_checker.py:799`
   already loops every reference with its text. It is simply not returned.
2. Add the four statuses. Three map to existing outcomes; **`Not checked` has no
   equivalent** and Zac's own note says hold it until confirmed:
   - Verified — `CREF` pass (`:770`)
   - Not found — CrossRef couldn't verify (`:780-784`)
   - DOI mismatch — `:676-702`
   - Not checked — **must be decided, not invented**
3. **Never regex the prose messages in the frontend.** `script.js:737` does exactly this
   today; do not port that pattern.

**Do — frontend, once the payload exists and Zac's redraw is ready:** single stacked column;
DOI text links to
`https://doi.org/{doi}` in a new tab; mismatched DOIs shown as plain text, never linked;
missing DOI gets *"No DOI found for this reference."* — never an empty field; rows ordered
problems-first (Not found → DOI mismatch → Verified), with Verified collapsed.

**One design note for Zac:** he asks to lead with problems and suggests no red-alarm styling
for "Not found" — a reference can be real and simply not in CrossRef. Agreed, and worth
preserving: this screen's job is to inform, not to accuse. Our `color/error` token is
already used for the "Needs your decision" group in Z-02, so these two screens will read
differently; make sure that's intentional rather than an artefact of token reuse.

**Accept:** every valid DOI is clickable; mismatched DOIs are labelled and unlinked; a
missing DOI shows a message; no prose-parsing in the new code path.

### Z-07 — Z-11 File requirements copy
**Owner: Humaid** (copy + aria labels) + **Gurman** (config) · Effort: S · Deps: **D-04, D-11**

Zac asks for positive and error variants of six cases, worded identically on Upload, Help,
accessibility labels, and support prefill — and explicitly asks us to **flag what is already
done** ("im not sure if this was done before").

**Answering that question — most of it is built, in two places:**

| Case | Status | Where |
|---|---|---|
| unsupported file type | ✓ client, ✓ server | `openeditor.js:80` · `main.py:636` |
| file too large | ✓ client, ✓ server | `openeditor.js:83` · `main.py:59` (413) |
| too many words | ✓ server | `main.py:649` |
| empty file | **✗** | — |
| corrupted / password-protected | ✓ client, **✗ server** | `openeditor.js:88-93` · no server check |
| upload / network failure | ✓ client | `api.js:39-44` (`NETWORK_FAIL`) |

So: **three cases missing server-side** (empty, corrupt, password) — that's D-04 step 4 —
and the wording is inconsistent across all of them. The three existing client messages are
individually well-written but use different registers, and none of them is reachable through
the real error contract (D-04). So the substantive remaining work is **consistency**, not
invention.

**Do:** one requirements statement, generated from backend config (D-11), reused verbatim in
the Help page, the `aria-label`s, and the support-form prefill. Every error variant carries
`error` + `detail` (the corrective action) per D-04.

**Accept:** one source for the limits; identical wording in all four surfaces; every rejection
names the corrective action.

---

## 7. P2 — cleanup and polish

### D-13 — Dead code sweep
**Owner: Gurman** · Effort: S

Confirmed unreferenced from any production path:

| Location | What |
|---|---|
| `body_format_corrections.py` (whole file) | `apply_normal_style_corrections` has zero callers. **Duplicate implementation of the 1.15/276 rule** — see D-14. |
| `reference_checker.py:887-961` | `check_submitted_hyperlinks` — the whole HREF rule family is unreachable |
| `reference_checker.py:964-1053` | `check_text_dois` — the whole DOIT rule family is unreachable |
| `output_generation_samfix.py:3474-3508` | `_check_citation_components_with_llm` — no caller, `except Exception: pass` |
| `grammar_corrections.py:312,520` | `get_grammar_corrections` / `apply_grammar_corrections` — tests only. **Confirm intent before deleting:** the pipeline deliberately uses the deterministic `apply_contingent_grammar_comments` instead. |
| `feedback_gen_pipeline.py:728-735` | `_SAM_COVERED` / `filtered_report` — no-op over an empty list |
| `feedback_gen_pipeline.py:7` | `ThreadPoolExecutor` import, unused |
| `body_format_corrections.py` vs `output_generation_samfix.py:5940` | two implementations of the same normalisation rule |
| `index.html`, `script.js` | dead frontend (see D-02) |
| `main.py:1004` `summary` | computed, returned, never read |

Two of these are *decoys* rather than waste: `body_format_corrections.py` and the HREF/DOIT
families look like live features and will be assumed live by the next reader.

### D-14 — Make the 1.15 line-spacing rule explicit and single-sourced
**Owner: Gurman** · Effort: S–M · Deps: D-01

Sprint 2's headline acceptance criterion is line spacing 1.15, not 2.0. It **is** applied
— but via a path nobody would guess, and with real gaps.

Applied at `output_generation_samfix.py:8142-8147`, writing `w:line="276"` +
`lineRule="auto"`, using constants at `:3753-3755`. It reaches the document through the
`Normal` style copied from `app/domain/JUTLP Template 2026.docx`
(`output_generation_samfix.py:279`) — the template file is the de facto source of truth.

Gaps:
1. `body_format_corrections.py:25-26` sets the same `276`/`auto` and has **no callers** —
   two implementations of one rule.
2. `_body_line_spacing_ok` (`output_generation_samfix.py:3969`) returns `True` when
   `line_spacing is None`, assuming inheritance is correct. A document with a tampered
   `Normal` style therefore **passes silently**. Direct `w:line="480"` (2.0) *is* caught,
   because python-docx reports it as a float and `abs(2.0 - 1.15) > 0.05`.
3. **Reference entries are never checked.** The loop at `:4203-4229` covers only
   `Normal`-styled paragraphs between Introduction and end of body. Reference paragraphs
   use `APA7ReferenceListEntry`, whose template spacing is `<w:spacing w:after="0"/>` with
   no `w:line` at all — so references inherit whatever `Normal` says, unchecked.
4. The validator tells authors *"body text should use the Normal style (11pt Arial,
   left-justified, 1.15 line-spacing)"* (`jutlp_validator.py:640`) while the code sets
   `jc="both"` (justified). User-visible and wrong.

**Do:** pick one implementation, delete the other; make the target value a profile
constant rather than a module-level literal; extend the check to reference paragraphs;
fix the validator message. Add a test asserting a 2.0-spaced body paragraph comes out at
1.15 — that is the Sprint 2 acceptance criterion and it currently has no direct test.

**Accept:** a document at 2.0 line spacing returns a reviewed document at 1.15, verified
by test. One implementation of the rule.

### D-15 — Fix the line-spacing and tracked-change ID collision risk
**Owner: Gurman** · Effort: S · Deps: D-01

Two competing revision-ID allocation schemes coexist. The pipeline seeds carefully
(`feedback_gen_pipeline.py:789`, `1026` — `_max_revision_id(out) + 1`). Sam's builder uses
hardcoded bases at `output_generation_samfix.py:9415` (`1000`), `:8295` (`7300`), `:9605`
(`1200`), `:9632` (`9500`), `:9692` (`9000`). The pipeline's own docstring
(`feedback_gen_pipeline.py:79-81`) acknowledges the collision risk — but only the pipeline
side respects it. A manuscript long enough for two base ranges to overlap produces corrupt
tracked changes.

**Accept:** one ID allocator, tested against a document long enough to collide.

### D-16 — Sampling and determinism of the article feed
**Owner: Gurman** · Effort: S · Deps: D-10

`_sample_articles` (`jutlp_articles.py:79-88`) calls `random.shuffle` on **every** request,
so a healthy cached feed still shows the same article twice in a row occasionally. Rotation
only starts when `length > 1` (`openeditor.js:256`), so the fallback single article never
rotates.

---

## 8. Sprint-cut line

**If you can only do a few things before the next milestone, do these four.** They are the
difference between a demo that shows its own screens and a product that does what the
problem statement says.

| # | Ticket | Why it is on the cut |
|---|---|---|
| 1 | **D-01** (validator on) | The core promise. Without it, Structure/Front Page/Style are always empty and nothing is applied deterministically. |
| 2 | **D-02** (real results) | Users are currently shown fabricated numbers. Nothing else matters until this is true. |
| 3 | **D-04** (error envelope) | Unbreaks a red CI, and every error state depends on it. |
| 4 | **D-05** (LLM isolation) | One expired API key currently means no output for anyone. |

**Then, in order:** **D-17** (TTL + cookie ownership — no infrastructure, and it makes the
false privacy claim at `writer.html:36` true) → D-06 (the terminal-state cleanup that
survives the TTL work) → D-03 → D-11 → D-10 → the P2 sweep.

**D-07 is deferred**, not on the cut. It is the only ticket that needs a database, and
`docs/session-identity-design.md` §5 gives the trigger: the first time you need
`--workers N`, deploy to Vercel, or care that a restart doesn't lose an in-flight client.

**The Z-tickets slot in here like this.** Each is *agree the design with Zac → build it*,
so the ones worth starting early are those whose **backend or data work doesn't depend on
the design at all** — those can proceed while Zac redraws:

| After | Do next | Why |
|---|---|---|
| Nothing — start now | **Z-04** (mislabelled / non-executable files) | Pure backend security-adjacent gap. No Zac dependency. |
| Nothing — start now | **Z-06 backend** (`references[]` payload) | Data shape is determined by the data. The frontend is blocked on it, so starting late blocks both. |
| Nothing — start now | **Z-05** (Z-09 stub) | Pure frontend, no deps, states already in his ticket. Coordination is confirmation, not invention. |
| Nothing — start now | **D-17** (TTL + cookie ownership) | No infrastructure, no migration, no DB. Independent of D-01. Fixes the false privacy claim and the missing ownership check. |
| D-04 | **Z-03 backend** (reject empty doc) | The word count that makes the no-issues screen honest. Copy depends on D-04's error contract. |
| D-01 + D-02 | **Z-02** (Results screen) | Markup over an adapter that doesn't exist yet. Building it before D-02 is building against fiction. |
| D-04 + D-11 | **Z-07** (Z-11 copy) | Consistency work, not invention. Needs the error contract and config-driven limits first. |
| D-06 | **Z-01** (Z-07 help page) | The privacy disclosure cannot be written until retention behaviour is decided. Writing it first means rewriting it. |
**Parallelisable:** D-04, D-05, D-10, **Z-04, Z-05, Z-06-backend** and the P2 sweep can all
proceed while D-01 runs — they touch different files. D-02 depends on D-01 (no point wiring
an adapter to an empty payload). D-06 step 1 is independent of D-04 except for the
rejection-path leak.

**The one sequencing risk:** everything gated on "Zac's redraw" will slip if his board
isn't finalised. Chase the **Z-06 backend** and **Z-04** first specifically because they
can land regardless — that way the Z-tickets still move even if the design lags.

---

## 9. Open questions for Joey / BA

These block dev work. Each has a default assumption so it can proceed unblocked if nobody
has an answer by the time it matters.

| # | Question | Blocks | Default if unanswered |
|---|---|---|---|
| 1 | **Is an empty document an error, or a valid result?** A user may legitimately want a structural check on a stub. | D-04 step 5 | Reject it — a "passing review" on a 0-word file is the worst failure mode we have. |
| 2 | **File retention TTL** — 24 h, or 15 min? Read from env either way. | D-06 | 24 h. |
| 3 | **Upload limits** — keep 16 MB / 10k, or move to the 20 MB / 15k in Zac's spec? | D-11 | Keep backend values; fix the copy. Raising limits changes pipeline cost for every upload, so it should be a deliberate call. |
| 4 | **Is the carousel worth it?** It is decorative and the only feature that breaks when a third party's HTML changes. | D-10 | Keep, but with a visible degraded state. Removing it is a one-line change and removes an external dependency. |
| 5 | **Auth** — the checked-in `.env` sets `SKIP_AUTH=true`; both provider verifiers are stubs that can never succeed (`access_validation.py:81,103`), so **without the bypass every gated path 403s.** `session["authed"]` (`:193`) is never read by `_require_access` — the `/login` flow and the access gate are disconnected. `main.py:163-167` is dead code: denied page loads get JSON, not HTML. | demo readiness | Out of scope for this backlog, but it must be resolved before any external demo. |
| 6 | **Is multi-worker/Vercel in scope?** If yes, D-07 is a hard prerequisite, not a nice-to-have. | D-07 | Assume yes — the Vercel deploy already exists in `vercel.json`. |
| 7 | **Do we disclose that some edits are model-generated?** `build_body_edit_plan` puts LLM-written replacements into the author's prose as tracked changes (`body_llm_edits.py:505`) — one call per body paragraph. The problem statement promises *"formatting corrections applied deterministically against APA7"*, and that is not what this is. Zac's Z-07 asks for a deterministic/AI write-up, which forces the question. **This is a product decision with legal weight**, not a copy decision: the options are to disclose it plainly, label those edits differently in the UI, or stop making them. Recommend asking before any of Z-01 is written, because the disclosure is the hardest part to walk back. | Z-01, Z-07 | Disclose plainly. |
| 8 | **Can the support form accept file attachments?** If yes, user manuscripts end up in a Google account, which cuts against Z-07's "without exposing manuscripts". | Z-01 | Recommend a linked Google Form with **no** attachment field. |
| 9 | **Z-10: does a "Not checked" state exist?** Three of the four statuses map to real outcomes; `Not checked` has no equivalent in the current pipeline. Either introduce a skip path or drop the status. Zac's own note says hold it. | Z-06 | Drop it for now. Three states, all truthful, beats four with one invented. |

---

## 10. Current build state

For anyone picking this up cold — **`main`/`dev` are red.** 38 test failures on `dev` at
`33ca8f2`; 49 pre-existing on `document-processing` (verified in an isolated worktree, so
the merge improved it rather than causing it).

- `tests/test_upload_guardrails.py:64` — `KeyError: 'error'`. **Fixed by D-04 step 1.**
- ~37 further failures across `test_jutlp_validator.py`, `test_output_generation.py`,
  `test_reference_checker.py`, `test_prompt_builder.py`, `test_suspicious_ref_comments.py`,
  `test_front_page_style_fixes.py`, `test_output_filename.py`. Sample error:
  `assert 'add_affiliation…match_comment' == 'none'`, `KeyError: 'MET001'`,
  `SEC002 should pass on valid doc`. **Not yet triaged** — worth a task to determine
  whether these are real regressions from the H-07 validator removal, stale expectations
  from before the deterministic passes were added, or fixture problems. Do not assume they
  are all the same thing.
- `ruff` is not installed in the local `.venv`; CI runs it separately.
