"""C-27 evidence tests: the font sweep normalises every layer to Calibri.

Covers what the old Arial-only run pass never did: headers/footers,
footnotes/endnotes/comments parts, style-level fonts, docDefaults (the
Cambria-via-theme leak), theme-bound runs, character-style inheritance —
and that symbol typefaces are never rewritten.
"""

import shutil
import zipfile

import pytest
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt
from lxml import etree
from unittest.mock import patch

from app.domain import reporting_ownership as ro
from app.services import output_generation_samfix as S
from app.services.apa7_formatting_checks import check_fonts
from app.services.apa7_validator import validate as apa_validate
from app.services.run_font_corrections import (
    _is_text_part,
    apply_run_font_corrections,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

SRC = "tests/jutlp_sample_docx_test_pack/01_valid_identified.docx"


def _run_fonts(part_root):
    """Map run text -> ascii font for every text run in a part."""
    out = {}
    for r in part_root.iter(f"{WQ}r"):
        t = r.find(f"{WQ}t")
        if t is None or not (t.text or "").strip():
            continue
        rpr = r.find(f"{WQ}rPr")
        rf = rpr.find(f"{WQ}rFonts") if rpr is not None else None
        out[t.text.strip()] = rf.get(f"{WQ}ascii") if rf is not None else None
    return out


def _inject_text_part(src, part_name, rel_type, content_type, inner_xml):
    """Add a header/footer/footnote/endnote/comment part to a docx copy."""
    with zipfile.ZipFile(str(src)) as z:
        members = {i.filename: z.read(i.filename) for i in z.infolist()}
    tag = {
        "word/footnotes.xml": "footnotes",
        "word/endnotes.xml": "endnotes",
        "word/comments.xml": "comments",
    }[part_name]
    part_el = etree.Element(f"{WQ}{tag}", nsmap={"w": W})
    # Re-parse the raw inner xml directly as children of the part element.
    wrapper = etree.fromstring(f"<wrap>{inner_xml}</wrap>".encode())
    for child in wrapper:
        part_el.append(child)
    members[part_name] = etree.tostring(
        part_el, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    ct = etree.fromstring(members["[Content_Types].xml"])
    override = etree.SubElement(ct, f"{{{CT_NS}}}Override")
    override.set("PartName", f"/{part_name}")
    override.set("ContentType", content_type)
    members["[Content_Types].xml"] = etree.tostring(
        ct, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    rels = etree.fromstring(members["word/_rels/document.xml.rels"])
    used = {
        r.get("Id", "") for r in rels.findall(f"{{{REL_NS}}}Relationship")
    }
    n = 1
    while f"rId{n}" in used:
        n += 1
    rel = etree.SubElement(rels, f"{{{REL_NS}}}Relationship")
    rel.set("Id", f"rId{n}")
    rel.set("Type", rel_type)
    rel.set("Target", part_name.split("/", 1)[1])
    members["word/_rels/document.xml.rels"] = etree.tostring(
        rels, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    out = str(src) + ".withpart.docx"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in members.items():
            zout.writestr(name, data)
    return out


def _footnote_xml(text="Footnote in the wrong font.", font="Times New Roman"):
    return (
        f'<w:footnote { _ns() } w:id="1"><w:p><w:r><w:rPr>'
        f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}"/>'
        f"</w:rPr>"
        f"<w:t>{text}</w:t></w:r></w:p></w:footnote>"
    )


def _ns():
    return f'xmlns:w="{W}"'


# ── part-name predicate ──────────────────────────────────────────────────

FOOTNOTES_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes"


@pytest.mark.parametrize("name,expected", [
    ("word/document.xml", True),
    ("word/header1.xml", True),
    ("word/header2.xml", True),
    ("word/footer1.xml", True),
    ("word/footnotes.xml", True),
    ("word/endnotes.xml", True),
    ("word/comments.xml", True),
    ("word/styles.xml", False),
    ("word/theme/theme1.xml", False),
    ("word/_rels/document.xml.rels", False),
    ("[Content_Types].xml", False),
])
def test_text_part_predicate(name, expected):
    assert _is_text_part(name) is expected


# ── run layer across parts ───────────────────────────────────────────────

def test_header_run_swept(tmp_path):
    doc = Document()
    doc.add_paragraph("Body.")
    run = doc.sections[0].header.paragraphs[0].add_run("Header in Times.")
    run.font.name = "Times New Roman"
    src = tmp_path / "in.docx"
    doc.save(str(src))
    out = tmp_path / "out.docx"

    _, actions = apply_run_font_corrections(str(src), str(out))

    with zipfile.ZipFile(str(out)) as z:
        header = etree.fromstring(z.read("word/header1.xml"))
    fonts = _run_fonts(header)
    assert fonts.get("Header in Times.") == "Calibri"
    assert any(a["part"] == "word/header1.xml" and a["scope"] == "run" for a in actions)


def test_footnote_part_swept(tmp_path):
    doc = Document()
    doc.add_paragraph("Body.")
    src0 = tmp_path / "base.docx"
    doc.save(str(src0))
    src = _inject_text_part(
        src0, "word/footnotes.xml", FOOTNOTES_REL,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml",
        _footnote_xml(),
    )
    out = tmp_path / "out.docx"

    _, actions = apply_run_font_corrections(src, str(out))

    with zipfile.ZipFile(str(out)) as z:
        notes = etree.fromstring(z.read("word/footnotes.xml"))
    assert _run_fonts(notes).get("Footnote in the wrong font.") == "Calibri"
    assert any(a["part"] == "word/footnotes.xml" for a in actions)


def test_theme_bound_run_gets_explicit_calibri(tmp_path):
    """A run with only w:asciiTheme (resolves to Cambria via the theme) is
    rewritten to explicit Calibri — the docDefaults/style sweep alone cannot
    fix it because theme bindings bypass styles entirely."""
    doc = Document()
    p = doc.add_paragraph()
    run = p.add_run("Theme-bound text.")
    src0 = tmp_path / "s0.docx"
    doc.save(str(src0))
    with zipfile.ZipFile(str(src0)) as z:
        root = etree.fromstring(z.read("word/document.xml"))
        members = {i.filename: z.read(i.filename) for i in z.infolist()}
    rpr = root.find(f"{WQ}body").find(f"{WQ}p").find(f"{WQ}r").find(f"{WQ}rPr")
    if rpr is None:
        rpr = etree.SubElement(
            root.find(f"{WQ}body").find(f"{WQ}p").find(f"{WQ}r"), f"{WQ}rPr"
        )
    rf = etree.SubElement(rpr, f"{WQ}rFonts")
    rf.set(f"{WQ}asciiTheme", "minorHAnsi")
    rf.set(f"{WQ}hAnsiTheme", "minorHAnsi")
    members["word/document.xml"] = etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    src = tmp_path / "in.docx"
    with zipfile.ZipFile(str(src), "w", zipfile.ZIP_DEFLATED) as zout:
        for n, d in members.items():
            zout.writestr(n, d)
    out = tmp_path / "out.docx"

    _, actions = apply_run_font_corrections(str(src), str(out))

    with zipfile.ZipFile(str(out)) as z:
        root2 = etree.fromstring(z.read("word/document.xml"))
    rf2 = root2.find(f"{WQ}body").find(f"{WQ}p").find(f"{WQ}r").find(
        f"{WQ}rPr/{WQ}rFonts"
    )
    assert rf2.get(f"{WQ}ascii") == "Calibri"
    assert rf2.get(f"{WQ}asciiTheme") is None
    assert any(a.get("reason") == "theme" for a in actions)


def test_symbol_run_preserved(tmp_path):
    doc = Document()
    p = doc.add_paragraph()
    run = p.add_run("∑")
    run.font.name = "Symbol"
    src = tmp_path / "in.docx"
    doc.save(str(src))
    out = tmp_path / "out.docx"

    apply_run_font_corrections(str(src), str(out))

    with zipfile.ZipFile(str(out)) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    r = root.find(f"{WQ}body").find(f"{WQ}p").find(f"{WQ}r")
    rf = r.find(f"{WQ}rPr/{WQ}rFonts")
    assert rf.get(f"{WQ}ascii") == "Symbol"
    assert r.find(f"{WQ}rPr/{WQ}rPrChange") is None


def test_char_style_inherited_run_fixed(tmp_path):
    doc = Document()
    cs = doc.styles.add_style("Times Char", WD_STYLE_TYPE.CHARACTER)
    cs.font.name = "Times New Roman"
    p = doc.add_paragraph()
    p.add_run("Char-styled text.", style="Times Char")
    src = tmp_path / "in.docx"
    doc.save(str(src))
    out = tmp_path / "out.docx"

    _, actions = apply_run_font_corrections(str(src), str(out))

    with zipfile.ZipFile(str(out)) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    rf = root.find(f"{WQ}body").find(f"{WQ}p").find(f"{WQ}r").find(
        f"{WQ}rPr/{WQ}rFonts"
    )
    assert rf.get(f"{WQ}ascii") == "Calibri"
    assert any(a.get("reason") == "char-style" for a in actions)


# ── style layer ──────────────────────────────────────────────────────────

def _style_fonts(path):
    with zipfile.ZipFile(str(path)) as z:
        root = etree.fromstring(z.read("word/styles.xml"))
    out = {}
    for s in root.findall(f"{WQ}style"):
        rf = s.find(f"{WQ}rPr/{WQ}rFonts")
        if rf is not None:
            out[s.get(f"{WQ}styleId")] = rf.get(f"{WQ}ascii")
    return out


def test_custom_style_font_swept_run_untouched(tmp_path):
    doc = Document()
    st = doc.styles.add_style("Custom Times", WD_STYLE_TYPE.PARAGRAPH)
    st.font.name = "Times New Roman"
    doc.add_paragraph("Styled text.", style="Custom Times")
    src = tmp_path / "in.docx"
    doc.save(str(src))
    out = tmp_path / "out.docx"

    _, actions = apply_run_font_corrections(str(src), str(out))

    fonts = _style_fonts(out)
    assert fonts.get("CustomTimes") == "Calibri"
    assert any(a["scope"] == "style" for a in actions)
    # The inheriting run itself gets no tracked change — the style owns it.
    assert not any(
        a["scope"] == "run" and a.get("reason") in ("explicit", "theme", "char-style")
        for a in actions
    )


def test_symbol_character_style_preserved(tmp_path):
    doc = Document()
    cs = doc.styles.add_style("Symbol Char", WD_STYLE_TYPE.CHARACTER)
    cs.font.name = "Symbol"
    src = tmp_path / "in.docx"
    doc.save(str(src))
    out = tmp_path / "out.docx"

    apply_run_font_corrections(str(src), str(out))

    fonts = _style_fonts(out)
    sym = [v for k, v in fonts.items() if (k or "").lower().startswith("symbol")]
    assert sym and all(v == "Symbol" for v in sym)


def test_docdefaults_pinned_to_explicit_calibri(tmp_path):
    doc = Document()
    doc.add_paragraph("Body.")
    src = tmp_path / "in.docx"
    doc.save(str(src))
    out = tmp_path / "out.docx"

    _, actions = apply_run_font_corrections(str(src), str(out))

    with zipfile.ZipFile(str(out)) as z:
        root = etree.fromstring(z.read("word/styles.xml"))
    rpr = root.find(f"{WQ}docDefaults/{WQ}rPrDefault/{WQ}rPr")
    assert rpr is not None
    rf = rpr.find(f"{WQ}rFonts")
    assert rf is not None
    assert rf.get(f"{WQ}ascii") == "Calibri"
    assert rf.get(f"{WQ}hAnsi") == "Calibri"
    assert rf.get(f"{WQ}asciiTheme") is None
    assert any(a["scope"] == "defaults" for a in actions)


# ── APA002 check ─────────────────────────────────────────────────────────

def test_apa002_fails_before_passes_after(tmp_path):
    doc = Document()
    p = doc.add_paragraph("Body in the wrong font.")
    for run in p.runs:
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)
    src = tmp_path / "in.docx"
    doc.save(str(src))

    before = check_fonts(str(src))
    assert before[0]["rule_id"] == "APA002"
    assert before[0]["status"] == "fail"
    assert "Times New Roman" in before[0]["message"]

    out = tmp_path / "out.docx"
    apply_run_font_corrections(str(src), str(out))
    after = check_fonts(str(out))
    assert after[0]["status"] == "pass"


def test_apa002_is_sam_fixed_and_in_family_table():
    assert "APA002" in ro.SAM_FIXED_RULE_IDS
    family = "APA"
    assert family in ro.FAMILY_VERDICTS
    entry = ro.FAMILY_VERDICTS[family]
    assert "APA002" in (entry[2] if len(entry) > 2 else [])


def test_apa002_emitted_by_apa_validator(tmp_path):
    doc = Document()
    doc.add_paragraph("Plain.")
    src = tmp_path / "in.docx"
    doc.save(str(src))
    ids = [r["rule_id"] for r in apa_validate(str(src))["results"]]
    assert "APA002" in ids


# ── end-to-end evidence (mirrors test_sam_fixes_validator_rules) ─────────

def _status_of(report, rule_id):
    return {r["rule_id"]: r["status"] for r in report["results"]}.get(rule_id, "(absent)")


def test_full_build_clears_apa002(tmp_path):
    """APA002 fixed by the font sweep: a Times-injected fixture fails before
    build_edited_document and passes after."""
    src = tmp_path / "in.docx"
    shutil.copy(SRC, src)
    doc = Document(str(src))
    for p in doc.paragraphs[:3]:
        for run in p.runs:
            if (run.text or "").strip():
                run.font.name = "Times New Roman"
                break
    doc.save(str(src))
    assert _status_of(apa_validate(str(src)), "APA002") == "fail"

    out = tmp_path / "out.docx"
    with patch.object(S, "call_llm_json", side_effect=Exception("skip llm")):
        with patch.object(S, "build_body_edit_plan", return_value={"action": "none", "edits": []}):
            with patch.object(
                S, "build_editorial_review_comment_plan",
                return_value={"action": "none", "comments": []},
            ):
                S.build_edited_document(str(src), str(out))
    assert _status_of(apa_validate(str(out)), "APA002") == "pass"
