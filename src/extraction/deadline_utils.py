"""Deadline detection and normalization utilities for v1 extraction."""

from __future__ import annotations

import re
from datetime import datetime

from src.extraction.patterns import DEADLINE_PATTERNS
from src.utils.datetime_utils import normalize_deadline_relative_text


def extract_deadline_text(text: str | None) -> str | None:
    """
    Extract a raw deadline phrase from text using conservative patterns.

    Returns the matched substring, or None if no deadline phrase is detected.
    """
    if not text:
        return None
    s = text.strip()
    if not s:
        return None

    for pat in DEADLINE_PATTERNS:
        m = re.search(pat, s, flags=re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return None


def normalize_deadline_text(
    deadline_text: str | None,
    ref_dt: datetime | None = None,
) -> str | None:
    """
    Normalize deadline text to `YYYY-MM-DD` if easy, else return None.

    v1 is intentionally conservative.
    """
    if not deadline_text:
        return None
    ref = ref_dt or datetime.utcnow()
    return normalize_deadline_relative_text(deadline_text, ref)

