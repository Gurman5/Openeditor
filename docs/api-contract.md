# OpenEditor — API Contract (G-01)

> Source of truth for how the frontend (writer.html) talks to the Flask backend.
> Covers the 4 canonical screens: Upload → Processing → Results → Download.
> Endpoints and line refs below match the current `app/main.py`.

---

## Screen 1 — Upload

### `POST /api/upload`

**Request:** `multipart/form-data`, field name `file`, a `.docx` file.

**Success (200):**
```json
{ "session_id": "d83eff1c-1e94-4638-9c4c-801fa3875112" }
```
Processing starts immediately in a background thread — frontend should move to the
Processing screen and begin polling `GET /api/results/<session_id>` right away.

**Failure (400):**
```json
{ "error": "No file uploaded" }
```
```json
{ "error": "Only .docx files are accepted" }
```
```json
{
  "error": "Document is too long (18,342 words). The maximum is 10,000 words. Please shorten the manuscript and try again.",
  "word_count": 18342,
  "max_word_count": 10000
}
```

**Failure (413 — file too large):**
```json
{ "error": "File too large", "detail": "Maximum upload size is 16 MB." }
```
> ⚠️ Backend defaults are **16 MB / 10,000 words**. PRD/Zac's design specifies **20 MB / ~15,000 words**.
> This is a live mismatch — resolving it is G-02's job (env vars `MAX_UPLOAD_MB` and `MAX_WORD_COUNT`
> need to be updated to match, or the frontend copy needs to change — team decision needed).

**Client-side vs. server-side validation:**
- File type, empty file, obviously-wrong extension → **client-side**, before any request is sent (per Z-02: "user knows exactly why a file is rejected before anything is submitted to the backend").
- File size, word count, fake `.docx` (wrong content), corrupted file, password-protected file → **server-side**, since these require actually reading the file. These come back as 400/413 above.
- Network failure mid-upload → **client-side** (fetch/XHR error handling, no server response).

---

## Screen 2 — Processing

### `GET /api/results/<session_id>` (polled repeatedly while processing)

**While running (202):**
```json
{ "status": "processing", "progress": 45, "stage": "structure" }
```

**Stage → step-label mapping** (per `STAGE_TO_STEP` in `app/static/script.js`):
| `stage` value | UI step |
|---|---|
| `starting`, `structure`, `analysis` | 0 |
| `refs`, `references` | 1 |
| `llm`, `editorial` | 2 |
| `building`, `finalizing`, `done` | 3 |

**Done (200):** see Results screen below — same endpoint, different payload once `status` isn't `processing`.

**Cancelled (409):**
```json
{ "status": "cancelled", "error": "Processing cancelled" }
```

**Timeout (504):**
```json
{ "status": "timeout", "error": "Analysis exceeded the 10-minute time limit and was stopped. The document may be very large or complex — try shortening it and submitting again." }
```
> Server timeout is `ANALYSIS_TIMEOUT_SECONDS` (default 600s = 10 min) — matches PRD's ~10 min ceiling from Z-03. No change needed here, unlike the upload limits above.

**Pipeline error (500):**
```json
{ "error": "Pipeline failed" }
```

### `POST /api/cancel/<session_id>`

**Request:** no body needed, just the session ID in the URL.

**Success (200):**
```json
{ "status": "cancelled" }
```
Sets `cancel_requested: true` server-side — the pipeline checks this cooperatively at its next
progress checkpoint and stops. **Not instant** — there may be a brief delay between clicking
Cancel and the backend actually halting, depending on which pipeline stage it's in.

**Not found (404):**
```json
{ "error": "Session not found" }
```

**Guarantee after cancel:** no file is retained — the session is marked cancelled, and the temp
directory holding the uploaded file is not referenced again. Frontend should treat cancel as
"return to a fresh Upload screen, nothing retained" per Z-03.

### `GET /api/jutlp-articles` (carousel)

**Request:** optional query param `limit` (default 10, max 12, min 1 — note: main.py's docstring
says default 30, but the service function itself defaults to 10 — worth reconciling).

**Success (200):**
```json
{
  "articles": [
    {
      "title": "The Artificial Intelligence Assessment Scale (AIAS): A Framework for Ethical Integration of Generative AI in Educational Assessment",
      "author": "Mike Perkins, Leon Furze, Jasper Roe, Jason MacVaugh",
      "abstract": "This JUTLP article introduces the AI Assessment Scale as a practical framework for deciding when and how generative AI can be used in educational assessment...",
      "url": "https://open-publishing.org/journals/index.php/jutlp/article/view/810/769"
    }
  ]
}
```

**⚠️ Important — this is a live scraper, not static data.** `get_jutlp_articles()` fetches and
parses real pages from `open-publishing.org` (the JUTLP journal site) on a cache miss, caching
results for 6 hours. If the scrape fails entirely (site down, structure changed, network issue),
it falls back to one hardcoded article (the AIAS one shown above) so the endpoint never errors
out — it always returns at least one article. Worth flagging to the team: this is an external
dependency outside our control, and if `open-publishing.org` changes its page structure, the
scraper could silently degrade to always showing the fallback article without any error surfacing.

Implement carousel as a **toggle flag** (`CAROUSEL_ENABLED`), default ON, with the existing
fallback article as the safety net — per G-03 spec. Pending Joey sign-off (Z-03 note).

---

## Screen 3 — Results

### `GET /api/results/<session_id>` (same endpoint as polling, once done)

**Success (200):**
```json
{
  "total_notes": 12,
  "high_priority": 3,
  "categories": { "Structure": 2, "Front Page": 4, "Style": 5, "References": 1, "Editorial": 0 },
  "issues": [
    { "rule_id": "SEC004", "message": "Missing Methods subsection", "status": "fail", "source": "validator" }
  ],
  "ref_verifications": [ "..." ],
  "language_corrections": [ "..." ],
  "summary": "Issues found: Missing Methods subsection; ... (+2 more)",
  "download_url": "/api/download/d83eff1c-1e94-4638-9c4c-801fa3875112",
  "filename": "manuscript.docx",
  "output_filename": "manuscript_reviewed.docx",
  "llm_available": true,
  "llm_error": null,
  "stage_errors": []
}
```

**Zero-issue run:** `total_notes: 0`, `issues: []` — frontend must still render a success state
("processed successfully, no major issues found" per Z-04), not treat this as an error.

**Paywall fields:** none of the current payload has `free`/`locked` split fields — the
`freeItems`/`lockedItems` split in the old `writer.html` was hardcoded client-side mock data, not
something the backend ever returned. **G-04 to confirm:** frontend should map `issues` by
`status` (`fail` = needs action, `warn` = flagged) rather than expecting a free/locked field —
this naturally fits Z-04's "auto-fixed vs. needs-action" framing without backend changes.

**Clean vs. tracked-changes toggle:** not currently supported — `download_url` returns one file
(the tracked-changes version). A separate "clean" version would require a new endpoint or query
param — **not built this sprint**. G-04 should document this as: tracked-only for now, clean-vs-tracked
toggle deferred.

---

## Screen 4 — Download

### `GET /api/download/<session_id>`

**Success (200):** binary file stream, `Content-Disposition` set for download, filename from
`output_filename`.

**Not found (404):**
```json
{ "error": "Session not found" }
```

**Retry semantics (G-05 — see separate decision doc):** the endpoint is currently **idempotent**
— nothing in the code marks a session as "consumed" after download, so re-calling this endpoint
again with the same `session_id` will succeed again as long as the session/temp file still exist.
**Recommended contract (per G-05):** treat first *successful, byte-complete* transfer as consumed
client-side (`hasDownloaded = true`), keep the file server-side until session TTL expires (24h per
Joey), so a failed/interrupted download can be retried without re-uploading. No backend change
needed to support this — it's a frontend-side bookkeeping decision layered on an already-idempotent
endpoint.

---

## Open items for follow-up tasks

- **G-02:** resolve the 16MB/10k-word (backend) vs. 20MB/15k-word (PRD) mismatch.
- **G-03:** confirm `jutlp-articles` payload shape; implement `CAROUSEL_ENABLED` toggle.
- **G-04:** confirm `issues[].status` → auto-fixed/needs-action mapping is sufficient; document
  that clean-vs-tracked toggle is deferred.
- **G-05:** written retry rule (drafted above) — needs explicit reply to Humaid to unblock H-05.
- **G-06:** none of the failure payloads above currently include `session_id` or `filename`
  consistently across all error cases — needs a pass to guarantee `{ error_code, session_id,
  filename }` shape everywhere, per G-06.


  ---

## G-02 — Upload validation error codes

| Code | Trigger | Client or Server | HTTP Status | Implemented? |
|---|---|---|---|---|
| `BAD_TYPE` | Wrong file extension | Client (pre-upload) | — | Backend fallback: 400 `"Only .docx files are accepted"` |
| `EMPTY` | No file selected | Client (pre-upload) | — | Backend fallback: 400 `"No file uploaded"` |
| `TOO_LARGE` | File exceeds size limit | Server | 413 | ✅ Implemented |
| `OVER_WORD_LIMIT` | Word count exceeds max | Server | 400 | ✅ Implemented |
| `NETWORK_FAIL` | Connection drops mid-upload | Client only | — | ✅ Frontend concern only |
| `FAKE_DOCX` | `.docx` extension, corrupted internal structure | Server | 400 | ❌ Not implemented — currently would crash ungracefully in the pipeline instead of returning a clean error |
| `CORRUPT` | File can't be opened/parsed | Server | 400 | ❌ Not implemented — same gap |
| `PASSWORD_LOCKED` | Document is password-protected | Server | 400 | ❌ Not implemented — no check exists |

**`.doc` handling:** Already rejected by the existing `.endswith(".docx")` check, just with the generic wrong-type message. Open question: does `.doc` need its own specific copy ("older format not supported, please save as .docx"), or is the generic message fine?

**Word count method:** Backend is authoritative — `_document_word_count()` opens the file and counts every paragraph via `python-docx`. No client-side estimate currently exists. Open question: does the frontend need a rough pre-upload estimate for instant feedback, or is waiting for the server count acceptable?

**Action required:** `FAKE_DOCX`, `CORRUPT`, and `PASSWORD_LOCKED` need real backend implementation (wrapping the document-open call in error handling and mapping specific failure types to these codes) — this isn't just a documentation task, it's a follow-up dev task.



---

## G-03 — Processing poll/state machine + Cancel/timeout + carousel

**Poll loop:** After `POST /api/upload` returns a `session_id`, frontend polls `GET /api/results/<session_id>` on a fixed interval (recommend every 1-2 seconds) until `status` is no longer `"processing"`.

**Stage → step-label mapping** (reusing `STAGE_TO_STEP` from `app/static/script.js`):
| `stage` value | UI step |
|---|---|
| `starting`, `structure`, `analysis` | 0 |
| `refs`, `references` | 1 |
| `llm`, `editorial` | 2 |
| `building`, `finalizing`, `done` | 3 |

**Timeout — which fires first:**
- Server-side: `ANALYSIS_TIMEOUT_SECONDS` (default 600s / 10 min) — the pipeline itself aborts and the session status becomes `"timeout"`, returned as HTTP 504 on the next poll.
- Client-side: PRD specifies a ~10:00 client timeout too. Since the server ceiling is already 10 min, the client timeout should be set to fire *after* the server's (e.g. 10:05) so the server's clean timeout message always wins over a generic client-side "giving up" message. If the client timer fires first, it should still just show the same "took too long" messaging, not a different one.

**Cancel semantics (`POST /api/cancel/<session_id>`):**
- Sets `cancel_requested: true` server-side. The pipeline checks this cooperatively at its next progress checkpoint — **not instant**, there can be a short delay before the backend actually stops, depending on which stage it's in.
- After cancel, polling `GET /api/results/<session_id>` returns 409 `{ "status": "cancelled", "error": "Processing cancelled" }`.
- Guarantee: no file is retained after cancel — frontend should treat this as "return to a fresh Upload screen, nothing kept," matching Z-03's spec.

**Carousel (`GET /api/jutlp-articles`):**
- Returns `{ "articles": [{ title, author, abstract, url }] }`.
- **This is a live scraper**, not static data — it fetches real pages from `open-publishing.org` on cache miss (6-hour cache), falling back to one hardcoded article if scraping fails entirely. It always returns at least one article, but could silently degrade to only the fallback if the source site changes structure.
- Implement as a toggle: `CAROUSEL_ENABLED` env var, default `true`. When `false`, frontend should not call this endpoint or show the carousel at all.
- Pending Joey's sign-off per Z-03/H-03 note — carousel default (on/off) needs explicit client confirmation before shipping.



---

## G-04 — Results payload shape

**Endpoint:** same `GET /api/results/<session_id>` used for polling — once `status` isn't
`"processing"`, this is the final results payload.

**Two Zac states, mapped from the existing payload:**

- **Issues found:** `issues[]` already exists in the payload. Map by `status` field:
  `status: "fail"` → *needs action* (mirrors "flagged for user review, still needs attention").
  `status: "warn"` → *auto-fixed / advisory* (lower severity, informational).
  This achieves the auto-fixed vs. needs-action split from Z-04 **without any backend change** —
  it's a frontend mapping decision on the existing `issues[].status` field.
- **No issues:** `total_notes: 0` and `issues: []`. Frontend must render the success state
  ("Your manuscript was processed successfully. No major formatting issues were found.") rather
  than treating an empty issues array as an error or blank screen.

**`successful_checks[]`:** not currently a field the backend returns. If Z-04's design needs an
explicit "what passed" list (not just "what failed"), this is a **backend gap** — the pipeline
currently only surfaces problems, not passes. Flag to team: either backend adds this, or the
Results screen infers "checks not mentioned = passed" without an explicit list.

**Paywall fields:** confirmed removed. The old `writer.html`'s `freeItems`/`lockedItems` split was
hardcoded client-side mock data — the real backend payload has never had free/locked fields. No
backend change needed to "remove" them; just don't build that split into the new Results screen.

**Clean vs. tracked-changes toggle:** **not feasible this sprint.** `download_url` returns exactly
one file — the tracked-changes version (Sam's `build_edited_document` output). Producing a second
"clean" version would need either a new endpoint or an additional pipeline run generating a second
file, which is backend work not currently planned. **Contract: tracked-only for this sprint.**
Z-04's toggle proposal should be logged as a future enhancement, not built now.

**Header counts:** `total_notes` (int) is already returned — matches Z-04's "N corrections applied"
header requirement directly.


---

## G-06 — Support/error passthrough

**Goal:** every failure path (upload, poll, download) returns enough info for Humaid's future
"Report an issue" links to pre-fill an error code and session context, without the user needing
to describe what happened.

**Current gap:** looking at the actual failure payloads across the three endpoints, they are
**inconsistent** — some include useful context, most don't:

| Endpoint | Failure | Current payload | Has `session_id`? | Has `filename`? |
|---|---|---|---|---|
| `POST /api/upload` | Bad type / empty | `{ "error": "..." }` | ❌ No (session doesn't exist yet at this point) | ❌ No |
| `POST /api/upload` | Over word limit | `{ "error": "...", "word_count": N, "max_word_count": N }` | ❌ No | ❌ No |
| `GET /api/results/<id>` | Error / timeout / cancelled | `{ "error": "..." }` or `{ "status": "...", "error": "..." }` | ✅ Yes (it's in the URL) | ❌ No |
| `GET /api/download/<id>` | Not found | `{ "error": "Session not found" }` | ✅ Yes (URL) | ❌ No |

**Recommended fix:** standardise every failure response to include:
```json
{ "error": "...", "error_code": "TOO_LARGE", "session_id": "...", "filename": "..." }
```
- `error_code` — one of the G-02 codes (or a new one for pipeline/timeout/cancelled failures).
- `session_id` — `null` for upload-stage failures (no session exists yet), populated for poll/download failures.
- `filename` — the original uploaded filename where known, `null` otherwise. **Never the file contents.**

**Passthrough format for "Report an issue" links:** query string on the support page, e.g.:

**Explicitly not sent, ever:** file contents, manuscript text, any extracted document content —
only the filename string and error metadata. Matches the privacy constraint from Z-07 (no
manuscript retention/transmission).

**Status:** requires backend changes to add `error_code`/`filename` to error responses that
don't currently have them — flagging as a small follow-up task, not done in this doc pass.


---

## Update — Sprint 2 (D-12): contract corrections

The sections above described the backend as it existed before this sprint's hardening
work. The following corrections bring the doc back in line with the actual code.

**Upload failure envelope (D-04):** all upload failure responses now include `error`,
`error_code`, `message`, and `detail` consistently. New codes added: `EMPTY_FILE`,
`CORRUPT`, `PASSWORD_LOCKED`, `FAKE_DOCX` (a `.docx`-named file containing non-zip
content), and `UNSUPPORTED_CONTENT` (macros or unexpected embedded objects, Z-04). All
checked server-side on the file's header bytes/zip contents.

**LLM failure isolation (D-05):** `run_editorial_review` and `generate_commented_docx`
are now wrapped in try/except. A missing or invalid `OPENAI_API_KEY` no longer kills the
whole pipeline — deterministic corrections still complete, and `stage_errors` includes an
entry with `severity: "critical"` for the AI review stage.

**Download endpoint (D-06, D-08):** `/api/download/<id>` now returns `409 NOT_READY` if
the session isn't done, `404 FILE_MISSING` if the file no longer exists on disk, and
`410 ALREADY_DOWNLOADED` on a second download attempt. A successful download triggers
immediate temp-directory cleanup via `@after_this_request`.

**Temp file lifecycle (D-06):** every terminal pipeline state now cleans up its temp
directory. A background sweeper thread runs every 5 minutes, deleting any session's
files once `FILE_TTL_SECONDS` (default 24h, env-configurable) has elapsed.

**Session store (D-07) — explicitly deferred.** Given the planned migration from Vercel
to Railway, implementing Redis now was judged not worth the time cost. Interim
mitigation: gunicorn pinned to a single worker, `_sessions` mutations wrapped in a lock,
pruned by the D-06 TTL sweeper.

**Upload limits (D-11):** `writer.html` now receives `max_upload_mb`/`max_word_count`
from the `/` route, sourced from the same env vars the backend enforces.

**Article carousel (D-10):** `GET /api/jutlp-articles` now returns
`{"articles": [...], "degraded": bool}`. Abstracts trimmed to 400 characters. A
fetch-in-progress lock prevents concurrent crawl stampedes. A circuit breaker opens after
3 consecutive failures, pausing attempts for 15 minutes. `limit` default is now `10`
everywhere.

**References payload (Z-06):** `check_references` now returns
`tuple[list[dict], list[dict]]` — existing flat results plus a structured `references[]`
array, built in the same pass (no duplicate CrossRef calls). Each entry has `raw_text`,
`authors`, `year`, `doi`, `source_url`, and `status`
(`verified`/`doi_mismatch`/`not_found`). `title` is currently always `null` — would need
a second CrossRef call per reference; flagged as a known gap.

**Test fixtures:** `01_valid_identified.docx` was found corrupted (missing its
References section) and was regenerated. Note: 2 tests in `test_jutlp_validator.py`
(`TestDeidentifiedWithAuthorLeak`) are still failing due to a separate fixture issue with
`06_deidentified_author_leak.docx` triggering unrelated structural check failures — not
caused by this sprint's D-04 through D-12 changes, flagged as a follow-up.

## Open — not yet closed

- `references[].title` is always null.
- 2 tests in `test_jutlp_validator.py` failing on a fixture generation issue, unrelated
  to this sprint's core changes — needs follow-up.
- D-01/D-02 status needs verification against current `main`.