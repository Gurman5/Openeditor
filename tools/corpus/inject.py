"""Defect injector (K-I1, recipes from K-I2 onwards).

Takes a known-good .docx, breaks one APA rule on purpose (or several, for a
composite), writes the result, and RETURNS the manifest row for it. It never
writes manifest.json (Person A owns that) and never changes the base file.

  python -m tools.corpus.inject --base good.docx --defect APA-03 --out bad.docx
  python -m tools.corpus.inject --base good.docx --defect APA-03 --defect APA-00 --out composite.docx
  options: --seed N (default 0)  --where style|paragraph  --no-verify

--defect takes a RECIPE id (see RECIPES). Most ids are the matrix row
("APA-03"); a row with several recipes gets a letter ("APA-02a" disallowed
font, "APA-02b" wrong size). A composite can break each matrix row once.
The row's "defects_injected" lists matrix rows; "injections" names the recipes.

--where is optional: each recipe has its own default (APA-03: paragraph;
style only when asked for). An explicit --where applies to every chosen
recipe that supports it; the others keep their default.

The row is printed as JSON. Field names follow the K-S2 manifest schema where
they apply; "verdicts" only lists the injected rows (expected "fail") - the
other rows come from the base document's own manifest row.

Safety:
  - the base must have no tracked changes and must PASS every targeted row
  - after injecting, every targeted row must FAIL (skip with --no-verify)
  - same base + defects + seed + where -> byte-identical output (the zip is
    written with fixed timestamps in the base's part order)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import zipfile
from pathlib import Path

from lxml import etree

from tools.corpus.defects.format_defects import DOC, FORMAT_RECIPES
from tools.corpus.docx_view import accepted_view, parse_xml, read_parts, w

RECIPES = {**FORMAT_RECIPES}
WHERE_CHOICES = ("style", "paragraph")
_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class InjectionError(ValueError):
    """The injection request is invalid or did not produce the defect."""


class _Parts(dict):
    """Part name -> parsed XML root, parsed the first time a recipe asks for it."""

    def __init__(self, raw: dict[str, bytes]):
        super().__init__()
        self._raw = raw

    def __missing__(self, name: str):
        if name not in self._raw:
            raise KeyError(f"base has no part {name!r}")
        root = parse_xml(self._raw[name])
        self[name] = root
        return root


def _check_request(base: Path, defects: list[str], out: Path, where: str | None) -> None:
    if not defects:
        raise InjectionError("give at least one --defect")
    unknown = [d for d in defects if d not in RECIPES]
    if unknown:
        raise InjectionError(f"no recipe for {unknown}; available: {sorted(RECIPES)}")
    rows = [RECIPES[d].matrix_id for d in defects]
    dupes = sorted({r for r in rows if rows.count(r) > 1})
    if dupes:
        raise InjectionError(f"one defect per matrix row; repeated: {dupes}")
    if where is not None and not any(where in RECIPES[d].wheres for d in defects):
        raise InjectionError(f"none of {defects} supports where={where!r}")
    if out.name.lower() == "manifest.json":
        raise InjectionError("the injector never writes manifest.json")
    if out.resolve() == base.resolve():
        raise InjectionError("--out must not be the base file")


def _has_tracked_changes(parts: dict[str, bytes]) -> bool:
    root = parse_xml(parts[DOC])
    return any(True for _ in root.iter(w("ins"), w("del"), w("moveFrom"), w("moveTo")))


def _write_deterministic(parts: dict[str, bytes], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w") as z:
        for name, data in parts.items():            # base order
            info = zipfile.ZipInfo(name, date_time=_FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            z.writestr(info, data)


def inject(base: str | Path, defects: list[str], out: str | Path, *, seed: int = 0,
           where: str | None = None, verify: bool = True) -> dict:
    """Inject `defects` into `base`, write `out`, return the manifest row."""
    base, out = Path(base), Path(out)
    _check_request(base, defects, out, where)

    parts = read_parts(base)
    if _has_tracked_changes(parts):
        raise InjectionError("base has tracked changes; inject into a clean known-good doc")
    base_view = accepted_view(base)
    recipes = [RECIPES[d] for d in defects]
    for recipe in recipes:
        status = recipe.check(base_view)["status"]
        if status != "pass":
            raise InjectionError(f"base must pass {recipe.matrix_id} before injecting it "
                                 f"(it is {status!r})")

    roots = _Parts(parts)
    rng = random.Random(seed)
    injections = []
    for recipe in recipes:
        use = where if where in recipe.wheres else recipe.default_where
        details = recipe.apply(roots, rng, use, base_view)
        injections.append({"matrix_id": recipe.matrix_id, "recipe_id": recipe.id,
                           "recipe": recipe.name, **details})

    for name, root in roots.items():         # only the parts a recipe opened
        parts[name] = etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                                     standalone=True)
    _write_deterministic(parts, out)

    if verify:
        out_view = accepted_view(out)
        still_passing = [r.matrix_id for r in recipes
                         if r.check(out_view)["status"] != "fail"]
        if still_passing:
            raise InjectionError(f"injection did not make {still_passing} fail")

    return {
        "id": f"{base.stem}__{'+'.join(defects)}__s{seed}",
        "derived_from": base.name,
        "defects_injected": [r.matrix_id for r in recipes],
        "verdicts": {r.matrix_id: "fail" for r in recipes},
        "injections": injections,
        "seed": seed,
        "where": where,
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "notes": "",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Inject APA defects into a known-good .docx")
    ap.add_argument("--base", required=True, help="known-good .docx (not changed)")
    ap.add_argument("--defect", required=True, action="append",
                    help=f"recipe id; repeat for a composite ({', '.join(RECIPES)})")
    ap.add_argument("--out", required=True, help="where to write the injected .docx")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--where", choices=WHERE_CHOICES, default=None,
                    help="override the recipe default (APA-03 defaults to paragraph)")
    ap.add_argument("--no-verify", action="store_true", help="skip the after-injection check")
    args = ap.parse_args(argv)
    row = inject(args.base, args.defect, args.out, seed=args.seed, where=args.where,
                 verify=not args.no_verify)
    print(json.dumps(row, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
