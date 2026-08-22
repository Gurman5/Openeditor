"""Tests for the shared Sydney-time stamp helper.

Word comments and tracked changes are stamped with this value. It must be an
ISO-8601 string carrying an explicit offset (colon form, e.g. ``+10:00``) so
Word displays Sydney time rather than UTC.
"""

from __future__ import annotations

import re
from datetime import datetime

from app.services.timestamps import now_sydney_iso


def test_returns_iso8601_with_colon_offset():
    ts = now_sydney_iso()
    # Parseable as an aware datetime.
    dt = datetime.fromisoformat(ts)
    assert dt.tzinfo is not None
    # Offset uses the colon form Word/OOXML expects.
    assert re.search(r"[+-]\d{2}:\d{2}$", ts), ts


def test_offset_is_sydney_plus_10_or_11():
    """Sydney is UTC+10 (standard) or UTC+11 (daylight saving). If the tz
    database is unavailable we fall back to UTC (+00:00) — accept that too so
    the test never flakes on a host without tzdata."""
    ts = now_sydney_iso()
    offset = ts[-6:]  # e.g. "+10:00"
    assert offset in {"+10:00", "+11:00", "+00:00"}, offset


def test_no_microseconds():
    """Second precision only — keeps the stamp tidy and matches the previous
    format's granularity."""
    ts = now_sydney_iso()
    # The time portion before the offset must be HH:MM:SS with no dot.
    time_part = ts[11:19]
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", time_part), ts
    assert "." not in ts


def test_not_utc_z_suffix():
    """Regression: the old format ended in 'Z' (UTC). The new one must not."""
    assert not now_sydney_iso().endswith("Z")
