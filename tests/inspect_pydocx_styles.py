"""Check what python-docx reports for paragraph styles vs raw XML style IDs."""
import zipfile

from docx import Document
from lxml import etree

WQ = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

path = r'C:\Users\Abdul\Downloads\Ashton-Hay2_JUTLP_2025.docx'

# python-docx view
doc = Document(path)
print('=== python-docx para styles (first 90 paragraphs) ===')
for i, p in enumerate(doc.paragraphs):
    style_name = p.style.name if p.style else 'NO_STYLE'
    text = (p.text or '').strip()[:80]
    if text or style_name not in ('Normal', ''):
        print(f'{i:3}  [{style_name:35}] {text}')
    if i > 90:
        break

# Cross-check raw XML
with zipfile.ZipFile(path) as z:
    doc_xml = etree.fromstring(z.read('word/document.xml'))
body = doc_xml.find(f'{WQ}body')
print()
print('=== Raw XML style vals for heading-like paragraphs ===')
for i, para in enumerate(body):
    if para.tag != f'{WQ}p':
        continue
    pPr = para.find(f'{WQ}pPr')
    style_val = ''
    if pPr is not None:
        ps = pPr.find(f'{WQ}pStyle')
        if ps is not None:
            style_val = ps.get(f'{WQ}val', '')
    text = ''.join(t.text or '' for t in para.findall(f'.//{WQ}t')).strip()
    if 'heading' in style_val.lower() or text.lower() in ('references', 'introduction', 'conclusion', 'acknowledgments', 'method', 'results', 'discussion'):
        print(f'{i:3}  xml_val=[{style_val}]  text=[{text[:60]}]')
    if i > 200:
        break
