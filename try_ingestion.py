from pathlib import Path
from app.services.document_injestion_services import read_docx

for filename in ["tmp_banner_input.docx", "tmp_textbox_input.docx", "tmp_textbox_output.docx"]:
    print(f"\n{'='*50}")
    print(f"FILE: {filename}")
    print('='*50)
    doc = read_docx(Path(filename))
    print(f"Number of paragraphs: {len(doc.paragraphs)}")
    for i, para in enumerate(doc.paragraphs):
        print(f"{i}: '{para.text}'")

print(f"\n{'='*50}")
print("XML CHECK: tmp_textbox_input.docx")
print('='*50)
doc = read_docx(Path("tmp_textbox_input.docx"))
xml_str = doc.element.xml
if "Institution" in xml_str:
    print("Text box content IS in the raw XML — confirmed it's just not being read by .paragraphs")
else:
    print("Not found in XML at all — different explanation needed")

import hashlib

def file_hash(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

print(f"\n{'='*50}")
print("FILE COMPARISON")
print('='*50)
print(f"banner_input hash:   {file_hash('tmp_banner_input.docx')}")
print(f"textbox_input hash:  {file_hash('tmp_textbox_input.docx')}")
print(f"textbox_output hash: {file_hash('tmp_textbox_output.docx')}")



print(f"\n{'='*50}")
print("FULL XML LENGTH CHECK")
print('='*50)
doc = read_docx(Path("tmp_banner_input.docx"))
banner_xml = doc.element.xml
doc2 = read_docx(Path("tmp_textbox_input.docx"))
textbox_xml = doc2.element.xml
print(f"banner_input XML length: {len(banner_xml)}")
print(f"textbox_input XML length: {len(textbox_xml)}")
print(f"Are they identical? {banner_xml == textbox_xml}")

import zipfile

print(f"\n{'='*50}")
print("ZIP CONTENTS COMPARISON")
print('='*50)

with zipfile.ZipFile('tmp_banner_input.docx') as z:
    banner_files = set(z.namelist())

with zipfile.ZipFile('tmp_textbox_input.docx') as z:
    textbox_files = set(z.namelist())

print("Files only in banner_input:", banner_files - textbox_files)
print("Files only in textbox_input:", textbox_files - banner_files)
print("\nAll files in textbox_input:")
for name in sorted(textbox_files):
    print(f"  {name}")