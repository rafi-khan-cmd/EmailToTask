"""Utilities for loading and reusing the spaCy model safely."""

from __future__ import annotations

import importlib
import sys
from functools import lru_cache

from typing import Any

SPACY_MODEL_NAME = "en_core_web_sm"


class SpacyModelLoadError(RuntimeError):
    """Raised when spaCy model is not installed or cannot be loaded."""


@lru_cache(maxsize=1)
def get_nlp_model() -> Any:
    """
    Load and cache the spaCy model.

    The cache prevents reloading on Streamlit reruns.
    """
    try:
        import spacy
    except ImportError as exc:
        raise SpacyModelLoadError(
            "spaCy is not installed. Run:\n"
            "pip install -r requirements.txt"
        ) from exc
    try:
        return spacy.load(SPACY_MODEL_NAME)
    except OSError as exc:
        # Some environments install the model as a package that can be imported
        # directly even when `spacy.load(name)` lookup fails.
        try:
            pkg = importlib.import_module(SPACY_MODEL_NAME)
            if hasattr(pkg, "load"):
                return pkg.load()
        except Exception:
            pass
        raise SpacyModelLoadError(
            "spaCy English model is missing for this Python environment.\n"
            f"Python executable in use: {sys.executable}\n"
            "Install with:\n"
            f"{sys.executable} -m spacy download en_core_web_sm"
        ) from exc


def is_spacy_model_available() -> bool:
    """Return True when `en_core_web_sm` can be loaded."""
    try:
        get_nlp_model()
        return True
    except SpacyModelLoadError:
        return False

