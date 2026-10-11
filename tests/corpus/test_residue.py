from docx import Document

from tools.corpus.checks.residue import (
    check_residue,
)


def _make_docx(path, paragraphs):
    document = Document()

    for text in paragraphs:
        document.add_paragraph(text)

    document.save(path)


def test_clean_document_passes(tmp_path):
    input_path = tmp_path / "input.docx"
    output_path = tmp_path / "output.docx"

    _make_docx(
        input_path,
        [
            "Example APA paper",
            "Normal body text.",
        ],
    )

    _make_docx(
        output_path,
        [
            "Example APA paper",
            "Normal body text.",
        ],
    )

    result = check_residue(
        output_path,
        input_path,
    )

    assert result["status"] == "pass"


def test_practitioner_notes_added_fails(tmp_path):
    input_path = tmp_path / "input.docx"
    output_path = tmp_path / "output.docx"

    _make_docx(
        input_path,
        [
            "Example APA paper",
            "Normal body text.",
        ],
    )

    _make_docx(
        output_path,
        [
            "Example APA paper",
            "Practitioner Notes",
        ],
    )

    result = check_residue(
        output_path,
        input_path,
    )

    assert result["status"] == "fail"


def test_credit_added_fails(tmp_path):
    input_path = tmp_path / "input.docx"
    output_path = tmp_path / "output.docx"

    _make_docx(
        input_path,
        [
            "Example APA paper",
        ],
    )

    _make_docx(
        output_path,
        [
            "Example APA paper",
            "CRediT author statement",
        ],
    )

    result = check_residue(
        output_path,
        input_path,
    )

    assert result["status"] == "fail"


def test_existing_residue_in_input_is_na(tmp_path):
    input_path = tmp_path / "input.docx"
    output_path = tmp_path / "output.docx"

    _make_docx(
        input_path,
        [
            "Practitioner Notes",
        ],
    )

    _make_docx(
        output_path,
        [
            "Practitioner Notes",
        ],
    )

    result = check_residue(
        output_path,
        input_path,
    )

    assert result["status"] == "na"