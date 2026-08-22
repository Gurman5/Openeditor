import re

from app.domain.jutlp_editorial_examples import EDITORIAL_EXAMPLES
from app.domain.jutlp_guidelines import JUTLP_GUIDELINES
from app.domain.models import ParagraphRecord
from app.services.document_analysis_services import (
    extract_abstract,
    extract_keywords,
    extract_practitioner_notes,
    get_front_page,
    word_count,
)

# JUTLP's maximum title length. Used to pre-compute word count for the LLM
# so it doesn't have to count tokens itself (LLMs are unreliable word
# counters and were flagging short titles as "too long").
JUTLP_TITLE_WORD_LIMIT = 15

VALID_CATEGORIES = [
    "title_quality",
    "abstract_quality",
    "practitioner_notes_quality",
    "introduction_quality",
    "literature_quality",
    "method_quality",
    "results_quality",
    "discussion_quality",
    "conclusion_quality",
    "apa_style",
    "acknowledgements_quality",
    "appendices_quality",
    "general",
]

SYSTEM_PROMPT_TEMPLATE = """\
You are an activist sub-editor / copy editor for the Journal of University \
Teaching and Learning Practice (JUTLP). You review manuscripts that have \
ALREADY been accepted for publication after ~8-9 months of peer review, and \
your job is to surface polish-level improvements for the handling editor to \
consider — not to re-review the substance of the paper.

Your output is read by an editor, never shown directly to the author. The \
editor decides what (if anything) to pass on. Act accordingly: make \
suggestions, don't issue verdicts.

## JUTLP Editorial Guidelines

{guidelines}

## Your Task

Review the manuscript content below against these guidelines. For each issue \
you find, produce an editorial note with:
- category: one of [{categories}]
- severity: "high" (must fix before submission), "medium" (should fix), \
"low" (suggestion for improvement)
- section: which section of the paper the issue is in
- message: clear, specific description of the problem — quote the \
problematic text where possible
- suggestion: a focused fix — a replacement word, corrected phrase, or at \
most a short example sentence the author can adapt. Feedback, not \
ghostwriting.
- quote: a short verbatim excerpt (up to ~20 words) copied exactly from the \
manuscript text that the issue applies to. Leave as an empty string ("") only \
if the issue is section-level with no specific text to quote.

The message and suggestion must work together as a two-part unit: \
message = what is wrong, suggestion = a pointed fix the author can apply.

The following issues were already flagged by automated checks. Do NOT repeat \
or duplicate any of these in your notes — focus only on what they missed.

## Automated Check Results

### Structural / Rule Checks
{deterministic_results}

### Reference Checks
{ref_results}

## Structural Validation (false-positive review)

The automated structural checks above sometimes fire incorrectly. For example:
- A section titled "Introduction: Background and Motivation" may be flagged as \
"Introduction not found" because the checker expected an exact heading match.
- All Method subsection checks (MET001–MET00x) may fire when the "Method" \
section is absent — even though the section simply uses a heading like \
"Methodology".

Read the manuscript content and for each [FAIL] structural rule (SEC, MET, DIS, \
FP, SPE, CON, STY rules only — NOT CREF or REFE), decide:
- "confirm" — the failure is genuine given the manuscript
- "false_positive" — the check fired incorrectly (e.g. section exists under a \
  slightly different heading, or the failure cascaded from an unrelated cause)

Include your verdicts in the structural_validations output array. Only classify \
rules you have direct evidence about from the manuscript text. Leave out rules \
where you are unsure.

## Tone and Style of Feedback

- Frame feedback as **suggestions**, not directives. Prefer "Consider…", \
"You might…", "One option would be…" over "Change X to Y" or "This must be…".
- Do NOT rewrite the author's prose. When a change is worth considering, \
offer 2–3 alternative options (especially for titles, headings, and short \
phrasings) and let the editor choose — do not prescribe a single replacement.
- The paper has already passed peer review. Do NOT re-litigate the argument, \
methodology, or findings. If a section feels substantively weak, that is a \
signal for the handling editor, not a rewrite request — flag it briefly at \
low/medium severity and move on.
- Keep messages short and neutral in tone. Avoid language that sounds like a \
reviewer ("this is unclear", "the authors fail to…"). Prefer editor-facing \
phrasing ("the reader may benefit from…", "clarity could be improved by…").

## Important Rules

- Focus ONLY on content-level editorial quality that requires semantic \
understanding.
- Do NOT flag any of the following (they are checked by a separate automated \
validator and flagging them here wastes tokens):
  - Missing or extra sections/subsections
  - Section ordering
  - Abstract word count
  - Number of practitioner notes
  - Number of keywords
  - Missing front page elements (title, authors, affiliations)
  - Forbidden styles (e.g. Guidance Notes)
- Do NOT check references or citations (handled by a separate reference \
checker).
- Do NOT check in-text citation vs reference list matching.
- Title length: The user prompt shows the exact word count next to the \
title (e.g. "## Title (11 words; JUTLP limit is 15)"). Do NOT flag the title \
for length unless the given word count is STRICTLY GREATER THAN the limit. \
Never claim a title is "too long" when its word count is ≤ the limit. \
Colon-separated subtitles ("Main Title: Subtitle") are the standard format \
but a subtitle is NOT required — do NOT flag a title for lacking one. \
If the title exceeds the limit, propose 1–2 specific shorter alternative \
titles in the suggestion field.
- Significance statement: If the Introduction section is present, check \
whether it contains a paragraph that explicitly states the significance or \
contribution of the study. If this paragraph is absent, flag it as \
"introduction_quality". Do NOT flag this if the Introduction section itself \
is missing (that is a structural issue handled elsewhere).
- Colloquial language: Flag informal or colloquial words and phrases \
(e.g. "a lot of", "quick", "get", "show up", "kids") and suggest formal \
academic equivalents in the suggestion field (e.g. "numerous", "efficient", \
"obtain", "appear", "students").
- Paragraph length/shape: Flag only normal prose paragraphs within a body \
section (Introduction, Literature, Method, Results, Discussion, Conclusion). \
Do NOT flag headings, subheadings, table/figure captions, table text, \
reference entries, practitioner notes, keywords, or other front-page \
elements. Use category "general", note the section, and put the exact \
offending paragraph excerpt in quote.
- Suggestion scope: Suggestions are FEEDBACK, not rewrites. Your role is to \
help the author revise their own work — not to ghostwrite it. Do NOT \
produce full replacement paragraphs, replacement sections, or multi-sentence \
drafts. Keep each suggestion to at most one short example sentence, a \
replaced phrase, or a focused structural instruction (e.g. "move this \
sentence to the discussion", "add a sentence near the end stating X"). \
Never write "Replace the final paragraph with:" followed by a new paragraph.
- Subheading markers: The user prompt marks author-styled bold subheadings \
within section bodies using the form "[Subheading] <text>" on its own line. \
These are an internal annotation, NOT author content. Treat them as \
subheadings when reasoning about structure. Do NOT quote the word \
"[Subheading]" or any bracket notation in your message or suggestion — \
refer to the heading by its text only (e.g. the 'Theoretical Framework' \
subheading).
- Be specific: reference actual text from the manuscript when possible.
- Limit output to genuine issues. Do not pad with praise or trivial notes.

{examples}
"""

MAIN_SECTIONS = [
    "Introduction",
    "Literature",
    "Method",
    "Results",
    "Discussion",
    "Conclusion",
    "Conclusions",
    "Acknowledgements",
]

# Section names to match by text (case-insensitive), including common variants
SECTION_NAME_VARIANTS = {
    "Introduction": {"introduction"},
    "Literature": {"literature", "literature review"},
    "Method": {"method", "methods", "methodology"},
    "Results": {"results", "findings"},
    "Discussion": {"discussion"},
    "Conclusion": {"conclusion", "conclusions"},
    "Acknowledgements": {"acknowledgements", "acknowledgments"},
    "References": {"references"},
}

# Flattened lookup: lowercase text -> canonical section name
_TEXT_TO_SECTION = {}
for canonical, variants in SECTION_NAME_VARIANTS.items():
    for v in variants:
        _TEXT_TO_SECTION[v] = canonical

# Upper bound on heading length. Longer bold paragraphs are almost certainly
# captions or emphasised sentences, not headings.
MAX_PSEUDO_HEADING_CHARS = 120

# Marker used in the user prompt to annotate headings/subheadings within
# section bodies. We picked "[Subheading]" over "### " because the LLM
# previously quoted the markdown marker verbatim in its feedback ("the
# '### Theoretical Framework' heading"), leaking our internal prompt
# scaffolding into user-facing output. "[Subheading]" reads clearly as an
# annotation, and we also post-process notes to strip any stray markers.
SUBHEADING_MARKER = "[Subheading]"


def _is_table_or_figure_text(p: ParagraphRecord) -> bool:
    style = (p.style or "").lower()
    text = (p.text or "").strip()
    return (
        "table" in style
        or "figure" in style
        or style == "caption"
        or re.match(r"^(table|figure)\s+\d+\b", text, re.IGNORECASE) is not None
    )


def _is_pseudo_heading(p: ParagraphRecord) -> bool:
    """Detect paragraphs the author visually styled as a heading (all-bold,
    short, no sentence-ending punctuation) but tagged with 'Normal' style.

    These appear in submissions where the author didn't apply Heading 1/2
    styles. Without this, short bold subheadings bleed into section body text
    and trigger false-positive 'single-sentence paragraph' flags from the LLM.
    """
    if p.is_empty or not p.is_all_bold:
        return False
    text = p.text.strip()
    if len(text) > MAX_PSEUDO_HEADING_CHARS:
        return False
    # Headings rarely end in sentence-terminal punctuation. This also filters
    # out figure captions that happen to be fully bold.
    if text.endswith((".", "!", "?")):
        return False
    return True


def _canonical_section_for(text: str) -> str | None:
    """Map a heading's text to its canonical JUTLP section name, or None.

    Handles canonical names, aliases (``Methodology`` → ``Method``,
    ``Findings`` → ``Results``, ``Literature Review`` → ``Literature``) and
    titled headings (``Introduction: Background`` → ``Introduction``). Mirrors
    the alias handling the deterministic validator uses, so a section the
    validator recognises is never dropped from the LLM prompt.
    """
    t = (text or "").strip().lower()
    if not t:
        return None
    if t in _TEXT_TO_SECTION:
        return _TEXT_TO_SECTION[t]
    head = t.split(":", 1)[0].strip()
    if head != t:
        return _TEXT_TO_SECTION.get(head)
    return None


def _find_sections_by_text(
    paragraphs: list[ParagraphRecord],
) -> dict[str, tuple[int, int]]:
    """Find section boundaries by mapping heading text to canonical sections.

    Returns dict of canonical section name -> (start_index, end_index).

    A paragraph is treated as a section heading when its text maps to a
    canonical section (incl. aliases / titled headings) AND it is heading-like:
    a real heading style, a bold pseudo-heading, or its whole text is exactly a
    section name. The exact-text clause keeps unstyled headings working; the
    heading-like gate stops a body sentence that merely starts with a section
    word (``Discussion: we found…``) from being mistaken for a heading.
    """
    heading_positions = []
    for p in paragraphs:
        if p.is_empty:
            continue
        canonical = _canonical_section_for(p.text)
        if canonical is None:
            continue
        exact = p.text.strip().lower() in _TEXT_TO_SECTION
        if not (
            p.style in ("Heading 1", "Heading 2")
            or _is_pseudo_heading(p)
            or exact
        ):
            continue
        heading_positions.append((p.index, canonical))

    bounds = {}
    for i, (start, name) in enumerate(heading_positions):
        if i + 1 < len(heading_positions):
            end = heading_positions[i + 1][0]
        else:
            end = len(paragraphs)
        if name not in bounds:
            bounds[name] = (start, end)

    return bounds


def _get_section_text_by_bounds(
    paragraphs: list[ParagraphRecord],
    start: int,
    end: int,
) -> str:
    """Extract a section's body text between two paragraph indices.

    Heading-styled paragraphs and author-styled pseudo-headings (all-bold
    short lines) are rendered as ``[Subheading]`` markers so the LLM doesn't
    confuse them with body prose; table/figure caption text is dropped.
    """
    lines = []
    for p in paragraphs[start + 1 : end]:
        if p.is_empty:
            continue
        if _is_table_or_figure_text(p):
            continue
        if p.style in ("Heading 1", "Heading 2") or _is_pseudo_heading(p):
            lines.append(f"\n{SUBHEADING_MARKER} {p.text}\n")
        else:
            lines.append(p.text)
    return "\n".join(lines)


def _format_flagged_results(results: list[dict]) -> str:
    flagged = [r for r in results if r.get("status") != "pass"]
    if not flagged:
        return "None — all automated checks passed."
    return "\n".join(
        f"- [{r['status'].upper()}] {r['rule_id']}: {r['message']}"
        for r in flagged
    )


def _build_system_prompt(
    deterministic_check_result: dict | None,
    ref_check_result: dict | None = None,
) -> str:
    categories_str = ", ".join(VALID_CATEGORIES)
    deterministic_check_result = deterministic_check_result or {}
    ref_check_result = ref_check_result or {}
    deterministic_results = _format_flagged_results(
        (deterministic_check_result or {}).get("results", [])
    )
    ref_results = _format_flagged_results(
        (ref_check_result or {}).get("results", [])
    )

    return SYSTEM_PROMPT_TEMPLATE.format(
        guidelines=JUTLP_GUIDELINES,
        categories=categories_str,
        examples=EDITORIAL_EXAMPLES,
        deterministic_results=deterministic_results,
        ref_results=ref_results,
    )


def _extract_front_page_content(
    paragraphs: list[ParagraphRecord],
) -> dict[str, str]:
    """Extract front page content using style-based matching first, then
    positional fallback for documents that don't use JUTLP template styles."""
    front = get_front_page(paragraphs)

    # Title: try Article Title style, fallback to first non-empty paragraph
    title_paras = [p for p in front if p.style == "Article Title" and not p.is_empty]
    if title_paras:
        title = title_paras[0].text
    elif front:
        non_empty = [p for p in front if not p.is_empty]
        title = non_empty[0].text if non_empty else "Not found"
    else:
        title = "Not found"

    # Authors: try Authors style, fallback to second non-empty paragraph
    author_paras = [p for p in front if p.style == "Authors" and not p.is_empty]
    if author_paras:
        authors = author_paras[0].text
    else:
        non_empty = [p for p in front if not p.is_empty]
        authors = non_empty[1].text if len(non_empty) > 1 else "Not found"

    # Abstract: try style-based extraction, fallback to text after "Abstract" heading
    abstract_info = extract_abstract(paragraphs)
    if abstract_info["found"] and abstract_info["paragraphs"]:
        abstract = " ".join(p.text for p in abstract_info["paragraphs"])
    else:
        # Fallback: find paragraph with text "Abstract" and grab text after it
        # Don't break on Heading 1 — some docs style the abstract body as Heading 1
        stop_texts = {"practitioner notes", "keywords", "citation", "introduction"}
        abstract_parts = []
        found_abstract = False
        for p in front:
            if found_abstract:
                if p.is_empty:
                    continue
                if p.text.lower() in stop_texts:
                    break
                abstract_parts.append(p.text)
            elif p.text.lower() == "abstract":
                found_abstract = True
        abstract = " ".join(abstract_parts) if abstract_parts else "Not found"

    # Practitioner notes: try style-based, fallback to text after "Practitioner Notes"
    pn = extract_practitioner_notes(paragraphs)
    if not pn:
        pn_texts = []
        found_pn = False
        for p in front:
            if found_pn:
                if p.is_empty:
                    continue
                if p.text.lower() == "keywords":
                    break
                if p.style == "Heading 1":
                    break
                pn_texts.append(p.text)
            elif p.text.lower() == "practitioner notes":
                found_pn = True
        pn_notes = pn_texts
    else:
        pn_notes = [p.text for p in pn]

    # Keywords: try style-based extraction, fallback to text after "Keywords"
    keywords = extract_keywords(paragraphs)
    if not keywords:
        found_kw = False
        for p in front:
            if found_kw:
                if not p.is_empty and p.style != "Heading 1":
                    kw_text = p.text
                    keywords = [k.strip() for k in kw_text.split(",") if k.strip()]
                break
            elif p.text.lower() == "keywords":
                found_kw = True

    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "practitioner_notes": pn_notes,
        "keywords": keywords,
    }


def _build_user_prompt(
    paragraphs: list[ParagraphRecord],
    parsed_structure: dict,

) -> str:
    parts = []

    # Front page content with fallback extraction
    fp = _extract_front_page_content(paragraphs)

    # Only emit sections that were actually found. Missing front-page elements
    # are flagged by the deterministic checker — if we send "Not found" here,
    # the LLM treats it as an instruction to flag the absence and duplicates
    # the deterministic check (wasting tokens and producing redundant notes).
    if fp["title"] != "Not found":
        # Pre-compute the word count so the LLM doesn't have to. Previously
        # the LLM mis-counted words and falsely flagged titles under 15 words
        # as "too long." Presenting the exact count plus the limit makes the
        # length check a trivial lookup rather than a counting task.
        title_words = word_count(fp["title"])
        parts.append(
            f"## Title ({title_words} words; JUTLP limit is "
            f"{JUTLP_TITLE_WORD_LIMIT})\n{fp['title']}"
        )
    if fp["authors"] != "Not found":
        parts.append(f"## Authors\n{fp['authors']}")
    if fp["keywords"]:
        parts.append(f"## Keywords\n{', '.join(fp['keywords'])}")
    if fp["abstract"] != "Not found":
        parts.append(f"## Abstract\n{fp['abstract']}")
    if fp["practitioner_notes"]:
        notes_text = "\n".join(
            f"{i + 1}. {text}" for i, text in enumerate(fp["practitioner_notes"])
        )
        parts.append(f"## Practitioner Notes\n{notes_text}")

    # Main sections — detected by canonical mapping (alias- and titled-heading
    # aware) so a section the validator recognises is never dropped from the
    # prompt. Previously a style-based path matched section headings by exact
    # string, so an alias heading ("Methodology", "Findings", "Literature
    # Review") was silently omitted and the LLM then reported the section
    # "not present in the manuscript".
    section_bounds = _find_sections_by_text(paragraphs)
    emitted: set[str] = set()
    for section in MAIN_SECTIONS:
        canonical = _canonical_section_for(section)
        if canonical is None or canonical in emitted:
            continue
        if canonical not in section_bounds:
            continue
        start, end = section_bounds[canonical]
        text = _get_section_text_by_bounds(paragraphs, start, end)
        if text:
            parts.append(f"## Section: {canonical}\n{text}")
            emitted.add(canonical)

    return "\n\n".join(parts)


def build_prompts(
    paragraphs: list[ParagraphRecord],
    parsed_structure: dict,
    deterministic_check_result: dict | None = None,
    ref_check_result: dict | None = None,
) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) from parsed document data."""
    return (
        _build_system_prompt(deterministic_check_result, ref_check_result),
        _build_user_prompt(paragraphs, parsed_structure),
    )
