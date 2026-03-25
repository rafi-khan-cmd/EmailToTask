"""Regex patterns and heuristic lists for v1 extraction."""

from __future__ import annotations

import re

# Common urgency words/phrases.
URGENT_PATTERNS = [
    r"\burgent\b",
    r"\basap\b",
    r"\bimmediately\b",
    r"\bas soon as possible\b",
    r"\bby end of day\b",
    r"\bby eod\b",
    r"\btoday\b",
    r"\bend of day\b",
    r"\bno later than\b",
]

# Deadline phrase cues (not perfect, but deterministic).
DEADLINE_PATTERNS = [
    r"\bby\s+\d{1,2}\s*(?:am|pm)\b",
    r"\bby\s+\d{1,2}\s*:\s*\d{2}\s*(?:am|pm)\b",
    r"\bby\s+\d{1,2}\s*(?:am|pm)\b",
    r"\bbefore noon\b",
    r"\bby noon\b",
    r"\bby\s+the\s+end\s+of\s+day\b",
    r"\bby\s+friday\b",
    r"\bby\s+monday\b",
    r"\bby\s+tuesday\b",
    r"\bby\s+wednesday\b",
    r"\bby\s+thursday\b",
    r"\bby\s+saturday\b",
    r"\bby\s+sunday\b",
    r"\btoday\b",
    r"\btomorrow\b",
    r"\bnext week\b",
    r"\bnext\s+monday\b",
    r"\bnext\s+tuesday\b",
    r"\bnext\s+wednesday\b",
    r"\bnext\s+thursday\b",
    r"\bnext\s+friday\b",
    r"\bend of week\b",
    r"\bend of day\b",
]

DAY_NAMES = {
    "monday": "monday",
    "tuesday": "tuesday",
    "wednesday": "wednesday",
    "thursday": "thursday",
    "friday": "friday",
    "saturday": "saturday",
    "sunday": "sunday",
}

# Action verbs for task extraction.
ACTION_VERBS = [
    "send",
    "review",
    "fix",
    "update",
    "schedule",
    "complete",
    "finish",
    "prepare",
    "call",
    "reply",
    "submit",
    "confirm",
    "follow up",
    "follow-up",
    "draft",
    "share",
]

# A compact regex for capturing "verb + short phrase".
# This is heuristic and biased towards business emails.
ACTION_VERB_REGEX = r"|".join(re.escape(v) for v in sorted(ACTION_VERBS, key=len, reverse=True))

ACTION_PHRASE_REGEX = re.compile(
    rf"\b(?:please\s+|kindly\s+|can you\s+|could you\s+|would you\s+|reminder:\s*|let's\s+)?"
    rf"(?:{ACTION_VERB_REGEX})\b"
    rf"(?:\s+[a-zA-Z0-9/&\-_]+){{0,8}}",
    flags=re.IGNORECASE,
)

