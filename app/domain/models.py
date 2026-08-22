from dataclasses import dataclass


@dataclass
class ParagraphRecord:
    index: int
    text: str
    style: str
    is_empty: bool
    # True when every run in the paragraph is bold (and the paragraph has at
    # least one run). Used to detect pseudo-headings — paragraphs the author
    # styled visually (bold, sometimes larger font) without applying the
    # Heading 1 / Heading 2 Word styles. Without this signal, short bold
    # lines leak into surrounding section body and get mis-flagged as
    # single-sentence paragraphs.
    is_all_bold: bool = False
