import re
import sys

sys.path.insert(0, r'c:\Users\Abdul\copy-editor-ai')
from app.services.reference_checker import extract_references

refs = extract_references(r'C:\Users\Abdul\Downloads\testAuthor_JUTLP_2026_CopyEdit1.docx')
print(f'Total references: {len(refs)}')

doi_re = re.compile(r'10\.\d{4,9}/[^\s,;>"\']+')
doi_url_re = re.compile(r'https?://doi\.org/', re.IGNORECASE)
doi_count = len([r for r in refs if doi_re.search(r)])
doi_url_count = len([r for r in refs if doi_url_re.search(r)])
print(f'References with DOIs: {doi_count}')
print(f'References with DOI URLs: {doi_url_count}')
print(f'References without any DOI: {len(refs) - doi_count}')
