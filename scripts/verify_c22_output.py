"""
Runs build_edited_document on the 01_valid_identified.docx fixture and asserts
the APA 7 geometry C-22a / C-22b landed in the output:

  APA-00  every sectPr carries pgMar 1440 (1in) on all four sides
  APA-05  a PAGE field lives in the running header (default, and first when
          titlePg is enabled)
  APA-01  Normal style is double spaced (line=480, after=0)
  APA-03  Normal style is left aligned (jc=left)
  APA-04  Normal style carries a 0.5in first-line indent (firstLine=720)
  C-27    Normal style body font is Calibri

Body paragraphs are also checked so no direct JUTLP formatting (jc=both,
line=276, after!=0) survives to override the APA Normal style.
"""
# TODO: Delete script after completion of Track C
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutil
import tempfile
import zipfile

from lxml import etree

from app.services.output_generation_samfix import build_edited_document

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"
RQ = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
SRC = "tests/jutlp_sample_docx_test_pack/01_valid_identified.docx"

MARGIN = "1440"
SPACING_LINE = "480"
SPACE_AFTER = "0"
FIRST_LINE = "720"

failures = []


def check(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        failures.append(label)


tmp = tempfile.mkdtemp(prefix="c22_")
src = os.path.join(tmp, "in.docx")
out = os.path.join(tmp, "out.docx")
shutil.copy(SRC, src)
build_edited_document(src, out)
print("built:", out, os.path.getsize(out), "bytes")
print()

z = zipfile.ZipFile(out)
names = z.namelist()
doc_root = etree.fromstring(z.read("word/document.xml"))
styles_root = etree.fromstring(z.read("word/styles.xml"))
rels_root = etree.fromstring(z.read("word/_rels/document.xml.rels"))

print("== APA-00 margins (C-22a) ==")
# Only real sections: sectPrChange nests a copy of the old sectPr, which a
# naive iter() would count as an extra section (and which *should* keep old values).
body_el = doc_root.find(f"{WQ}body")
sect_list = list(body_el.findall(f"{WQ}sectPr"))
sect_list.extend(body_el.findall(f".//{WQ}pPr/{WQ}sectPr"))
check("document has at least one section", len(sect_list) >= 1,
      f"{len(sect_list)} section(s)")
for i, sect_pr in enumerate(sect_list):
    pg_mar = sect_pr.find(f"{WQ}pgMar")
    vals = {}
    if pg_mar is not None:
        for side in ("top", "right", "bottom", "left"):
            vals[side] = pg_mar.get(f"{WQ}{side}")
    ok = all(vals.get(side) == MARGIN for side in ("top", "right", "bottom", "left"))
    check(f"sectPr[{i}] pgMar 1in all sides", ok, str(vals))
    change = sect_pr.find(f"{WQ}sectPrChange")
    check(f"sectPr[{i}] tracked sectPrChange present", change is not None)
print()

print("== APA-05 running page number (C-22b) ==")
header_parts = sorted(n for n in names if re.match(r"word/header\d+\.xml$", n))
print("  header parts:", header_parts)
check("at least one header part exists", len(header_parts) > 0)

for ref_type in ("default", "first"):
    refs = [r for r in sect_list[0].findall(f"{WQ}headerReference")
            if r.get(f"{WQ}type") == ref_type]
    if not refs:
        print(f"  (no {ref_type} headerReference)")
        continue
    rid = refs[0].get(f"{RQ}id")
    target = None
    for rel in rels_root:
        if rel.get("Id") == rid:
            target = rel.get("Target")
    part = "word/" + target.lstrip("/") if target else None
    ok_part = part in names if part else False
    has_page = False
    if ok_part:
        hdr = etree.fromstring(z.read(part))
        has_page = any("PAGE" in f.get(f"{WQ}instr", "") for f in hdr.iter(f"{WQ}fldSimple"))
    check(f"{ref_type} header part exists", ok_part, str(part))
    check(f"{ref_type} header contains PAGE field", has_page)

# content-type overrides for every header part
ct = z.read("[Content_Types].xml").decode("utf8")
for part in header_parts:
    check(f"content-type override for {part}",
          f'PartName="/{part}"' in ct)

title_pg = sect_list[0].find(f"{WQ}titlePg") is not None
print(f"  titlePg enabled: {title_pg}")
print()

print("== APA-01/03/04 + C-27 Normal style ==")
normal = None
for st in styles_root.findall(f"{WQ}style"):
    nm = st.find(f"{WQ}name")
    if nm is not None and nm.get(f"{WQ}val") == "Normal":
        normal = st
        break
check("Normal style present", normal is not None)
if normal is not None:
    sp = normal.find(f"{WQ}pPr/{WQ}spacing")
    jc = normal.find(f"{WQ}pPr/{WQ}jc")
    ind = normal.find(f"{WQ}pPr/{WQ}ind")
    rf = normal.find(f"{WQ}rPr/{WQ}rFonts")
    check("Normal spacing line=480 (APA-01)", sp is not None and sp.get(f"{WQ}line") == SPACING_LINE,
          sp.get(f"{WQ}line") if sp is not None else None)
    check("Normal spacing after=0 (APA-01)", sp is not None and sp.get(f"{WQ}after") == SPACE_AFTER,
          sp.get(f"{WQ}after") if sp is not None else None)
    check("Normal jc=left (APA-03)", jc is not None and jc.get(f"{WQ}val") == "left",
          jc.get(f"{WQ}val") if jc is not None else None)
    check("Normal firstLine=720 (APA-04)",
          ind is not None and ind.get(f"{WQ}firstLine") == FIRST_LINE,
          ind.get(f"{WQ}firstLine") if ind is not None else None)
    check("Normal rFonts=Calibri (C-27)",
          rf is not None and rf.get(f"{WQ}ascii") == "Calibri",
          rf.get(f"{WQ}ascii") if rf is not None else None)
    check("Normal rFonts hAnsi/cs/eastAsia=Calibri (C-27)",
          rf is not None and all(rf.get(f"{WQ}{a}") == "Calibri"
                                 for a in ("hAnsi", "cs", "eastAsia")),
          {a: (rf.get(f"{WQ}{a}") if rf is not None else None)
           for a in ("hAnsi", "cs", "eastAsia")})
    check("Normal rFonts carries no theme binding (C-27)",
          rf is not None and all(rf.get(f"{WQ}{a}") is None
                                 for a in ("asciiTheme", "hAnsiTheme",
                                           "eastAsiaTheme", "cstheme")),
          "theme-bound" if rf is not None and any(
              rf.get(f"{WQ}{a}") is not None
              for a in ("asciiTheme", "hAnsiTheme",
                        "eastAsiaTheme", "cstheme")) else "explicit")
print()

print("== body paragraphs free of JUTLP overrides ==")
paras = list(doc_root.find(f"{WQ}body").iter(f"{WQ}p"))
body_checked = 0
bad_jc = bad_spacing = bad_after = 0
for p in paras:
    p_style = p.find(f"{WQ}pPr/{WQ}pStyle")
    style_val = p_style.get(f"{WQ}val") if p_style is not None else "Normal"
    if style_val != "Normal":
        continue
    text = "".join(t.text or "" for t in p.iter(f"{WQ}t")).strip()
    if not text:
        continue
    body_checked += 1
    jc = p.find(f"{WQ}pPr/{WQ}jc")
    if jc is not None and jc.get(f"{WQ}val") == "both":
        bad_jc += 1
    sp = p.find(f"{WQ}pPr/{WQ}spacing")
    if sp is not None:
        if sp.get(f"{WQ}line") not in (None, SPACING_LINE):
            bad_spacing += 1
        if sp.get(f"{WQ}after") not in (None, SPACE_AFTER):
            bad_after += 1
check(f"checked {body_checked} Normal body paragraphs", body_checked > 0)
check("no body paragraph left justified (jc=both)", bad_jc == 0, f"{bad_jc} bad")
check("no body paragraph left at JUTLP line spacing", bad_spacing == 0, f"{bad_spacing} bad")
check("no body paragraph left with non-zero after spacing", bad_after == 0, f"{bad_after} bad")
print()

print("RESULT:", "PASS" if not failures else f"FAIL ({len(failures)}: {failures})")
print("output kept at:", out)
raise SystemExit(0 if not failures else 1)
