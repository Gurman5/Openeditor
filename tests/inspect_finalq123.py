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

    # Collect ins text (w:t not inside w:del)
    ins_parts = []
    skip = False
    for el in para.iter():
        if el.tag == f'{WQ}del':
            skip = True
        if skip and el.tag == f'{WQ}del':
            # we'll stop skipping after we've processed the del subtree
            pass
        if not skip and el.tag == f'{WQ}t':
            ins_parts.append(el.text or '')
        if el.tag == f'{WQ}del':
            skip = False  # reset after del (iter goes depth-first so this is wrong)

    # Simpler: collect all w:t not under w:del
    ins_parts = []
    for el in para.iter(f'{WQ}t'):
        # Check if any ancestor is w:del
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

    print(f'Entry {entry_num}:')
    print(f'  DEL: {repr(del_text[:250])}')
    print(f'  INS: {repr(ins_text[:250])}')
    print()
