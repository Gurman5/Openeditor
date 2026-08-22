"""Shared timestamp helper for Word comments and tracked changes.

Word stores the ``w:date`` attribute on comments and tracked-change elements
and displays it in the reader's local timezone. Historically the bot wrote a
UTC timestamp (``2026-06-03T02:51:00Z``); readers whose Word/OS locale didn't
auto-convert saw UTC, which doesn't match the Australian editors using the
tool.

This module produces an **Australia/Sydney** offset timestamp instead
(``2026-06-03T12:51:00+10:00``). The offset is DST-aware — Sydney is UTC+10 in
winter and UTC+11 during daylight saving — because we resolve it through
``zoneinfo`` rather than hard-coding a fixed offset. Word honours the explicit
offset, so the displayed time is correct for Sydney readers and still
unambiguous for anyone elsewhere.

``zoneinfo`` needs the IANA tz database. Linux (Railway) ships it with the OS;
Windows does not, so ``tzdata`` is listed in requirements.txt as the portable
source. If the zone can't be resolved for any reason we fall back to UTC so
timestamping never crashes the pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_SYDNEY = "Australia/Sydney"


def _sydney_tz():
    try:
        return ZoneInfo(_SYDNEY)
    except (ZoneInfoNotFoundError, Exception):
        # No tz database available — degrade to UTC rather than crash.
        return timezone.utc


def now_sydney_iso() -> str:
    """Return the current time as an ISO-8601 string with the Sydney offset.

    Example: ``2026-06-03T12:51:00+10:00`` (or ``+11:00`` during daylight
    saving). Falls back to a UTC ``...+00:00`` string if the tz database is
    unavailable.

    Uses ``isoformat`` (with second precision, no microseconds) so the offset
    carries the colon (``+10:00``) that OOXML / Word expects, rather than the
    ``+1000`` that ``strftime('%z')`` would produce.
    """
    return datetime.now(_sydney_tz()).replace(microsecond=0).isoformat()
