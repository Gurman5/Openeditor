"""Developer word-gate CLI: check whether MS Word can open .docx files.

Two layers:
  - OOXML schema-shape validation (works anywhere, no Word needed)
  - real MS Word COM open test (Windows + Word + pywin32 required)

Usage:
    python tools/word_check.py file1.docx [file2.docx ...]
    python tools/word_check.py --com-only file1.docx
    python tools/word_check.py --json file1.docx        # machine-readable

Exit codes: 0 all pass, 1 some problem, 2 Word unavailable.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.dev import word_gate  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument("paths", nargs="+", help=".docx files to check")
    parser.add_argument("--com-only", action="store_true", help="skip static OOXML checks")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    if args.com_only and not word_gate.word_available():
        print("pywin32 not available; COM layer cannot run", file=sys.stderr)
        return word_gate.EXIT_NO_WORD

    report: dict[str, dict] = {}
    failed = False
    for path in args.paths:
        entry: dict = {}
        if not args.com_only:
            problems = word_gate.static_check(path)
            entry["ooxml"] = {"ok": not problems, "problems": problems}
            failed = failed or bool(problems)
        if word_gate.word_available():
            com = word_gate.run_com_gate([path])[0]
            entry["word_com"] = {k: v for k, v in com.items() if k != "path"}
            failed = failed or not com.get("ok", False)
        else:
            entry["word_com"] = {"skipped": "pywin32 not installed"}
        report[str(path)] = entry

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    else:
        for path, entry in report.items():
            print(f"== {path}")
            if "ooxml" in entry:
                status = "PASS" if entry["ooxml"]["ok"] else "FAIL"
                print(f"  OOXML  : {status}")
                for problem in entry["ooxml"]["problems"]:
                    print(f"           - {problem}")
            if "word_com" in entry:
                wc = entry["word_com"]
                if "ok" in wc:
                    print(
                        f"  MS Word: {'PASS' if wc['ok'] else 'FAIL'}"
                        f" ({wc.get('pages', '?')} pages, {wc.get('duration_ms', '?')}ms)"
                    )
                    if wc.get("error"):
                        print(f"           error: {wc['error']}")
                else:
                    print(f"  MS Word: SKIPPED ({wc.get('skipped')})")

    return (word_gate.EXIT_PROBLEMS if failed else word_gate.EXIT_OK)


if __name__ == "__main__":
    raise SystemExit(main())
