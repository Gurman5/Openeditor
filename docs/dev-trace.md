# Developer-Debug Pipeline Trace (D-TR)

A dev-gated observability layer for the document pipeline. When disabled it
costs nothing; no behaviour, output, or test changes.

## Why

"Is there a way to somehow see what's happening with the document while it's
being processed?" — this is that. The trace records, per session:

- **Stage timeline** — every pipeline stage (normalisation → validators → LLM
  review → assembly → each correction pass → reference cluster → finalise):
  which function ran, duration, edit/comment counts, errors with severity.
- **LLM calls** — full system + user prompts (this is the text the model was
  shown), the schema used, retry attempts, token usage, and the complete
  parsed response (notes + structural-validation verdicts) as JSON files.
- **External API calls** — every CrossRef request and DOI content-negotiation
  call with status, latency and cache-hit info.
- **Comment dedupe** — how many pending comments were collapsed in assembly.
- **OOXML / MS Word gate** — schema-shape validation plus (optional) a real
  opening of the document by MS Word via COM automation. Built around the
  recurring "opens wrong in Word" failures.
- **Document snapshots** *(optional)* — copies of the .docx at key moments
  (after normalisation, after assembly, after tracked changes, after the
  reference cluster, final).

## Enabling

Set environment variables before starting the app (or CLI):

| Variable                     | Effect                                           |
|------------------------------|--------------------------------------------------|
| `PIPELINE_TRACE=1`           | Event timeline                                   |
| `PIPELINE_TRACE=2`           | Timeline **plus** document snapshots             |
| `PIPELINE_TRACE_SNAPSHOTS=1` | Forces snapshots (same as `2`)                   |
| `PIPELINE_TRACE_WORD=1`      | Also runs the real MS Word COM gate at the end   |

The CLI `--trace` flag always includes snapshots (explicit developer intent),
regardless of `PIPELINE_TRACE_SNAPSHOTS`.

PowerShell (this must be set in the shell **before** starting the server/CLI,
because the gate is read at start time):

```powershell
$env:PIPELINE_TRACE = '1'
$env:PIPELINE_TRACE_WORD = '1'   # optional, Windows + installed Word
```

Bash:

```bash
export PIPELINE_TRACE=1
export PIPELINE_TRACE_WORD=1
```

## Where the data goes

**CLI runs** — a `trace_cli/` folder next to the input .docx:

```
<dir-of-your-docx>/trace_cli/
├── trace_index.json      # the full event timeline
├── trace_report.html     # rendered viewer (see "Visualize it" below)
├── llm_calls/            # NN_<call>_request.json / NN_<call>_response.json
└── snapshots/            # intermediate .docx copies (when enabled)
```

**HTTP runs** — under the session temp dir:

```
<tmp_dir>/trace_<session_id>/        # same three entries as above
```

Note: the OpenAI response body and full prompts contain manuscript text —
treat the trace dir as sensitive.

## How to run the trace (two options)

### Option A — CLI (fastest, no upload limits)

From the repo root, with the project's virtualenv active:

```powershell
python -m app.pipelines.feedback_gen_pipeline "C:\path\to\manuscript.docx" --trace
```

- `--trace` records the timeline + snapshots + LLM artifacts and prints
  `[dev-trace] wrote <path>\trace_cli` when finished.
- Add `--trace-word` to also open the final document in real MS Word via COM
  (Windows, installed Word, `pip install -r requirements-dev.txt` for pywin32).
- The OpenAI key is read from `.env` automatically (config loads dotenv on
  import), so the LLM stages run for real; no key → the editorial stage fails
  and that error is captured in the trace as an `error` stage event.
- Rough runtime for a ~3k-word paper with live LLM calls: 1–3 minutes.

### Option B — Web app (in-app live trace)

1. Start the server with tracing on (in the shell that runs it):

   ```powershell
   $env:PIPELINE_TRACE = '1'          # add PIPELINE_TRACE_SNAPSHOTS=1 for snapshots
   python -m app.main                 # serves on http://127.0.0.1:5009
   ```

2. Upload the file (any HTTP client; `-F` field name is `file`):

   ```powershell
   $r = Invoke-RestMethod -Uri http://127.0.0.1:5009/api/upload -Method Post -Form @{ file = Get-Item 'C:\path\to\manuscript.docx' }
   $sid = $r.session_id
   ```

3. Poll until done (every 1–2 s; `status` flips from `processing` to a
   terminal state):

   ```powershell
   Invoke-RestMethod "http://127.0.0.1:5009/api/results/$sid"
   ```

4. Fetch the trace — works **live while processing** and after `finish`:

   ```powershell
   Invoke-WebRequest "http://127.0.0.1:5009/api/trace/$sid" -OutFile trace_index.json
   ```

   Returns `409` if tracing is off (server started without `PIPELINE_TRACE`),
   `404` for unknown sessions. The HTTP path adds a `run_start` event
   (input filename) as its first event.

   Uploading requires the file to pass the normal guardrails: ≤ 20 MB and
   ≤ 15,000 words (defaults; override with `MAX_UPLOAD_MB` / `MAX_WORD_COUNT`).

## Visualize it (HTML report)

Both options above produce a `trace_index.json`; turn it into a browsable
single-file HTML report with:

```powershell
python tools/render_trace.py <path>\trace_index.json            # writes trace_report.html next to the index
python tools/render_trace.py <path>\trace_index.json --out mine.html
```

The report is fully self-contained (open it in any browser, no server) and
contains:

- a **stage timeline** — one bar per stage, colour-coded ok/error/running,
  bar width log-scaled to duration (hover a bar to see the source function);
- **filter buttons** per event kind (stages, llm_call, api_call, snapshots,
  ooxml/word gates, finish) to dim everything else;
- every **LLM call with its full prompts and response embedded** — expand
  the `prompts / response` disclosure under each call;
- every **CrossRef/API call** (provider, URL, status, latency, cache hit);
- a **snapshots table** linking the intermediate .docx files — keep the
  report next to the trace dir (or use `--out` inside it) so the links work;
- summary counts in the header (event kinds, total errors, trace dir path).

So a complete loop for any .docx is:

```powershell
python -m app.pipelines.feedback_gen_pipeline "C:\path\file.docx" --trace
python tools\render_trace.py "C:\path\trace_cli\trace_index.json"
# then open C:\path\trace_cli\trace_report.html in a browser
```

## What's in a trace_index.json

Flat `events` array, ordered by `seq`, each with `kind`, UTC timestamp `t`
and `t_offset_s` from run start. Kinds: `run_start` (HTTP only),
`stage_start` (updated in place with `status` ok/error, `duration_ms`,
`error`, edit/comment counts), `llm_call` (schema, attempts, token usage,
links to the request/response artifact files), `api_call`, `snapshot`,
`dedup_comments`, `ooxml_check`, `word_gate`, `finish` (elapsed +
`event_counts`). API `status` may be an HTTP code (int) or the string
`"cached"` for cache hits.

## Reading it live

```
GET /api/trace/<session_id>
```

Serves `trace_index.json` (409 if tracing is off; 404 for unknown sessions).
Poll it the same way the frontend polls `/api/results`.

## Word gate alone (no pipeline)

```bash
pip install -r requirements-dev.txt        # pywin32 (Windows only)
python tools/word_check.py out.docx        # + --com-only / --json flags
```

## What "Word unopenable" evidence looks like

`word_gate` event in the trace with `ok:false`, an `error` string, and
`source:"word_com"`. A COM failure is evidence, not a verdict — a stale Word
process or a modal dialog can fail the open even when the file is fine
(`error_kind:"com_error"` + `partial_open` distinguish plumbing from
corruption). `trace_index.json` lists which stage the output last passed
OOXML checks, so the first Word-breaking stage can be localised.

# Known limits

- The ambient recorder is process-wide: two concurrent traced sessions will
  cross-reference LLM/API events (stage events, which go by explicit
  `trace=`, stay correctly attributed). Fine for a developer tool.
- COM gate is Windows + installed-Word + pywin32; other platforms run the
  static layer only.
- The HTML report embeds prompts/responses but links snapshots by file path —
  move the report and the trace dir together if you want the .docx links to
  keep working.
