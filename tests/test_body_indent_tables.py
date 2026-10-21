"""JB-08: the body first-line-indent pass must not indent table captions,
headings, or subheadings (cell paragraphs were already outside the pass).
"""

from docx import Document
from lxml import etree

from app.services.output_generation_samfix import (
    _apply_tracked_body_format_fixes,
    _load_body_paras_raw,
    _table_caption_paragraph_indices,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"


def _paragraph_texts(body_paras):
    return ["".join(t.text or "" for t in p.iter(f"{WQ}t")) for p in body_paras]


def _has_first_line_indent(para_el):
    ind = para_el.find(f"{WQ}pPr/{WQ}ind")
    return ind is not None and ind.get(f"{WQ}firstLine") == "720"


def test_table_caption_paragraph_indices_detects_paragraph_above_table(tmp_path):
    input_path = tmp_path / "input.docx"

    doc = Document()
    doc.add_paragraph("Descriptive statistics")  # not a caption label
    doc.add_table(rows=1, cols=1)
    doc.add_paragraph("Body text.")
    doc.save(input_path)

    doc_root, body_paras = _load_body_paras_raw(str(input_path))
    heading_idx = _paragraph_texts(body_paras).index("Descriptive statistics")

    skip = _table_caption_paragraph_indices(doc_root, body_paras)
    assert heading_idx in skip


def test_body_indent_skips_table_caption_but_indents_body(tmp_path):
    input_path = tmp_path / "input.docx"
    output_path = tmp_path / "output.docx"

    doc = Document()
    doc.add_paragraph("Table 1. Results of the experiment")
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Header A"
    table.cell(0, 1).text = "Header B"
    doc.add_paragraph("This is a normal body paragraph.")
    doc.save(input_path)

    doc_root, body_paras = _load_body_paras_raw(str(input_path))
    texts = _paragraph_texts(body_paras)
    caption_idx = texts.index("Table 1. Results of the experiment")
    body_idx = texts.index("This is a normal body paragraph.")

    skip = _table_caption_paragraph_indices(doc_root, body_paras)
    assert caption_idx in skip
    assert body_idx not in skip

    fixes = [
        {"paragraph_index": caption_idx, "indent": True},
        {"paragraph_index": body_idx, "indent": True},
    ]
    assert _apply_tracked_body_format_fixes(str(input_path), str(output_path), fixes, 5000) is True

    out_root, out_paras = _load_body_paras_raw(str(output_path))
    assert _has_first_line_indent(out_paras[body_idx]) is True
    assert _has_first_line_indent(out_paras[caption_idx]) is False

    # Table cell paragraphs are never touched (they are not body children).
    for tbl in out_root.iter(f"{WQ}tbl"):
        for cell_para in tbl.iter(f"{WQ}p"):
            assert _has_first_line_indent(cell_para) is False
