"""Font check (K-H3, matrix row APA-02).

Every run with visible text must use an allowed font family at that family's
allowed size. Fonts are resolved through the style chain, docDefaults and the
theme (tools/corpus/style_resolver.py), so style-level and theme fonts count.

Scope:
  - body text: family AND size are checked
  - text inside tables: family only (APA allows 8-14 pt in tables)
  - headers, footers, footnotes and text boxes are not checked
    (the accepted view does not include them)

The allowed list is not confirmed by the client yet, so it can be changed
without editing this file:
  - in code:   check_fonts(doc, allowed={"Calibri": 11})
  - in a shell: $env:CORPUS_ALLOWED_FONTS = "Calibri:11,Arial:11"

A run whose font cannot be worked out (e.g. a theme font with no theme part)
goes in "unresolved" and does not fail the check.

Usage:
  python -m tools.corpus.checks.fonts --docx file.docx [--allowed "Calibri:11,Arial:11"]
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

from tools.corpus.docx_view import AcceptedView, accepted_view
from tools.corpus.style_resolver import UNSET, resolve_effective

MATRIX_ID = "APA-02"
ENV_VAR = "CORPUS_ALLOWED_FONTS"

# Family -> required size in points. Change here, or override (see above).
ALLOWED_FONTS: dict[str, float] = {
    "Calibri": 11,
    "Arial": 11,
    "Times New Roman": 12,
    "Georgia": 11,
    "Lucida Sans Unicode": 10,
}


def parse_allowed(text: str) -> dict[str, float]:
    """"Calibri:11,Times New Roman:12" -> {"Calibri": 11.0, "Times New Roman": 12.0}."""
    allowed = {}
    for item in text.split(","):
        if not item.strip():
            continue
        family, sep, size = item.rpartition(":")
        try:
            if not sep or not family.strip():
                raise ValueError
            allowed[family.strip()] = float(size)
        except ValueError:
            raise ValueError(
                f"bad allowed-font entry {item.strip()!r}; expected 'Family:size', "
                f"e.g. 'Calibri:11'") from None
    if not allowed:
        raise ValueError("allowed-font list is empty")
    return allowed


def allowed_fonts(allowed: dict[str, float] | None = None) -> dict[str, float]:
    """The allowed list to use: argument, else $CORPUS_ALLOWED_FONTS, else ALLOWED_FONTS."""
    if allowed is not None:
        return dict(allowed)
    if os.environ.get(ENV_VAR):
        return parse_allowed(os.environ[ENV_VAR])
    return dict(ALLOWED_FONTS)


def check_fonts(doc: AcceptedView | str | Path,
                allowed: dict[str, float] | None = None) -> dict:
    """Run the APA-02 font check. Returns pass/fail/na plus evidence."""
    view = doc if isinstance(doc, AcceptedView) else accepted_view(doc)
    allowed = allowed_fonts(allowed)
    by_lower = {family.lower(): (family, float(size)) for family, size in allowed.items()}

    offending, unresolved = [], []
    families: Counter[str] = Counter()
    checked = 0

    for p in view.paragraphs:
        for run in p.runs:
            if not run.text.strip():
                continue
            checked += 1
            eff = resolve_effective(run, view)
            font, size_pt = eff["font"], eff["units"]["size_pt"]
            evidence = {
                "paragraph": p.index,
                "in_table": p.in_table,
                "text": run.text.strip()[:40],
                "font": font,
                "size_pt": size_pt,
                "font_source": eff["sources"].get("font"),
                "size_source": eff["sources"].get("size"),
            }
            if font == UNSET:
                unresolved.append({**evidence, "reason": "font could not be resolved"})
                continue

            families[font] += 1
            match = by_lower.get(font.lower())
            if match is None:
                offending.append({**evidence, "reason": "font not allowed"})
            elif not p.in_table and size_pt != match[1]:
                offending.append({**evidence,
                                  "reason": f"{match[0]} needs {match[1]:g}pt, got {size_pt}"})

    if checked == 0:
        status = "na"
    else:
        status = "fail" if offending else "pass"
    return {
        "check": "fonts",
        "matrix_id": MATRIX_ID,
        "status": status,
        "allowed": allowed,
        "runs_checked": checked,
        "offending": offending,
        "unresolved": unresolved,
        "families_used": dict(families),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="APA-02 font check")
    ap.add_argument("--docx", required=True, help="path to a .docx file")
    ap.add_argument("--allowed", help='override, e.g. "Calibri:11,Arial:11"')
    args = ap.parse_args(argv)
    allowed = parse_allowed(args.allowed) if args.allowed else None
    print(json.dumps(check_fonts(args.docx, allowed), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
