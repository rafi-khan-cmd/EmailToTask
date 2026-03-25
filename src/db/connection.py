"""SQLite connection utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.config import get_db_path
from src.db.schema import SCHEMA_SQL

_SCHEMA_READY = False


def _ensure_schema(conn: sqlite3.Connection) -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    with conn:
        conn.executescript(SCHEMA_SQL)
    _SCHEMA_READY = True


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """
    Create and return a SQLite connection.

    Uses `row_factory` to allow easy dict conversion.
    """
    p = db_path or get_db_path()
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn

