"""Logging helper utilities."""

from __future__ import annotations

import logging
from typing import Final


def get_logger(name: str = "email-to-task") -> logging.Logger:
    """Return a configured logger for the app."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler: Final = logging.StreamHandler()
    fmt: Final = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    return logger

