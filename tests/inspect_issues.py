import re
import zipfile

from lxml import etree

WQ = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
REF_STYLES = {
    'APA7ReferenceListEntry', 'APA 7 Reference List Entry',
    'APA7 Reference List Entry', 'APAReferenceListEntry', 'Reference List Entry'
}

path = r'C:\Users\Abdul\Downloads\finalq123Author_JUTLP_2026_CopyEdit1.docx'
with zipfile.ZipFile(path) as z:
    doc = etree.fromstring(z.read('word/document.xml'))

body = doc.find(f'{WQ}body')
in_refs = False
entry_num = 0

for para in body:
    if para.tag != f'{WQ}p':
        continue
    pPr = para.find(f'{WQ}pPr')
    style = ''
    if pPr is not None:
        ps = pPr.find(f'{WQ}pStyle')
        if ps is not None:
            style = ps.get(f'{WQ}val', '')
    all_text = ''.join(t.text or '' for t in para.findall(f'.//{WQ}t')).strip()
    if style in ('Heading1', 'Heading 1') and all_text.lower() in ('references', 'reference list'):
        in_refs = True
        continue
    if in_refs and style in ('Heading1', 'Heading 1'):
        break
    if not in_refs or style not in REF_STYLES:
        continue
    entry_num += 1

    has_del = para.find(f'.//{WQ}del') is not None
    has_ins = para.find(f'.//{WQ}ins') is not None
    if not (has_del or has_ins):
        continue

    del_text = ''.join(t.text or '' for t in para.findall(f'.//{WQ}delText')).strip()
    ins_parts = []
    for el in para.iter(f'{WQ}t'):
        in_del = False
        parent = el.getparent()
        while parent is not None:
            if parent.tag == f'{WQ}del':
                in_del = True
                break
            parent = parent.getparent()
        if not in_del:
            ins_parts.append(el.text or '')
    ins_text = ''.join(ins_parts).strip()

    issues = []
    if '&amp;' in ins_text or '&Amp;' in ins_text or '&lt;' in ins_text or '&gt;' in ins_text:
        issues.append('HTML_ENTITY')
    doi_del = re.search(r'10\.\d{4,}/\S+', del_text)
    doi_ins = re.search(r'10\.\d{4,}/\S+', ins_text)
    if doi_del and doi_ins and doi_del.group().rstrip('.') != doi_ins.group().rstrip('.'):
        issues.append('DOI_CHANGED')
    year_del = re.search(r'\((\d{4})', del_text)
    year_ins = re.search(r'\((\d{4})', ins_text)
    if year_del and year_ins and abs(int(year_del.group(1)) - int(year_ins.group(1))) > 2:
        issues.append(f'YEAR_MISMATCH:{year_del.group(1)}->{year_ins.group(1)}')
    if ins_text.startswith(',') or '& .' in ins_text or ', & .' in ins_text:
        issues.append('MALFORMED_APA')
    if re.search(r'\.\s*https?://', ins_text) is None and 'https://' in ins_text:
        issues.append('NO_SPACE_BEFORE_URL')

    if issues:
        print(f'Entry {entry_num} [{", ".join(issues)}]')
        print(f'  DEL: {repr(del_text[:130])}')
        print(f'  INS: {repr(ins_text[:130])}')
        print()
