"""Inspect the processed output vs the original to find comment placement issues."""
import zipfile

from lxml import etree

WQ = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
WQ14 = '{http://schemas.microsoft.com/office/word/2010/wordml}'

OUTPUT = r'C:\Users\Abdul\Downloads\rrrfrfrfrfrfrfrfinalAbstract_JUTLP_2026_CopyEdit1.docx'
ORIGINAL = r'C:\Users\Abdul\Downloads\Ashton-Hay2_JUTLP_2025.docx'


def get_comments(path):
    with zipfile.ZipFile(path) as z:
        if 'word/comments.xml' not in z.namelist():
            return []
        root = etree.fromstring(z.read('word/comments.xml'))
    results = []
    for c in root.findall(f'{WQ}comment'):
        cid = c.get(f'{WQ}id', '?')
        author = c.get(f'{WQ}author', '?')
        text = ''.join(t.text or '' for t in c.iter(f'{WQ}t'))
        results.append((int(cid) if cid.lstrip('-').isdigit() else cid, author, text))
    return sorted(results, key=lambda x: x[0])


def get_comment_anchors(path):
    """Map comment id -> paragraph text snippet where the anchor sits."""
    with zipfile.ZipFile(path) as z:
        doc = etree.fromstring(z.read('word/document.xml'))
    body = doc.find(f'{WQ}body')
    anchors = {}
    for para in body.iter(f'{WQ}p'):
        para_text = ''.join(t.text or '' for t in para.iter(f'{WQ}t')).strip()
        for el in para.iter(f'{WQ}commentRangeStart'):
            cid = el.get(f'{WQ}id', '?')
            anchors[cid] = para_text[:120]
    return anchors


def get_ref_entries(path):
    """Return numbered reference entries from the document."""
    REF_STYLES = {
        'APA7ReferenceListEntry', 'APA 7 Reference List Entry',
        'APA7 Reference List Entry', 'APAReferenceListEntry', 'Reference List Entry'
    }
    with zipfile.ZipFile(path) as z:
        doc = etree.fromstring(z.read('word/document.xml'))
    body = doc.find(f'{WQ}body')
    in_refs = False
    entries = []
    for para in body:
        if para.tag != f'{WQ}p':
            continue
        pPr = para.find(f'{WQ}pPr')
        style = ''
        if pPr is not None:
            ps = pPr.find(f'{WQ}pStyle')
            if ps is not None:
                style = ps.get(f'{WQ}val', '')
        text = ''.join(t.text or '' for t in para.findall(f'.//{WQ}t')).strip()
        if style in ('Heading1', 'Heading 1') and text.lower() in ('references', 'reference list'):
            in_refs = True
            continue
        if in_refs and style in ('Heading1', 'Heading 1'):
            break
        if in_refs and style in REF_STYLES and text:
            entries.append(text)
    return entries


print('=' * 70)
print('OUTPUT COMMENTS (rrrfr...)')
print('=' * 70)
comments = get_comments(OUTPUT)
anchors = get_comment_anchors(OUTPUT)
for cid, author, text in comments:
    anchor = anchors.get(str(cid), '[no anchor found]')
    print(f'[{cid}] {author}')
    print(f'  COMMENT: {text[:200]}')
    print(f'  ANCHOR:  {anchor[:120]}')
    print()

print()
print('=' * 70)
print('ORIGINAL REFERENCE ENTRIES (Ashton-Hay2)')
print('=' * 70)
orig_refs = get_ref_entries(ORIGINAL)
for i, r in enumerate(orig_refs, 1):
    print(f'{i:3}. {r[:150]}')

print()
print('=' * 70)
print('OUTPUT REFERENCE ENTRIES (rrrfr...)')
print('=' * 70)
out_refs = get_ref_entries(OUTPUT)
for i, r in enumerate(out_refs, 1):
    print(f'{i:3}. {r[:150]}')
