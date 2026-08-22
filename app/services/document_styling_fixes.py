import pprint
import sys

from docx import Document

from app.domain.canonical_jultp_template import (
    CANONICAL_STRUCTURE,
    strip_leading_section_number,
)
from app.services.document_analysis_services import get_section_bounds, load_paragraphs


# extract styles from template: {style_name: style_xml}
def extract_template_styles(template_path):
    xml_styles = {}
    doc = Document(template_path)

    for style in doc.styles:
        style_name = style.name
        if style_name not in xml_styles:
            xml_styles[style_name] = style._element.xml

    return xml_styles


# extract headings only (Heading 1/2/3/4)
def extract_headings(docx_path):
    paragraphs = load_paragraphs(docx_path)
    headings = []

    for paragraph in paragraphs:
        if paragraph.is_empty is True:
            continue

        if paragraph.style in ["Heading 1", "Heading 2", "Heading 3", "Heading 4"]:
            headings.append(
                {
                    "index": paragraph.index,
                    "style": paragraph.style,
                    "text": paragraph.text,
                }
            )

    return headings


def _front_page_limit(paragraphs):
    for paragraph in paragraphs:
        if paragraph.style == "Heading 1":
            text = paragraph.text.strip().lower()
            if text == "introduction" or text.startswith("introduction:"):
                return paragraph.index
    return len(paragraphs)


def _front_page_paragraphs(paragraphs):
    limit = _front_page_limit(paragraphs)
    front = []

    for paragraph in paragraphs:
        if paragraph.index >= limit:
            continue
        front.append(paragraph)

    return front


def _find_first_text(paragraphs, text):
    wanted = text.strip().lower()
    for paragraph in paragraphs:
        if paragraph.text.strip().lower() == wanted:
            return paragraph
    return None


def _collect_until(front_page, start_index, stop_words):
    items = []
    for paragraph in front_page:
        if paragraph.index <= start_index:
            continue
        if paragraph.is_empty is True:
            continue

        lower_text = paragraph.text.strip().lower()
        if lower_text in stop_words:
            break

        items.append(paragraph)
    return items


def _section_name_matches(found_text, section_name):
    found = strip_leading_section_number(found_text).strip().lower()
    canonical = section_name.strip().lower()

    aliases = []
    alias_map = CANONICAL_STRUCTURE["section_aliases"]
    if section_name in alias_map:
        aliases = alias_map[section_name]

    names = [canonical]
    for alias in aliases:
        names.append(alias.strip().lower())

    for name in names:
        if found == name:
            return True
        if found.startswith(name + ":"):
            return True

    return False


def _canonical_index(heading_text):
    main_sections = CANONICAL_STRUCTURE["main_sections"]
    for index, section_name in enumerate(main_sections):
        if _section_name_matches(heading_text, section_name):
            return index
    return None


def compare_document_styles(target_docx_path):
    paragraphs = load_paragraphs(target_docx_path)
    front_page = _front_page_paragraphs(paragraphs)
    mismatches = []

    front_non_empty = []
    for paragraph in front_page:
        if paragraph.is_empty is False:
            front_non_empty.append(paragraph)

    # Title style
    if len(front_non_empty) > 0:
        title_expected = CANONICAL_STRUCTURE["front_page"]["title_style"]
        title_paragraph = front_non_empty[0]
        if title_paragraph.style != title_expected:
            mismatches.append(
                {
                    "type": "front_page",
                    "part": "title",
                    "index": title_paragraph.index,
                    "expected_style": title_expected,
                    "actual_style": title_paragraph.style,
                    "text": title_paragraph.text,
                }
            )

    # Authors style
    authors_expected = CANONICAL_STRUCTURE["front_page"]["authors_style"]
    authors_found = False
    for paragraph in front_page:
        if paragraph.style == authors_expected:
            authors_found = True
            break
    if authors_found is False:
        if len(front_non_empty) > 1:
            candidate = front_non_empty[1]
            mismatches.append(
                {
                    "type": "front_page",
                    "part": "authors",
                    "index": candidate.index,
                    "expected_style": authors_expected,
                    "actual_style": candidate.style,
                    "text": candidate.text,
                }
            )
        else:
            mismatches.append(
                {
                    "type": "front_page",
                    "part": "authors",
                    "index": None,
                    "expected_style": authors_expected,
                    "actual_style": None,
                    "text": "",
                }
            )

    # Affiliations style
    affiliations_expected = CANONICAL_STRUCTURE["front_page"]["affiliations_style"]
    affiliations_found = False
    for paragraph in front_page:
        if paragraph.style == affiliations_expected:
            affiliations_found = True
            break
    if affiliations_found is False:
        if len(front_non_empty) > 2:
            candidate = front_non_empty[2]
            mismatches.append(
                {
                    "type": "front_page",
                    "part": "affiliations",
                    "index": candidate.index,
                    "expected_style": affiliations_expected,
                    "actual_style": candidate.style,
                    "text": candidate.text,
                }
            )
        else:
            mismatches.append(
                {
                    "type": "front_page",
                    "part": "affiliations",
                    "index": None,
                    "expected_style": affiliations_expected,
                    "actual_style": None,
                    "text": "",
                }
            )

    # Abstract heading + body
    heading_front_page_style = "Heading Front Page"
    front_page_text_style = CANONICAL_STRUCTURE["front_page"]["abstract_style"]

    abstract_heading = _find_first_text(front_page, "Abstract")
    if abstract_heading is None:
        mismatches.append(
            {
                "type": "front_page",
                "part": "abstract_heading",
                "index": None,
                "expected_style": heading_front_page_style,
                "actual_style": None,
                "text": "Abstract",
            }
        )
    else:
        if abstract_heading.style != heading_front_page_style:
            mismatches.append(
                {
                    "type": "front_page",
                    "part": "abstract_heading",
                    "index": abstract_heading.index,
                    "expected_style": heading_front_page_style,
                    "actual_style": abstract_heading.style,
                    "text": abstract_heading.text,
                }
            )

        stop_words = ["practitioner notes", "keywords", "citation"]
        abstract_body = _collect_until(front_page, abstract_heading.index, stop_words)
        for paragraph in abstract_body:
            if paragraph.style != front_page_text_style:
                mismatches.append(
                    {
                        "type": "front_page",
                        "part": "abstract_text",
                        "index": paragraph.index,
                        "expected_style": front_page_text_style,
                        "actual_style": paragraph.style,
                        "text": paragraph.text,
                    }
                )

    # Practitioner Notes heading + items
    practitioner_heading = _find_first_text(front_page, "Practitioner Notes")
    if practitioner_heading is None:
        mismatches.append(
            {
                "type": "front_page",
                "part": "practitioner_notes_heading",
                "index": None,
                "expected_style": heading_front_page_style,
                "actual_style": None,
                "text": "Practitioner Notes",
            }
        )
    else:
        if practitioner_heading.style != heading_front_page_style:
            mismatches.append(
                {
                    "type": "front_page",
                    "part": "practitioner_notes_heading",
                    "index": practitioner_heading.index,
                    "expected_style": heading_front_page_style,
                    "actual_style": practitioner_heading.style,
                    "text": practitioner_heading.text,
                }
            )

        pn_style = CANONICAL_STRUCTURE["front_page"]["practitioner_notes_style"]
        stop_words = ["keywords", "citation"]
        pn_body = _collect_until(front_page, practitioner_heading.index, stop_words)
        for paragraph in pn_body:
            if paragraph.style != pn_style:
                mismatches.append(
                    {
                        "type": "front_page",
                        "part": "practitioner_notes_item",
                        "index": paragraph.index,
                        "expected_style": pn_style,
                        "actual_style": paragraph.style,
                        "text": paragraph.text,
                    }
                )

    # Keywords heading + text
    keywords_heading = _find_first_text(front_page, "Keywords")
    if keywords_heading is None:
        mismatches.append(
            {
                "type": "front_page",
                "part": "keywords_heading",
                "index": None,
                "expected_style": heading_front_page_style,
                "actual_style": None,
                "text": "Keywords",
            }
        )
    else:
        if keywords_heading.style != heading_front_page_style:
            mismatches.append(
                {
                    "type": "front_page",
                    "part": "keywords_heading",
                    "index": keywords_heading.index,
                    "expected_style": heading_front_page_style,
                    "actual_style": keywords_heading.style,
                    "text": keywords_heading.text,
                }
            )

        stop_words = ["citation"]
        keyword_body = _collect_until(front_page, keywords_heading.index, stop_words)
        for paragraph in keyword_body:
            if paragraph.style != front_page_text_style:
                mismatches.append(
                    {
                        "type": "front_page",
                        "part": "keywords_text",
                        "index": paragraph.index,
                        "expected_style": front_page_text_style,
                        "actual_style": paragraph.style,
                        "text": paragraph.text,
                    }
                )

    # Citation heading + text (optional section)
    citation_heading = _find_first_text(front_page, "Citation")
    if citation_heading is not None:
        if citation_heading.style != heading_front_page_style:
            mismatches.append(
                {
                    "type": "front_page",
                    "part": "citation_heading",
                    "index": citation_heading.index,
                    "expected_style": heading_front_page_style,
                    "actual_style": citation_heading.style,
                    "text": citation_heading.text,
                }
            )

        citation_body = _collect_until(front_page, citation_heading.index, [])
        for paragraph in citation_body:
            if paragraph.style != front_page_text_style:
                mismatches.append(
                    {
                        "type": "front_page",
                        "part": "citation_text",
                        "index": paragraph.index,
                        "expected_style": front_page_text_style,
                        "actual_style": paragraph.style,
                        "text": paragraph.text,
                    }
                )

    # Body heading structure
    headings = extract_headings(target_docx_path)
    found_h1_texts = []
    for heading in headings:
        if heading["style"] == "Heading 1":
            found_h1_texts.append(heading["text"])

    expected_h1 = CANONICAL_STRUCTURE["main_sections"]

    for section_name in expected_h1:
        section_found = False
        for heading_text in found_h1_texts:
            if _section_name_matches(heading_text, section_name):
                section_found = True
                break

        if section_found is False:
            mismatches.append(
                {
                    "type": "body_structure",
                    "part": "missing_heading_1",
                    "index": None,
                    "expected_style": "Heading 1",
                    "actual_style": None,
                    "text": section_name,
                }
            )

    for heading_text in found_h1_texts:
        is_known = False
        for section_name in expected_h1:
            if _section_name_matches(heading_text, section_name):
                is_known = True
                break
        if is_known is False:
            mismatches.append(
                {
                    "type": "body_structure",
                    "part": "unexpected_heading_1",
                    "index": None,
                    "expected_style": "Canonical Heading 1",
                    "actual_style": "Heading 1",
                    "text": heading_text,
                }
            )

    found_order = []
    for heading_text in found_h1_texts:
        idx = _canonical_index(heading_text)
        if idx is not None:
            found_order.append(idx)

    sorted_order = sorted(found_order)
    if found_order != sorted_order:
        mismatches.append(
            {
                "type": "body_structure",
                "part": "heading_order",
                "index": None,
                "expected_style": "Canonical Heading 1 Order",
                "actual_style": "Out of order",
                "text": found_h1_texts,
            }
        )

    # Reference style checks
    reference_bounds = get_section_bounds(paragraphs, "References")
    if reference_bounds is None:
        mismatches.append(
            {
                "type": "references",
                "part": "references_heading",
                "index": None,
                "expected_style": "Heading 1",
                "actual_style": None,
                "text": "References",
            }
        )
    else:
        start, end = reference_bounds
        expected_ref_style = CANONICAL_STRUCTURE["style_rules"]["reference_entry"]

        for paragraph in paragraphs[start + 1:end]:
            if paragraph.is_empty is True:
                continue
            if paragraph.style != expected_ref_style:
                mismatches.append(
                    {
                        "type": "references",
                        "part": "reference_entry_style",
                        "index": paragraph.index,
                        "expected_style": expected_ref_style,
                        "actual_style": paragraph.style,
                        "text": paragraph.text,
                    }
                )

    return mismatches


def compare_template_and_document(template_path, target_docx_path):
    template_styles = extract_template_styles(template_path)
    mismatches = compare_document_styles(target_docx_path)
    headings = extract_headings(target_docx_path)

    return {
        "template_style_count": len(template_styles),
        "target_heading_count": len(headings),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }




if __name__ == "__main__":
    target_doc = "tests/section_sepcif_docs_for_testing/Polly_2025_JUTLP.docx"
    template_doc = "app/domain/JUTLP Template 2026.docx"

    if len(sys.argv) > 1:
        target_doc = sys.argv[1]
    if len(sys.argv) > 2:
        template_doc = sys.argv[2]

    result = compare_template_and_document(template_doc, target_doc)
    pprint.pprint(result)
