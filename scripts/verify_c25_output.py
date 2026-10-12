"""
C-25 References-block verification: runs build_edited_document on the
01_valid_identified.docx fixture and asserts the APA-12 form:

  APA010  References starts on a new page
  APA011  "References" heading is bold and centred (via Heading 1 style)
  APA012  every reference entry has left=720 hanging=720 and no firstLine
  APA-12  no direct w:jc on the References heading (the style governs)
"""
# TODO: Delete script after completion of Track C
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutil
import tempfile
import zipfile

from lxml import etree

from app.services.apa7_formatting_checks import (
    check_references_hanging_indent,
    check_references_heading_format,
    check_references_page_break,
)
from app.services.docx_format_helpers import (
    normalise_heading_text,
    paragraph_text,
    para_style_id,
)
from app.services.output_generation_samfix import build_edited_document
from app.services.reference_indent_corrections import (
    _already_correct,
    _build_style_hanging_map,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"
SRC = "tests/jutlp_sample_docx_test_pack/01_valid_identified.docx"
HANGING = "720"

failures = []


def check(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        failures.append(label)


tmp = tempfile.mkdtemp(prefix="c25_")
src = os.path.join(tmp, "in.docx")
out = os.path.join(tmp, "out.docx")
shutil.copy(SRC, src)
build_edited_document(src, out)
print("built:", out, os.path.getsize(out), "bytes")
print()

z = zipfile.ZipFile(out)
doc_root = etree.fromstring(z.read("word/document.xml"))
styles_root = etree.fromstring(z.read("word/styles.xml"))
styles_by_name = {}
for st in styles_root.findall(f"{WQ}style"):
    nm = st.find(f"{WQ}name")
    if nm is not None:
        styles_by_name[nm.get(f"{WQ}val", "").strip().lower()] = st

print("== References heading ==")
body_paras = [el for el in doc_root.find(f"{WQ}body") if el.tag == f"{WQ}p"]
heading = None
for p in body_paras:
    if normalise_heading_text(paragraph_text(p)) == "references":
        heading = p
        break
check("References heading found", heading is not None)
if heading is None:
    raise SystemExit(1)

sid = para_style_id(heading)
style_name = ""
for st in styles_root.findall(f"{WQ}style"):
    if st.get(f"{WQ}styleId") == sid:
        nm = st.find(f"{WQ}name")
        style_name = (nm.get(f"{WQ}val", "") if nm is not None else "").strip().lower()
check("References heading uses a Heading 1 style", style_name == "heading 1",
      f"{sid} -> {style_name!r}")

h1 = styles_by_name.get("heading 1")
if h1 is not None:
    jc = h1.find(f"{WQ}pPr/{WQ}jc")
    check("Heading 1 style is centred", jc is not None and jc.get(f"{WQ}val") == "center",
          jc.get(f"{WQ}val") if jc is not None else None)
    check("Heading 1 style is bold", h1.find(f"{WQ}rPr/{WQ}b") is not None)

check("References heading carries no direct w:jc",
      heading.find(f"{WQ}pPr/{WQ}jc") is None)

pb = heading.find(f"{WQ}pPr/{WQ}pageBreakBefore")
if pb is None:
    trailing = any(br.get(f"{WQ}type") == "page" for br in heading.iter(f"{WQ}br"))
else:
    trailing = True
    val = (pb.get(f"{WQ}val", "true") or "true").lower()
    check("pageBreakBefore is enabled", val not in ("false", "0", "off"), val)
check("References starts on a new page", trailing,
      "pageBreakBefore" if pb is not None else "trailing <w:br type=page>")
print()

print("== reference entries: hanging indent ==")
ref_paras = 0
bad = []
# Resolve styleId -> style NAME: reference style ids carry no spaces
# ("APA7ReferenceListEntry"), so matching on the id alone misses them.
style_name_by_id = {}
for st in styles_root.findall(f"{WQ}style"):
    sid = st.get(f"{WQ}styleId")
    nm = st.find(f"{WQ}name")
    if sid and nm is not None:
        style_name_by_id[sid] = nm.get(f"{WQ}val", "").strip().lower()

# The template supplies the hanging indent on the reference style, so entries
# inherit it rather than carrying a direct w:ind. Resolve the effective value
# through the basedOn chain exactly as the fixer does.
with zipfile.ZipFile(out) as zz:
    style_hanging = _build_style_hanging_map(zz)

for p in body_paras:
    ps = p.find(f"{WQ}pPr/{WQ}pStyle")
    sid = (ps.get(f"{WQ}val") if ps is not None else "") or ""
    sname = style_name_by_id.get(sid, sid.lower())
    text = paragraph_text(p)
    if not text:
        continue
    if "reference list entry" not in sname:
        continue
    ref_paras += 1
    p_pr = p.find(f"{WQ}pPr")
    if p_pr is None:
        p_pr = etree.Element(f"{WQ}pPr")
    if not _already_correct(p_pr, style_hanging.get(sid, "")):
        ind = p_pr.find(f"{WQ}ind")
        attrs = {k.split("}")[-1]: v for k, v in ind.attrib.items()} if ind is not None else {}
        bad.append((text[:40], attrs))
check(f"found {ref_paras} reference entries", ref_paras > 0)
check("every reference entry has hanging indent, no firstLine", not bad,
      f"{len(bad)} bad: {bad[:2]}")
print()

print("== APA010/011/012 checks on built output ==")
for label, res in (
    ("APA010 page break", check_references_page_break(out)),
    ("APA011 heading format", check_references_heading_format(out)),
    ("APA012 hanging indent", check_references_hanging_indent(out)),
):
    check(f"{label} reported", bool(res))
    if res:
        check(f"{label} passes", res[0]["status"] == "pass", res[0].get("message", ""))
print()

print("RESULT:", "PASS" if not failures else f"FAIL ({len(failures)}: {failures})")
raise SystemExit(0 if not failures else 1)