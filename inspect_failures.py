import sys
import os

# Add 'src' directory to Python path if jutlp_validator lives inside src/
sys.path.insert(0, os.path.abspath("src"))

try:
    from jutlp_validator import validate_document
except ModuleNotFoundError:
    # If it's located elsewhere, adjust as necessary
    try:
        from jutlp_validator.validator import validate_document
    except ModuleNotFoundError:
        print("Could not import validate_document. Checking current directory layout...")
        raise

files = [
    "tests/jutlp_sample_docx_test_pack/03_front_page_issues.docx",
    "tests/jutlp_sample_docx_test_pack/05_valid_deidentified.docx",
    "tests/jutlp_sample_docx_test_pack/06_deidentified_author_leak.docx"
]

for fname in files:
    print(f"\n--- {fname} ---")
    try:
        report = validate_document(fname)
        failed = [r for r in report.get('results', []) if r['status'] == 'fail']
        print(f"Total failures: {len(failed)}")
        for f in failed:
            print(f"  FAIL [{f.get('rule_id')}]: {f.get('message')}")
    except Exception as e:
        print(f"  ERROR running validator: {e}")