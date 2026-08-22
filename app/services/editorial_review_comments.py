"""Turn LLM editorial review notes into Word comments on the reviewed .docx.

The plan mirrors the shape used by `_apply_document_body_plan` so the existing
`_write_single_comment_docx` helper can anchor each note to a section heading.
Paragraph-specific notes use the LLM quote when possible; other notes fall
back to the heading paragraph of the note's section.
"""

import re

from app.services.ai.editorial_review_service import run_editorial_review
from app.services.document_analysis_services import load_paragraphs
from app.services.jutlp_validator import validate

SECTION_TEXT_ALIASES = {
    "introduction": "introduction",
    "literature": "literature",
    "literature review": "literature",
    "method": "method",
    "methods": "method",
    "methodology": "method",
    "results": "results",
    "findings": "results",
    "discussion": "discussion",
    "conclusion": "conclusion",
    "conclusions": "conclusion",
    "acknowledgements": "acknowledgements",
    "acknowledgments": "acknowledgements",
    "references": "references",
    "abstract": "abstract",
    "practitioner notes": "practitioner_notes",
    "keywords": "keywords",
    "citation": "citation",
}

CATEGORY_TO_SECTION_KEY = {
    "title_quality": "title",
    "abstract_quality": "abstract",
    "practitioner_notes_quality": "practitioner_notes",
    "introduction_quality": "introduction",
    "literature_quality": "literature",
    "method_quality": "method",
    "results_quality": "results",
    "discussion_quality": "discussion",
    "conclusion_quality": "conclusion",
    "apa_style": "references",
    "acknowledgements_quality": "acknowledgements",
    "general": None,
}

SEVERITY_PREFIX = {
    "high": "[High]",
    "medium": "[Medium]",
    "low": "[Low]",
}

BODY_SECTION_KEYS = {
    "introduction",
    "literature",
    "method",
    "results",
    "discussion",
    "conclusion",
}


def _build_section_anchor_map(paragraphs) -> dict:
    anchors = {}

    article_title = next(
        (p for p in paragraphs if p.style == "Article Title" and not p.is_empty),
        None,
    )
    if article_title is not None:
        anchors["title"] = article_title.index
    elif paragraphs:
        non_empty = next((p for p in paragraphs if not p.is_empty), None)
        if non_empty is not None:
            anchors["title"] = non_empty.index

    for p in paragraphs:
        if p.is_empty:
            continue
        key = SECTION_TEXT_ALIASES.get(p.text.strip().lower())
        if key is None:
            continue
        if key not in anchors:
            anchors[key] = p.index

    return anchors


def _normalise_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


def _section_key_from_heading(text: str) -> str | None:
    low = _normalise_text(text).rstrip(":")
    key = SECTION_TEXT_ALIASES.get(low)
    if key is not None:
        return key
    for alias, alias_key in SECTION_TEXT_ALIASES.items():
        if low.startswith(alias + ":"):
            return alias_key
    return None


def _section_ranges(paragraphs) -> dict:
    headings = [
        (p.index, _section_key_from_heading(p.text))
        for p in paragraphs
        if not p.is_empty and p.style == "Heading 1"
    ]
    headings = [(i, key) for i, key in headings if key is not None]
    ranges = {}
    for pos, (start, key) in enumerate(headings):
        if key not in ranges:
            end = headings[pos + 1][0] if pos + 1 < len(headings) else len(paragraphs)
            ranges[key] = (start, end)
    return ranges


def _note_section_key(note: dict) -> str | None:
    key = SECTION_TEXT_ALIASES.get((note.get("section") or "").strip().lower())
    if key is not None:
        return key
    return CATEGORY_TO_SECTION_KEY.get((note.get("category") or "").strip().lower())


def _is_table_or_figure_text(p) -> bool:
    style = (p.style or "").lower()
    text = (p.text or "").strip()
    return (
        "table" in style
        or "figure" in style
        or style == "caption"
        or re.match(r"^(table|figure)\s+\d+\b", text, re.IGNORECASE) is not None
    )


def _is_body_prose(p) -> bool:
    return (
        not p.is_empty
        and p.style == "Normal"
        and not p.is_all_bold
        and not _is_table_or_figure_text(p)
    )


def _is_paragraph_length_note(note: dict) -> bool:
    text = _normalise_text(
        (note.get("message") or "") + " " + (note.get("suggestion") or "")
    )
    return "paragraph" in text and "sentence" in text


def _quote_anchor(note: dict, paragraphs, ranges: dict, body_only=False) -> int | None:
    quote = _normalise_text(note.get("quote") or "")
    if quote == "":
        return None
    key = _note_section_key(note)
    if key in BODY_SECTION_KEYS and key in ranges:
        start, end = ranges[key]
        search = paragraphs[start + 1 : end]
    elif body_only:
        search = []
        for body_key in BODY_SECTION_KEYS:
            if body_key in ranges:
                start, end = ranges[body_key]
                search.extend(paragraphs[start + 1 : end])
    else:
        search = paragraphs
    for p in search:
        if _is_body_prose(p) and quote in _normalise_text(p.text):
            return p.index
    return None


def _resolve_anchor(note: dict, anchor_map: dict, default_index: int) -> int:
    section_raw = (note.get("section") or "").strip().lower()
    key = SECTION_TEXT_ALIASES.get(section_raw)
    if key is None:
        category = (note.get("category") or "").strip().lower()
        key = CATEGORY_TO_SECTION_KEY.get(category)
    if key is not None and key in anchor_map:
        return anchor_map[key]
    return default_index


def _format_comment(note: dict) -> str:
    severity = (note.get("severity") or "").strip().lower()
    prefix = SEVERITY_PREFIX.get(severity, "")
    section = (note.get("section") or "").strip()
    category = (note.get("category") or "").strip()
    message = (note.get("message") or "").strip()
    suggestion = (note.get("suggestion") or "").strip()

    header_bits = [b for b in [prefix, section or category] if b]
    header = " ".join(header_bits).strip()

    lines = []
    if header:
        lines.append(header)
    if message:
        lines.append(message)
    if suggestion:
        lines.append(f"Suggestion: {suggestion}")
    return "\n".join(lines)


def _comment_family(message: str) -> str | None:
    low = _normalise_text(message)
    if "acronym" in low:
        return "acronym"
    if "abbreviation" in low:
        return "abbreviation"
    return None


def _group_similar_comments(comments: list[dict]) -> list[dict]:
    """Group high-volume same-family LLM notes into one comment."""
    grouped: dict[str, list[dict]] = {}
    output: list[dict] = []

    for comment in comments:
        family = _comment_family(comment.get("message", ""))
        if family is None:
            output.append(comment)
            continue
        grouped.setdefault(family, []).append(comment)

    for family, items in grouped.items():
        first = min(items, key=lambda item: item.get("anchor_pos", 0))
        count = len(items)
        label = "acronym" if family == "acronym" else "abbreviation"
        message = (
            f"Please check {label} use across the manuscript. {count} similar "
            f"{label} notes were grouped here to keep the comment pane "
            "manageable."
        )
        if family == "acronym":
            message += " Expand acronyms on first use and use the acronym form thereafter."
        output.append({"anchor_pos": first.get("anchor_pos", 0), "message": message})

    return sorted(output, key=lambda item: item.get("anchor_pos", 0))


def build_editorial_review_comment_plan(docx_path: str) -> dict:
    try:
        deterministic = validate(docx_path)
    except Exception as exc:
        return {
            "action": "none",
            "reason": f"deterministic validate failed: {exc}",
            "comments": [],
        }

    try:
        review = run_editorial_review(docx_path, deterministic_check_result=deterministic)
    except Exception as exc:
        return {
            "action": "none",
            "reason": f"editorial review LLM failed: {exc}",
            "comments": [],
        }

    raw_notes = [
        {
            "category": n.category,
            "severity": n.severity,
            "section": n.section,
            "message": n.message,
            "suggestion": n.suggestion,
            "quote": n.quote,
        }
        for n in (review.notes or [])
    ]
    if not raw_notes:
        return {
            "action": "none",
            "reason": "No editorial notes returned by LLM",
            "comments": [],
        }

    paragraphs = load_paragraphs(docx_path)
    if not paragraphs:
        return {
            "action": "none",
            "reason": "Document has no paragraphs",
            "comments": [],
        }

    anchor_map = _build_section_anchor_map(paragraphs)
    ranges = _section_ranges(paragraphs)
    default_index = anchor_map.get("title", paragraphs[0].index)

    comments = []
    for note in raw_notes:
        message = _format_comment(note)
        if not message:
            continue
        paragraph_length_note = _is_paragraph_length_note(note)
        quote_anchor = _quote_anchor(note, paragraphs, ranges, paragraph_length_note)
        if paragraph_length_note and quote_anchor is None:
            continue
        anchor_pos = quote_anchor or _resolve_anchor(note, anchor_map, default_index)
        comments.append({"anchor_pos": anchor_pos, "message": message})

    if not comments:
        return {
            "action": "none",
            "reason": "No editorial notes had a usable anchor",
            "comments": [],
        }

    comments = _group_similar_comments(comments)

    return {
        "action": "add_editorial_review_comments",
        "reason": f"{len(comments)} editorial review note(s) from LLM",
        "comments": comments,
    }
