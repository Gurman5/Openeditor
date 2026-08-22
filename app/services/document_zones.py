"""Document-zone detection shared across correction passes.

A JUTLP paper has three distinct zones from the perspective of automated
prose mutations:

* ``front``    — title, authors, abstract, practitioner notes, keywords
* ``body``     — Introduction → Conclusion
* ``outside``  — Acknowledgements, References, anything that follows

Why a shared module: previously each correction pass invented its own
skip rules. ``acronym_corrections`` tracked zones; ``decimal_corrections``,
``number_word_corrections``, and ``language_corrections`` did not — so a
reference entry styled "Normal" (a common artefact from authors pasting
from citation managers) would get its decimals flagged and its digits
spelled-out, even though the acronym pass correctly ignored it. This
module exposes one canonical zone-detector and one canonical skip-style
set so the four passes agree on what counts as body prose.

``SKIP_STYLES`` is also extended here to include caption styles (Figure
Title / Number, Table Title / Number) sourced from
``canonical_jultp_template.CANONICAL_STRUCTURE`` — captions stay
numeric-only by journal policy and were previously left exposed.
"""

from __future__ import annotations

import re

from lxml import etree

from app.domain.canonical_jultp_template import CANONICAL_STRUCTURE

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"

# Pull caption style names from the canonical template so the skip-set
# stays in sync with the source of truth.
_STYLE_RULES = CANONICAL_STRUCTURE["style_rules"]

# Paragraph styles whose body should NEVER be touched by prose-mutating
# passes (acronym / decimal / number-word / AU-spelling).
SKIP_STYLES: frozenset[str] = frozenset({
    # Headings — sub-section labels, not body prose.
    "Heading 1", "Heading 2", "Heading 3", "Heading 4",
    # Reference list entries — multiple aliases for robustness across
    # documents that came through different template versions. The
    # "APA7ReferenceListEntry" variant (no spaces, with "7") was added by
    # develop's inline _SKIP_STYLES; including it here keeps the canonical
    # set comprehensive after the merge.
    _STYLE_RULES["reference_entry"],  # canonical "APA 7 Reference List Entry"
    "APA7 Reference List Entry",
    "APA7ReferenceListEntry",
    "APAReferenceListEntry",
    "Reference List Entry",
    "References",
    # Front-page labels.
    "Article Title",
    "ArticleTitle",
    "Authors",
    "Author Affiliations",
    "AuthorAffiliations",
    # Caption styles — figures and tables stay numeric-only by journal policy.
    _STYLE_RULES["figure_number"],   # "Figure Number"
    _STYLE_RULES["figure_title"],    # "Figure Title"
    "Figure/Table Number",
    "Figure/Table Title",
    "FigureTableNumber",
    "FigureTableTitle",
    _STYLE_RULES["table_number"],    # "Table Number"
    _STYLE_RULES["table_title"],     # "Table Title"
    # Block-quote styles. Direct quotations must retain the source's
    # original spelling, grammar, hyphenation, and punctuation — JUTLP
    # house policy. The friendly name "Quote" and the style ID "Quote"
    # are the same in Word; cover the common aliases too so docs imported
    # from other templates (Block Text, Block Quote) get the same
    # protection.
    "Quote",
    "Quotation",
    "Block Text",
    "BlockText",
    "Block Quote",
    "BlockQuote",
    "IntenseQuote",
    "Intense Quote",
})

# Wider skip-set for prose-development checks (e.g. "expand to 3 sentences").
# These checks are only meaningful on real body prose, so they additionally
# skip table cells, block quotes, practitioner notes, comment text, and
# guidance/front-page text — none of which are paragraphs that should be
# expanded for readability. Kept distinct from SKIP_STYLES because the
# spelling/decimal/number-word passes legitimately edit some of these styles
# (e.g. Table Text containing a comma-decimal).
PROSE_DEV_SKIP_STYLES: frozenset[str] = SKIP_STYLES | frozenset({
    # Friendly names (with spaces) as Word normally surfaces them.
    "Heading Front Page",
    "Front Page Text",
    "Practitioner Notes",
    "Table Text",
    "Table Emphasis",
    "Quote",
    "Guidance Notes",
    "CommentText",
    "Caption",
    "Default Paragraph Style",
    "Title",
    "Subtitle",
    # Style IDs (no spaces) — Word stores these in <w:pStyle w:val=...>
    # so the same paragraph reads as "PractitionerNotes" not "Practitioner
    # Notes" when you inspect the XML. Cover both spellings.
    "HeadingFrontPage",
    "FrontPageText",
    "PractitionerNotes",
    "TableText",
    "TableEmphasis",
    "GuidanceNotes",
    "DefaultParagraphStyle",
    # Other front-matter / template styles that journals use for editor
    # placeholders, copyright notices, and abstracts. None of these are
    # body prose where the 3-sentence rule applies.
    "JournalInformation",
    "Copyright",
    "Abstract",
    "AbstractBody",
    "AbstractHeading",
    "Keywords",
    "KeywordsHeading",
    # HTML-imported paragraphs (Word's "Normal (Web)" style). Authors
    # who paste from a webpage land here; the style is unreliable as a
    # body-prose marker.
    "NormalWeb",
    "Normal (Web)",
})

# Headings that trigger zone transitions.
INTRO_HEADINGS: frozenset[str] = frozenset(
    {"introduction"}
    | {s.lower() for s in CANONICAL_STRUCTURE["section_aliases"]["Introduction"]}
)
END_BODY_HEADINGS: frozenset[str] = frozenset({
    "acknowledgement",
    "acknowledgements",
    "acknowledgment",
    "acknowledgments",
    "references",
    "reference list",
    "bibliography",
} | {s.lower() for s in CANONICAL_STRUCTURE["section_aliases"]["References"]}
  | {s.lower() for s in CANONICAL_STRUCTURE["section_aliases"]["Acknowledgements"]})

# Strip a leading numeric or Roman prefix so "1. Introduction" or
# "II) References" still match the canonical keys above.
_HEADING_PREFIX = re.compile(
    r"^\s*(?:[ivx]+|\d+)\s*[.)]\s+", re.IGNORECASE
)


def get_style_name(para_el: etree._Element) -> str:
    """Return the ``w:val`` of the paragraph's ``w:pStyle``, or ``""``."""
    pPr = para_el.find(f"{WQ}pPr")
    if pPr is None:
        return ""
    pStyle = pPr.find(f"{WQ}pStyle")
    if pStyle is None:
        return ""
    return pStyle.get(f"{WQ}val", "") or ""


def para_plain_text(para_el: etree._Element) -> str:
    """Concatenate every visible ``w:t`` text node inside the paragraph."""
    return "".join(t.text or "" for t in para_el.iter(f"{WQ}t") if t.text)


def normalise_heading(text: str) -> str:
    """Lower-case, strip numeric prefix and trailing colon-suffix."""
    cleaned = _HEADING_PREFIX.sub("", text or "", count=1)
    cleaned = cleaned.split(":", 1)[0]
    return re.sub(r"\s+", " ", cleaned).strip().lower().rstrip(".;").strip()


def heading_zone_transition(style: str, text: str, current_zone: str) -> str:
    """Return the new zone given a heading paragraph's style and text.

    A real Heading style is not required: authors often type "Introduction" or
    "References" as Normal/bold text. Exact section-label text still changes
    zone so later prose passes don't mutate references or acknowledgements.
    The boundary paragraph itself belongs to the zone it transitions into.
    """
    norm = normalise_heading(text)
    if not norm:
        return current_zone
    is_transition_heading = norm in INTRO_HEADINGS or norm in END_BODY_HEADINGS
    if not style.startswith("Heading") and not is_transition_heading:
        return current_zone
    if current_zone == "front" and norm in INTRO_HEADINGS:
        return "body"
    if current_zone in {"front", "body"} and norm in END_BODY_HEADINGS:
        return "outside"
    return current_zone


def initial_zone(doc_root: etree._Element) -> str:
    """Determine the starting zone for the very first paragraph.

    If the document has no Introduction heading anywhere, treat everything
    before the first end-of-body heading (Acknowledgements / References)
    as body content — otherwise an Introduction-less paper would never
    fire any body-zone action.
    """
    has_intro = False
    has_end = False
    for p in doc_root.iter(f"{WQ}p"):
        norm = normalise_heading(para_plain_text(p))
        if norm in INTRO_HEADINGS:
            has_intro = True
            break
        if norm in END_BODY_HEADINGS:
            has_end = True
            break
    if has_intro:
        return "front"
    if has_end:
        return "body"
    return "body"

def iter_paragraphs_with_zone(doc_root: etree._Element):
    """Yield ``(para_el, zone)`` for every ``w:p`` in document order.

    Convenience for the simple correction passes that just need to skip
    the ``outside`` zone — they don't care about the front/body split.
    """
    zone = initial_zone(doc_root)
    for para_el in doc_root.iter(f"{WQ}p"):
        style = get_style_name(para_el)
        zone = heading_zone_transition(style, para_plain_text(para_el), zone)
        yield para_el, zone


# Matches a paragraph that opens with a figure/table caption label —
# ``Figure 1.``, ``Figure A.``, ``Fig. 3.``, ``Table 2.`` — followed by a
# space and more text. The trailing period is the signal that the
# paragraph is a caption rather than a body reference ("Figure 3 shows…"
# or "(Figure 3)"), which never has the period directly after the label.
_CAPTION_LABEL_RE = re.compile(
    r"^\s*(?:Figure|Fig\.?|Table)\s+(?:[A-Z]|\d+(?:\.\d+)?)\.\s+\S",
    re.IGNORECASE,
)


def looks_like_caption_paragraph(para_el: etree._Element) -> bool:
    """Return True when ``para_el`` opens with a Figure/Table caption label.

    Captures the common defect where an author writes the full caption
    in a single Normal-styled paragraph ("Figure 1. Two-stage design for
    the project…") rather than splitting it across the canonical APA 7
    label/title/note paragraphs. Without this check, mutating passes
    would touch the caption's prose — which has produced bugs like
    `Two-stage → Twostage` on Normal-styled captions.
    """
    text = para_plain_text(para_el)
    if not text:
        return False
    return _CAPTION_LABEL_RE.match(text) is not None


def should_skip_paragraph(para_el: etree._Element, zone: str) -> bool:
    """Return True if a prose-mutating pass should ignore this paragraph.

    Skips when:
    * we're in the ``outside`` zone (Acknowledgements / References onward), or
    * the paragraph style is in :data:`SKIP_STYLES`, or
    * the paragraph's text shape matches a figure/table caption label
      (``Figure 1. …``) — catches captions that authors typed as Normal
      paragraphs and which would otherwise be touched by mutating passes.
    """
    if zone == "outside":
        return True
    if get_style_name(para_el) in SKIP_STYLES:
        return True
    if looks_like_caption_paragraph(para_el):
        return True
    return False


def is_in_table(para_el: etree._Element) -> bool:
    """Return True if ``para_el`` has a ``<w:tbl>`` ancestor.

    Used by prose-development checks that should never fire on table cell
    contents (single numeric cells, header labels, etc.).
    """
    for ancestor in para_el.iterancestors():
        if ancestor.tag == f"{WQ}tbl":
            return True
    return False


def is_list_item(para_el: etree._Element) -> bool:
    """Return True if ``para_el`` carries a list-numbering reference.

    Word marks bulleted and numbered list items with ``<w:pPr><w:numPr/></w:pPr>``.
    Prose-development checks should not fire on individual list items.
    """
    pPr = para_el.find(f"{WQ}pPr")
    if pPr is None:
        return False
    return pPr.find(f"{WQ}numPr") is not None


def should_skip_prose_paragraph(para_el: etree._Element, zone: str) -> bool:
    """Return True when a prose-development check should ignore this paragraph.

    Stricter than :func:`should_skip_paragraph` — also skips table cells,
    list items, and any style in :data:`PROSE_DEV_SKIP_STYLES`.
    """
    if zone == "outside":
        return True
    if get_style_name(para_el) in PROSE_DEV_SKIP_STYLES:
        return True
    if is_in_table(para_el):
        return True
    if is_list_item(para_el):
        return True
    return False
