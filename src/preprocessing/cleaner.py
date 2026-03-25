"""Email preprocessing/cleaning utilities."""

from __future__ import annotations

import re


def normalize_whitespace(s: str) -> str:
    """Collapse excessive whitespace and normalize line breaks."""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def clean_email_text(subject: str | None, body: str | None) -> str:
    """
    Normalize text for extraction while leaving original content untouched in storage.

    The cleaner is intentionally simple for v1.
    """
    parts: list[str] = []
    if subject and str(subject).strip():
        parts.append(str(subject).strip())
    if body and str(body).strip():
        parts.append(str(body).strip())

    combined = "\n\n".join(parts)
    combined = normalize_whitespace(combined)

    # Remove common email footer artifacts (best-effort).
    combined = re.sub(r"\n--+\n.*$", "", combined, flags=re.DOTALL)
    combined = re.sub(r"\b(sent from|from my iphone)\b.*$", "", combined, flags=re.IGNORECASE)
    return combined.strip()

