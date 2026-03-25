"""Datetime-related helper functions used throughout the app."""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.utcnow()


def parse_received_at(value: object) -> str | None:
    """
    Parse incoming received_at values into an ISO-8601 string.

    Returns None if parsing fails.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return datetime.combine(value, time.min).isoformat()

    s = str(value).strip()
    if not s:
        return None

    # Try a few common formats before falling back.
    fmts = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.isoformat()
        except ValueError:
            pass

    # ISO-like: let datetime.fromisoformat handle.
    try:
        return datetime.fromisoformat(s).isoformat()
    except ValueError:
        return None


def to_yyyy_mm_dd(d: date) -> str:
    """Convert a `date` to `YYYY-MM-DD`."""
    return d.strftime("%Y-%m-%d")


def next_weekday(from_date: date, weekday: int) -> date:
    """
    Return the next date that matches the given weekday.

    weekday: Monday=0 ... Sunday=6
    """
    days_ahead = (weekday - from_date.weekday()) % 7
    if days_ahead == 0:
        return from_date
    return from_date + timedelta(days=days_ahead)


def next_weekday_strict(from_date: date, weekday: int) -> date:
    """
    Return the upcoming weekday strictly in the future (>= from_date + 1 day if same day).
    """
    days_ahead = (weekday - from_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return from_date + timedelta(days=days_ahead)


def normalize_deadline_relative_text(text: str, ref_dt: datetime) -> str | None:
    """
    Best-effort normalization for common deadline phrases.

    This is intentionally conservative for v1: return None when ambiguous.
    """
    if text is None:
        return None
    s = text.strip().lower()
    if not s:
        return None

    base = ref_dt.date()

    # Explicit day offsets.
    if re.search(r"\btoday\b", s):
        return to_yyyy_mm_dd(base)
    if re.search(r"\btomorrow\b", s):
        return to_yyyy_mm_dd(base + timedelta(days=1))
    if re.search(r"\bnext week\b", s):
        return to_yyyy_mm_dd(base + timedelta(days=7))

    # End-of-week: pick the upcoming Friday (or today if it's Friday).
    if re.search(r"\bend of week\b", s):
        # Friday = 4
        return to_yyyy_mm_dd(next_weekday(base, 4))
    if re.search(r"\bend of day\b", s):
        # Map to today (time-of-day omitted in normalized date).
        return to_yyyy_mm_dd(base)
    if re.search(r"\basap\b", s) or re.search(r"\bimmediately\b", s):
        return to_yyyy_mm_dd(base)

    # Next <weekday>.
    weekday_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    for day_name, wd in weekday_map.items():
        if re.search(rf"\bnext\s+{day_name}\b", s):
            return to_yyyy_mm_dd(next_weekday_strict(base, wd))

    # Plain <weekday>.
    for day_name, wd in weekday_map.items():
        if re.search(rf"\b{day_name}\b", s):
            return to_yyyy_mm_dd(next_weekday(base, wd))

    # by <time> / before noon: normalize only if we have an explicit day cue.
    has_explicit_day = bool(
        re.search(r"\btoday\b|\btomorrow\b|\bnext week\b|\bend of week\b", s)
        or any(re.search(rf"\b{d}\b", s) for d in weekday_map.keys())
    )
    if not has_explicit_day:
        return None

    # If there's an explicit day cue, return that day even if we can't pin a time.
    if re.search(r"\bby\b|\bbefore\b|\bnoon\b", s):
        # Prefer the explicit day already handled above, but keep fallback to base.
        return to_yyyy_mm_dd(base)

    return None

