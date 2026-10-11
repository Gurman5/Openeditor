"""
Runs build_edited_document on the 01_valid_identified.docx fixture, 
then asserts the output got Normal 480/left and that _ensure_template_styles_available injects 
Calibri Normal from the new template on request. Takes ~a minute (full build pass chain).

"""
#TODO: Delete script after completion of Track C
import os
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

tmp = tempfile.mkdtemp(prefix="c47_")
src = os.path.join(tmp, "in.docx")
out = os.path.join(tmp, "out.docx")
shutil.copy(SRC, src)
build_edited_document(src, out)
print("built:", out, os.path.getsize(out), "bytes")

z = zipfile.ZipFile(out)
root = etree.fromstring(z.read("word/document.xml"))
sroot = etree.fromstring(z.read("word/styles.xml"))

normal = None
for st in sroot.findall(f"{WQ}style"):
    nm = st.find(f"{WQ}name")
    if nm is not None and nm.get(f"{WQ}val") == "Normal":
        normal = st
        break
sp = normal.find(f"{WQ}pPr/{WQ}spacing") if normal is not None else None
jc = normal.find(f"{WQ}pPr/{WQ}jc") if normal is not None else None
print("Normal spacing line:", sp.get(f"{WQ}line") if sp is not None else None)
print("Normal jc:", jc.get(f"{WQ}val") if jc is not None else None)

# C-47 mechanism check (isolated from C-27's Arial pin): the template must
# supply Calibri Normal when requested with replace_existing=True.
from app.services.output_generation_samfix import _ensure_template_styles_available
scratch = os.path.join(tmp, "scratch.docx")
shutil.copy(src, scratch)
applied = _ensure_template_styles_available(scratch, scratch, ["Normal"], replace_existing=True)
zs = zipfile.ZipFile(scratch)
sroot2 = etree.fromstring(zs.read("word/styles.xml"))
n2 = None
for st in sroot2.findall(f"{WQ}style"):
    nm = st.find(f"{WQ}name")
    if nm is not None and nm.get(f"{WQ}val") == "Normal":
        n2 = st
        break
rf2 = n2.find(f"{WQ}rPr/{WQ}rFonts") if n2 is not None else None
print("template-supplied Normal applied:", applied)
print("template-supplied Normal rFonts ascii:", rf2.get(f"{WQ}ascii") if rf2 is not None else None)

ok = (
    sp is not None and sp.get(f"{WQ}line") == "480"
    and jc is not None and jc.get(f"{WQ}val") == "left"
    and applied is True
    and rf2 is not None and rf2.get(f"{WQ}ascii") == "Calibri"
)
print("RESULT:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
