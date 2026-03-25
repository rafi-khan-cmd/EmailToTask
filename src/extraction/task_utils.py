"""Task title extraction utilities for v1."""

from __future__ import annotations

import re

from src.extraction.patterns import ACTION_PHRASE_REGEX


def _clean_task_title(title: str) -> str:
    s = title.strip()
    # Remove common leading phrases that are not part of the actionable verb phrase.
    s = re.sub(r"^(please|kindly|can you|could you|would you|reminder:|let's)\s+", "", s, flags=re.IGNORECASE)
    # Truncate at common deadline/urgency separators.
    s = re.split(
        r"\b(by|before|tomorrow|today|next week|end of day|end of week|asap|urgent|immediately)\b",
        s,
        flags=re.IGNORECASE,
    )[0].strip()

    # Remove trailing punctuation.
    s = s.rstrip(" .;,:")
    # Normalize spaces.
    s = re.sub(r"\s+", " ", s)
    if not s:
        return s

    # Title-case the first character and keep rest as-is for readability.
    return s[0].upper() + s[1:]


def extract_task_title(
    *,
    cleaned_text: str | None,
    subject: str | None,
) -> tuple[str | None, bool]:
    """
    Extract a short actionable task title.

    Returns (task_title, action_phrase_found).
    """
    text = cleaned_text or ""
    s = text.strip()

    action_phrase_found = False
    if s:
        # Find the first action phrase in the email.
        m = ACTION_PHRASE_REGEX.search(s)
        if m:
            action_phrase_found = True
            extracted = m.group(0)
            title = _clean_task_title(extracted)
            # Enforce a short title.
            words = title.split()
            if len(words) > 8:
                title = " ".join(words[:8]).rstrip(",.;:")
            return title, action_phrase_found

    # Fallback: subject-based title (works well for non-actionable emails too).
    if subject and str(subject).strip():
        subj = re.sub(r"\s+", " ", str(subject).strip())
        words = subj.split()
        title = " ".join(words[:8]).rstrip(",.;:") or None
        return title, False

    # Last fallback.
    if s:
        words = s.split()
        title = " ".join(words[:8]).rstrip(",.;:") or None
        return title, False

    return None, False

