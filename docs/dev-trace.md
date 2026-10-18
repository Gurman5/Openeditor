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

| Variable                   | Effect                                            |
|----------------------------|---------------------------------------------------|
| `PIPELINE_TRACE=1`         | Event timeline                                    |
| `PIPELINE_TRACE=2`         | Timeline **plus** document snapshots              |
| `PIPELINE_TRACE_SNAPSHOTS=1` | Forces snapshots (same as `2`)                  |
| `PIPELINE_TRACE_WORD=1`    | Also runs the real MS Word COM gate at the end    |

The CLI `--trace` flag always includes snapshots (explicit developer intent),
regardless of `PIPELINE_TRACE_SNAPSHOTS`.

## Where the data goes

Everything is written under the session's temp directory:
`<tmp_dir>/trace_<session_id>/`

```
trace_<session_id>/
├── trace_index.json      # the full event timeline (served by /api/trace)
├── llm_calls/            # NN_<call>_request.json / NN_<call>_response.json
└── snapshots/            # intermediate .docx copies (when enabled)
```

Note: the OpenAI response body and full prompts contain manuscript text —
treat the session tmp dir as sensitive.

## Reading it live

```
GET /api/trace/<session_id>
```

Serves `trace_index.json` (409 if tracing is off; 404 for unknown sessions).
Poll it the same way the frontend polls `/api/results`.

## CLI (no web app needed)

```bash
# poster sample with trace + written trace_index.json
python -m app.pipelines.feedback_gen_pipeline path/to/sample.docx --trace

# also open the final document in real MS Word to verify it loads:
python -m app.pipelines.feedback_gen_pipeline path/to/sample.docx --trace --trace-word
```

The Word gate alone against any docx (outside the pipeline):

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
