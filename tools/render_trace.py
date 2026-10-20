"""Render a dev-trace trace_index.json into a single self-contained HTML report.

Usage:
    python tools/render_trace.py <trace_index.json> [--out report.html]

The report embeds the full event timeline, LLM prompts/responses (read from
the trace dir's llm_calls/ artifacts), API calls, snapshots and gate results,
so it can be opened in a browser without the trace dir being present. Snapshot
.docx files are linked, not embedded.
"""
from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any

KINDS = (
    "run_start",
    "stage_start",
    "llm_call",
    "api_call",
    "snapshot",
    "ooxml_check",
    "word_gate",
    "finish",
)


def esc(value: Any) -> str:
    return html.escape(str(value))


def fmt_dur(ms: Any) -> str:
    if ms is None:
        return "-"
    ms = float(ms)
    if ms < 1:
        return f"{ms:.2f} ms"
    if ms < 1000:
        return f"{ms:.0f} ms"
    if ms < 60000:
        return f"{ms / 1000:.2f} s"
    return f"{ms / 60000:.1f} min"


def _read_artifact(trace_dir: Path, path: str | None) -> str | None:
    if not path:
        return None
    try:
        return (trace_dir / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _llm_details(ev: dict[str, Any], trace_dir: Path) -> str:
    parts = []
    request = _read_artifact(trace_dir, ev.get("request_file"))
    if request is not None:
        try:
            payload = json.loads(request)
            parts.append(
                "<h4>System prompt</h4><pre>"
                + esc(payload.get("system_prompt") or "")
                + "</pre>"
            )
            parts.append(
                "<h4>User prompt</h4><pre>"
                + esc(payload.get("user_prompt") or "")
                + "</pre>"
            )
        except (json.JSONDecodeError, TypeError):
            parts.append("<h4>Request</h4><pre>" + esc(request) + "</pre>")
    response = _read_artifact(trace_dir, ev.get("response_file"))
    if response is not None:
        parts.append("<h4>Response</h4><pre>" + esc(response) + "</pre>")
    if not parts:
        parts.append("<p><em>Artifact files not found in trace dir.</em></p>")
    return "\n".join(parts)


def _snapshot_link(trace_dir: Path, ev: dict[str, Any]) -> str:
    path = ev.get("file") or ""
    if not path:
        return "-"
    try:
        rel = Path(path).relative_to(trace_dir)
        return f'<a href="file://{(trace_dir / rel).as_posix()}">{esc(rel.as_posix())}</a>'
    except ValueError:
        return f'<a href="file://{esc(path)}">{esc(path)}</a>'


def render_event(ev: dict[str, Any], trace_dir: Path) -> str:
    kind = ev.get("kind", "?")
    seq = esc(ev.get("seq", "?"))
    t = esc(ev.get("t", ""))
    offset = esc(ev.get("t_offset_s", ""))

    if kind == "run_start":
        body = f'<span class="ev-name">run start</span>'
        if ev.get("input_file"):
            body += f'<span class="ev-url">input: {esc(ev["input_file"])}</span>'
        return f'<div class="ev run-start" data-kind="run_start">{body}</div>'

    if kind == "stage_start":
        status = ev.get("status", "")
        cls = {"ok": "ok", "error": "err", "running": "run"}.get(status, "")
        body = f'<span class="ev-name">{esc(ev.get("name", ""))}</span>'
        if ev.get("fn"):
            body += f'<span class="ev-fn">{esc(ev["fn"])}</span>'
        body += f'<span class="ev-dur">{fmt_dur(ev.get("duration_ms"))}</span>'
        for key in ("edits_count", "comments_count"):
            if ev.get(key) is not None:
                body += f'<span class="ev-meta">{key}={esc(ev[key])}</span>'
        if status == "error" and ev.get("error"):
            body += f'<pre class="ev-error">{esc(ev["error"])}</pre>'
        return f'<div class="ev stage {cls}" data-kind="stage_start">{body}</div>'

    if kind == "llm_call":
        status = ev.get("status", "")
        cls = {"ok": "ok", "error": "err", "pending": "run"}.get(status, "")
        body = f'<span class="ev-name">{esc(ev.get("call_kind", ""))}</span>'
        if ev.get("schema_name"):
            body += f'<span class="ev-fn">schema: {esc(ev["schema_name"])}</span>'
        body += f'<span class="ev-meta">status: {esc(status)}</span>'
        if ev.get("attempts") is not None:
            body += f'<span class="ev-meta">attempts={esc(ev["attempts"])}</span>'
        if ev.get("token_usage"):
            body += f'<span class="ev-meta">tokens={esc(json.dumps(ev["token_usage"]))}</span>'
        if ev.get("notes_count") is not None:
            body += f'<span class="ev-meta">notes={esc(ev["notes_count"])}</span>'
        if ev.get("model"):
            body += f'<span class="ev-meta">model={esc(ev["model"])}</span>'
        if status == "error" and ev.get("error"):
            body += f'<pre class="ev-error">{esc(ev["error"])}</pre>'
        details = _llm_details(ev, trace_dir)
        return (
            f'<div class="ev llm {cls}" data-kind="llm_call">{body}'
            f"<details><summary>prompts / response</summary>{details}</details></div>"
        )

    if kind == "api_call":
        status = ev.get("status")
        try:
            code = int(status)
        except (TypeError, ValueError):
            code = None
        cls = "ok" if (code == 200 or status == "cached") else (
            "err" if code is not None and code >= 400 else ""
        )
        body = f'<span class="ev-name">{esc(ev.get("provider", ""))} {esc(ev.get("method", "GET"))}</span>'
        body += f'<span class="ev-url">{esc(ev.get("url", ""))}</span>'
        body += f'<span class="ev-meta">status={esc(status)}</span>'
        if ev.get("latency_ms") is not None:
            body += f'<span class="ev-dur">{fmt_dur(ev["latency_ms"])}</span>'
        if ev.get("cache_hit") is not None:
            body += f'<span class="ev-meta">cache_hit={str(ev["cache_hit"]).lower()}</span>'
        return f'<div class="ev api {cls}" data-kind="api_call">{body}</div>'

    if kind == "snapshot":
        body = f'<span class="ev-name">snapshot: {esc(ev.get("label", ""))}</span>'
        body += f'<span class="ev-url">{_snapshot_link(trace_dir, ev)}</span>'
        if ev.get("size_bytes") is not None:
            body += f'<span class="ev-meta">{esc(ev["size_bytes"])} bytes</span>'
        return f'<div class="ev snapshot" data-kind="snapshot">{body}</div>'

    if kind == "ooxml_check":
        ok = ev.get("ok")
        cls = "ok" if ok else "err"
        body = f'<span class="ev-name">ooxml_check after {esc(ev.get("after_stage", ""))}</span>'
        body += f'<span class="ev-meta">ok={str(bool(ok)).lower()}</span>'
        problems = ev.get("problems") or []
        if problems:
            body += '<pre class="ev-error">' + esc("\n".join(str(p) for p in problems[:20])) + "</pre>"
        return f'<div class="ev ooxml {cls}" data-kind="ooxml_check">{body}</div>'

    if kind == "word_gate":
        ok = ev.get("ok")
        cls = "ok" if ok else "err"
        body = f'<span class="ev-name">word_gate ({esc(ev.get("source", ""))}) after {esc(ev.get("after_stage", ""))}</span>'
        body += f'<span class="ev-meta">ok={str(bool(ok)).lower()}</span>'
        if ev.get("duration_ms") is not None:
            body += f'<span class="ev-dur">{fmt_dur(ev["duration_ms"])}</span>'
        if ev.get("error"):
            body += f'<pre class="ev-error">{esc(ev["error"])}</pre>'
        return f'<div class="ev wordgate {cls}" data-kind="word_gate">{body}</div>'

    if kind == "finish":
        counts = esc(json.dumps(ev.get("event_counts", {}), sort_keys=True))
        body = f'<span class="ev-name">finish</span><span class="ev-dur">{fmt_dur(ev.get("elapsed_s") if ev.get("elapsed_s") is None else ev["elapsed_s"] * 1000)}</span>'
        body += f'<span class="ev-meta">events: {counts}</span>'
        if ev.get("summary"):
            body += '<pre>' + esc(json.dumps(ev["summary"], indent=2, default=str)) + "</pre>"
        return f'<div class="ev finish" data-kind="finish">{body}</div>'

    body = esc(json.dumps(ev, indent=2, default=str))
    return f'<div class="ev other" data-kind="{esc(kind)}"><pre>{body}</pre></div>'


def render_stage_timeline(events: list[dict[str, Any]]) -> str:
    stages = [e for e in events if e["kind"] == "stage_start"]
    if not stages:
        return ""
    max_ms = max((float(e.get("duration_ms") or 0) for e in stages), default=1) or 1
    max_log = math.log10(max_ms + 1)
    bars = []
    for e in stages:
        ms = float(e.get("duration_ms") or 0)
        pct = max(2.0, math.log10(ms + 1) / max_log * 100)
        cls = {"ok": "ok", "error": "err", "running": "run"}.get(e.get("status", ""), "")
        label = esc(e.get("name", ""))
        dur = esc(fmt_dur(ms))
        title = esc(e.get("fn") or "")
        bars.append(
            f'<div class="bar-row {cls}" title="{title}">'
            f'<span class="bar-label">{label}</span>'
            f'<span class="bar" style="width:{pct:.1f}%"></span>'
            f'<span class="bar-dur">{dur}</span></div>'
        )
    return (
        '<div class="timeline">'
        + "\n".join(bars)
        + '<div class="timeline-note">bar width is log-scaled to duration; '
        "hover for the source function</div></div>"
    )


CSS = """
body{font-family:system-ui,sans-serif;margin:2rem auto;max-width:1100px;color:#1a1a1a}
h1{margin-bottom:.25rem}h2{border-bottom:2px solid #ddd;padding-bottom:.25rem;margin-top:2.5rem}
.meta{color:#666;margin-bottom:1rem}
.filters{margin:.5rem 0 1rem}
.filters button{margin-right:.5rem;padding:.25rem .75rem;border:1px solid #999;background:#f4f4f4;cursor:pointer;border-radius:4px}
.filters button.active{background:#1a1a1a;color:#fff;border-color:#1a1a1a}
.timeline{margin:.5rem 0 1rem}
.bar-row{display:flex;align-items:center;margin:2px 0}
.bar-label{width:220px;font-size:.85em;text-align:right;padding-right:.5rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar{display:inline-block;height:14px;background:#4a90d9;border-radius:2px}
.bar-row.err .bar{background:#d94a4a}.bar-row.run .bar{background:#e6b93d}
.bar-dur{margin-left:.5rem;font-size:.8em;color:#555;white-space:nowrap}
.timeline-note{font-size:.75em;color:#888}
.ev{padding:.4rem .6rem;margin:2px 0;border-left:4px solid #bbb;background:#fafafa;border-radius:2px}
.ev pre{background:#f0f0f0;padding:.5rem;overflow-x:auto;font-size:.8em;margin:.25rem 0 0}
.ev .ev-name{font-weight:600;margin-right:.75rem}
.ev .ev-fn{color:#555;font-size:.85em;margin-right:.75rem}
.ev .ev-url{color:#555;font-size:.85em;margin-right:.75rem;word-break:break-all}
.ev .ev-meta{color:#777;font-size:.85em;margin-right:.75rem}
.ev .ev-dur{color:#333;font-size:.85em;margin-right:.75rem}
.ev.ok{border-left-color:#3a9d4e}.ev.err{border-left-color:#d94a4a}.ev.run{border-left-color:#e6b93d}
.ev pre.ev-error{background:#fdecec;color:#7a1f1f}
details{margin:.25rem 0}summary{cursor:pointer;color:#4a90d9;font-size:.9em}
details h4{margin:.4rem 0 .2rem;font-size:.85em}
details pre{max-height:300px}
table{border-collapse:collapse;width:100%;font-size:.85em}
td,th{border:1px solid #ddd;padding:.3rem .5rem;text-align:left}
tr.err td{background:#fdecec}
"""

JS = """
const kinds = ["stage_start","llm_call","api_call","snapshot","ooxml_check","word_gate","finish","other"];
const buttons = document.querySelectorAll(".filters button");
function applyFilter(active){
  document.querySelectorAll(".ev").forEach(el=>{
    const k = el.dataset.kind;
    el.style.display = (active==="all" || k===active) ? "" : "none";
  });
  buttons.forEach(b=>b.classList.toggle("active", b.dataset.k===active));
}
buttons.forEach(b=>b.addEventListener("click",()=>applyFilter(b.dataset.k)));
"""


def build_report(index: dict[str, Any], trace_dir: Path) -> str:
    events = index.get("events", [])
    counts: dict[str, int] = {}
    for e in events:
        counts[e.get("kind", "?")] = counts.get(e.get("kind", "?"), 0) + 1
    n_err = sum(1 for e in events if e.get("status") == "error")

    filter_buttons = "".join(
        f'<button data-k="{k}"{" class=\"active\"" if k == "all" else ""}>{esc(k)}</button>'
        for k in ("all",) + KINDS + ("other",)
    )
    timeline = render_stage_timeline(events)
    body = "\n".join(render_event(e, trace_dir) for e in events)
    snap_events = [e for e in events if e["kind"] == "snapshot" and e.get("file")]
    snaps = "".join(
        f"<tr><td>{esc(e.get('label',''))}</td><td>{_snapshot_link(trace_dir, e)}</td>"
        f"<td>{esc(e.get('size_bytes',''))}</td></tr>"
        for e in snap_events
    ) or "<tr><td colspan=3><em>No snapshots in this trace (run with PIPELINE_TRACE=2 or --trace).</em></td></tr>"

    return f"""<!doctype html>
<meta charset="utf-8">
<title>dev-trace: {esc(index.get("session_id","?"))}</title>
<style>{CSS}</style>
<h1>dev-trace: {esc(index.get("session_id","?"))}</h1>
<div class="meta">
finished: {esc(index.get("finished"))} &middot;
include_snapshots: {esc(index.get("include_snapshots"))} &middot;
{esc(len(events))} events ({esc(n_err)} errors) &middot;
{esc(json.dumps(counts, sort_keys=True))}<br>
trace dir: <code>{esc(trace_dir)}</code>
</div>
{timeline}
<h2>Events</h2>
<div class="filters">{filter_buttons}</div>
<div id="events">
{body}
</div>
<h2>Snapshots</h2>
<table><tr><th>label</th><th>file</th><th>bytes</th></tr>{snaps}</table>
<script>{JS}</script>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a dev-trace index into one HTML report.")
    parser.add_argument("trace_index", help="Path to trace_index.json")
    parser.add_argument("--out", default=None, help="Output HTML path (default: trace_report.html next to the index)")
    args = parser.parse_args()

    index_path = Path(args.trace_index)
    payload = json.loads(index_path.read_text(encoding="utf-8", errors="replace"))
    trace_dir = Path(payload.get("trace_dir") or index_path.parent)
    if not trace_dir.is_dir():
        trace_dir = index_path.parent

    out = Path(args.out) if args.out else index_path.parent / "trace_report.html"
    out.write_text(build_report(payload, trace_dir), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
