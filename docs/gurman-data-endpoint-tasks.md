# Gurman — Data / Endpoint Tasks (Source of Truth)

> Scope: Gurman owns the **data/endpoint contract** between Humaid's revised frontend
> (H-01–H-07) and the Flask backend. Humaid = screens/markup, Gurman = fetch/poll/state.
> Zac active set: Z-01, 02, 03, 04, 05, 07-proposal, 09. Z-06 + Z-08 archived — no work for them.

## Backend truth (current codebase)

- `POST /api/upload` (multipart `.docx`) → `session_id` + background pipeline thread (`app/main.py:577`)
- `GET /api/results/<session_id>` → `202` + `stage` string while running,
  `200` + report/categories + `download_url: /api/download/<id>` when done (`app/main.py:768,975`)
- `GET /api/download/<session_id>` → file stream (`app/main.py:1043`)
- `POST /api/cancel/<session_id>` → cooperative cancel (`app/main.py:750`)
- `GET /api/jutlp-articles` → carousel feed (`app/main.py:443`)
- Poll stage strings mapped in `app/static/script.js` `STAGE_TO_STEP`:
  `starting/structure/analysis → 0, refs/references → 1, llm/editorial → 2, building/finalizing/done → 3`
- Note: backend defaults (16 MB / 10k words) differ from PRD (20 MB / ~15k) — G-02 resolves.

---

## G-01 — Endpoint inventory + contract doc (P0, unblocks H-01/H-02)

**Do:**
- One-page doc: endpoint, method, request shape, success shape, failure shape for the 4 screens
  (Upload → Processing → Results → Download).
- Mark reused-as-is vs needs-tweak for `writer.html` (limits, paywall-field removal).
- Confirm `download_url: /api/download/<id>` stays the contract Humaid codes against.
- Resolve H-01 from the data side: Checking = client-side pre-`POST /upload` gates +
  early `stage: starting/structure` polls, not a separate endpoint.

**Deliverable:** `docs/api-contract.md` draft + field confirmation.

## G-02 — Upload + validation error-code map (P0, pairs H-02)

**Do:**
- One code per Zac inline state: `BAD_TYPE / FAKE_DOCX / TOO_LARGE / OVER_WORD_LIMIT /
  EMPTY / CORRUPT / PASSWORD_LOCKED / NETWORK_FAIL`.
- State which are client-side (pre-`POST`) vs server-side (`POST /api/upload` 400/413/422).
- Confirm word-count method (client estimate vs backend `python-docx` authority) and max values (20/15k).
- `.doc` default-reject (TBC).

**Deliverable:** code → Zac message → HTTP status table (goes in `docs/api-contract.md`).

## G-03 — Processing poll/state machine + Cancel/timeout + carousel (P0, pairs H-03)

**Do:**
- Own poll loop: `POST /upload → poll GET /results` interval, `stage` → step-label mapping
  (reuse `STAGE_TO_STEP`), elapsed timer, 10:00 client timeout vs `ANALYSIS_TIMEOUT_SECONDS`
  server timeout — state which fires first and what each returns.
- Define `POST /cancel/<id>` semantics: what it kills mid-pipeline, what poll returns after
  cancel, "fresh Upload, nothing retained" guarantee.
- Carousel: `GET /api/jutlp-articles` shape + fallback article + rotate interval.
  Implement as **toggle-able flag** (`CAROUSEL_ENABLED=true/false`), default ON with fallback —
  pending Joey sign-off per H-03 note.

**Deliverable:** poll/cancel/timeout spec + carousel flag (spec in contract doc, impl in `app/static/`).

## G-04 — Results payload shape (P1, pairs H-04)

**Do:**
- 200 payload for two Zac states: `issues_found[]` split `auto_fixed[] vs needs_action[]`,
  `successful_checks[]`, `zero_issue: bool`, header counts ("N corrections applied").
- Strip all `free/locked` paywall fields from writer flow.
- Answer toggle question: dual clean-vs-tracked preview feasible (two URLs/counts?) else
  tracked-only fallback. If infeasible this sprint, contract returns tracked-only.

**Deliverable:** payload schema + preview-feasibility answer.

## G-05 — Download + retry semantics (P1, pairs H-05 — answers Humaid's open question)

**Decision required from Gurman (H-05 is holding on this):**
if download fails mid-transfer, does the file persist for retry, or is one click the single attempt?

**Recommended:** endpoint idempotent until session expiry — first *successful* byte-complete
transfer counts as consumed (`hasDownloaded=true`); failed attempt keeps file + `hasDownloaded=false`.
`Content-Disposition` + retry-safe headers; after TTL (24h per Joey) → `410 Gone` → "re-upload" message.

**Deliverable:** written retry rule; explicit Gurman→Humaid reply (not just a meeting note).

## G-06 — Support/error passthrough (P2, pairs H-07)

**Do (no ticket backend — client discussion pending):**
- Guarantee every failure path returns `{ error_code, session_id, filename }` across
  upload/poll/download so Humaid's "Report an issue" footer/error links can pre-fill.
- Define query/fragment format, e.g. `?err=BAD_TYPE&sid=…`.

**Deliverable:** passthrough fields + format in contract doc.

## G-07 — Handoff: frontend data layer + open-questions log (P2, pairs H-01/Z-09)

**Do:**
- Single `fetch` wrapper + polling/cancel/timeout/carousel-flag module Humaid imports (no markup).
- Log owners: Cancel kill-scope, word-count authority, delete timing (24h rule),
  style signal `stylesAvailable:["APA7"]`, preview feasibility, carousel default.

**Deliverable:** data-layer module + owners log.

---

## Order + handshakes

1. G-01, G-02 first (H-02 blocked without error codes).
2. G-03 (H-03 blocked without poll/cancel/timeout + carousel flag).
3. G-05 answer unlocks H-05 guard logic — explicit Gurman→Humaid reply.
4. G-04, G-06, G-07 close with Z-09.

## Where artifacts live

| Artifact | Location | Why |
|---|---|---|
| `docs/api-contract.md` (G-01/02/04/05) | Codebase `docs/` | Versioned with code; PR-reviewable; Humaid builds against it |
| Data layer (`api.js`), backend tweaks | Codebase (`app/static/`, `app/main.py`, tests) | Runtime code, must ship with app |
| Decisions needing Joey sign-off (carousel default, retry rule, preview, 24h TTL) | GitHub Wiki | Decision log + sign-off comment; code links to it |

## Publication checklist

- [ ] `docs/api-contract.md` drafted + PR reviewed by Humaid
- [ ] Wiki "API Decisions (sign-off)" page: 5 checkboxes + contract link
- [ ] G-05 retry answer posted as Gurman→Humaid reply (unblocks H-05)
