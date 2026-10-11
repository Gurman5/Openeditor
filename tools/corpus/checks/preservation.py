"""Text-preservation check (K-H9): the hard preservation flag.

Not an APA matrix row (matrix_id is None). It catches the engine losing or
mangling the author's text, and its hard flag is what the regression gate
(K-B4) fails on.

How it works:
  1. normalise the INPUT with the engine's own
     app.services.document_normalisation_services.normalise_docx (into a temp
     folder; the input is never changed). That is the engine's real starting
     point: author tracked changes accepted, colour/highlight stripped,
     Guidance Notes and blank paragraphs removed. Comparing against the raw
     input (or a "rejected view" of the output) would be wrong.
  2. take the accepted-view text (tools/corpus/docx_view.py) of the
     normalised input and of the OUTPUT: engine insertions count as present,
     engine deletions as gone. Body text and tables only, not headers,
     footers or footnotes.
  3. diff in two levels: paragraphs first, then word by word inside the
     paragraphs that changed. Paragraph breaks themselves don't count, so a
     merged or split paragraph is zero changed words.
  4. ratio = (inserted + deleted characters) / characters in the normalised
     input. The hard flag is raised when ratio > the limit.

The limit (default 0.10 = 10%) can be changed:
  - in code:   check_preservation(out, inp, max_ratio=0.05)
  - in a shell: $env:CORPUS_PRESERVATION_MAX_RATIO = "0.05"

Not in v1: an allow-list of intended edits from the manifest.

Usage:
  python -m tools.corpus.checks.preservation --docx output.docx --input original.docx
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import tempfile
from pathlib import Path

from tools.corpus.docx_view import accepted_view

MAX_CHANGE_RATIO = 0.10
ENV_VAR = "CORPUS_PRESERVATION_MAX_RATIO"
TOP_CHANGES = 5
_REPORT_FIELDS = ("accepted_revisions", "runs_colour_stripped", "runs_highlight_stripped",
                  "guidance_paragraphs_deleted", "blank_paragraphs_removed")


def change_limit(value: float | None = None) -> float:
    """Argument, else $CORPUS_PRESERVATION_MAX_RATIO, else MAX_CHANGE_RATIO."""
    if value is not None:
        return float(value)
    if os.environ.get(ENV_VAR):
        try:
            return float(os.environ[ENV_VAR])
        except ValueError:
            raise ValueError(f"{ENV_VAR} must be a number like 0.1, got "
                             f"{os.environ[ENV_VAR]!r}") from None
    return MAX_CHANGE_RATIO


def _paragraphs(docx_path) -> list[str]:
    """Accepted-view paragraphs as whitespace-normalised strings (empty ones dropped)."""
    out = []
    for p in accepted_view(docx_path).paragraphs:
        text = " ".join(p.text.split())
        if text:
            out.append(text)
    return out


def _chars(words: list[str]) -> int:
    return sum(len(wd) for wd in words)


def _snippet(words: list[str]) -> str:
    text = " ".join(words)
    return text if len(text) <= 60 else text[:57] + "..."


def diff_words(reference: list[str], output: list[str]) -> dict:
    """Two-level diff of paragraph lists. Returns counts + the changes."""
    ins_words = del_words = ins_chars = del_chars = 0
    changes = []

    def word_diff(before: list[str], after: list[str]):
        nonlocal ins_words, del_words, ins_chars, del_chars
        sm = difflib.SequenceMatcher(None, before, after, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            gone, new = before[i1:i2], after[j1:j2]
            del_words += len(gone)
            ins_words += len(new)
            del_chars += _chars(gone)
            ins_chars += _chars(new)
            changes.append({"type": tag, "chars": _chars(gone) + _chars(new),
                            "before": _snippet(gone), "after": _snippet(new)})

    paras = difflib.SequenceMatcher(None, reference, output, autojunk=False)
    for tag, i1, i2, j1, j2 in paras.get_opcodes():
        if tag != "equal":
            word_diff(" ".join(reference[i1:i2]).split(), " ".join(output[j1:j2]).split())

    changes.sort(key=lambda c: c["chars"], reverse=True)
    return {"inserted_words": ins_words, "deleted_words": del_words,
            "inserted_chars": ins_chars, "deleted_chars": del_chars, "changes": changes}


def check_preservation(output_docx: str | Path, input_docx: str | Path | None = None, *,
                       normalised: str | Path | None = None,
                       max_ratio: float | None = None) -> dict:
    """Compare the output's accepted text with normalise_docx(input).

    Pass `normalised=` (an already-normalised copy of the input) to skip
    running normalise_docx again, e.g. in baseline runs."""
    if input_docx is None and normalised is None:
        raise ValueError("give input_docx or normalised")
    limit = change_limit(max_ratio)

    normalisation = None
    if normalised is not None:
        reference = _paragraphs(normalised)
    else:
        # Imported here so the other checks don't need Flask (app/__init__.py).
        from app.services.document_normalisation_services import normalise_docx
        with tempfile.TemporaryDirectory() as tmp:
            norm_path = Path(tmp) / "normalised.docx"
            report = normalise_docx(input_docx, norm_path)
            normalisation = {f: getattr(report, f) for f in _REPORT_FIELDS}
            reference = _paragraphs(norm_path)

    result = {"check": "preservation", "matrix_id": None, "max_ratio": limit,
              "normalisation": normalisation}
    ref_chars = _chars(" ".join(reference).split())
    if ref_chars == 0:
        return {**result, "status": "na", "hard_flag": False, "ratio": None,
                "reason": "normalised input has no text"}

    diff = diff_words(reference, _paragraphs(output_docx))
    ratio = round((diff["inserted_chars"] + diff["deleted_chars"]) / ref_chars, 4)
    flag = ratio > limit
    return {**result, "status": "fail" if flag else "pass", "hard_flag": flag,
            "ratio": ratio, "reference_chars": ref_chars,
            **{k: v for k, v in diff.items() if k != "changes"},
            "biggest_changes": diff["changes"][:TOP_CHANGES]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Text-preservation check (hard flag)")
    ap.add_argument("--docx", required=True, help="engine OUTPUT .docx")
    ap.add_argument("--input", required=True, help="original INPUT .docx")
    ap.add_argument("--max-ratio", type=float, help="limit, default 0.10")
    args = ap.parse_args(argv)
    result = check_preservation(args.docx, args.input, max_ratio=args.max_ratio)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
