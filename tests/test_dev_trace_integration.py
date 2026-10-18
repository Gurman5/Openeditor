"""Integration tests for the dev-trace layer (D-TR).

Recorder primitives are covered in test_dev_trace.py; these exercise them the
way the pipeline and the word gate use them: stage contexts wired into a run,
snapshot gating, run_gate recording, and — on a machine with MS Word — the
real COM gate against a synthetic known-good document.
"""

from pathlib import Path

import pytest

from app.services import dev_trace
from app.services.dev import word_gate
from tools.corpus.fixtures import build_good_docx


@pytest.fixture
def recorder(tmp_path):
    return dev_trace.TraceRecorder(session_id="t", root_dir=tmp_path, include_snapshots=True)


def _good_docx(tmp_path):
    return build_good_docx(tmp_path / "synthetic_apa7_good.docx")


def test_stage_fn_none_is_null():
    stage = dev_trace.stage_fn(None)
    with stage("any") as ctx:
        ctx.count(3)
        ctx.meta(k="v")
    assert stage is dev_trace.noop_stage


def test_stage_records_error_and_reraises(recorder):
    with pytest.raises(ValueError):
        with recorder.stage("boom", fn="x.y"):
            raise ValueError("kaput")
    stages = [e for e in recorder.events if e["kind"] == "stage_start"]
    assert len(stages) == 1
    assert stages[0]["status"] == "error"
    assert "ValueError" in stages[0]["error"]
    assert stages[0]["duration_ms"] >= 0


def test_stage_records_ok_and_counts(recorder):
    with recorder.stage("s1", fn="a.b") as ctx:
        ctx.count(7)
        ctx.meta(prompt_chars=100)
    ev = recorder.events[-1]
    assert ev["stage"] == "s1"
    assert ev["fn"] == "a.b"
    assert ev["status"] == "ok"
    assert ev["edits_count"] == 7
    assert ev["meta"] == {"prompt_chars": 100}


def test_snapshot_disabled_returns_none(tmp_path):
    rec = dev_trace.TraceRecorder(session_id="t", root_dir=tmp_path, include_snapshots=False)
    docx = _good_docx(tmp_path)
    assert rec.snapshot(docx, "after_x") is None
    assert not list(rec.trace_dir.glob("snapshots/*.docx"))
    assert [e for e in rec.events if e["kind"] == "snapshot"] == []


def test_snapshot_enabled_copies_and_records(recorder, tmp_path):
    docx = _good_docx(tmp_path)
    out = recorder.snapshot(docx, "after_x")
    assert out is not None and Path(out).is_file()
    snap_events = [e for e in recorder.events if e["kind"] == "snapshot"]
    assert len(snap_events) == 1
    assert snap_events[0]["label"] == "after_x"
    assert snap_events[0]["size_bytes"] > 0


def test_snapshot_missing_file_quietly_noops(recorder, tmp_path):
    missing = tmp_path / "nope.docx"
    assert recorder.snapshot(missing, "label") is None
    assert [e for e in recorder.events if e["kind"] == "snapshot"] == []
    assert [e for e in recorder.events if e["kind"] == "snapshot_error"] == []


def test_finish_writes_index_with_counts(recorder, tmp_path):
    docx = _good_docx(tmp_path)
    recorder.snapshot(docx, "snap")
    recorder.finish(summary={"output_path": str(docx)})
    payload = recorder.index_payload()
    assert payload["finished"] is True
    finish_events = [e for e in payload["events"] if e["kind"] == "finish"]
    assert len(finish_events) == 1
    # counts are computed over pre-finish events by design
    assert finish_events[0]["event_counts"] == {"snapshot": 1}
    assert (recorder.trace_dir / "trace_index.json").is_file()
    # idempotent: a second finish() changes nothing
    recorder.finish()
    assert recorder.index_payload() == payload


def test_run_gate_records_ooxml_event(recorder, tmp_path):
    docx = _good_docx(tmp_path)
    summary = word_gate.run_gate([docx], trace=recorder, after_stage="final", include_com=False)
    checks = [e for e in recorder.events if e["kind"] == "ooxml_check"]
    assert len(checks) == 1
    assert checks[0]["after_stage"] == "final"
    assert checks[0]["ok"] == (not summary["static"][str(docx)])
    assert [e for e in recorder.events if e["kind"] == "word_gate"] == []


def test_run_gate_survives_missing_file(recorder, tmp_path):
    missing = tmp_path / "gone.docx"
    summary = word_gate.run_gate([missing], trace=recorder, include_com=False)
    assert summary["static"][str(missing)]


def test_ambient_recorder_reaches_deep_services(recorder):
    assert dev_trace.current_trace() is None
    try:
        dev_trace.set_ambient(recorder)
        assert dev_trace.current_trace() is recorder
    finally:
        dev_trace.set_ambient(None)
    assert dev_trace.current_trace() is None


def test_com_gate_opens_real_word(tmp_path):
    """Real MS Word opens the synthetic fixture. Windows + Word required."""
    if not word_gate.word_available():
        pytest.skip("pywin32 not installed")
    docx = _good_docx(tmp_path)
    results = word_gate.run_com_gate([docx])
    assert len(results) == 1
    r = results[0]
    if r.get("error_kind") == "com_error" and not r.get("partial_open"):
        pytest.skip(f"Word COM plumbing failure on this machine: {r['error']}")
    assert r["ok"] is True, r["error"]
    assert r["pages"] >= 1
    assert r["words"] > 0


def test_com_gate_reports_missing_file():
    if not word_gate.word_available():
        pytest.skip("pywin32 not installed")
    results = word_gate.run_com_gate(["Z:/definitely/not/here.docx"])
    assert results[0]["ok"] is False
    assert results[0]["error"] == "file missing"
