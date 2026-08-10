"""Working-day arithmetic for the inactivity alarm.

The team does not work on Saturday or Sunday, so a tracker that was last touched
on Friday evening is *not* neglected by Monday morning — no message should go
out for the weekend gap. This module measures elapsed time in **working days**
only: any span that falls on a Saturday or Sunday contributes zero.

Only the inactivity alarm uses this. Every other figure in the monitor (the
7-day activity windows, per-day counts, report scheduling) keeps counting
calendar days, because those describe what the sheets contain rather than how
long the team has been silent.

Weekends are evaluated in the team's local timezone, not UTC: 01:00 IST on a
Monday is still Sunday in UTC, and the alarm must follow the working week the
team actually keeps.
"""

from __future__ import annotations

import logging
from datetime import datetime, time, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Monday=0 … Sunday=6 — the days nobody is expected to update the tracker.
WEEKEND_WEEKDAYS = frozenset({5, 6})

# Guard against a nonsense ``last_update`` (e.g. a 1970 epoch value) making the
# day-by-day walk below run for millions of iterations.
_MAX_SPAN_DAYS = 3650


def _zone(timezone_name: str):
    """Resolve an IANA timezone name, falling back to UTC if unavailable."""
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(timezone_name)
    except Exception:  # pragma: no cover - missing tzdata / bad name
        logger.warning("Unknown timezone %r; counting weekends in UTC", timezone_name)
        return timezone.utc


def is_weekend(moment: datetime, timezone_name: str = "UTC") -> bool:
    """True when ``moment`` falls on a Saturday or Sunday locally."""
    local = _as_aware(moment).astimezone(_zone(timezone_name))
    return local.weekday() in WEEKEND_WEEKDAYS


def _as_aware(moment: datetime) -> datetime:
    """Treat a naive datetime as UTC so comparisons never explode."""
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=timezone.utc)


def working_days_between(
    start: datetime, end: datetime, timezone_name: str = "UTC"
) -> float:
    """Elapsed working days between two instants, excluding Sat/Sun entirely.

    The result is fractional: a span from Friday 18:00 to Monday 06:00 counts
    only the 6 hours of Monday plus the 6 remaining hours of Friday (0.5 days),
    because the whole weekend in between contributes nothing.

    Returns 0.0 when ``end`` is not after ``start``.
    """
    start, end = _as_aware(start), _as_aware(end)
    if end <= start:
        return 0.0

    tz = _zone(timezone_name)
    local_start, local_end = start.astimezone(tz), end.astimezone(tz)

    if (local_end - local_start).days > _MAX_SPAN_DAYS:
        logger.warning(
            "Span of %s days exceeds the sanity limit; clamping the weekend walk",
            (local_end - local_start).days,
        )
        local_start = local_end - timedelta(days=_MAX_SPAN_DAYS)

    seconds = 0.0
    day = local_start.date()
    while day <= local_end.date():
        if day.weekday() not in WEEKEND_WEEKDAYS:
            day_open = datetime.combine(day, time.min, tzinfo=tz)
            window_start = max(local_start, day_open)
            window_end = min(local_end, day_open + timedelta(days=1))
            if window_end > window_start:
                seconds += (window_end - window_start).total_seconds()
        day += timedelta(days=1)

    return round(seconds / 86400.0, 2)


def calendar_days_between(start: datetime, end: datetime) -> float:
    """Plain elapsed days, weekends included — kept for display and context."""
    start, end = _as_aware(start), _as_aware(end)
    return round(max((end - start).total_seconds(), 0.0) / 86400.0, 2)


def next_working_moment(moment: datetime, timezone_name: str = "UTC") -> Optional[datetime]:
    """Start of the next working day when ``moment`` is a weekend, else ``None``.

    Used only for log/message wording ("alarm resumes Monday 00:00 IST").
    """
    tz = _zone(timezone_name)
    local = _as_aware(moment).astimezone(tz)
    if local.weekday() not in WEEKEND_WEEKDAYS:
        return None
    day = local.date()
    while day.weekday() in WEEKEND_WEEKDAYS:
        day += timedelta(days=1)
    return datetime.combine(day, time.min, tzinfo=tz)
