"""
C-26 verification: runs build_edited_document on the 01_valid_identified
fixture and asserts the APA-08/09 abstract and keywords form:

  APA008  "Abstract" heading bold + centred; body unindented, Front Page Text
  APA009  Keywords label italic; keywords line indented 0.5in
  APA-20  no Practitioner Notes block anywhere (required, checked or inserted)
  APA-08  the JUTLP "lines 7-23" wording is gone from the output comments
"""
# TODO: Delete script after completion of Track C
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutil
import tempfile
import zipfile

from lxml import etree

from app.domain.canonical_jultp_template import CANONICAL_STRUCTURE
from app.services.apa7_formatting_checks import check_abstract_format, check_keywords_format
from app.services.document_analysis_services import (
    extract_abstract,
    extract_keywords,
    load_paragraphs,
)
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


tmp = tempfile.mkdtemp(prefix="c26_")
src = os.path.join(tmp, "in.docx")
out = os.path.join(tmp, "out.docx")
shutil.copy(SRC, src)
build_edited_document(src, out)
print("built:", out, os.path.getsize(out), "bytes")
print()

print("== template carries the front-matter styles (C-47) ==")
tpl = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "domain", "APA7 Base Template.docx",
)
with zipfile.ZipFile(tpl) as z:
    tstyles = etree.fromstring(z.read("word/styles.xml"))
tnames = {
    s.find(f"{WQ}name").get(f"{WQ}val")
    for s in tstyles.findall(f"{WQ}style") if s.find(f"{WQ}name") is not None
}
for want in ("Heading Front Page", "Front Page Text", "Keywords", "Keywords Label"):
    check(f"template defines {want!r}", want in tnames)
check("template has no Practitioner Notes style",
      "Practitioner Notes" not in tnames)
print()

print("== APA-08 abstract ==")
res = check_abstract_format(out)
check("APA008 reported", bool(res))
if res:
    print("   ", res[0]["message"])
    check("APA008 passes", res[0]["status"] == "pass")

z = zipfile.ZipFile(out)
root = etree.fromstring(z.read("word/document.xml"))
paras = [el for el in root.find(f"{WQ}body") if el.tag == f"{WQ}p"]
with zipfile.ZipFile(src) as zs:
    src_root = etree.fromstring(zs.read("word/document.xml"))
src_paras = [el for el in src_root.find(f"{WQ}body") if el.tag == f"{WQ}p"]


def _text(p):
    return "".join(t.text or "" for t in p.iter(f"{WQ}t")).strip()


abstract_heading = next(
    (p for p in paras if _text(p).lower() == "abstract"), None
)
check("Abstract heading present in output", abstract_heading is not None)
if abstract_heading is not None:
    ps = abstract_heading.find(f"{WQ}pPr/{WQ}pStyle")
    print("    style:", ps.get(f"{WQ}val") if ps is not None else None)
print()

print("== APA-09 keywords ==")
res = check_keywords_format(out)
check("APA009 reported", bool(res))
if res:
    print("   ", res[0]["message"])
    check("APA009 passes", res[0]["status"] == "pass")
print()

print("== APA-20 Practitioner Notes removed ==")
front = CANONICAL_STRUCTURE["front_page"]
check("no practitioner_notes_count in canonical structure",
      "practitioner_notes_count" not in front)
for gone in ("practitioner_notes_heading", "practitioner_notes_style"):
    check(f"no {gone} in canonical structure", gone not in front)
comments = ""
if "word/comments.xml" in z.namelist():
    croot = etree.fromstring(z.read("word/comments.xml"))
    comments = "\n".join(
        "".join(t.text or "" for t in c.iter(f"{WQ}t"))
        for c in croot.findall(f"{WQ}comment")
    )
# The app no longer REQUIRES, CHECKS, REPORTS or INSERTS the block: that is
# what APA-20 covers. Content the author already wrote is left untouched —
# silently deleting an author's paragraphs would be destructive, so the
# fixture's Practitioner Notes block is expected to survive verbatim.
check("no Practitioner Notes in comments",
      "practitioner notes" not in comments.lower(),
      "found" if "practitioner notes" in comments.lower() else "clean")
check("no JUTLP line-region wording in comments",
      "lines 7" not in comments and "7 to 23" not in comments)
src_block = [p for p in src_paras if "practitioner" in _text(p).lower()]
out_block = [p for p in paras if "practitioner" in _text(p).lower()]
check("author-supplied Practitioner Notes left intact (not silently deleted)",
      len(out_block) == len(src_block),
      f"in={len(src_block)} out={len(out_block)}")
print()

print("== abstract measurement ==")
ab = extract_abstract(load_paragraphs(out))
check("abstract found", ab["found"] is True, str(ab["word_count"]) + " words")
check("abstract carries no line_count payload", "line_count" not in ab)
print()

print("RESULT:", "PASS" if not failures else f"FAIL ({len(failures)}: {failures})")
raise SystemExit(0 if not failures else 1)