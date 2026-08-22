"""Compare reference entry detection between original and output documents.
Diagnoses comment anchoring misalignment."""
import re
import zipfile

from lxml import etree

WQ = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
REF_STYLES = {
    'APA7ReferenceListEntry', 'APA 7 Reference List Entry',
    'APA7 Reference List Entry', 'APAReferenceListEntry', 'Reference List Entry'
}
YEAR_RE = re.compile(r'\(\d{4}[a-z]?\)')

ORIGINAL = r'C:\Users\Abdul\Downloads\Ashton-Hay2_JUTLP_2025.docx'
OUTPUT   = r'C:\Users\Abdul\Downloads\rrrfrfrfrfrfrfrfinalAbstract_JUTLP_2026_CopyEdit1.docx'


def get_all_para_info(path):
    """Return info on every paragraph: (index, style, text[:120])"""
    with zipfile.ZipFile(path) as z:
        doc = etree.fromstring(z.read('word/document.xml'))
    body = doc.find(f'{WQ}body')
    result = []
    for i, para in enumerate(body):
        if para.tag != f'{WQ}p':
            continue
        pPr = para.find(f'{WQ}pPr')
        style = ''
        if pPr is not None:
            ps = pPr.find(f'{WQ}pStyle')
            if ps is not None:
                style = ps.get(f'{WQ}val', '')
        text = ''.join(t.text or '' for t in para.findall(f'.//{WQ}t')).strip()
        result.append((i, style, text))
    return result


def find_refs_section(paras):
    """Find start index of References section and return (start, end) para indices."""
    start = end = None
    for i, (idx, style, text) in enumerate(paras):
        if style in ('Heading1', 'Heading 1') and text.lower() in ('references', 'reference list'):
            start = i
        elif start is not None and style in ('Heading1', 'Heading 1') and i > start:
            end = i
            break
    return start, end


def select_ref_entries(paras, start, end):
    """Mirror _select_reference_entries: prefer styled, fallback to heuristic."""
    window = paras[start+1:end] if end else paras[start+1:]
    styled = [(i, idx, s, t) for i, (idx, s, t) in enumerate(window) if s in REF_STYLES]
    if styled:
        return [(i+1, idx, s, t) for i, idx, s, t in styled]  # 1-based entry num
    # Fallback
    return [
        (i+1, idx, s, t)
        for i, (idx, s, t) in enumerate(window)
        if len(t) > 20 and YEAR_RE.search(t)
    ]


print('=' * 70)
print('ORIGINAL DOCUMENT — paragraphs around References section')
print('=' * 70)
orig_paras = get_all_para_info(ORIGINAL)
o_start, o_end = find_refs_section(orig_paras)
print(f'References heading at para list index {o_start}, end at {o_end}')
if o_start:
    print('\nParagraphs BEFORE References (last 10):')
    for idx, style, text in orig_paras[max(0,o_start-10):o_start]:
        print(f'  [{style:30}] {text[:100]}')
    print('\nFirst 15 paragraphs IN References section:')
    window_end = o_end if o_end else o_start + 20
    for idx, style, text in orig_paras[o_start:window_end][:16]:
        print(f'  [{style:40}] {text[:100]}')

print()
print('Reference entries as checker would see them (original):')
orig_entries = select_ref_entries(orig_paras, o_start, o_end)
for n, idx, style, text in orig_entries[:20]:
    print(f'  {n:3}. [{style:30}] {text[:90]}')

print()
print('=' * 70)
print('OUTPUT DOCUMENT — reference entries')
print('=' * 70)
out_paras = get_all_para_info(OUTPUT)
out_start, out_end = find_refs_section(out_paras)
out_entries = select_ref_entries(out_paras, out_start, out_end)
print(f'Total output entries: {len(out_entries)}')
for n, idx, style, text in out_entries:
    print(f'  {n:3}. {text[:120]}')

print()
print('=' * 70)
print('DIFF: entries only in original numbering vs output numbering')
print('=' * 70)
orig_texts = {n: t for n, _, _, t in orig_entries}
out_texts  = {n: t for n, _, _, t in out_entries}
print(f'Original count: {len(orig_entries)}, Output count: {len(out_entries)}')

# Check for duplicates in output
seen = {}
for n, idx, s, t in out_entries:
    norm = re.sub(r'\s+', ' ', t[:60].lower())
    if norm in seen:
        print(f'DUPLICATE: Entry {n} matches Entry {seen[norm]}: {t[:80]}')
    seen[norm] = n
