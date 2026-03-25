"""SQLite connection utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.config import get_db_path


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """
    Create and return a SQLite connection.

    Uses `row_factory` to allow easy dict conversion.
    """
    p = db_path or get_db_path()
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn

