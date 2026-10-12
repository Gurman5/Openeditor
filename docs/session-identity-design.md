# Session identity & persistence — design note

> Replaces part of **D-06** and most of **D-07** in `docs/dev-tasks-open.md`.
> Those tickets described the problem; this is the shape of the fix.
>
> **Decision taken:** no database this sprint. Ship TTL eviction + cookie-bound
> session ownership (**D-17**). The database is designed here but **deferred**, with an
> explicit trigger for building it (**D-18**).
>
> Verified against `dev` at `33ca8f2`. Line refs will drift.

---

## 1. The problem, briefly

`_sessions` is a plain in-process dict (`app/main.py:250`), written at `:662` and `:1062`
and **never pruned** — no `pop`, no `del`, no TTL, no cap. It produces five failures:

| # | Failure | Fixable now? |
|---|---|---|
| 1 | Unbounded growth — every entry retains a full report, held for the life of the process | ✓ TTL |
| 2 | Restart orphans in-flight manuscripts on disk, unreachable | ✗ needs a store |
| 3 | Multi-worker: poll hits a different worker → 404 forever | ✗ needs a store |
| 4 | No ownership check — any holder of the ID can download (`main.py:1073`) | ✓ cookie |
| 5 | Unsynchronised mutation — `_sessions[id].update()` from three threads, no lock (`:689-695`) | ✓ lock |

The Procfile pins `gunicorn --workers 1 --threads 8`, so #3 is latent today. It becomes
live the moment anyone scales out or deploys to Vercel — and `vercel.json` already
configures the app as a horizontally-scaled serverless function, so **the Vercel deploy is
already broken for this reason**, independent of anything else in the backlog.

Fixes 1, 4 and 5 need no database. That is the scope of D-17.

---

## 2. What a session actually holds — and why that matters

Sized for a 10k-word manuscript with 50 journal-article references:

| Key | Type | Size | JSON-ready? |
|---|---|---|---|
| `ref_results` | `list[dict]`, 355 rows | **45–54 KB** | yes |
| `sam_result` | nested dict, ~50 keys | **60–150 KB** | yes |
| `llm_result` | **`EditorialReviewResult` dataclass** | 13–40 KB | **no** |
| `spelling_corrections` | per-occurrence, undeduped | 12–30 KB | yes |
| `report` | `{"results":[]}` today; 6–40 KB after D-01 | 0–40 KB | yes |
| `spell_check_corrections` | deduped by distinct word | 1–7 KB | yes |
| `grammar_corrections` | **never populated** (see D-09) | 0 | yes |
| scalars | status/progress/stage/paths | ~490 B | yes |
| **Total** | | **0.1–0.3 MB** | |

**This number drives the whole design.** At the 10 uploads/hour limit (`main.py:100`), a day
of traffic is **24–72 MB** if nothing is deleted. Storing 300 KB per row in a database means
using a database as a temp directory — with the backup, vacuum and replication
consequences of that. The files are *already on disk*; the store should index them, not
absorb them.

Two things worth noting from the sizing:

- **`ref_check` and `ref_results` are the same rows** (`main.py:760-761` stores the report
  dict and its `["results"]` list). Storing both serialises ~45 KB twice. Collapse to one.
- **`sam_result` is ~2× inflated by construction** — the `plan` sub-dict and ~10 top-level
  `*_plan` keys reference the same sub-dicts. Only `plan.*` is ever read
  (`_sam_plan_to_issues`, `main.py:392`). Storing just `plan` roughly halves the largest key.
- **`llm_result` raises on `json.dumps`.** It is a dataclass
  (`app/domain/editorial_feedback.py:22`), not an OpenAI SDK object — `call_llm` already
  discards the SDK response and hand-builds a dict (`ai/llm_client.py:83-145`), so no
  non-serialisable handles leak in. One `dataclasses.asdict()` at the boundary is enough.
  But **that boundary does not exist today**, and building it is the cost of a database.

---

## 3. Session ID format

**Today:** `str(uuid.uuid4())` (`main.py:661`) — a bare UUID in the URL.

Cryptographically fine, operationally poor: 36 chars with hyphens, no environment marker,
and a user transcribing it into a support form will mistype it. Z-07's feedback form needs
exactly that transcription to work.

**Proposed:**

```
ses_p_2k3m9x_7f4q2wz8c5rv6n1t
│    │  │      └─ 15 chars ≈ 75 bits — the ONLY secret segment
│    │  └─ 6 chars, base32, day precision
│    └─ environment: p = prod, d = dev, t = test
└─ self-describing prefix
```

| Property | Why |
|---|---|
| `ses_` prefix | greppable in logs; self-documenting in a support ticket |
| env segment | a dev session pasted into a prod ticket is *visibly* wrong |
| day-precision timestamp | tells you roughly *when* without a store lookup |
| 75 bits of randomness | comparable to a short UUID; ample when the cookie is the real proof |
| base32, no hyphens | excludes `0/O/1/l`, so it survives human transcription |
| **uppercase only** | base32 is case-sensitive; uppercase is forgiving to retype |

### Two caveats, stated so they aren't rediscovered as bugs later

1. **The timestamp is for triage, not secrecy.** Entropy comes solely from the random
   segment. Do not later treat `time` as a security boundary or an authorisation signal.
2. **A forged prefix grants nothing.** Anyone can write `ses_p_` — every request is still
   validated against server state *and* the cookie. The format is ergonomics, not security.

**Do not** introduce a separate "public ID" and "internal key" now. There is no benefit, and
it complicates every log line and support conversation. If a DB arrives, the same string is
the primary key.

---

## 4. D-17 — TTL eviction + cookie ownership (build now)

**Effort: M · Deps: D-04 (for the rejection-path temp-dir leak) · Replaces: most of D-06, fixes D-07 items 1/4/5**

No new infrastructure. No database. This makes the retention promise in `writer.html:36`
true, and closes the ownership hole in `/api/download`.

### 4.1 Ownership — a signed cookie holding owned session IDs

Flask already signs the session cookie with `SECRET_KEY` (`main.py:108`), so this costs
nothing and needs no shared store.

**One precondition:** `SECRET_KEY` must be set in production. It falls back to
`secrets.token_hex(32)` when unset (`main.py:108`), which generates a *new* key on every
restart — invalidating every session cookie, including the ownership list. `.env.example`
leaves it blank. It is a signing key for cookies now that they carry session ownership, so
it stops being optional.

- On successful upload, append the new ID to a list in the Flask session.
- On `/api/results/<id>`, `/api/cancel/<id>`, `/api/download/<id>`, verify membership
  **before** doing anything. Non-member → `404` (not `403` — do not confirm a session exists
  to someone who doesn't own it).
- Cap the list at **20 IDs** (~600 bytes against a 4 KB browser limit), dropping the oldest.
  Those have expired anyway.

**The useful part:** this fixes ownership *across workers* with no shared state, because the
cookie is client-side and self-verifying. Two workers can both validate the same request
correctly. It is the one multi-worker problem a store is not needed for.

**When the access gate is implemented, this becomes account binding for free** — the cookie
is already the identity, so swapping the anonymous cookie for a real account is a change to
what is stored in the row, not a new mechanism.

### 4.2 TTL — two lifetimes, not one

A single TTL is wrong: in-flight work is bounded by the existing 600 s analysis cap, and
protecting it for 24 h would be meaningless.

| Session state | TTL | Source |
|---|---|---|
| `processing` | `ANALYSIS_TIMEOUT_SECONDS + 60` | `main.py:69` |
| `done` / `error` / `timeout` / `cancelled` | `SESSION_TTL_SECONDS`, default 24 h | new env var |

`SESSION_TTL_SECONDS` is read from env so the BA decision (open question 2 in
`dev-tasks-open.md`) is a config change, not a code change. `gurman-sprint2-tasks.md` G-05
already specifies 24 h with a 15 min alternative under discussion with Joey.

### 4.3 Sweeper

A daemon thread on a 60 s interval, mirroring the existing pattern at `main.py:723,771`.
**Guard with a `threading.Lock`** — `--threads 8` means eight request threads hit this dict
concurrently, and D-07 already identified the unguarded read-modify-write at `:689-695`.

On expiry: pop the session, then `rmtree` its `tmp_dir`.

Also add an opportunistic sweep on the upload path, so expired sessions are reclaimed even
if the sweeper thread is starved. Cheap, and it bounds disk growth between ticks.

### 4.4 `410 Gone` on expiry

Once swept, `/api/download` returns `410` with the "file no longer available" copy, per
D-06. This is what makes the retention promise **enforceable** rather than aspirational.

### 4.5 What D-17 does *not* do — say this in the PR

- **Does not fix multi-worker.** Session *state* is still per-process, so a poll hitting a
  different serverless instance still 404s. **The Vercel deploy remains broken.** D-17 fixes
  retention, the privacy claim, and ownership — not scale-out.
- **Does not survive a restart.** An in-flight session is lost; its temp file is orphaned.
  The 4.3 sweep will eventually collect the file, but the client sees a 404.
- **Does not make downloads single-use.** See below.

### 4.6 Open decision: consumed-once vs TTL-only

`gurman-sprint2-tasks.md` G-05 asks for a consume-flag so a second download returns `410`.
**D-17 as designed does not implement that** — it is TTL-only, so unlimited re-downloads
within the window.

I recommend TTL-only: a mis-click or a failed transfer should not destroy the only copy of
someone's manuscript. But it is a real behaviour change from the documented plan, so it
needs a decision rather than a default.

### 4.7 Acceptance

- Every session is reclaimed at its TTL regardless of terminal state; disk usage is flat
  under sustained load.
- A session ID not present in the caller's cookie returns `404` and changes nothing.
- Concurrent access under `--threads 8` shows no lost updates or double-free of `tmp_dir`.
- `writer.html:36` / `:129` / `:189` become true, or are corrected to match.

---

## 5. D-18 — Database (deferred — do not build yet)

**Effort: M · Trigger: the first time you need `--workers N`, deploy to Vercel, or care that
a restart doesn't lose an in-flight client.**

The schema is cheap to write now and expensive to retrofit, so it lives here to be ready.
The split below is the whole design; the trigger is what matters.

### 5.1 The shape

**Metadata in Postgres, payload on disk.** A 300 KB JSONB row is a database being used as a
temp directory. The files are already on disk — the row should index them.

```sql
CREATE TABLE sessions (
  id                TEXT PRIMARY KEY,          -- ses_p_2k3m9x_7f4q...
  status            TEXT NOT NULL,            -- processing|done|error|timeout|cancelled
  progress          SMALLINT NOT NULL DEFAULT 0,
  stage             TEXT,
  filename          TEXT,
  output_filename   TEXT,
  word_count        INT,                      -- already computed at main.py:646, currently discarded
  results           JSONB,                    -- only what /api/results returns, ~5 KB
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at        TIMESTAMPTZ NOT NULL,     -- the sweeper becomes one DELETE
  downloaded_at     TIMESTAMPTZ
);
CREATE INDEX sessions_expires_at_idx ON sessions (expires_at);
```

- Row stays **~5 KB** instead of 300 KB.
- `sam_result` and `llm_result` go to a **JSON sidecar beside the output file** — the
  pattern already used at `document_normalisation_services.py:98`
  (`docx_path.with_suffix(".normalisation.json")`, best-effort, never blocks the pipeline).- The sweeper collapses to `DELETE FROM sessions WHERE expires_at < now()`, and the orphan
  problem becomes a sidecar-file cleanup rather than a `tmp_dir` walk.
- `word_count` is a free win: it is already computed at `main.py:646` and thrown away. The
  Z-03 no-issues screen needs it as proof the document was read.

**Three data-hygiene rules to apply whenever the payload is persisted** — all of them
reduce size and are true today, independent of the DB:

1. Store `ref_results` once, not `ref_check` *and* `ref_results`.
2. Store only `sam_result["plan"]`, not the duplicated top-level `*_plan` keys.
3. Store the grouped spelling summary, not the raw per-occurrence list —
   `summarize_spelling_corrections` is idempotent and `/api/results` re-applies it anyway.

### 5.2 The cost of a store, stated honestly

A database fixes D-07 items 2 and 3. It makes two things **worse**, and both need handling:

- **Concurrency.** Today a shared dict means "404 forever" under multi-worker. With a shared
  store, two workers can both pick up the same session — you trade a loud failure for a
  subtle one. Fixing it properly needs a claim/lock (`SELECT … FOR UPDATE SKIP LOCKED`, or an
  advisory lock on the session ID) and a lease that expires if a worker dies. **This is the
  real work in D-18, not the schema.**
- **A serialisation boundary that does not exist today.** `llm_result` is a dataclass and
  raises on `json.dumps`. Persisting a row means `dataclasses.asdict()` at the boundary,
  plus a decision about what happens when a *new* field is added to a dataclass and an old
  row lacks it.

Both are why the trigger is written as a trigger and not a date.

### 5.3 Choosing the database

Undecided, and recorded as an open question rather than a recommendation:

- **Postgres** (Railway add-on) — the natural fit. The Procfile already pins `--workers 1`,
  so it works on a single instance today and scales when needed. Requires `psycopg` and a
  migration step; CI currently has no service container (`ci.yml`), so migrations need a
  test story.
- **SQLite** — zero infrastructure, file-based, already precedented
  (`acronym_store.py:25` writes `acronyms.json`, env-overridable via `ACRONYM_DB_PATH`,
  which `test_acronym_api.py:21` points at a temp dir — a good pattern to copy). But no
  persistent disk on Vercel, and not safe across multiple workers.
- **Redis** — good TTL story and cheap; `main.py:89` already anticipates it for the rate
  limiter. But it is a *cache*: sessions need explicit write-through, and losing Redis loses
  in-flight jobs.

If the decision stays open, write against **Postgres behind a thin repository interface**
so the choice stays swappable.

### 5.4 Do not copy the existing cache pattern

`reference_checker.py:26` writes `.crossref_cache.json`, rewriting the **entire file on
every single set** (`:41-50`), with no locking and `except Exception: pass`. Fine for a small
memo; wrong for concurrent session writes. Use the sidecar pattern
(`document_normalisation_services.py:98`) instead — write once, best-effort, never blocks.

---

## 6. Relationship to the rest of the backlog

| Ticket | Effect |
|---|---|
| **D-04** | Step 6 (moving `mkdtemp` after validation) still applies — it is a *leak*, not a *lifetime*. D-17's sweeper does not cover directories created by rejected uploads, because no session is ever created for them. |
| **D-06** | Split. The TTL, sweeper and `410` move here. Making the privacy copy true stays in D-06, gated on D-17 shipping. |
| **D-07** | Reduced to items 2 and 3 (restart, multi-worker), both deferred to D-18. Items 1, 4 and 5 are fixed by D-17. |
| **Z-01 / Z-07** | The support form needs a human-typeable session ID (§3) and the word count (§5.1). Both become available without a database. |
| **Z-03** | Its backend half — rejecting empty documents — is D-04 step 5, not this. |
| **Z-06** | Unaffected. Its `references[]` payload is a different problem, in a different file. |

**Sequencing note.** D-17 is independent of D-01 and can run in parallel with it. It is also
the cheapest meaningful win in the backlog after the error contract: no new infrastructure,
no migration, and it makes a false claim in shipped copy become true.

---

## 7. Open questions

1. **Consumed-once or TTL-only?** §4.6. Recommend TTL-only.
2. **Which database, if D-18 triggers?** §5.3. Recommend Postgres behind a repository
   interface; SQLite is a defensible stopgap if Railway is the only target.
3. **Is Vercel still a deployment target?** If yes, D-18 is not optional — the app does not
   work there without it. `deployment.md` lists `openeditor.vercel.app` as the live URL while
   the Procfile is Railway-only, so the two are currently in tension.
4. **What is the `processing` TTL grace period?** 60 s above the 600 s analysis cap is a
   guess. It only needs to cover the cooperative-cancel latency noted in
   `gurman-sprint2-tasks.md` G-03.
