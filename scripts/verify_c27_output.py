"""
C-27 font-sweep verification: runs build_edited_document on the
01_valid_identified.docx fixture and asserts every font layer in the output
resolves to Calibri:

  APA002  no run declares a non-Calibri, non-symbol typeface (document,
          headers, footers); no run is left theme-bound
  C-27    every styles.xml rFonts is explicit Calibri (symbol styles
          excepted); docDefaults carries explicit Calibri, no *Theme binding
  APA002  check_fonts() passes on the built output
"""
# TODO: Delete script after completion of Track C
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutil
import tempfile
import zipfile

from lxml import etree

from app.services.apa7_formatting_checks import check_fonts
from app.services.output_generation_samfix import build_edited_document

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"
SRC = "tests/jutlp_sample_docx_test_pack/01_valid_identified.docx"
SYMBOLS = {"symbol", "wingdings", "wingdings 2", "wingdings 3", "webdings"}

failures = []


def check(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        failures.append(label)


tmp = tempfile.mkdtemp(prefix="c27_")
src = os.path.join(tmp, "in.docx")
out = os.path.join(tmp, "out.docx")
shutil.copy(SRC, src)
build_edited_document(src, out)
print("built:", out, os.path.getsize(out), "bytes")
print()

z = zipfile.ZipFile(out)
names = z.namelist()
text_parts = [n for n in names
              if n == "word/document.xml"
              or n in ("word/footnotes.xml", "word/endnotes.xml", "word/comments.xml")
              or (n.rsplit("/", 1)[-1].startswith(("header", "footer"))
                  and n.endswith(".xml"))]

print("== runs: explicit Calibri, inheriting, or symbol ==")
bad_runs = []
theme_runs = 0
for part in text_parts:
    root = etree.fromstring(z.read(part))
    for r in root.iter(f"{WQ}r"):
        t = r.find(f"{WQ}t")
        if t is None or not (t.text or "").strip():
            continue
        rpr = r.find(f"{WQ}rPr")
        rf = rpr.find(f"{WQ}rFonts") if rpr is not None else None
        if rf is None:
            continue  # inherits from the (swept) paragraph style
        ascii_font = rf.get(f"{WQ}ascii")
        if ascii_font is None:
            if any(rf.get(f"{WQ}a") is not None
                   for a in ("asciiTheme", "hAnsiTheme",
                             "eastAsiaTheme", "cstheme")):
                theme_runs += 1
            continue
        if ascii_font.strip().lower() in SYMBOLS:
            continue
        if ascii_font != "Calibri":
            bad_runs.append(f"{part}: {(t.text or '').strip()[:40]!r} -> {ascii_font}")
check("no non-Calibri explicit run font", not bad_runs,
      f"{len(bad_runs)} bad" + (f": {bad_runs[:3]}" if bad_runs else ""))
check("no theme-bound runs left", theme_runs == 0, f"{theme_runs} bound")
print()

print("== styles.xml + docDefaults ==")
sroot = etree.fromstring(z.read("word/styles.xml"))
bad_styles = []
for st in sroot.findall(f"{WQ}style"):
    rf = st.find(f"{WQ}rPr/{WQ}rFonts")
    if rf is None:
        continue
    vals = [rf.get(f"{WQ}a") for a in ("ascii", "hAnsi", "eastAsia", "cs")]
    vals = [v for v in vals if v]
    if vals and all(v.strip().lower() in SYMBOLS for v in vals):
        continue
    themed = any(rf.get(f"{WQ}a") is not None
                 for a in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"))
    wrong = [v for v in vals if v != "Calibri" and v.strip().lower() not in SYMBOLS]
    if wrong or themed:
        bad_styles.append(
            f"{st.get(f'{WQ}styleId')}: wrong={wrong} themed={themed}")
check("all style fonts explicit Calibri (symbol excepted)", not bad_styles,
      f"{len(bad_styles)} bad" + (f": {bad_styles[:3]}" if bad_styles else ""))
dd = sroot.find(f"{WQ}docDefaults/{WQ}rPrDefault/{WQ}rPr/{WQ}rFonts")
check("docDefaults present", dd is not None)
if dd is not None:
    check("docDefaults ascii/hAnsi=Calibri",
          dd.get(f"{WQ}ascii") == "Calibri" and dd.get(f"{WQ}hAnsi") == "Calibri",
          dd.get(f"{WQ}ascii"))
    check("docDefaults has no theme binding",
          all(dd.get(f"{WQ}a") is None
              for a in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme")))
print()

print("== APA002 check on built output ==")
res = check_fonts(out)
check("APA002 present", bool(res) and res[0]["rule_id"] == "APA002")
if res:
    check("APA002 passes", res[0]["status"] == "pass", res[0].get("message", ""))
print()

print("RESULT:", "PASS" if not failures else f"FAIL ({len(failures)}: {failures})")
raise SystemExit(0 if not failures else 1)
