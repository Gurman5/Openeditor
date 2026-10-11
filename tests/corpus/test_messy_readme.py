"""K-R2 guard: tests/corpus/messy/ holds only its README, which names the
excluded JUTLP pack and every file in it.
Run:  python -m pytest tests/corpus/test_messy_readme.py -v
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MESSY = ROOT / "tests" / "corpus" / "messy"
PACK = ROOT / "tests" / "jutlp_sample_docx_test_pack"


def test_messy_folder_holds_only_the_readme():
    assert [p.name for p in MESSY.iterdir()] == ["README.md"]


def test_no_docx_anywhere_under_messy():
    assert not list(MESSY.rglob("*.docx"))


def test_readme_names_the_excluded_pack_and_its_files():
    readme = (MESSY / "README.md").read_text(encoding="utf-8")
    assert "tests/jutlp_sample_docx_test_pack/" in readme
    for docx in sorted(PACK.glob("*.docx")):
        assert docx.name in readme, f"{docx.name} is in the pack but not in the README"
