from docx import Document

from tools.corpus.checks.appendices import (
    check_appendices,
)


def _make_docx(path, paragraphs):
    document = Document()

    for text in paragraphs:
        document.add_paragraph(text)

    document.save(path)


def test_appendix_preserved_passes(tmp_path):
    input_path = tmp_path / "input.docx"
    output_path = tmp_path / "output.docx"

    _make_docx(
        input_path,
        [
            "Example paper",
            "Appendix A",
            "Additional material.",
        ],
    )

    _make_docx(
        output_path,
        [
            "Example paper",
            "Appendix A",
            "Additional material.",
        ],
    )

    result = check_appendices(
        output_path,
        input_path,
    )

    assert result["status"] == "pass"


def test_missing_appendix_fails(tmp_path):
    input_path = tmp_path / "input.docx"
    output_path = tmp_path / "output.docx"

    _make_docx(
        input_path,
        [
            "Example paper",
            "Appendix A",
            "Additional material.",
        ],
    )

    _make_docx(
        output_path,
        [
            "Example paper",
        ],
    )

    result = check_appendices(
        output_path,
        input_path,
    )

    assert result["status"] == "fail"


def test_no_input_appendix_is_na(tmp_path):
    input_path = tmp_path / "input.docx"
    output_path = tmp_path / "output.docx"

    _make_docx(
        input_path,
        [
            "Example paper",
            "Normal body text.",
        ],
    )

    _make_docx(
        output_path,
        [
            "Example paper",
            "Normal body text.",
        ],
    )

    result = check_appendices(
        output_path,
        input_path,
    )

    assert result["status"] == "na"


def test_multiple_appendices_preserved(tmp_path):
    input_path = tmp_path / "input.docx"
    output_path = tmp_path / "output.docx"

    _make_docx(
        input_path,
        [
            "Example paper",
            "Appendix A",
            "First appendix.",
            "Appendix B",
            "Second appendix.",
        ],
    )

    _make_docx(
        output_path,
        [
            "Example paper",
            "Appendix A",
            "First appendix.",
            "Appendix B",
            "Second appendix.",
        ],
    )

    result = check_appendices(
        output_path,
        input_path,
    )

    assert result["status"] == "pass"