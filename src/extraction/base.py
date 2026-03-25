"""Base extractor interface.

All extractors must implement the same `extract()` contract so the UI and services
do not depend on extraction internals.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypedDict


class EmailForExtraction(TypedDict, total=False):
    """Minimal email schema required by extractors."""

    id: str
    sender: str | None
    subject: str | None
    body: str | None
    received_at: str | None
    cleaned_text: str | None


class ExtractorOutput(TypedDict):
    """Standard structured output for all extractors."""

    task_title: str | None
    deadline_text: str | None
    normalized_deadline: str | None
    priority: str
    extraction_confidence: float
    needs_review: bool
    extraction_method: str


class BaseExtractor(ABC):
    """Extraction interface."""

    @abstractmethod
    def extract(self, email: EmailForExtraction) -> ExtractorOutput:
        """Extract tasks/deadlines/priorities from a single email record."""
        raise NotImplementedError

