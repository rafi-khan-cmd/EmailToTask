"""Placeholder for a future LLM-based extractor.

Implementation idea (future):
  - Provide the cleaned email text to an LLM.
  - Parse and validate the response against the `ExtractorOutput` schema.
  - Keep `needs_review` high when the model is uncertain.
"""

from __future__ import annotations

from src.extraction.base import BaseExtractor, EmailForExtraction, ExtractorOutput


class LLMExtractor(BaseExtractor):
    """Stub for future LLM-based extraction."""

    def extract(self, email: EmailForExtraction) -> ExtractorOutput:
        raise NotImplementedError("LLMExtractor is a stub in v1.")

