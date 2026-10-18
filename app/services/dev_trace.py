"""Developer-debug pipeline trace (D-TR).

Records a structured, per-session event timeline of the document pipeline:
which stage ran, which function, how long it took, how many edits/comments it
produced, what the LLM was asked and answered, which external APIs were hit,
and whether the generated document passed OOXML / MS Word checks.

Everything here is a no-op unless a recorder is explicitly constructed by the
host (HTTP handler, CLI) with PIPELINE_TRACE=1 in the environment. The pipeline
code is written against a single duck-typed surface:

    trace.stage("stage_id", fn="module.func") -> context manager
    trace.snapshot(docx_path, label)
    trace.llm_request(...) / trace.llm_response(...) / trace.llm_error(...)
    trace.api_call(...)
    trace.ooxml_result(...) / trace.word_gate_result(...)
    trace.finish()

A pipeline running without tracing passes ``trace=None`` straight through, so
this module can never affect production behaviour.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRACE_ENV = "PIPELINE_TRACE"
SNAPSHOT_ENV = "PIPELINE_TRACE_SNAPSHOTS"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def is_enabled() -> bool:
    """True when the PIPELINE_TRACE gate is on."""
    return os.environ.get(TRACE_ENV, "") in ("1", "2")


def snapshots_enabled() -> bool:
    """True when per-stage document snapshots should be dumped to disk.

    PIPELINE_TRACE=1   -> events only
    PIPELINE_TRACE=2   -> events + per-stage document snapshots
    PIPELINE_TRACE_SNAPSHOTS=1 actually beats this rule.
    """
    return os.environ.get(SNAPSHOT_ENV) == "1" or os.environ.get(TRACE_ENV) == "2"


# ---------------------------------------------------------------------------
# current-trace plumbing (so deep services like llm_client can find the
# recorder without threading it through every call signature)
# ---------------------------------------------------------------------------

class _Ambient:
    def __init__(self) -> None:
        self.recorder: TraceRecorder | None = None


_ambient = _Ambient()


def set_ambient(tr: TraceRecorder | None) -> None:
    """Process-wide fallback recorder (CLI mode)."""
    _ambient.recorder = tr


def current_trace() -> TraceRecorder | None:
    """Ambient recorder for the current process, or None when tracing is off."""
    return _ambient.recorder


# ---------------------------------------------------------------------------
# recorder
# ---------------------------------------------------------------------------

class TraceRecorder:
    """Collects ordered trace events for one pipeline run.

    Small events live in ``events`` (the index payload /api/trace serves);
    large artifacts (full LLM prompts/responses, document snapshots) are
    written as files under ``trace_dir`` and referenced by path.
    """

    def __init__(
        self,
        session_id: str,
        root_dir: str | os.PathLike[str],
        include_snapshots: bool | None = None,
    ) -> None:
        self.session_id = session_id
        self.include_snapshots = (
            snapshots_enabled() if include_snapshots is None else include_snapshots
        )
        self.trace_dir = Path(root_dir) / f"trace_{session_id}"
        self.snapshots_dir = self.trace_dir / "snapshots"
        self.llm_dir = self.trace_dir / "llm_calls"
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        if self.include_snapshots:
            self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        self.events: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._t0 = time.perf_counter()
        self._finished = False

    # core

    def add_event(self, kind: str, **fields: Any) -> dict[str, Any]:
        with self._lock:
            seq = len(self.events) + 1
        event: dict[str, Any] = {
            "seq": seq,
            "t": _now_iso(),
            "t_offset_s": round(time.perf_counter() - self._t0, 3),
            "kind": kind,
        }
        event.update(fields)
        with self._lock:
            self.events.append(event)
        return event

    def index_payload(self) -> dict[str, Any]:
        """Deep copy of the event index (for the /api/trace endpoint)."""
        with self._lock:
            events = copy.deepcopy(self.events)
        return {
            "session_id": self.session_id,
            "trace_dir": str(self.trace_dir),
            "include_snapshots": self.include_snapshots,
            "finished": self._finished,
            "events": events,
        }

    def write_index_file(self) -> Path:
        payload = self.index_payload()
        path = self.trace_dir / "trace_index.json"
        try:
            path.write_text(
                json.dumps(payload, indent=2, default=str, ensure_ascii=False),
                encoding="utf-8",
            )
        except (OSError, TypeError):
            pass
        return path

    def finish(self, summary: dict[str, Any] | None = None) -> None:
        if self._finished:
            return
        self._finished = True
        counts: dict[str, int] = {}
        with self._lock:
            snapshot_of = list(self.events)
        for e in snapshot_of:
            counts[e["kind"]] = counts.get(e["kind"], 0) + 1
        self.add_event(
            "finish",
            elapsed_s=round(time.perf_counter() - self._t0, 3),
            event_counts=counts,
            summary=summary or {},
        )
        self.write_index_file()

    # stage tracing

    def stage(self, stage_id: str, name: str | None = None, fn: str | None = None) -> "_StageCtx":
        return _StageCtx(self, stage_id, name or stage_id, fn)

    # snapshots

    def snapshot(self, docx_path: str | os.PathLike[str], label: str) -> str | None:
        """Copy an intermediate .docx into the trace snapshot dir."""
        if not self.include_snapshots:
            return None
        try:
            src = Path(docx_path)
            if not src.is_file():
                return None
            target = self.snapshots_dir / f"{_snapshot_label(self.events, label)}.docx"
            shutil.copy2(src, target)
            self.add_event(
                "snapshot",
                label=label,
                file=str(target),
                size_bytes=target.stat().st_size,
            )
            return str(target)
        except OSError as exc:
            self.add_event("snapshot_error", label=label, error=str(exc))
            return None

    # LLM calls

    def llm_request(
        self,
        call_kind: str,
        schema_name: str,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any] | None:
        """Persist the full prompts of an LLM call; returns an artifact handle."""
        artifact: dict[str, Any] = {
            "call_kind": call_kind,
            "schema_name": schema_name,
            "system_prompt_chars": len(system_prompt or ""),
            "user_prompt_chars": len(user_prompt or ""),
            "attempts": 0,
            "status": "pending",
        }
        try:
            self.llm_dir.mkdir(parents=True, exist_ok=True)
            seq = len(
                [e for e in self.events if e["kind"] == "llm_call"]
            ) + 1
            artifact["seq"] = seq
            request_file = self.llm_dir / f"{seq:02d}_{call_kind}_request.json"
            request_file.write_text(
                json.dumps(
                    {
                        "schema_name": schema_name,
                        "system_prompt": system_prompt,
                        "user_prompt": user_prompt,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            artifact["request_file"] = str(request_file)
            artifact["_event"] = self.add_event(
                "llm_call",
                call_kind=call_kind,
                schema_name=schema_name,
                request_file=str(request_file),
                status="pending",
            )
            return artifact
        except OSError as exc:
            artifact["error"] = str(exc)
            artifact["_event"] = self.add_event(
                "llm_call", call_kind=call_kind, status="pending",
                artifact_write_error=str(exc),
            )
            return artifact

    def llm_response(
        self,
        artifact: dict[str, Any] | None,
        parsed: Any,
        model: str | None = None,
        token_usage: dict[str, int] | None = None,
        attempts: int = 1,
    ) -> None:
        if artifact is None:
            return

        event = artifact.get("_event") or self.add_event(
            "llm_call", call_kind=artifact.get("call_kind"), status="ok"
        )

        # Small summarising fields go into the index event; the full parse goes
        # to a response file referenced by it.
        if isinstance(parsed, dict):
            if "notes" in parsed:
                notes = parsed.get("notes") or []
                event["notes_count"] = len(notes)
                verdicts = {
                    sv.get("rule_id"): sv.get("verdict")
                    for sv in parsed.get("structural_validations") or []
                    if isinstance(sv, dict)
                }
                if verdicts:
                    event["verdicts"] = verdicts
            else:
                event["top_level_keys"] = sorted(parsed.keys())

        response_file = None
        seq = artifact.get("seq")
        if seq is not None:
            try:
                self.llm_dir.mkdir(parents=True, exist_ok=True)
                response_file = self.llm_dir / f"{seq:02d}_{artifact['call_kind']}_response.json"
                response_file.write_text(
                    json.dumps(parsed, ensure_ascii=False, indent=2, default=str),
                    encoding="utf-8",
                )
            except (OSError, TypeError):
                response_file = None

        if model:
            event["model"] = model
        event["attempts"] = attempts
        event["status"] = "ok"
        if token_usage:
            event["token_usage"] = token_usage
        if response_file is not None:
            event["response_file"] = str(response_file)

        artifact["status"] = "ok"
        artifact["attempts"] = attempts

    def llm_error(
        self, artifact: dict[str, Any] | None, error: str, attempts: int = 0
    ) -> None:
        if artifact is None:
            return
        event = artifact.get("_event") or self.add_event(
            "llm_call", call_kind=artifact.get("call_kind"), status="error"
        )
        event.update({"status": "error", "error": error, "attempts": attempts})
        artifact["status"] = "error"

    # external APIs (CrossRef, MemberPress,...)

    def api_call(
        self,
        provider: str,
        url: str,
        method: str = "GET",
        status: Any = None,
        latency_ms: float | None = None,
        cache_hit: bool | None = None,
        detail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.add_event(
            "api_call",
            provider=provider,
            url=url,
            method=method,
            status=status,
            latency_ms=round(latency_ms, 1) if latency_ms is not None else None,
            cache_hit=cache_hit,
            detail=detail or {},
        )

    # document health checks

    def ooxml_result(self, path: str, problems: list[str], after_stage: str) -> dict[str, Any]:
        return self.add_event(
            "ooxml_check",
            path=str(path),
            after_stage=after_stage,
            ok=not problems,
            problems=problems[:20],
        )

    def word_gate_result(
        self,
        path: str,
        ok: bool,
        error: str | None = None,
        duration_ms: float | None = None,
        after_stage: str | None = None,
        source: str = "word_com",
    ) -> dict[str, Any]:
        return self.add_event(
            "word_gate",
            path=str(path),
            ok=ok,
            error=error,
            duration_ms=round(duration_ms, 1) if duration_ms is not None else None,
            after_stage=after_stage,
            source=source,
        )


class _StageCtx:
    """Context manager collecting one pipeline stage's timing/outcome.

    records stage_start when entered, updates that same event on exit with
    status (ok / error), duration_ms and any counts the caller attached via
    .count() / .meta(). Exceptions are recorded then re-raised so the
    pipeline's existing try/except wiring stays in charge of severity.
    """

    def __init__(self, recorder: TraceRecorder, stage_id: str, name: str, fn: str | None) -> None:
        self._recorder = recorder
        self._event = recorder.add_event(
            "stage_start", stage=stage_id, name=name, fn=fn, status="running"
        )
        self.stage_id = stage_id
        self.name = name
        self.fn = fn
        self._t0 = time.perf_counter()

    def count(self, n: int) -> None:
        self._event["edits_count"] = int(n)

    def meta(self, **fields: Any) -> None:
        self._event.setdefault("meta", {}).update(fields)

    def __enter__(self) -> "_StageCtx":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._event["duration_ms"] = round((time.perf_counter() - self._t0) * 1000, 1)
        if exc_type is None:
            self._event["status"] = "ok"
        else:
            self._event["status"] = "error"
            self._event["error"] = f"{exc_type.__name__}: {exc}"
        return False


class _NullStage:
    def count(self, n: int) -> None:  # pragma: no cover
        return None

    def meta(self, **fields: Any) -> None:  # pragma: no cover
        return None

    def __enter__(self) -> "_NullStage":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


@contextmanager
def noop_stage(stage_id: str, name: str | None = None, fn: str | None = None):
    """No-op replacement for trace.stage when tracing is disabled."""
    yield _NullStage()


def stage_fn(trace: TraceRecorder | None):
    """Stage factory for a run: the recorder's, or a null one."""
    if trace is not None:
        return trace.stage
    return noop_stage


def _snapshot_label(events: list[dict[str, Any]], label: str) -> str:
    n = sum(1 for e in events if e["kind"] == "snapshot")
    vt = _now_iso().replace(":", "").replace("-", "")
    return f"{n:03d}_{vt}_{label}"
