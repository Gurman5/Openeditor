"""Tests for the inline-quotation detection helper.

The helper underpins JUTLP's policy that direct quotations retain the
source's original text — every mutating pass relies on it to decide
whether a regex match or LLM edit sits inside a quoted span.
"""

from __future__ import annotations

from app.services.quotation_utils import find_quote_spans, is_in_quote


class TestFindQuoteSpans:
    def test_no_quotes_returns_empty(self):
        assert find_quote_spans("just some plain prose.") == []

    def test_single_straight_double_quote_pair(self):
        text = 'He said "hello" loudly.'
        spans = find_quote_spans(text)
        assert spans == [(8, 15)]
        assert text[spans[0][0]:spans[0][1]] == '"hello"'

    def test_single_curly_double_quote_pair(self):
        text = "He said “hello” loudly."
        spans = find_quote_spans(text)
        assert len(spans) == 1
        assert text[spans[0][0]:spans[0][1]] == "“hello”"

    def test_multiple_quoted_segments(self):
        text = '"first" then "second" then "third".'
        spans = find_quote_spans(text)
        assert len(spans) == 3

    def test_unmatched_straight_quote_ignored(self):
        # Single stray double-quote: should NOT lock the whole paragraph.
        text = 'He said hello".'
        spans = find_quote_spans(text)
        # Pairs are positional, so first " becomes opener with no closer →
        # no span emitted.
        assert spans == []

    def test_unmatched_curly_opener_ignored(self):
        text = "He said “hello loudly."
        # Curly opener with no closer.
        assert find_quote_spans(text) == []

    def test_single_quotes_are_NOT_treated_as_quotes(self):
        """Single quote marks are ambiguous (apostrophes!) so the helper
        deliberately doesn't pair them. A possessive or contraction
        must never accidentally lock half a paragraph."""
        text = "Smith's analysis didn't address rock 'n' roll."
        assert find_quote_spans(text) == []

    def test_curly_opener_not_closed_by_straight(self):
        text = "He said “hello\""
        # Curly open + straight close — types must match, so no pair.
        assert find_quote_spans(text) == []


class TestIsInQuote:
    def test_match_inside_quote(self):
        text = 'She said "the data was complete."'
        # "was" sits inside the quote.
        idx = text.find("was")
        assert is_in_quote(text, idx, idx + 3) is True

    def test_match_outside_quote(self):
        text = 'She said "hello" before lunch.'
        idx = text.find("before")
        assert is_in_quote(text, idx, idx + 6) is False

    def test_match_with_default_end_is_point_query(self):
        text = 'She said "hello".'
        # The 'h' of hello is inside the quote.
        assert is_in_quote(text, text.find("hello")) is True

    def test_swapped_start_end_normalised(self):
        text = '"abc"'
        assert is_in_quote(text, 4, 1) is True

    def test_empty_string_safe(self):
        assert is_in_quote("", 0) is False
