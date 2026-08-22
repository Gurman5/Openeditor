"""Spell out whole numbers 0-9 in running prose as tracked changes.

Most academic style guides (including the journal's house style) require small
whole numbers to be written out as words when they appear in a sentence — so
"We surveyed nine participants" rather than "We surveyed 9 participants".

The rule has many real-world exceptions: numbers inside parentheses, numbers
attached to units of measurement, numbered references like "Section 5" or
"Table 2", dates, decimal values, version numbers, and so on. We err on the
side of NOT replacing when the surrounding context is ambiguous — the human
editor can always spell out a missed case, but every false positive costs them
a tracked-change rejection click.

Replacements are emitted as `<w:del>` + `<w:ins>` pairs so the editor sees
them in Word's "All Markup" view and accepts or rejects each individually.
"""

from __future__ import annotations

import os
import re
import zipfile

from lxml import etree

from app.services.document_zones import iter_paragraphs_with_zone, should_skip_paragraph

# Reuse the same skip styles and zone iterator as the AU spelling pass —
# headings, reference entries, captions, and front-matter labels must not be
# touched, and the body of Acknowledgements/References (zone == "outside")
# must be skipped wholesale.
from app.services.language_corrections import (
    WQ,
    _merge_adjacent_runs,
    _split_run_at_match,
)
from app.services.quotation_utils import find_quote_spans

_DIGIT_TO_WORD = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}

# Words that, when they immediately precede a digit, mark it as a label
# reference (e.g. "Section 5", "Table 2") rather than a count in prose.
# Matched case-insensitively. Trailing dot in the source is allowed.
_LABEL_WORDS = {
    "section", "sections",
    "table", "tables",
    "figure", "figures", "fig", "figs",
    "step", "steps",
    "equation", "equations", "eq", "eqs",
    "appendix", "appendices",
    "phase", "phases",
    "round", "rounds",
    "stage", "stages",
    "volume", "volumes", "vol",
    "issue", "issues", "iss",
    "page", "pages", "p", "pp",
    "chapter", "chapters", "ch",
    "day", "days",
    "year", "years",
    "week", "weeks",
    "month", "months",
    "item", "items",
    "question", "questions", "q",
    "group", "groups",
    "level", "levels",
    "no",
    "number", "numbers",
    "model", "models",
    # Participant identifiers — qualitative research routinely labels
    # interviewees as "student 3", "participant 5", etc. These are
    # identifiers, not counts, so the digit must stay numeric.
    "student", "students",
    "participant", "participants",
    "respondent", "respondents",
    "interviewee", "interviewees",
    "informant", "informants",
    "subject", "subjects",
    # Statistical labels.
    "n", "m", "sd", "df", "f", "t", "r",
}

# Units that, when they follow a digit (with or without a space), mark it as
# a measurement and therefore not eligible for spelling out.
# Symbol units (non-word chars like % and °) don't need a trailing word
# boundary; alphabetic units do, so "5m" matches but "5may" doesn't.
_SYMBOL_UNITS = ("%", "°c", "°f", "°")
_WORD_UNITS = (
    "mm", "cm", "m", "km",
    "kg", "g", "mg",
    "ml", "l",
    "s", "sec", "secs", "min", "mins", "hr", "hrs", "h",
    "hz", "khz", "mhz", "ghz",
    "kb", "mb", "gb", "tb",
    "px", "pt",
)
_UNIT_FOLLOWING = re.compile(
    r"^\s*(?:"
    + "|".join(re.escape(u) for u in _SYMBOL_UNITS)
    + r"|(?:"
    + "|".join(re.escape(u) for u in _WORD_UNITS)
    + r")\b)",
    re.IGNORECASE,
)

_MONTH_NAMES = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
)
_MONTH_PRECEDING = re.compile(
    r"\b(" + "|".join(_MONTH_NAMES) + r")\.?\s+$",
    re.IGNORECASE,
)
# A digit acting as a day-of-month: "5 May 2024" or "5 May".
_MONTH_FOLLOWING = re.compile(
    r"^\s+(" + "|".join(_MONTH_NAMES) + r")\b",
    re.IGNORECASE,
)
# Year-like pattern after "5, 2024" or "5/2024".
_YEAR_FOLLOWING = re.compile(r"^[,/]\s*\d{2,4}\b")

# Last "word" preceding the digit — letters or dot, no whitespace.
_LAST_WORD = re.compile(r"([A-Za-z][A-Za-z\.]*)\.?\s*$")

# A standalone single digit 0-9 — no other digit, letter, or dot adjacent.
# Using lookarounds rather than \b so "9.10" does NOT match the "9" or the
# "10" individually (the dot is the disqualifier).
_DIGIT_PATTERN = re.compile(r"(?<![\w.])([0-9])(?![\w.])")


def _bracket_spans(text: str) -> list[tuple[int, int]]:
    """Return character spans (start, end) covered by paren/bracket/brace pairs.

    Unmatched open-brackets extend to end of string so we conservatively skip
    everything after them.
    """
    spans: list[tuple[int, int]] = []
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    openers = set("([{")
    for i, ch in enumerate(text):
        if ch in openers:
            stack.append((ch, i))
        elif ch in pairs:
            if stack and stack[-1][0] == pairs[ch]:
                _, start = stack.pop()
                spans.append((start, i + 1))
    # Any unclosed opener — treat from its position to end as bracketed.
    for _, start in stack:
        spans.append((start, len(text)))
    return spans


def _in_any_span(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= pos < end for start, end in spans)


def _is_sentence_start(text: str, pos: int) -> bool:
    """True if position is at the start of a sentence.

    "Start of sentence" = beginning of paragraph, or the previous non-space
    character is one of `.!?` (or `:` followed by a capital — close enough).
    """
    j = pos - 1
    while j >= 0 and text[j].isspace():
        j -= 1
    if j < 0:
        return True
    return text[j] in ".!?"


def _should_replace(text: str, match_start: int, bracket_spans: list[tuple[int, int]]) -> bool:
    """Apply the deny-list of contexts. Return True only when safe to replace."""
    if _in_any_span(match_start, bracket_spans):
        return False

    if _is_sentence_start(text, match_start):
        return False

    # Look-behind for a label word like "Section", "Table 2", "n =".
    before = text[:match_start]
    last_word_match = _LAST_WORD.search(before)
    if last_word_match:
        last_word = last_word_match.group(1).rstrip(".").lower()
        if last_word in _LABEL_WORDS:
            return False

    # "= 5" patterns are stat reports — keep digits.
    stripped_before = before.rstrip()
    if stripped_before.endswith(("=", "≈", "≤", "≥", "<", ">", "+", "-", "×", "*", "/")):
        return False

    after = text[match_start + 1:]

    # Unit-following: "5%", "5 km".
    if _UNIT_FOLLOWING.match(after):
        return False

    # Date: "5 May", "5, 2024", "5/2024".
    if _MONTH_FOLLOWING.match(after) or _YEAR_FOLLOWING.match(after):
        return False
    if _MONTH_PRECEDING.search(before):
        return False

    # Hyphen-attached: "5-year-old", "9-point". Hyphen on either side
    # adjoining a letter means we treat it as a compound modifier.
    if before.endswith("-"):
        # Only reject if the char before the hyphen is alpha/digit (not a
        # leading dash like a list bullet).
        if len(before) >= 2 and before[-2].isalnum():
            return False
    if after.startswith("-") and len(after) >= 2 and after[1].isalpha():
        return False

    return True


def _para_plain_text(para_el: etree._Element) -> str:
    """Concatenate the run text of `para_el` excluding tracked-change wrappers."""
    chunks: list[str] = []
    for r in para_el.iter(f"{WQ}r"):
        parent = r.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        for t in r.findall(f"{WQ}t"):
            chunks.append(t.text or "")
    return "".join(chunks)


def _apply_corrections_to_para(
    para_el: etree._Element,
    change_id: int,
    made: list[dict],
) -> int:
    """Apply digit→word tracked changes to one paragraph, run-by-run."""
    _merge_adjacent_runs(para_el)

    # Build paragraph-level context for exclusion checks once. We re-run the
    # search per-run for replacement, but the bracket-span analysis and
    # neighbouring-word checks need the whole paragraph.
    para_text = _para_plain_text(para_el)
    if not _DIGIT_PATTERN.search(para_text):
        return change_id

    bracket_spans = _bracket_spans(para_text)

    # We loop because each replacement re-shapes the run list.
    changed = True
    while changed:
        changed = False
        # Recompute paragraph plain text + bracket spans every iteration —
        # the previous replacement may have shifted offsets.
        para_text = _para_plain_text(para_el)
        bracket_spans = _bracket_spans(para_text)
        # Quote-protection: digits inside direct quotations retain the
        # source's original form (e.g. a participant quote "3 students…"
        # stays as `3`, not `three`).
        quote_spans = find_quote_spans(para_text)

        # Walk the runs in document order. Track the cumulative offset of
        # each run's text within the paragraph so we can map a per-run
        # match back to the paragraph-level context check.
        offset = 0
        target_run = None
        target_match: re.Match | None = None
        target_para_offset = 0

        for r in para_el.iter(f"{WQ}r"):
            parent = r.getparent()
            if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
                # Tracked-change wrappers don't contribute visible text and
                # mustn't be edited.
                continue
            t_el = r.find(f"{WQ}t")
            if t_el is None:
                continue
            run_text = t_el.text or ""

            for m in _DIGIT_PATTERN.finditer(run_text):
                para_pos = offset + m.start()
                # Skip digits sitting inside a direct quotation.
                if any(
                    para_pos < e and s < para_pos + (m.end() - m.start())
                    for s, e in quote_spans
                ):
                    continue
                if _should_replace(para_text, para_pos, bracket_spans):
                    target_run = r
                    target_match = m
                    target_para_offset = para_pos
                    break
            if target_run is not None:
                break
            offset += len(run_text)

        if target_run is None or target_match is None:
            return change_id

        digit = target_match.group(1)
        word = _DIGIT_TO_WORD[digit]
        # Match capitalisation context: digits don't have case, but if the
        # digit is the first word after a sentence-ending period that we
        # didn't filter, default to lowercase. Sentence-start was already
        # filtered.
        replacement = word

        next_id = _split_run_at_match(target_run, target_match, replacement, change_id)
        made.append(
            {
                "original": digit,
                "replacement": replacement,
                "para_offset": target_para_offset,
            }
        )
        change_id = next_id
        changed = True

    return change_id


def apply_number_word_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Scan body paragraphs and emit tracked-change replacements for digits 0-9.

    Returns `(next_change_id, corrections_made)` where each correction is a
    dict with `original`, `replacement`, and `para_offset` keys.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        doc_xml = z.read("word/document.xml")

    doc_root = etree.fromstring(doc_xml)
    made: list[dict] = []

    # Zone-aware iteration — replaces develop's _is_references_heading branch.
    # The shared helpers skip not just References but also Acknowledgements,
    # captions (Figure/Table Title/Number), and front-matter labels uniformly,
    # matching what the acronym and AU-spelling passes already do.
    for para_el, zone in iter_paragraphs_with_zone(doc_root):
        if should_skip_paragraph(para_el, zone):
            continue
        next_change_id = _apply_corrections_to_para(para_el, next_change_id, made)

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    tmp = output_path + ".numwords.tmp"
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
