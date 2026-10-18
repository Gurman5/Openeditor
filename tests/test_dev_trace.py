import json

import pytest

from app.services import dev_trace
from app.services.dev_trace import TraceRecorder, is_enabled


@pytest.fixture()
def recorder(tmp_path):
    return TraceRecorder("sess-test", tmp_path, include_snapshots=True)


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("PIPELINE_TRACE", raising=False)
    assert is_enabled() is False


def test_enabled_flag(monkeypatch):
    monkeypatch.setenv("PIPELINE_TRACE", "1")
    assert is_enabled() is True
    monkeypatch.setenv("PIPELINE_TRACE", "2")
    assert dev_trace.snapshots_enabled() is True
    monkeypatch.setenv("PIPELINE_TRACE", "1")
    monkeypatch.delenv("PIPELINE_TRACE_SNAPSHOTS", raising=False)
    assert dev_trace.snapshots_enabled() is False


def test_stage_ok_and_error(recorder):

    with recorder.stage("headings", fn="a.b") as st:
        st.count(3)
    with pytest.raises(ValueError):
        with recorder.stage("spelling", fn="c.d"):
            raise ValueError("boom")
    events = recorder.index_payload()["events"]
    starts = [e for e in events if e["kind"] == "stage_start"]
    assert len(starts) == 2
    assert starts[0]["status"] == "ok"
    assert starts[0]["edits_count"] == 3
    assert starts[0]["duration_ms"] >= 0
    assert starts[1]["status"] == "error"
    assert "ValueError" in starts[1]["error"]


def test_stage_duration_positive(recorder):
    import time

    with recorder.stage("slow", fn="x.y"):
        time.sleep(0.005)
    ev = recorder.index_payload()["events"][0]
    assert ev["duration_ms"] >= 4


def test_llm_artifacts_written(recorder):
    art = recorder.llm_request(
        call_kind="call_llm",
        schema_name="editorial_review",
        system_prompt="SYS",
        user_prompt="USER TEXT",
    )
    assert art["request_file"].endswith("01_call_llm_request.json")
    recorder.llm_response(
        art,
        {"notes": [{"category": "apa_style"}], "structural_validations": [
            {"rule_id": "APA001", "verdict": "confirm"},
        ]},
        model="gpt-4o-mini",
        token_usage={"total_tokens": 10},
        attempts=2,
    )
    ev = recorder.index_payload()["events"][0]
    assert ev["status"] == "ok"
    assert ev["notes_count"] == 1
    assert ev["verdicts"] == {"APA001": "confirm"}
    assert ev["request_file"] is not None
    assert ev["response_file"] is not None
    req = json.loads(recorder.index_payload()["trace_dir"] and open(
        ev["request_file"], encoding="utf-8").read())
    assert req["system_prompt"] == "SYS"


def test_llm_error(recorder):
    art = recorder.llm_request("call_llm_json", "s", "sys", "user")
    recorder.llm_error(art, "RateLimit", attempts=3)
    ev = recorder.index_payload()["events"][0]
    assert ev["status"] == "error"
    assert "RateLimit" in ev["error"]


def test_snapshot_copies_docx(recorder, tmp_path):
    docx = tmp_path / "doc.docx"
    docx.write_bytes(b"PK\x03\x04")
    out = recorder.snapshot(docx, "after_headings")
    assert out is not None
    assert out.endswith("after_headings.docx")
    assert (recorder.index_payload()["events"][0]["kind"] == "snapshot")


def test_snapshot_disabled(recorder, tmp_path):
    recorder.include_snapshots = False
    docx = tmp_path / "nodoc.docx"
    out = recorder.snapshot(docx, "x")
    assert out is None


def test_api_event(recorder):
    recorder.api_call(
        provider="crossref",
        url="https://api.crossref.org/works",
        status=200,
        latency_ms=123.4,
        cache_hit=False,
    )
    ev = recorder.index_payload()["events"][0]
    assert ev["kind"] == "api_call"
    assert ev["latency_ms"] == 123.4


def test_finish_writes_index(recorder):
    with recorder.stage("headings", fn="a.b"):
        pass
    recorder.finish(summary={"stages": 1})
    assert recorder.index_payload()["finished"] is True
    idx = recorder.trace_dir / "trace_index.json"
    assert idx.exists()
    payload = json.loads(idx.read_text(encoding="utf-8"))
    payload_kinds = [e["kind"] for e in payload["events"]]
    assert payload_kinds[-1] == "finish"
    assert payload_kinds[0] == "stage_start"
