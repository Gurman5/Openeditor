"""Tests for the LLM editorial-review stage (JB-01).

Regression context: the stage used to call ``.get("notes")`` on the
``EditorialReviewResult`` dataclass, raising ``AttributeError`` on every
*successful* review and discarding it downstream (``llm_result = None``).
These tests exercise the extracted stage block directly rather than running
the whole pipeline.
"""

from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from app.domain.editorial_feedback import EditorialNote, EditorialReviewResult
from app.pipelines.feedback_gen_pipeline import (
    _count_llm_notes,
    _run_llm_editorial_review_stage,
)

STAGE_NAME = "Editorial review (AI)"


class _MetaRecorder:
    """Stub for the stage's ``st`` handle; records ``meta(**fields)`` calls."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def meta(self, **fields) -> None:
        self.calls.append(fields)


@pytest.fixture
def recorder() -> _MetaRecorder:
    return _MetaRecorder()


@pytest.fixture
def fake_stage(recorder: _MetaRecorder):
    @contextmanager
    def _stage(name: str, **kwargs) -> Iterator[_MetaRecorder]:
        yield recorder

    return _stage


@pytest.fixture
def stage_error_records() -> list[dict]:
    return []


@pytest.fixture
def on_stage_error(stage_error_records: list[dict]):
    def _record(stage_label: str, exc: Exception, severity: str = "minor") -> None:
        stage_error_records.append({"stage": stage_label, "error": str(exc), "severity": severity})

    return _record


def _make_note(message: str = "Polish this sentence") -> EditorialNote:
    return EditorialNote(
        category="Style",
        severity="minor",
        section="Introduction",
        message=message,
        suggestion="Consider rephrasing.",
        quote="some sentence",
    )


class TestSuccessPath:
    def test_successful_review_is_returned_not_discarded(
        self, monkeypatch, fake_stage, on_stage_error, recorder
    ):
        review = EditorialReviewResult(notes=[_make_note(), _make_note("second")])
        monkeypatch.setattr(
            "app.pipelines.feedback_gen_pipeline.run_editorial_review",
            lambda *args, **kwargs: review,
        )

        result = _run_llm_editorial_review_stage(
            "fake.docx",
            deterministic_check_result={},
            ref_check_result={},
            stage=fake_stage,
            on_stage_error=on_stage_error,
        )

        assert result is review
        assert [n.message for n in result.notes] == ["Polish this sentence", "second"]

    def test_meta_reports_note_count(self, monkeypatch, fake_stage, on_stage_error, recorder):
        monkeypatch.setattr(
            "app.pipelines.feedback_gen_pipeline.run_editorial_review",
            lambda *args, **kwargs: EditorialReviewResult(notes=[_make_note()]),
        )

        _run_llm_editorial_review_stage(
            "fake.docx",
            deterministic_check_result={},
            ref_check_result={},
            stage=fake_stage,
            on_stage_error=on_stage_error,
        )

        assert recorder.calls == [{"notes": 1}]

    def test_success_records_no_stage_error(
        self, monkeypatch, fake_stage, on_stage_error, stage_error_records
    ):
        monkeypatch.setattr(
            "app.pipelines.feedback_gen_pipeline.run_editorial_review",
            lambda *args, **kwargs: EditorialReviewResult(notes=[_make_note()]),
        )

        _run_llm_editorial_review_stage(
            "fake.docx",
            deterministic_check_result={},
            ref_check_result={},
            stage=fake_stage,
            on_stage_error=on_stage_error,
        )

        assert stage_error_records == []


class TestFailurePath:
    def test_raising_review_returns_none_and_records_critical_error(
        self, monkeypatch, fake_stage, on_stage_error, stage_error_records
    ):
        def _boom(*args, **kwargs):
            raise RuntimeError("OpenAI unavailable")

        monkeypatch.setattr("app.pipelines.feedback_gen_pipeline.run_editorial_review", _boom)

        result = _run_llm_editorial_review_stage(
            "fake.docx",
            deterministic_check_result={},
            ref_check_result={},
            stage=fake_stage,
            on_stage_error=on_stage_error,
        )

        assert result is None
        assert len(stage_error_records) == 1
        entry = stage_error_records[0]
        assert entry["stage"] == STAGE_NAME
        assert entry["severity"] == "critical"
        assert "OpenAI unavailable" in entry["error"]


class TestCountLlmNotes:
    @pytest.mark.parametrize(
        ("shape", "expected"),
        [
            (EditorialReviewResult(notes=[_make_note(), _make_note()]), 2),
            (EditorialReviewResult(notes=[]), 0),
            ({"notes": [_make_note()]}, 1),
            ({"notes": None}, 0),
            ({}, 0),
            (None, 0),
            (object(), 0),
        ],
    )
    def test_shape_matrix(self, shape, expected):
        assert _count_llm_notes(shape) == expected
