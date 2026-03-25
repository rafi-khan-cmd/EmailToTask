"""Priority detection utilities for v1 extraction."""

from __future__ import annotations

import re
from typing import Tuple

from src.extraction.patterns import URGENT_PATTERNS


def has_urgent_signal(text: str | None) -> bool:
    if not text:
        return False
    s = text.lower()
    return any(re.search(pat, s, flags=re.IGNORECASE) for pat in URGENT_PATTERNS)


def determine_priority(text: str | None, deadline_detected: bool) -> str:
    """
    Determine priority using v1 heuristic rules.

    High if urgency keywords found.
    Medium if deadline present but not urgent.
    Low otherwise.
    """
    if has_urgent_signal(text):
        return "High"
    if deadline_detected:
        return "Medium"
    return "Low"


def priority_confidence_boost(text: str | None, deadline_detected: bool) -> float:
    """Return a small confidence contribution for priority extraction."""
    if has_urgent_signal(text):
        return 0.2
    if deadline_detected:
        return 0.1
    return 0.0

