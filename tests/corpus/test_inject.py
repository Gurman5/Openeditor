"""Tests for tools/corpus/inject.py + tools/corpus/defects/format_defects.py (K-I1).

The base is always the K-0.3a synthetic fixture.
Run:  python -m pytest tests/corpus/test_inject.py -v
"""

import copy
import json

import pytest
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_BREAK

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
    assert set(RECIPES) == {"APA-03", "APA-00", "APA-01", "APA-04", "APA-02a", "APA-02b",
                            "APA-05", "APA-11a", "APA-11b", "APA-08a", "APA-08b", "APA-08c",
                            "APA-12a", "APA-12b", "APA-12c", "APA-18a"}
    assert RECIPES["APA-03"] is FORMAT_RECIPES["APA-03"]
    assert {RECIPES[r].matrix_id for r in ("APA-02a", "APA-02b")} == {"APA-02"}


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


# ---------------- K-I2 formatting recipes ----------------

@pytest.mark.parametrize("recipe, where, row", [
    ("APA-01", "paragraph", "APA-01"),
    ("APA-01", "style", "APA-01"),
    ("APA-04", "paragraph", "APA-04"),
    ("APA-04", "style", "APA-04"),
    ("APA-02a", "paragraph", "APA-02"),
    ("APA-02a", "style", "APA-02"),
    ("APA-02b", "paragraph", "APA-02"),
    ("APA-02b", "style", "APA-02"),
    ("APA-05", None, "APA-05"),
])
def test_k_i2_recipe_breaks_exactly_its_row(base, tmp_path, recipe, where, row):
    out = tmp_path / f"{recipe}_{where}.docx"
    result = inject(base, [recipe], out, where=where)
    assert _changed(all_statuses(base), all_statuses(out)) == {row}
    assert result["defects_injected"] == [row]
    assert result["injections"][0]["recipe_id"] == recipe
    assert result["injections"][0]["where"] == (where or RECIPES[recipe].default_where)


def test_spacing_style_mode_pins_reference_entries(base, tmp_path):
    out = tmp_path / "spacing_style.docx"
    row = inject(base, ["APA-01"], out, where="style")
    assert len(row["injections"][0]["pinned_paragraphs"]) == 3      # the 3 references
    assert all_statuses(out)["APA-12"] == "pass"


def test_indent_style_mode_pins_keywords_and_run_in_headings(base, tmp_path):
    # Add a Level 4 run-in heading so the run-in pinning is exercised too.
    doc = Document(base)
    anchor = next(p for p in doc.paragraphs if p.text == "Participants")
    para = anchor.insert_paragraph_before("")
    anchor._p.addnext(para._p)                     # move it to just after "Participants"
    para.add_run("Recruitment Method.").bold = True
    para.add_run(" Students were invited by email.")
    doc.save(base)
    before = all_statuses(base)
    assert before["APA-11"] == "pass"

    out = tmp_path / "indent_style.docx"
    row = inject(base, ["APA-04"], out, where="style")
    assert len(row["injections"][0]["pinned_paragraphs"]) == 2     # keywords + run-in
    after = all_statuses(out)
    assert (after["APA-09"], after["APA-11"]) == ("pass", "pass")
    assert _changed(before, after) == {"APA-04"}


def test_page_number_recipe_strips_both_field_forms(base, tmp_path):
    row = inject(base, ["APA-05"], tmp_path / "nopage.docx")
    assert row["injections"][0]["fields_removed"] == 2              # fldSimple + fldChar
    assert len(row["injections"][0]["parts"]) == 2


def test_two_recipes_for_one_row_are_refused(base, tmp_path):
    with pytest.raises(InjectionError, match="one defect per matrix row"):
        inject(base, ["APA-02a", "APA-02b"], tmp_path / "x.docx")


def test_k_i2_composite_breaks_exactly_those_rows(base, tmp_path):
    out = tmp_path / "composite_k_i2.docx"
    row = inject(base, ["APA-01", "APA-04", "APA-05"], out)
    assert _changed(all_statuses(base), all_statuses(out)) == {"APA-01", "APA-04", "APA-05"}
    assert row["verdicts"] == {"APA-01": "fail", "APA-04": "fail", "APA-05": "fail"}


def test_header_edit_is_byte_identical(base, tmp_path):
    a = inject(base, ["APA-05", "APA-02b"], tmp_path / "a.docx", seed=4)
    b = inject(base, ["APA-05", "APA-02b"], tmp_path / "b.docx", seed=4)
    assert a["sha256"] == b["sha256"]


# ---------------- K-I3a structure recipes ----------------

@pytest.mark.parametrize("recipe, row", [
    ("APA-11a", "APA-11"),
    ("APA-11b", "APA-11"),
    ("APA-08a", "APA-08"),
    ("APA-08b", "APA-08"),
])
def test_k_i3a_recipe_breaks_exactly_its_row(base, tmp_path, recipe, row):
    out = tmp_path / f"{recipe}.docx"
    result = inject(base, [recipe], out)
    after = all_statuses(out)
    assert after[row] == "fail"
    assert _changed(all_statuses(base), after) == {row}
    assert result["verdicts"] == {row: "fail"}
    assert result["check_options"] == {}


def test_numbered_headings_recipe(base, tmp_path):
    out = tmp_path / "numbered.docx"
    row = inject(base, ["APA-11a"], out)
    assert [h["text"] for h in row["injections"][0]["headings"]] == [
        "1. Method", "2. Results", "3. Discussion"]
    problems = [p for h in check_headings(accepted_view(out))["APA-11"]["headings"]
                for p in h["problems"]]
    assert problems == ['heading should not be numbered (typed "1.")',
                        'heading should not be numbered (typed "2.")',
                        'heading should not be numbered (typed "3.")']


def test_long_abstract_recipe_goes_over_250(base, tmp_path):
    out = tmp_path / "long.docx"
    row = inject(base, ["APA-08a"], out)
    words = check_abstract(accepted_view(out))["APA-08"]["subchecks"]["word_count"]["words"]
    assert words == row["injections"][0]["words_after"]
    assert words > 260


def test_missing_abstract_declares_its_side_effect(base, tmp_path):
    out = tmp_path / "noabstract.docx"
    row = inject(base, ["APA-08c"], out)
    assert row["verdicts"] == {"APA-08": "fail", "APA-09": "na"}
    assert row["check_options"] == {"APA-08": {"require_abstract": True}}
    # Default grading says na; grading with the row's check_options says fail.
    assert check_abstract(accepted_view(out))["APA-08"]["status"] == "na"
    assert check_abstract(accepted_view(out), require_abstract=True)["APA-08"]["status"] == "fail"
    # Nothing else changes besides the two declared rows.
    assert _changed(all_statuses(base), all_statuses(out)) == {"APA-08", "APA-09"}


# ---------------- K-I3b reference recipes ----------------

@pytest.mark.parametrize("recipe, row", [
    ("APA-12a", "APA-12"),
    ("APA-12b", "APA-12"),
    ("APA-12c", "APA-12"),
    ("APA-18a", "APA-18"),
])
def test_k_i3b_recipe_breaks_exactly_its_row(base, tmp_path, recipe, row):
    out = tmp_path / f"{recipe}.docx"
    result = inject(base, [recipe], out)
    after = all_statuses(out)
    assert after[row] == "fail"
    assert _changed(all_statuses(base), after) == {row}
    assert result["verdicts"] == {row: "fail"}


def _references_label(doc):
    return next(p for p in doc.paragraphs if p.text == "References")


def _paragraph_before(doc, para):
    elements = [p._p for p in doc.paragraphs]
    return doc.paragraphs[elements.index(para._p) - 1]


def _break_in_previous_run(doc):
    label = _references_label(doc)
    label.paragraph_format.page_break_before = None
    _paragraph_before(doc, label).add_run().add_break(WD_BREAK.PAGE)


def _break_from_style(doc):
    style = doc.styles.add_style("NewPageLabel", WD_STYLE_TYPE.PARAGRAPH)
    style.base_style = doc.styles["Normal"]
    style.paragraph_format.page_break_before = True
    label = _references_label(doc)
    label.style = style
    label.paragraph_format.page_break_before = None


def _section_break_before(doc):
    label = _references_label(doc)
    label.paragraph_format.page_break_before = None
    sect = copy.deepcopy(doc.sections[-1]._sectPr)        # a full, valid section
    _paragraph_before(doc, label)._p.get_or_add_pPr().append(sect)


def _two_breaks(doc):
    _paragraph_before(doc, _references_label(doc)).add_run().add_break(WD_BREAK.PAGE)


@pytest.mark.parametrize("setup, removed", [
    (_break_in_previous_run, ["page break in run"]),
    (_break_from_style, ["pageBreakBefore from style:NewPageLabel switched off"]),
    (_section_break_before, ["section break made continuous"]),
    (_two_breaks, ["direct pageBreakBefore removed", "page break in run"]),
])
def test_same_page_recipe_removes_every_kind_of_break(base, tmp_path, setup, removed):
    doc = Document(base)
    setup(doc)
    doc.save(base)
    before = all_statuses(base)
    assert before["APA-12"] == "pass"

    out = tmp_path / "same_page.docx"
    row = inject(base, ["APA-12a"], out)
    assert [r["what"] for r in row["injections"][0]["removed"]] == removed
    new_page = check_references(accepted_view(out))["APA-12"]["subchecks"]["new_page"]
    assert new_page["status"] == "fail"
    assert _changed(before, all_statuses(out)) == {"APA-12"}


def test_out_of_order_recipe_moves_first_entry_last(base, tmp_path):
    out = tmp_path / "order.docx"
    row = inject(base, ["APA-12c"], out)
    assert row["injections"][0]["moved_entry"].startswith("Adams")
    problems = check_references(accepted_view(out))["APA-12"]["subchecks"]["alphabetical"]["problems"]
    assert problems[0]["keys"] == ["davis", "adams"]


def test_old_doi_recipe_follows_the_seed(base, tmp_path):
    rows = [inject(base, ["APA-18a"], tmp_path / f"doi{s}.docx", seed=s) for s in range(6)]
    paragraphs = {r["injections"][0]["paragraph"] for r in rows}
    assert len(paragraphs) > 1                                   # different seeds, different DOIs
    sub = check_references(accepted_view(tmp_path / "doi0.docx"))["APA-18"]["subchecks"]
    assert [p["reason"] for p in sub["https_doi_org"]["problems"]] == ["dx.doi.org"]


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
