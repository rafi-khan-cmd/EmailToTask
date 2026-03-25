"""Extractor factory to support multiple extraction methods."""

from __future__ import annotations

from src.config import EXTRACTOR_RULE_BASED, EXTRACTOR_SPACY, get_default_extractor_method
from src.extraction.base import BaseExtractor
from src.extraction.rule_based import RuleBasedExtractor


def resolve_extractor_method(preferred: str | None = None) -> str:
    """
    Resolve a usable extractor method.

    Prefers the requested/configured method; falls back to rule_based when spaCy model is unavailable.
    """
    m = (preferred or get_default_extractor_method()).strip().lower()
    if m == EXTRACTOR_SPACY:
        try:
            from src.extraction.spacy_utils import is_spacy_model_available
        except Exception:
            return EXTRACTOR_RULE_BASED
        if is_spacy_model_available():
            return EXTRACTOR_SPACY
        return EXTRACTOR_RULE_BASED
    return EXTRACTOR_RULE_BASED


def get_extractor(method: str | None = None) -> BaseExtractor:
    """Return an extractor instance for a given method."""
    m = resolve_extractor_method(method)
    if m in {EXTRACTOR_RULE_BASED, "rule"}:
        return RuleBasedExtractor()
    if m == EXTRACTOR_SPACY:
        try:
            from src.extraction.spacy_extractor import SpacyExtractor
            from src.extraction.spacy_utils import SpacyModelLoadError
            return SpacyExtractor()
        except (SpacyModelLoadError, ImportError):
            return RuleBasedExtractor()
        except Exception:
            return RuleBasedExtractor()
    raise ValueError(f"Unknown extractor method: {method!r}")

