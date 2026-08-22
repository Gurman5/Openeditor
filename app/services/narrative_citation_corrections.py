"""Fix APA narrative citation ampersands as Word tracked changes.

APA narrative citations use "and" between two authors in running prose:
"Smith and Jones (2024)". Parenthetical citations keep the ampersand:
"(Smith & Jones, 2024)".
"""

from __future__ import annotations

import os
import re
import zipfile

from lxml import etree

from app.services.language_corrections import (
    _SKIP_STYLES,
    WQ,
    _get_style_name,
    _merge_adjacent_runs,
    _split_run_at_match,
)

_NAME_TOKEN = r"[A-Z][A-Za-z'.-]+"
_NAME_PARTICLE = r"(?:da|de|del|den|der|di|du|la|le|van|von)"
_AUTHOR_NAME = rf"{_NAME_TOKEN}(?:\s+(?:{_NAME_PARTICLE}|{_NAME_TOKEN}))*"
_NARRATIVE_CITATION_RE = re.compile(
    rf"\b(?P<left>{_AUTHOR_NAME})\s+(?P<amp>&)\s+"
    rf"(?P<right>{_AUTHOR_NAME})\s+\(\s*\d{{4}}[a-z]?\s*\)"
)
_SKIP_STYLE_IDS = _SKIP_STYLES | {
    "Heading1",
    "Heading2",
    "Heading3",
    "Heading4",
    "APA7ReferenceListEntry",
    "APAReferenceListEntry",
    "ArticleTitle",
    "AuthorAffiliations",
}


def _bracket_spans(text: str) -> list[tuple[int, int]]:
    """Return spans covered by matched or unclosed brackets."""
    spans: list[tuple[int, int]] = []
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for i, ch in enumerate(text):
        if ch in "([{":
            stack.append((ch, i))
        elif ch in pairs and stack and stack[-1][0] == pairs[ch]:
            _, start = stack.pop()
            spans.append((start, i + 1))
    for _, start in stack:
        spans.append((start, len(text)))
    return spans


def _in_any_span(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= pos < end for start, end in spans)


def _plain_text(para_el: etree._Element) -> str:
    chunks: list[str] = []
    for run_el in para_el.iter(f"{WQ}r"):
        parent = run_el.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        for text_el in run_el.findall(f"{WQ}t"):
            chunks.append(text_el.text or "")
    return "".join(chunks)


def _replace_ampersand_at_offset(
    para_el: etree._Element,
    target_offset: int,
    change_id: int,
) -> int:
    offset = 0
    for run_el in para_el.iter(f"{WQ}r"):
        parent = run_el.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        text_el = run_el.find(f"{WQ}t")
        if text_el is None:
            continue
        run_text = text_el.text or ""
        run_end = offset + len(run_text)
        if offset <= target_offset < run_end:
            local_offset = target_offset - offset
            for match in re.finditer(r"&", run_text):
                if match.start() == local_offset:
                    return _split_run_at_match(run_el, match, "and", change_id)
            return change_id
        offset = run_end
    return change_id


def _apply_corrections_to_para(
    para_el: etree._Element,
    change_id: int,
    made: list[dict],
) -> int:
    """Replace narrative-citation ampersands in one paragraph."""
    _merge_adjacent_runs(para_el)

    while True:
        para_text = _plain_text(para_el)
        bracket_spans = _bracket_spans(para_text)
        target: re.Match | None = None

        for match in _NARRATIVE_CITATION_RE.finditer(para_text):
            amp_pos = match.start("amp")
            if not _in_any_span(amp_pos, bracket_spans):
                target = match
                break

        if target is None:
            return change_id

        before_id = change_id
        change_id = _replace_ampersand_at_offset(para_el, target.start("amp"), change_id)
        if change_id == before_id:
            return change_id

        made.append(
            {
                "original": "&",
                "replacement": "and",
                "citation": target.group(0),
            }
        )


def apply_narrative_citation_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Apply tracked "&" -> "and" fixes for APA narrative citations."""
    with zipfile.ZipFile(input_path, "r") as z:
        doc_xml = z.read("word/document.xml")

    doc_root = etree.fromstring(doc_xml)
    made: list[dict] = []

    for para_el in doc_root.iter(f"{WQ}p"):
        if _get_style_name(para_el) in _SKIP_STYLE_IDS:
            continue
        if "&" not in _plain_text(para_el):
            continue
        next_change_id = _apply_corrections_to_para(para_el, next_change_id, made)

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    tmp = output_path + ".narrcite.tmp"
    try:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
            tmp, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return next_change_id, made
