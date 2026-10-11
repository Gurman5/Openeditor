"""Tests for tools/corpus/inject.py + tools/corpus/defects/format_defects.py (K-I1).

The base is always the K-0.3a synthetic fixture.
Run:  python -m pytest tests/corpus/test_inject.py -v
"""

import json

import pytest
from docx import Document

from tools.corpus.checks.abstract import check_abstract
from tools.corpus.checks.fonts import check_fonts
from tools.corpus.checks.headings import check_headings
from tools.corpus.checks.layout import check_layout
from tools.corpus.checks.refs import check_references
from tools.corpus.docx_view import accepted_view
from tools.corpus.fixtures import build_good_docx
from tools.corpus.inject import RECIPES, InjectionError, inject, main


@pytest.fixture
def base(tmp_path):
    return build_good_docx(tmp_path / "good.docx")


def all_statuses(path) -> dict:
    """{matrix_id: status} from every check we have (preservation excluded)."""
    view = accepted_view(path)
    rows = {"APA-02": check_fonts(view)}
    for result in (check_abstract(view), check_headings(view), check_layout(view),
                   check_references(view)):
        rows.update(result)
    return {mid: row["status"] for mid, row in rows.items()}


def _changed(before: dict, after: dict) -> set:
    return {mid for mid in before if before[mid] != after[mid]}


def test_registry_comes_from_format_defects():
    from tools.corpus.defects.format_defects import FORMAT_RECIPES
    assert set(RECIPES) == {"APA-03", "APA-00"}
    assert RECIPES["APA-03"] is FORMAT_RECIPES["APA-03"]


@pytest.mark.parametrize("where", ["style", "paragraph"])
def test_justified_breaks_exactly_apa03(base, tmp_path, where):
    out = tmp_path / f"bad_{where}.docx"
    row = inject(base, ["APA-03"], out, where=where)
    before, after = all_statuses(base), all_statuses(out)
    assert after["APA-03"] == "fail"
    assert _changed(before, after) == {"APA-03"}
    assert row["defects_injected"] == ["APA-03"]
    assert row["verdicts"] == {"APA-03": "fail"}
    assert row["injections"][0]["where"] == where


def test_apa03_defaults_to_paragraph(base, tmp_path):
    row = inject(base, ["APA-03"], tmp_path / "default.docx")
    assert row["where"] is None                          # nothing requested
    assert row["injections"][0]["where"] == "paragraph"  # recipe default used


def test_where_applies_only_to_recipes_that_support_it(base, tmp_path):
    row = inject(base, ["APA-03", "APA-00"], tmp_path / "mixed.docx", where="style")
    assert [i["where"] for i in row["injections"]] == ["style", "section"]
    with pytest.raises(InjectionError, match="supports where='style'"):
        inject(base, ["APA-00"], tmp_path / "x.docx", where="style")


def test_style_justify_keeps_inheriting_heading_aligned(base, tmp_path):
    # Make Heading 2 inherit its (left) alignment from Normal, the case the
    # pinning protects: without it, Heading 2 would become justified too.
    doc = Document(base)
    doc.styles["Heading 2"].paragraph_format.alignment = None
    doc.save(base)

    out = tmp_path / "bad.docx"
    row = inject(base, ["APA-03"], out, where="style")
    assert row["injections"][0]["pinned_styles"]["Heading2"] == "left"
    after = all_statuses(out)
    assert after["APA-11"] == "pass"            # headings unaffected
    assert _changed(all_statuses(base), after) == {"APA-03"}


def test_paragraph_choice_follows_the_seed(base, tmp_path):
    def chosen(seed, name):
        row = inject(base, ["APA-03"], tmp_path / name, seed=seed, where="paragraph")
        return row["injections"][0]["paragraphs"]

    first = chosen(0, "a.docx")
    assert chosen(0, "b.docx") == first
    assert len(first) == 3
    assert any(chosen(s, f"s{s}.docx") != first for s in range(1, 10))


def test_same_inputs_give_byte_identical_output(base, tmp_path):
    a = inject(base, ["APA-03"], tmp_path / "a.docx", where="paragraph", seed=3)
    b = inject(base, ["APA-03"], tmp_path / "b.docx", where="paragraph", seed=3)
    assert a["sha256"] == b["sha256"]
    assert (tmp_path / "a.docx").read_bytes() == (tmp_path / "b.docx").read_bytes()


def test_margin_recipe_breaks_exactly_apa00(base, tmp_path):
    out = tmp_path / "margin.docx"
    row = inject(base, ["APA-00"], out)
    assert _changed(all_statuses(base), all_statuses(out)) == {"APA-00"}
    assert row["injections"][0]["twips"] == "1080"


def test_composite_breaks_both_rows(base, tmp_path):
    out = tmp_path / "composite.docx"
    row = inject(base, ["APA-03", "APA-00"], out)
    assert _changed(all_statuses(base), all_statuses(out)) == {"APA-03", "APA-00"}
    assert row["id"] == "good__APA-03+APA-00__s0"
    assert row["verdicts"] == {"APA-03": "fail", "APA-00": "fail"}
    assert [i["matrix_id"] for i in row["injections"]] == ["APA-03", "APA-00"]


# ---------------- refusals ----------------

@pytest.mark.parametrize("defects, message", [
    (["APA-99"], "no recipe"),
    (["APA-03", "APA-03"], "repeated"),
    ([], "at least one"),
])
def test_bad_requests_are_refused(base, tmp_path, defects, message):
    with pytest.raises(InjectionError, match=message):
        inject(base, defects, tmp_path / "x.docx")


def test_base_already_failing_is_refused(base, tmp_path):
    first = tmp_path / "already_bad.docx"
    inject(base, ["APA-03"], first)
    with pytest.raises(InjectionError, match="must pass APA-03"):
        inject(first, ["APA-03"], tmp_path / "again.docx")


@pytest.mark.parametrize("name", ["good.docx", "manifest.json", "MANIFEST.JSON"])
def test_dangerous_out_paths_are_refused(base, tmp_path, name):
    before = (tmp_path / "good.docx").read_bytes()
    with pytest.raises(InjectionError):
        inject(base, ["APA-03"], tmp_path / name)
    assert (tmp_path / "good.docx").read_bytes() == before


def test_only_the_output_file_is_written(base, tmp_path):
    out_dir = tmp_path / "out"
    inject(base, ["APA-03"], out_dir / "bad.docx")
    assert [p.name for p in out_dir.iterdir()] == ["bad.docx"]
    assert not list(tmp_path.rglob("manifest.json"))


def test_cli_prints_the_row(base, tmp_path, capsys):
    out = tmp_path / "cli.docx"
    assert main(["--base", str(base), "--defect", "APA-03", "--out", str(out),
                 "--where", "paragraph", "--seed", "1"]) == 0
    row = json.loads(capsys.readouterr().out)
    assert (row["id"], row["where"]) == ("good__APA-03__s1", "paragraph")
