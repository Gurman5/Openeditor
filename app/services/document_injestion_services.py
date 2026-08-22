from pathlib import Path

from docx import Document


def read_docx(filepath : Path) -> Document:
    f = open(filepath, 'rb')
    document = Document(f)
    f.close()
    return document


