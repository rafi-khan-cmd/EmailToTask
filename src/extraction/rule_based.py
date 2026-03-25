"""v1 rule-based extraction engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.extraction.base import BaseExtractor, EmailForExtraction, ExtractorOutput
from src.extraction.deadline_utils import extract_deadline_text, normalize_deadline_text
from src.extraction.priority_utils import determine_priority, priority_confidence_boost
from src.extraction.task_utils import extract_task_title
from src.utils.datetime_utils import now_utc


@dataclass
class ConfidenceSignals:
    task_title_found: bool
    deadline_found: bool
    urgency_found: bool
    deadline_normalized: bool
    fallback_used: bool


def _compute_confidence(signals: ConfidenceSignals) -> float:
    confidence = 0.0

    if signals.task_title_found:
        confidence += 0.45
    if signals.deadline_found:
        confidence += 0.2
    if signals.urgency_found:
        confidence += 0.2
    if signals.deadline_normalized:
        confidence += 0.1

    # Fallback title (subject-based) gets penalized.
    if signals.fallback_used and not signals.task_title_found:
        confidence -= 0.1
    if not signals.task_title_found:
        confidence -= 0.1

    # Priority contribution (small).
    # Keep it deterministic: boost is already included via urgency/deadline signals.
    confidence += 0.0

    # Clamp.
    if confidence < 0.0:
        confidence = 0.0
    if confidence > 1.0:
        confidence = 1.0
    return round(confidence, 3)


class RuleBasedExtractor(BaseExtractor):
    """Rule-based deterministic extractor for v1."""

    def extract(self, email: EmailForExtraction) -> ExtractorOutput:
        cleaned_text = email.get("cleaned_text") or ""
        subject = email.get("subject") or ""
        received_at = email.get("received_at")

        # Use UTC now for relative normalization (v1 conservative).
        ref_dt = datetime.utcnow()
        if received_at:
            # If `received_at` is parseable, use it as the normalization reference.
            try:
                ref_dt = datetime.fromisoformat(received_at)
            except ValueError:
                ref_dt = datetime.utcnow()

        deadline_text = extract_deadline_text(cleaned_text)
        normalized_deadline = normalize_deadline_text(deadline_text, ref_dt=ref_dt)

        # Task title extraction depends on cleaned_text + subject.
        task_title, action_phrase_found = extract_task_title(
            cleaned_text=cleaned_text, subject=subject
        )

        # Priority detection uses urgency signals + deadline presence.
        priority = determine_priority(cleaned_text, deadline_detected=bool(deadline_text))

        urgency_found = priority == "High"
        deadline_found = bool(deadline_text)
        deadline_normalized = normalized_deadline is not None
        fallback_used = not action_phrase_found and bool(subject.strip())
        task_title_found = action_phrase_found and task_title is not None

        confidence = _compute_confidence(
            ConfidenceSignals(
                task_title_found=task_title_found,
                deadline_found=deadline_found,
                urgency_found=urgency_found,
                deadline_normalized=deadline_normalized,
                fallback_used=fallback_used,
            )
        )

        # v1 needs_review heuristics:
        # - low confidence
        # - no action phrase clearly detected (fallback title only)
        # - deadline present but not normalized
        needs_review = False
        if confidence < 0.5:
            needs_review = True
        if not action_phrase_found:
            # Fallback title means extraction may be weak (including non-actionable emails).
            needs_review = True
        if deadline_found and normalized_deadline is None:
            needs_review = True
        if not task_title:
            needs_review = True

        return {
            "task_title": task_title,
            "deadline_text": deadline_text,
            "normalized_deadline": normalized_deadline,
            "priority": priority,
            "extraction_confidence": confidence,
            "needs_review": needs_review,
            "extraction_method": "rule_based",
        }

