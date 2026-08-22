"""Tests for body-font enforcement: the Normal style must carry Arial 11pt so
inherited body text is not left at Word's 10pt default."""

import zipfile

from docx import Document
from lxml import etree

from app.services.output_generation_samfix import (
    BODY_REQUIRED_FONT_NAME,
    BODY_REQUIRED_FONT_SIZE_XML,
    _ensure_normal_style_body_rpr,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"


def _normal_rpr(path):
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read("word/styles.xml"))
    for s in root.findall(f"{WQ}style"):
        nm = s.find(f"{WQ}name")
        if nm is not None and (nm.get(f"{WQ}val", "") or "").strip().lower() == "normal":
            return s.find(f"{WQ}rPr")
    return None


def _doc_with_normal(tmp_path, font="Times New Roman", sz="24"):
    """A docx whose Normal style is a non-template font/size."""
    doc = Document()
    doc.add_paragraph("Some body text.")
    path = tmp_path / "in.docx"
    doc.save(str(path))
    # Force the Normal style to a wrong font/size to mimic a converted doc.
    with zipfile.ZipFile(str(path)) as z:
        root = etree.fromstring(z.read("word/styles.xml"))
        members = {i.filename: z.read(i.filename) for i in z.infolist()}
    for s in root.findall(f"{WQ}style"):
        nm = s.find(f"{WQ}name")
        if nm is not None and (nm.get(f"{WQ}val", "") or "").strip().lower() == "normal":
            rpr = s.find(f"{WQ}rPr")
            if rpr is None:
                rpr = etree.SubElement(s, f"{WQ}rPr")
            rf = rpr.find(f"{WQ}rFonts") or etree.SubElement(rpr, f"{WQ}rFonts")
            for a in ("ascii", "hAnsi", "cs"):
                rf.set(f"{WQ}{a}", font)
            szel = rpr.find(f"{WQ}sz") or etree.SubElement(rpr, f"{WQ}sz")
            szel.set(f"{WQ}val", sz)
    members["word/styles.xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    forced = tmp_path / "forced.docx"
    with zipfile.ZipFile(str(forced), "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in members.items():
            zout.writestr(name, data)
    return str(forced)


def test_normal_style_pinned_to_arial_11pt(tmp_path):
    src = _doc_with_normal(tmp_path, font="Times New Roman", sz="20")
    out = tmp_path / "out.docx"
    changed = _ensure_normal_style_body_rpr(src, str(out))
    assert changed is True

    rpr = _normal_rpr(str(out))
    assert rpr is not None
    rfonts = rpr.find(f"{WQ}rFonts")
    assert rfonts.get(f"{WQ}ascii") == BODY_REQUIRED_FONT_NAME == "Arial"
    assert rpr.find(f"{WQ}sz").get(f"{WQ}val") == BODY_REQUIRED_FONT_SIZE_XML == "22"
    assert rpr.find(f"{WQ}szCs").get(f"{WQ}val") == "22"


def test_already_correct_normal_style_no_change(tmp_path):
    src = _doc_with_normal(tmp_path, font="Times New Roman", sz="24")
    out1 = tmp_path / "o1.docx"
    _ensure_normal_style_body_rpr(src, str(out1))
    out2 = tmp_path / "o2.docx"
    assert _ensure_normal_style_body_rpr(str(out1), str(out2)) is False
