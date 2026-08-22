from pathlib import Path

import app.services.output_filename as output_filename
from app.cli_copybot import _is_generic_copyedit_output, _rename_generic_copyedit_output


def test_generic_copyedit_output_matches_input_stem_only():
    input_path = Path("/tmp/ePortfolio+traditions.docx")

    assert _is_generic_copyedit_output(input_path, "/tmp/ePortfolio+traditions_CopyEdit.docx") is True
    assert _is_generic_copyedit_output(input_path, "/tmp/Identifiable+manuscript_4C_ID_model_CopyEdit.docx") is True
    assert _is_generic_copyedit_output(input_path, "/tmp/Sankey_JUTLP_2024_CopyEdit1.docx") is False


def test_generic_copyedit_output_is_renamed_to_jutlp_name(tmp_path, monkeypatch):
    input_path = tmp_path / "ePortfolio+traditions.docx"
    output_path = tmp_path / "ePortfolio+traditions_CopyEdit.docx"
    output_path.write_text("docx")

    monkeypatch.setattr(
        output_filename,
        "build_output_filename_from_author_line",
        lambda *_args, **_kwargs: "Sankey_JUTLP_2024_CopyEdit1.docx",
    )

    result = _rename_generic_copyedit_output(input_path, str(output_path), "Professor Michael Sankey")

    assert result == str(tmp_path / "Sankey_JUTLP_2024_CopyEdit1.docx")
    assert Path(result).read_text() == "docx"
    assert output_path.exists() is False
