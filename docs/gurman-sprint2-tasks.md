# Gurman — Sprint 2 Wiring Tasks (Frontend ↔ Backend Reference)

> Scope: Gurman owns the **data contract + wiring layer** between Humaid's screens (H-01–H-06)
> and Zac's designs (Z-01–Z-06). Humaid = markup/screens, Zac = design, Gurman = `fetch/poll/state`
> + `docs/api-contract.md` as source of truth. No markup, no copy writing — shapes, codes, modules.
>
> Standing constraint: **no membership check, no payment gate, no MemberPress integration.**
> Treat every request as an authenticated free pass for the Sprint 2 skeleton. Re-enable the
> shared-password `before_request` gate before client demo. Paid component fully parked.

## Backend truth (verified against `app/main.py`, `app/static/script.js`)

| Capability | Real route | Returns | File ref |
|---|---|---|---|
| Upload | `POST /api/upload` (multipart `.docx`) | `{session_id}`; `400 {error}` on wrong type / over word count | `app/main.py:577` |
| Poll / status | `GET /api/results/<session_id>` | `202 {status,progress,stage}` while running; `200` + report when done; `500` error; `504` timeout; `409` cancelled | `app/main.py:768` |
| Cancel | `POST /api/cancel/<session_id>` | `{status:"cancelled"}` (cooperative) | `app/main.py:750` |
| Download | `GET /api/download/<session_id>` | file stream via `send_file`; `404` if missing | `app/main.py:1043` |
| Carousel | `GET /api/jutlp-articles` | `{articles: [...]}` + hardcoded fallback in `script.js` | `app/main.py:443` |
| Stage map | — | `starting/structure/analysis→0, refs/references→1, llm/editorial→2, building/finalizing/done→3` | `app/static/script.js:60` |
| Timeout | — | `ANALYSIS_TIMEOUT_SECONDS=600` server-side + `worker.join(timeout)` guarantee | `app/main.py:67,700` |

> Do NOT create parallel routes (`POST /upload`, `GET /status/<id>`, `GET /results` without `/api`).
> Reuse the `/api/*` routes above and add thin adapters where the shape differs. `_sessions` is
> in-memory (single gunicorn worker OK; lost on restart) — flagged as a known skeleton limit.

---

## G-01 — Upload endpoint contract + file submission

Effort: M · Deps: H-02 · Priority: P0

Wire the drag-drop upload form to the existing backend.

- Use `POST /api/upload` with the `.doc/.docx` file. Returns `session_id` (not `job_id`).
- Add a structured `error_code` layer on top of the current plain `{error}` responses:
  wrong type, `>20 MB`, empty, corrupted, password-protected. Frontend consumes codes and
  surfaces Humaid's H-02 inline red-text messages (Gurman owns server re-validation, Humaid owns display).
- Apply the BA limits decision (16 MB/10k vs 20 MB/15k) to `MAX_UPLOAD_MB` / `MAX_WORD_COUNT`
  once confirmed; `.doc` default-reject until Dev confirms parser support.
- No payment gate, no member check.

Deliverable: contract section + error-code table in `docs/api-contract.md`.
Accept: valid file → `session_id`; each failure → correct code + inline message; no navigation away.

## G-02 — Processing status polling (reuse results-poll)

Effort: M · Deps: G-01, H-03 · Priority: P0

Give the Processing screen something real to poll against. No new `/status` route.

- Poll `GET /api/results/<session_id>`; map `202 {progress, stage}` → progress bar + step labels
  via existing `STAGE_TO_STEP`; `elapsed` stays client-side (not returned by backend).
- Transitions: `200` → auto-advance to Results; `500 {error}` → error state; `409` → confirmed-cancel
  state; `504` → timeout copy ("Unable to finish processing…").
- Client timeout mirrors server: if elapsed ≥ 600 s and still `processing`, treat as failed.
- HTMX polling interval hits the results endpoint; progress is monotonic 0–99 then 100 on done.

Deliverable: poll/state machine spec in contract + wiring in `app/static/`.
Accept: bar + timer update from real responses; complete/failed/cancelled/timeout each land correctly.

## G-03 — Cancel job (cooperative)

Effort: S · Deps: G-02 · Priority: P0

Backend support for the Cancel button flow. Route already exists.

- Use `POST /api/cancel/<session_id>`; sets `cancel_requested=True`, pipeline raises
  `ProcessingCancelled` at the next progress checkpoint; poll then returns `409 cancelled`.
- Align response to `{status:"cancelled"}` (current shape), not `{cancelled:true}`.
- Add immediate temp-file cleanup on cancel (missing today). Note the caveat: a stall inside a
  long network call (OpenAI/Crossref ~10 s, articles ~8/6 s) only aborts at the next checkpoint
  or `join(timeout)` — annotate as Dev/Sam follow-up; degrade gracefully to timeout copy.
- Frontend (H-03) owns confirm dialog → cancelled state → fresh Upload.

Deliverable: cancel semantics paragraph in contract + cleanup patch.
Accept: Cancel mid-run → `409` → fresh Upload, nothing retained; no frozen screen.

## G-04 — Results payload adapter

Effort: M · Deps: G-02 · Priority: P1

Feed the Results screen with real output data via an adapter, not a new endpoint.

- Source is the `200` results payload: `issues[] {rule_id,message,status,source: validator/refs/llm/sam}`
  + `categories/total_notes/summary/download_url` (`app/main.py:967`).
- Adapter maps: `sam` ≈ `auto_fixed` (track-changes model); `validator/refs fail` ≈ `needs_review`;
  `checks_passed` derived from rule set, or BA decision (B-14) that count-only suffices.
- `no_issues := total_notes == 0` (backend summary already returns "Document passed all checks").
  Both states show successful checks per Z-04.
- Strip all `free/locked` paywall fields from the writer flow. Tracked-changes only this sprint;
  clean-vs-tracked toggle deferred (no before/after fields in payload).

Deliverable: payload schema + mapping table + feasibility line in contract.
Accept: H-04 renders auto-fixed vs needs-action vs success from one payload; zero paywall branching.

## G-05 — Download endpoint + temp file lifecycle

Effort: S · Deps: G-04 · Priority: P1

Make Download functional and enforce the deletion policy. Only real new backend in this set.

- Serve via existing `GET /api/download/<session_id>` (`send_file`, `app/main.py:1043`).
- Add: consume-flag on first byte-complete success (`hasDownloaded=true`); failed/interrupted
  transfer keeps file + `false` so retry works without re-upload (per Michael steer: re-upload
  acceptable, manual refund case-by-case — no credit caching).
- Add: second attempt after consume → `410 Gone` → "file no longer available, re-upload" copy.
- Add: background sweep deleting un-downloaded files after TTL (24 h default; 15 min under
  discussion with Joey — read TTL from env so BA sign-off flips it without code change).
- Session/job ID is the only key; no account linkage.

Deliverable: retry/TTL rule + `410` handling + sweep job.
Accept: first download succeeds; second → `410`; un-downloaded files disappear after TTL.

## G-06 — Error + partial-failure contracts (Z-07 stubbed)

Effort: S · Deps: G-01–G-05 · Priority: P2

Define structured errors so every failure state has an assigned home.

- Standardise the envelope to `{error_code, message, session_id}` across upload (400),
  poll (500/504/409), download (404/410). Map Z-02 copy-deck codes:
  `BAD_TYPE / FAKE_DOCX / TOO_LARGE / OVER_WORD_LIMIT / EMPTY / CORRUPT / PASSWORD_LOCKED / NETWORK_FAIL`.
- Mid-run `status: failed` surfaces the timeout/error copy, never a blank screen.
- Guarantee `{error_code, session_id, filename}` passthrough + `?err=&sid=` format for future
  Report-a-problem links. Leave the Z-07 submission route as a stub until Joey approves.

Deliverable: error envelope + code table in contract.
Accept: every User Flow §8 failure returns a code the frontend can render inline/modal/banner.

---

## Order + handshakes

1. G-01, G-02 first (H-02/H-03 blocked without codes + poll).
2. G-03 (cancel semantics).
3. G-05 reply unblocks H-05 guard logic — explicit Gurman→Humaid reply.
4. G-04, G-06 close with Z-09; finish with the `api.js` fetch/poll/cancel/timeout/carousel-flag
   module + open-questions log (cancel kill-scope, word-count authority, TTL, `stylesAvailable:["APA7"]`).

## Artifacts

| Artifact | Location |
|---|---|
| `docs/api-contract.md` (G-01/02/04/05/06) | Codebase `docs/`, PR-reviewed by Humaid |
| Data layer (`api.js`), backend tweaks | `app/static/`, `app/main.py`, tests |
| Decisions needing sign-off (carousel default ON, retry rule, tracked-only, TTL, limits) | GitHub Wiki API Decisions page |
