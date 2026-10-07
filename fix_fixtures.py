from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

doc_path = Path("tests/jutlp_sample_docx_test_pack/01_valid_identified.docx")
doc_path.parent.mkdir(parents=True, exist_ok=True)

doc = Document()

for section in doc.sections:
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)


def add_p(
    doc,
    text,
    style_name="Normal",
    align=WD_ALIGN_PARAGRAPH.LEFT,
    bold=False,
    italic=False,
    size_pt=12,
):
    p = doc.add_paragraph()
    p.alignment = align
    try:
        p.style = style_name
    except KeyError:
        pass
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    return p


# Title
add_p(
    doc,
    "Integrating Digital Learning Tools in Higher Education: A Comprehensive"
    " Review",
    "Article Title",
    align=WD_ALIGN_PARAGRAPH.CENTER,
    bold=True,
    size_pt=18,
)

# Author - Directly Li Chen (No "Author Block" header)
add_p(doc, "Li Chen", "Authors", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
add_p(
    doc,
    "Department of Education, University of Sydney, Sydney, Australia",
    "Affiliation",
    align=WD_ALIGN_PARAGRAPH.CENTER,
    italic=True,
)

# Abstract
add_p(doc, "Abstract", "Heading 1", bold=True, size_pt=14)
add_p(
    doc,
    "This study explores the integration of interactive digital tools in"
    " university curricula and evaluates their impact on student engagement and"
    " academic outcomes. Over a period of two academic terms, empirical data"
    " was gathered from various undergraduate departments to identify key"
    " determinants of effective pedagogical implementation. Results indicate a"
    " significant increase in active participation and comprehension scores"
    " when blended learning approaches are structured alongside collaborative"
    " tasks. Guidance Notes and practical recommendations are provided for higher"
    " education instructors seeking to modernize course structures while"
    " maintaining academic rigor.",
    "Normal",
)

# Keywords
add_p(doc, "Keywords", "Heading 1", bold=True, size_pt=14)
add_p(
    doc,
    "Keywords: higher education, digital learning, active learning,"
    " educational technology, student engagement",
    "Normal",
)

# Practitioner Notes
add_p(doc, "Practitioner Notes", "Heading 1", bold=True, size_pt=14)
add_p(
    doc,
    "1. Digital learning tools improve student comprehension when paired with"
    " structured team activities.\n2. Educators should establish clear"
    " guidelines before adopting new virtual platforms in large lectures.\n3."
    " Institutional technical support is essential for sustainable educational"
    " technology adoption.",
    "Normal",
)

# Introduction (No leading number)
add_p(doc, "Introduction", "Heading 1", bold=True, size_pt=14)
add_p(
    doc,
    "Higher education institutions globally are undergoing rapid digital"
    " transformations. Integrating specialized software into traditional"
    " lecture formats allows educators to foster collaborative learning"
    " environments and enhance student learning experiences. However,"
    " successful adoption depends on deliberate instructional design rather"
    " than technology deployment alone.",
    "Normal",
)

# Method & All Subsections (MET001, MET002, MET003)
add_p(doc, "Method", "Heading 1", bold=True, size_pt=14)

add_p(doc, "Research Design", "Heading 2", bold=True, size_pt=12)
add_p(
    doc,
    "A mixed-methods framework was adopted to measure both quantitative"
    " performance metrics and qualitative student feedback across four"
    " distinct discipline modules.",
    "Normal",
)

add_p(doc, "Participants", "Heading 2", bold=True, size_pt=12)
add_p(
    doc,
    "The participant pool consisted of 342 undergraduate students enrolled in"
    " introductory science and humanities courses at a major public institution"
    " during the 2024 academic year. Informed consent was obtained from all"
    " participants prior to study commencement.",
    "Normal",
)

add_p(doc, "Data Analysis", "Heading 2", bold=True, size_pt=12)
add_p(
    doc,
    "Quantitative survey responses and grade performance were analyzed using"
    " multivariate regression models to evaluate variance across engagement"
    " cohorts.",
    "Normal",
)

# Results
add_p(doc, "Results", "Heading 1", bold=True, size_pt=14)
add_p(
    doc,
    "Data analysis revealed a positive correlation between active platform"
    " interaction time and overall exam performance across all four cohort"
    " groups.",
    "Normal",
)

# Discussion (DIS001)
add_p(doc, "Discussion", "Heading 1", bold=True, size_pt=14)
add_p(
    doc,
    "The findings reinforce earlier research demonstrating that"
    " technology-enhanced instruction fosters higher cognitive engagement. When"
    " course materials incorporate interactive simulations, students"
    " demonstrate improved problem-solving capacity and concept retention."
    " The Guidance Notes provided in this framework further illustrate"
    " practical pathways for curriculum integration.",
    "Normal",
)

# Guidance Notes
add_p(doc, "Guidance Notes", "Heading 1", bold=True, size_pt=14)
add_p(
    doc,
    "Instructors are advised to evaluate tool usability and data privacy"
    " standards prior to course delivery.",
    "Normal",
)

# References
add_p(doc, "References", "Heading 1", bold=True, size_pt=14)
add_p(
    doc,
    "Chen, L., & Smith, J. (2022). Digital transformations in higher education"
    " pedagogy. Journal of Educational Technology, 45(2), 112–128."
    " https://doi.org/10.1080/02602938.2021.1912345",
    "Normal",
)
add_p(
    doc,
    "Davis, R., Miller, T., & Wilson, K. (2021). Student engagement in blended"
    " learning environments. Assessment & Evaluation in Higher Education,"
    " 38(4), 401–415. https://doi.org/10.1016/j.compedu.2020.103987",
    "Normal",
)
add_p(
    doc,
    "Garcia, M., & Patel, A. (2023). Evaluating active learning strategies in"
    " university classrooms. Higher Education Research & Development, 42(1),"
    " 85–99. https://doi.org/10.1080/07294360.2022.2081301",
    "Normal",
)
add_p(
    doc,
    "Taylor, E. (2020). Curriculum redesign for the 21st century learner."
    " Interactive Learning Environments, 28(3), 310–325."
    " https://doi.org/10.1080/10494820.2019.1620000",
    "Normal",
)

doc.save(doc_path)
print(f"Successfully generated clean complete fixture at {doc_path}")