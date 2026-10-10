"""Generate the APA 7 base template document
Produces: app/domain/APA7 Base Template.docx
Consistent use of Calibri 11pt throughout,
Frame-based layout following APA-00/01/03/04/05/11/12
geometry from the Track C rule matrix.

"APA 7 Reference List Entry" is kept as a transition alias of "Reference"
(identical APA formatting) so existing passes keep working until C-25
retargets them to the APA base.

Run with: python scripts/gen_apa7_base_template.py
Note:
this script is not part of the OpenEditor engine,
its a utility for generating the template document seen in "\\app\\domain\\APA7 Base Template.docx"
"""

import os

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "domain")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "APA7 Base Template.docx")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _clear_children(pPr, tag):
    for el in pPr.findall(f".//{{{W_NS}}}{tag}"):
        # only remove direct children to avoid nuking nested runs content
        if el.getparent() is pPr:
            pPr.remove(el)


def _set_spacing(pPr, line="480", after="0"):
    _clear_children(pPr, "spacing")
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:line"), line)
    spacing.set(qn("w:lineRule"), "auto")
    spacing.set(qn("w:after"), after)
    pPr.insert(0, spacing)

# ? indentation can be set via paragraph_format.left_indent / first_line_indent, but that only sets the style's default;
# ? it doesn't override existing direct formatting on a paragraph.
# So we set the style's pPr directly to ensure the style is applied consistently to all paragraphs that use it,
def _set_ind(pPr, left="0", first_line=None, hanging=None):
    _clear_children(pPr, "ind")
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), left)
    if first_line is not None:
        ind.set(qn("w:firstLine"), first_line)
    if hanging is not None:
        ind.set(qn("w:hanging"), hanging)
    pPr.insert(0, ind)


def _set_font(style, bold=None, italic=None):
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    # ensure the style's own rPr carries Calibri (python-docx sets rFonts ascii+hAnsi)
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(f".//{{{W_NS}}}rFonts")
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in ("ascii", "hAnsi", "cs"):
        rFonts.set(qn(f"w:{attr}"), "Calibri")


def apply_normal_style(style):
    _set_font(style)
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pPr = style.element.get_or_add_pPr()
    _set_spacing(pPr, line="480", after="0")
    _set_ind(pPr, left="0", first_line="720")


def apply_heading_style(style, align, bold, italic, indent_twips=0):
    _set_font(style, bold=bold, italic=italic)
    style.paragraph_format.alignment = align
    pPr = style.element.get_or_add_pPr()
    _set_spacing(pPr, line="480", after="0")
    _set_ind(pPr, left=str(indent_twips))


def apply_reference_format(style):
    _set_font(style)
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pPr = style.element.get_or_add_pPr()
    _set_spacing(pPr, line="480", after="0")
    _set_ind(pPr, left="720", hanging="720")


def apply_title_style(style):
    _set_font(style, bold=True)
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER


def ensure_reference_styles(doc):
    """Create Reference + transition alias if absent (default template lacks them)."""
    normal = doc.styles["Normal"]
    for name in ("Reference", "APA 7 Reference List Entry"):
        if name in doc.styles:
            style = doc.styles[name]
        else:
            style = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            style.base_style = normal
        apply_reference_format(style)


def _ensure_para_style(doc, name):
    if name in doc.styles:
        return doc.styles[name]
    style = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style.base_style = doc.styles["Normal"]
    return style


def _ensure_char_style(doc, name, bold=None, italic=None):
    if name in doc.styles:
        style = doc.styles[name]
    else:
        style = doc.styles.add_style(name, WD_STYLE_TYPE.CHARACTER)
    _set_font(style, bold=bold, italic=italic)
    return style


def apply_caption_styles(doc):
    """APA-15/16 caption family + Char companions (Calibri 11, D2).

    JUTLP front-page styles (Article Title / Authors / Author Affiliations)
    are deliberately NOT created: APA has no equivalent and C-24 rebuilds
    the title page from Title + centred Normal lines.
    """
    paras = {
        # name: (bold, italic, keep_with_next)
        "Table Number": (True, False, True),
        "Table Title": (False, True, True),
        "Figure Number": (True, False, True),
        "Figure Title": (False, True, True),
        "Figure/Table Number": (True, False, True),
        "Figure/Table Title": (False, True, True),
        "Table Emphasis": (True, False, False),
        "Table Note": (False, True, False),
        "Figure/Table Notes": (False, True, False),
    }
    for name, (bold, italic, keep_next) in paras.items():
        style = _ensure_para_style(doc, name)
        _set_font(style, bold=bold, italic=italic)
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        style.paragraph_format.keep_with_next = keep_next
        pPr = style.element.get_or_add_pPr()
        _set_spacing(pPr, line="480", after="0")
    # Table Text: plain body inside tables.
    tt = _ensure_para_style(doc, "Table Text")
    _set_font(tt)
    tt.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pPr = tt.element.get_or_add_pPr()
    _set_spacing(pPr, line="480", after="0")
    # Table Grid: the Word default grid is fine as a definition; just ensure it exists.
    if "Table Grid" not in doc.styles:
        doc.styles.add_style("Table Grid", WD_STYLE_TYPE.TABLE)
    # Char companions mirror the paragraph formatting.
    chars = {
        "Table Number Char": (True, False),
        "Table Title Char": (False, True),
        "Figure Number Char": (True, False),
        "Figure Title Char": (False, True),
        "Figure/Table Number Char": (True, False),
        "Figure/Table Title Char": (False, True),
        "Figure/Table Notes Char": (False, True),
        "Table Emphasis Char": (True, False),
        "Table Note Char": (False, True),
        "Table Text Char": (None, None),
    }
    for name, (bold, italic) in chars.items():
        _ensure_char_style(doc, name, bold=bold, italic=italic)


def apply_quote_style(doc):
    """APA-14 block quote: indented both sides, no marks, double-spaced."""
    from docx.shared import Inches
    style = doc.styles["Quote"]
    _set_font(style, bold=False, italic=False)
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    style.paragraph_format.left_indent = Inches(0.5)
    style.paragraph_format.right_indent = Inches(0.5)
    style.paragraph_format.first_line_indent = Pt(0)
    pPr = style.element.get_or_add_pPr()
    _set_spacing(pPr, line="480", after="0")


def apply_page_margins(doc):
    sectPr = doc.sections[0]._sectPr
    # replace the template's default pgMar instead of appending a duplicate
    for existing in sectPr.findall(f".//{{{W_NS}}}pgMar"):
        sectPr.remove(existing)
    pgMar = OxmlElement("w:pgMar")
    for attr, val in [
        ("top", "1440"),
        ("right", "1440"),
        ("bottom", "1440"),
        ("left", "1440"),
        ("header", "720"),
        ("footer", "720"),
        ("gutter", "0"),
    ]:
        pgMar.set(qn(f"w:{attr}"), val)
    sectPr.append(pgMar)


def apply_page_numbers(doc):
    """APA-05: page number top-right on every page, incl. title page."""
    header = doc.sections[0].header
    header_para = header.paragraphs[0]
    header_para.clear()
    header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    rFonts = OxmlElement("w:rFonts")
    for attr in ("ascii", "hAnsi", "cs"):
        rFonts.set(qn(f"w:{attr}"), "Calibri")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "22")  # 11pt
    rPr.append(rFonts)
    rPr.append(sz)
    r.append(rPr)
    fld.append(r)
    header_para._p.append(fld)


def _centered(doc, text, style_name="Normal"):
    """Centred skeleton line (direct alignment; keeps the style itself clean)."""
    p = doc.add_paragraph(style=style_name)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(text)
    return p


def build_skeleton(doc):
    """APA student skeleton. Guidance phrasing mirrors APA's own instructional
    templates; every paragraph demonstrates exactly one style."""
    from docx.shared import Inches
    # ---- Title page (APA student order; no running head) ----
    for _ in range(3):
        doc.add_paragraph("", style="Normal")
    doc.add_paragraph(
        "Title of Paper in Bold Title Case Across Two Lines if Needed",
        style="Title",
    )
    doc.add_paragraph("", style="Normal")  # one blank double-spaced line
    _centered(doc, "Firstname M. Lastname")
    _centered(doc, "Department Name, University Name")
    _centered(doc, "PSY 101: Introduction to Psychology")
    _centered(doc, "Dr. Instructor Name")
    _centered(doc, "October 10, 2026")
    doc.add_page_break()
    # ---- Abstract + Keywords ----
    doc.add_paragraph("Abstract", style="Heading 1")
    abs_p = doc.add_paragraph(style="Normal")
    abs_p.paragraph_format.first_line_indent = Pt(0)
    abs_p.add_run(
        "This abstract is a single unindented paragraph of no more than 250 words "
        "summarising the paper topic, method, results, and conclusions. "
        "Replace this guidance text with the manuscript abstract."
    )
    kw = doc.add_paragraph(style="Normal")
    kw.paragraph_format.left_indent = Inches(0.5)
    run = kw.add_run("Keywords:")
    run.italic = True
    kw.add_run(" apa style, manuscript template, open editor")
    doc.add_page_break()
    # ---- Body (title repeated; no Introduction heading) ----
    doc.add_paragraph(
        "Title of Paper in Bold Title Case Across Two Lines if Needed",
        style="Title",
    )
    doc.add_paragraph(
        "The first body paragraph repeats the paper title bold and centred above it. "
        "There is no Introduction heading; opening text is assumed to be the introduction. "
        "Body paragraphs carry a half-inch first-line indent and double spacing.",
        style="Normal",
    )
    doc.add_paragraph("Method", style="Heading 1")
    doc.add_paragraph(
        "Describe participants, measures, and procedure in enough detail for replication. "
        "Use Level 2 headings for subsections of a Level 1 section.",
        style="Normal",
    )
    doc.add_paragraph("Participants", style="Heading 2")
    doc.add_paragraph(
        "State the sample, recruitment, and assignment used in this placeholder study.",
        style="Normal",
    )
    doc.add_paragraph("Measures", style="Heading 2")
    doc.add_paragraph(
        "Name each instrument and its scoring in a further subsection below.",
        style="Normal",
    )
    doc.add_paragraph("Self-Report Scale", style="Heading 3")
    doc.add_paragraph(
        "Level 3 headings are flush left, bold, and italic.",
        style="Normal",
    )
    doc.add_paragraph(
        "Level 4 Heading Ending With a Period. The paragraph text begins on the same line "
        "and continues as a regular paragraph, indented like this one.",
        style="Heading 4",
    )
    doc.add_paragraph(
        "Level 5 Heading Ending With a Period. The paragraph text begins on the same line "
        "in bold italic, exactly as this sentence demonstrates.",
        style="Heading 5",
    )
    doc.add_paragraph(
        "Quotations of forty or more words are set as block quotations without quotation marks, "
        "indented half an inch from the left margin, double-spaced, with the citation after the "
        "final punctuation, following the Publication Manual (American Psychological "
        "Association, 2020, p. 00). This paragraph demonstrates the Quote style.",
        style="Quote",
    )
    doc.add_paragraph("Results", style="Heading 1")
    doc.add_paragraph(
        "Report the findings here, referring to tables and figures by number.",
        style="Normal",
    )
    doc.add_paragraph("Table 1", style="Table Number")
    doc.add_paragraph(
        "Placeholder Table Title in Title Case Italics", style="Table Title"
    )
    table = doc.add_table(rows=2, cols=3, style="Table Grid")
    table.cell(0, 0).text = "Group"
    table.cell(0, 1).text = "M"
    table.cell(0, 2).text = "SD"
    table.cell(1, 0).text = "Example"
    table.cell(1, 1).text = "0.00"
    table.cell(1, 2).text = "0.00"
    doc.add_paragraph(
        "Note. Replace this placeholder note with table notes as needed.",
        style="Table Note",
    )
    doc.add_paragraph("Figure 1", style="Figure Number")
    doc.add_paragraph(
        "Placeholder Figure Title in Title Case Italics", style="Figure Title"
    )
    doc.add_paragraph(
        "Note. Figures carry a number, an italic title, and a note below.",
        style="Figure/Table Notes",
    )
    doc.add_paragraph("Discussion", style="Heading 1")
    doc.add_paragraph(
        "Interpret the results, note limitations, and suggest future directions.",
        style="Normal",
    )
    doc.add_page_break()
    # ---- References (new page, bold centred heading, hanging indent) ----
    doc.add_paragraph("References", style="Heading 1")
    for entry in (
        "American Psychological Association. (2020). Publication manual of the American "
        "Psychological Association (7th ed.). https://doi.org/10.1037/0000165-000",
        "Placeholder, A. U. (2026). Example reference entry with a hanging indent. "
        "Journal of Placeholder Studies, 1(1), 1-2. https://doi.org/10.0000/example",
    ):
        doc.add_paragraph(entry, style="APA 7 Reference List Entry")
    doc.add_page_break()
    # ---- Appendix (APA-19 allows appendices after references) ----
    doc.add_paragraph("Appendix A", style="Heading 1")
    doc.add_paragraph(
        "Appendices follow the references when supplementary material is needed.",
        style="Normal",
    )


def main():
    doc = Document()

    apply_normal_style(doc.styles["Normal"])

    apply_heading_style(doc.styles["Heading 1"], WD_ALIGN_PARAGRAPH.CENTER, True, False)
    apply_heading_style(doc.styles["Heading 2"], WD_ALIGN_PARAGRAPH.LEFT, True, False)
    apply_heading_style(doc.styles["Heading 3"], WD_ALIGN_PARAGRAPH.LEFT, True, True)
    apply_heading_style(doc.styles["Heading 4"], WD_ALIGN_PARAGRAPH.LEFT, True, False, 720)
    apply_heading_style(doc.styles["Heading 5"], WD_ALIGN_PARAGRAPH.LEFT, True, True, 720)

    apply_title_style(doc.styles["Title"])

    ensure_reference_styles(doc)
    apply_caption_styles(doc)
    apply_quote_style(doc)

    apply_page_margins(doc)
    apply_page_numbers(doc)

    build_skeleton(doc)

    doc.save(OUTPUT_PATH)
    print(f"saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
