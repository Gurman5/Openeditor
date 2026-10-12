"""
C-22 direct-formatting path test.

The 01_valid_identified fixture carries no direct paragraph formatting, so the
C-22a/C-22b check + apply changes (_body_*_ok and
_apply_tracked_body_paragraph_format) never fire for it. This test injects
explicit JUTLP formatting onto one body paragraph -- jc=both, line=276,
after=120, firstLine=0 -- runs the full build chain, and asserts the output
carries APA direct formatting instead.
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
SRC = "tests/jutlp_sample_docx_test_pack/01_valid_identified.docx"

failures = []


def check(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        failures.append(label)


tmp = tempfile.mkdtemp(prefix="c22direct_")
src = os.path.join(tmp, "in.docx")
out = os.path.join(tmp, "out.docx")
shutil.copy(SRC, src)

# --- inject JUTLP direct formatting onto the first body (Normal) paragraph ---
with zipfile.ZipFile(src, "r") as z:
    names = z.namelist()
    parts = {i.filename: z.read(i.filename) for i in z.infolist()}

root = etree.fromstring(parts["word/document.xml"])
body = root.find(f"{WQ}body")

target = None
for p in body.findall(f"{WQ}p"):
    ps = p.find(f"{WQ}pPr/{WQ}pStyle")
    style = ps.get(f"{WQ}val") if ps is not None else "Normal"
    text = "".join(t.text or "" for t in p.iter(f"{WQ}t")).strip()
    if style == "Normal" and text.startswith("This is the body text content for the Intro"):
        target = p
        break

check("found Introduction body paragraph to inject formatting into", target is not None)
if target is None:
    raise SystemExit(1)

p_pr = target.find(f"{WQ}pPr")
if p_pr is None:
    p_pr = etree.Element(f"{WQ}pPr")
    target.insert(0, p_pr)

jc = etree.SubElement(p_pr, f"{WQ}jc")
jc.set(f"{WQ}val", "both")

spacing = etree.SubElement(p_pr, f"{WQ}spacing")
spacing.set(f"{WQ}line", "276")
spacing.set(f"{WQ}lineRule", "auto")
spacing.set(f"{WQ}after", "120")

ind = etree.SubElement(p_pr, f"{WQ}ind")
ind.set(f"{WQ}left", "0")
ind.set(f"{WQ}firstLine", "0")

parts["word/document.xml"] = etree.tostring(
    root, xml_declaration=True, encoding="UTF-8", standalone=True
)
with zipfile.ZipFile(src, "w", zipfile.ZIP_DEFLATED) as zout:
    for name, data in parts.items():
        zout.writestr(name, data)
print("injected JUTLP formatting (jc=both, line=276, after=120, firstLine=0)")
print()

# --- run the full build chain ---
build_edited_document(src, out)
print("built:", os.path.getsize(out), "bytes")
print()

# --- assert APA direct formatting replaced it ---
z = zipfile.ZipFile(out)
out_root = etree.fromstring(z.read("word/document.xml"))
out_body = out_root.find(f"{WQ}body")

found = None
for p in out_body.findall(f"{WQ}p"):
    text = "".join(t.text or "" for t in p.iter(f"{WQ}t")).strip()
    if text.startswith("This is the body text content for the Intro"):
        found = p
        break

check("target paragraph still present in output", found is not None)
if found is not None:
    p_pr = found.find(f"{WQ}pPr")
    jc = p_pr.find(f"{WQ}jc") if p_pr is not None else None
    sp = p_pr.find(f"{WQ}spacing") if p_pr is not None else None
    ind = p_pr.find(f"{WQ}ind") if p_pr is not None else None
    change = p_pr.find(f"{WQ}pPrChange") if p_pr is not None else None

    check("jc corrected to left (APA-03)",
          jc is not None and jc.get(f"{WQ}val") == "left",
          jc.get(f"{WQ}val") if jc is not None else None)
    check("line spacing corrected to 480 (APA-01)",
          sp is not None and sp.get(f"{WQ}line") == "480",
          sp.get(f"{WQ}line") if sp is not None else None)
    check("after spacing corrected to 0 (APA-01)",
          sp is not None and sp.get(f"{WQ}after") == "0",
          sp.get(f"{WQ}after") if sp is not None else None)
    check("first-line indent corrected to 720 (APA-04)",
          ind is not None and ind.get(f"{WQ}firstLine") == "720",
          ind.get(f"{WQ}firstLine") if ind is not None else None)
    check("tracked pPrChange recorded on the paragraph", change is not None)

# --- references area must stay free of firstLine=720 body fixes ---
ref_p = None
for p in out_body.findall(f"{WQ}p"):
    ps = p.find(f"{WQ}pPr/{WQ}pStyle")
    if ps is not None and "Reference" in (ps.get(f"{WQ}val") or ""):
        ref_p = p
        break
if ref_p is not None:
    ind = ref_p.find(f"{WQ}pPr/{WQ}ind")
    ind_attrs = {k.split("}")[-1]: v for k, v in ind.attrib.items()} if ind is not None else {}
    check("reference entry keeps C-25 hanging indent (no firstLine body fix)",
          "firstLine" not in ind_attrs, str(ind_attrs))
else:
    print("  (no reference entry found to check)")

print()
print("RESULT:", "PASS" if not failures else f"FAIL ({len(failures)}: {failures})")
raise SystemExit(0 if not failures else 1)
