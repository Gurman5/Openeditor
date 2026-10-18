"""MS Word openability gate for generated .docx files (dev-gated).

Two layers, both optional and driven by the dev trace recorder:

1. ``static_check`` — schema-shape checks reusing ``tools.docx_ooxml_validator``:
   the parts Word actually refuses to load (invented settings elements, duplicate
   revision ids, ``<w:t>`` inside tracked deletions, orphaned comment anchors).
   Cheap, works everywhere, runs per traced pipeline run.

2. ``run_com_gate`` — real MS Word via COM automation (pywin32, Windows only).
   Opens candidate documents Read-Only with a killed repair dialog and records
   whether Word accepted the file. Slow (~seconds per file), so it runs only on
   the final document (plus snapshots when present) and only when the
   ``PIPELINE_TRACE_WORD`` gate is on.

A COM failure is evidence, not a verdict: transient Word/COM plumbing issues
(stale Word process, modal dialog held open) mimic corruption. ``run_com_gate``
reports the distinction in ``error_kind``.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

WORD_GATE_ENV = "PIPELINE_TRACE_WORD"

# Exit codes for tools/word_check.py
EXIT_OK = 0
EXIT_PROBLEMS = 1
EXIT_NO_WORD = 2


def com_gate_enabled() -> bool:
    return os.environ.get(WORD_GATE_ENV) == "1"


def static_check(path: str | os.PathLike[str]) -> list[str]:
    """Schema-shape problems Word would flag as 'unreadable content'. Empty = pass."""
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from tools.docx_ooxml_validator import validate

    return validate(str(path))


def _com_open_once(path: str, timeout_s: float) -> dict[str, Any]:
    """One Word COM open attempt. Bare implementation, no trace recording."""
    import pythoncom  # pywin32
    import win32com.client

    pythoncom.CoInitialize()
    word = None
    doc = None
    t0 = time.perf_counter()
    try:
        # DispatchEx forces a private instance instead of attaching to whatever
        # Word process the user has open — a stale user session must not make
        # the gate fail (or make it succeed by reusing an existing document).
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0  # wdAlertsNone: repair/compat dialogs are answered with the default
        doc = word.Documents.Open(
            path,
            ReadOnly=True,
            AddToRecentFiles=False,
            Visible=False,
        )
        # Forcing a value the layout engine computes proves Word actually parsed
        # content rather than failing silently into an empty document shell.
        laid_out_ok = True
        word_error: str | None = None
        try:
            repaginate = getattr(doc, "Repaginate", None)
            if repaginate is not None:
                repaginate()
        except Exception as exc:  # layout failure = Word can render but chokes on content
            laid_out_ok = False
            word_error = f"layout: {exc}"
        pages = doc.ComputeStatistics(2)  # wdStatisticPages
        words = doc.ComputeStatistics(0)  # wdStatisticWords
        doc.Close(SaveChanges=0)
        doc = None
        word.Quit(SaveChanges=0)
        word = None
        return {
            "ok": laid_out_ok,
            "error": word_error if laid_out_ok is False else None,
            "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
            "pages": pages,
            "words": words,
        }
    except Exception as exc:
        detail = str(exc)
        try:
            import pywintypes as _pw

            if isinstance(exc, _pw.com_error):
                detail = f"COM {exc.hresult:#010x}: {exc.excepinfo[2] if exc.excepinfo else exc}"
        except Exception:
            pass
        ok = word is not None and doc is not None
        if doc is not None:
            try:
                doc.Close(SaveChanges=0)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit(SaveChanges=0)
            except Exception:
                pass
        return {
            "ok": False,
            "error": detail,
            "error_kind": "com_error" if word is None else "word_error",
            "partial_open": ok,
            "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
        }
    finally:
        pythoncom.CoUninitialize()


def word_available() -> bool:
    try:
        import win32com.client  # noqa: F401

        return True
    except ImportError:
        return False


def run_com_gate(paths: list[str | os.PathLike[str]]) -> list[dict[str, Any]]:
    """Open each candidate in real Word; report per-file outcomes."""
    results: list[dict[str, Any]] = []
    for path in paths:
        path_str = str(path)
        if not Path(path_str).is_file():
            results.append({"path": path_str, "ok": False, "error": "file missing"})
            continue
        attempt = _com_open_once(path_str, timeout_s=60)
        attempt["path"] = path_str
        results.append(attempt)
    return results


def run_gate(
    paths: list[str | os.PathLike[str]],
    trace: Any = None,
    after_stage: str = "final",
    include_com: bool | None = None,
) -> dict[str, Any]:
    """Static + (optionally) COM checks on candidate documents, recorded to trace."""
    summary: dict[str, Any] = {"static": {}, "com": {}}
    for path in paths:
        path_str = str(path)
        try:
            problems = static_check(path_str)
        except OSError as exc:
            problems = [f"unreadable: {exc}"]
        if trace is not None:
            trace.ooxml_result(path_str, problems, after_stage=after_stage)
        summary["static"][path_str] = problems
    use_com = com_gate_enabled() if include_com is None else include_com
    if use_com:
        if not word_available():
            for path in paths:
                if trace is not None:
                    trace.word_gate_result(
                        str(path), ok=False, error="pywin32 not installed",
                        after_stage=after_stage, source="word_com",
                    )
            summary["com"] = {"skipped": "pywin32 not installed"}
            return summary
        com_results = run_com_gate([str(p) for p in paths])
        for r in com_results:
            if trace is not None:
                trace.word_gate_result(
                    r["path"], ok=r.get("ok", False), error=r.get("error"),
                    duration_ms=r.get("duration_ms"), after_stage=after_stage,
                    source="word_com",
                )
        summary["com"] = {r["path"]: r for r in com_results}
    return summary
