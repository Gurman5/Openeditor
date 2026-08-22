"""Tests for the upload guardrails added to app.main:

1. Whole-document word-count cap (rejects oversized manuscripts at upload).
2. Hard timeout on the whole analysis (cooperative + wall-clock guarantee).
"""

import io
import time

import pytest

import app.main as main

# A real .docx with actual prose so the word counter has something to count.
_FIXTURE = "app/domain/JUTLP Template 2026.docx"


def _client():
    main.app.config["TESTING"] = True
    return main.app.test_client()


def _upload(client, path=_FIXTURE, name="manuscript.docx"):
    with open(path, "rb") as fh:
        data = fh.read()
    return client.post(
        "/api/upload",
        data={"file": (io.BytesIO(data), name)},
        content_type="multipart/form-data",
    )


def _poll_until_final(client, session_id, timeout_s=10.0):
    """Poll /api/results until it returns a non-202 (final) response."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        res = client.get(f"/api/results/{session_id}")
        if res.status_code != 202:
            return res
        time.sleep(0.1)
    raise AssertionError("results never reached a final state")


# ── Word-count helper ────────────────────────────────────────────────────────

def test_document_word_count_is_positive_for_real_doc():
    assert main._document_word_count(_FIXTURE) > 0


# ── Word-count gate ──────────────────────────────────────────────────────────

def test_upload_rejected_when_over_word_limit(monkeypatch):
    monkeypatch.setattr(main, "_max_word_count", 5)
    # Pipeline must never run for a rejected upload.
    monkeypatch.setattr(
        main, "doc_analysis_pipeline",
        lambda *a, **k: pytest.fail("pipeline ran despite word-count rejection"),
    )
    res = _upload(_client())
    assert res.status_code == 400
    body = res.get_json()
    assert body["max_word_count"] == 5
    assert body["word_count"] > 5
    assert "too long" in body["error"].lower()


def test_upload_accepted_when_under_word_limit(monkeypatch):
    monkeypatch.setattr(main, "_max_word_count", 1_000_000)
    started = {"ran": False}

    def _fake_pipeline(input_path, output_path=None, progress_callback=None):
        started["ran"] = True
        if progress_callback:
            progress_callback(50, "refs")
        # Minimal shape the success path reads.
        return {
            "deterministic_check_results": {"results": []},
            "ref_check_result": {"results": []},
            "llm_result": None,
        }

    monkeypatch.setattr(main, "doc_analysis_pipeline", _fake_pipeline)
    res = _upload(_client())
    assert res.status_code == 200
    assert "session_id" in res.get_json()


# ── Timeout ──────────────────────────────────────────────────────────────────

def test_cooperative_timeout_via_progress_callback(monkeypatch):
    """A pipeline that keeps calling progress past the deadline is aborted at
    the next checkpoint and the session reports a 504 timeout."""
    monkeypatch.setattr(main, "_max_word_count", 1_000_000)
    monkeypatch.setattr(main, "_analysis_timeout_seconds", 1)

    def _slow_pipeline(input_path, output_path=None, progress_callback=None):
        for _ in range(200):
            if progress_callback:
                progress_callback(50, "building")  # raises once past deadline
            time.sleep(0.05)
        raise AssertionError("pipeline was not aborted by the timeout")

    monkeypatch.setattr(main, "doc_analysis_pipeline", _slow_pipeline)
    client = _client()
    session_id = _upload(client).get_json()["session_id"]
    res = _poll_until_final(client, session_id)
    assert res.status_code == 504
    assert res.get_json()["status"] == "timeout"


def test_hard_timeout_when_pipeline_ignores_callback(monkeypatch):
    """A pipeline that stalls without ever calling progress still flips the
    session to timeout via the join() wall-clock guarantee."""
    monkeypatch.setattr(main, "_max_word_count", 1_000_000)
    monkeypatch.setattr(main, "_analysis_timeout_seconds", 1)

    def _stalled_pipeline(input_path, output_path=None, progress_callback=None):
        time.sleep(30)  # never calls progress_callback

    monkeypatch.setattr(main, "doc_analysis_pipeline", _stalled_pipeline)
    client = _client()
    session_id = _upload(client).get_json()["session_id"]
    res = _poll_until_final(client, session_id, timeout_s=8.0)
    assert res.status_code == 504
    assert res.get_json()["status"] == "timeout"
