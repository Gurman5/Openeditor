"""Detect direct-quotation spans in body prose.

JUTLP house policy: direct quotations must retain the source's original
text — no spelling, grammar, hyphenation, comma, abbreviation, or other
copy-edit mutations. Block-quote-styled paragraphs are handled by the
`SKIP_STYLES` set in ``document_zones``; this module covers **inline**
quotations that live inside an otherwise-editable body paragraph.

A "direct quotation" here means a substring enclosed in paired DOUBLE
quotation marks — straight (``"...``"``) or curly
(``“...”``). We deliberately do NOT treat single quotation
marks as quote markers because single-quote characters are ambiguous in
English (apostrophes, possessives, abbreviations like ``rock 'n' roll``)
and trying to pair them up produces too many false positives that would
silence legitimate edits to ordinary prose.

Pairing strategy
----------------
We use a single-pass scan that pairs the first opening mark with the
next closing mark and resets. Three quote-character classes are
recognised, each paired with its matching closer:

  * ``"`` ↔ ``"`` (straight double — opener and closer are the same
    character; pairing is positional: first becomes opener, next becomes
    closer, alternating).
  * ``“`` ↔ ``”`` (left and right curly double).
  * ``«`` ↔ ``»`` (French guillemets — included because some
    JUTLP submissions cite non-English sources).

Unmatched marks are ignored — better to miss a quotation than to lock
half a paragraph from editing because of an orphan straight quote.

The returned spans are **half-open intervals** ``[start, end)`` over
the input string and INCLUDE the surrounding quote marks. Callers
should treat any offset that overlaps a span as inside a quotation.
"""

from __future__ import annotations

# Straight double quote — opener and closer are the same character;
# pairing is purely positional.
_STRAIGHT_DOUBLE = '"'

# Directional / smart double quotes — Word's autocorrect inserts these
# whenever the user types `"`. The opener is U+201C, the closer U+201D.
_CURLY_OPEN = "“"
_CURLY_CLOSE = "”"

# French guillemets — uncommon but cheap to support.
_GUILLEMET_OPEN = "«"
_GUILLEMET_CLOSE = "»"


def find_quote_spans(text: str) -> list[tuple[int, int]]:
    """Return a list of ``(start, end)`` half-open intervals locating every
    paired-double-quote span in ``text``.

    Spans include the surrounding marks. Unmatched marks are silently
    ignored. Spans are returned in document order.
    """
    spans: list[tuple[int, int]] = []
    if not text:
        return spans

    # Position of the most-recent opener still awaiting a closer, or -1
    # when we are NOT inside an open quote.
    open_pos = -1
    # Type of mark currently waiting to be closed — None when not in a
    # quote. We track this so a curly open isn't accidentally closed by
    # a stray straight quote and vice versa.
    open_kind: str | None = None

    for i, ch in enumerate(text):
        if open_pos == -1:
            # Looking for an opener.
            if ch in (_STRAIGHT_DOUBLE, _CURLY_OPEN, _GUILLEMET_OPEN):
                open_pos = i
                open_kind = ch
            # A stray closer with no opener (`...as he said".`) is
            # ignored — better to miss than to over-skip.
            continue

        # We are inside a quote — looking for the matching closer.
        if open_kind == _STRAIGHT_DOUBLE and ch == _STRAIGHT_DOUBLE:
            spans.append((open_pos, i + 1))
            open_pos, open_kind = -1, None
        elif open_kind == _CURLY_OPEN and ch == _CURLY_CLOSE:
            spans.append((open_pos, i + 1))
            open_pos, open_kind = -1, None
        elif open_kind == _GUILLEMET_OPEN and ch == _GUILLEMET_CLOSE:
            spans.append((open_pos, i + 1))
            open_pos, open_kind = -1, None
        # Any other character — keep scanning inside the open quote.

    # Trailing unmatched opener — leave it. Don't emit a span that
    # extends to end-of-paragraph: a single stray quote shouldn't lock
    # the rest of the paragraph from editing.

    return spans


def is_in_quote(text: str, start: int, end: int | None = None) -> bool:
    """Return True when the half-open range ``[start, end)`` overlaps any
    quotation span in ``text``.

    If ``end`` is omitted, only the single character at ``start`` is
    tested. Empty ranges (``end == start``) are treated as a point query.
    """
    if end is None:
        end = start + 1
    if end < start:
        start, end = end, start
    for s, e in find_quote_spans(text):
        # Half-open overlap test.
        if start < e and s < end:
            return True
    return False
