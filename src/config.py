"""Project configuration and shared constants."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# ----------------------------
# Priorities / statuses
# ----------------------------

PRIORITY_LOW = "Low"
PRIORITY_MEDIUM = "Medium"
PRIORITY_HIGH = "High"

PRIORITIES = [PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH]

STATUS_PENDING = "Pending"
STATUS_IN_PROGRESS = "In Progress"
STATUS_COMPLETED = "Completed"
STATUS_ARCHIVED = "Archived"

STATUSES = [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_ARCHIVED]

EXTRACTOR_RULE_BASED = "rule_based"
EXTRACTOR_SPACY = "spacy"
EXTRACTOR_OPTIONS = [EXTRACTOR_RULE_BASED, EXTRACTOR_SPACY]

# ----------------------------
# Storage configuration
# ----------------------------


def get_project_root() -> Path:
    """Return the project root (the directory that contains `app.py`)."""
    # config.py: src/config.py -> parents[1] is project root
    return Path(__file__).resolve().parents[1]


def get_app_data_dir() -> Path:
    """
    Directory where SQLite DB and other persisted files are stored.

    For Streamlit Community Cloud, we default to a user home directory (writable).
    """
    env = os.getenv("EMAIL_TO_TASK_DATA_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    # Default to a user-writable directory (works locally and on Streamlit Cloud).
    return (Path.home() / ".email_to_task").resolve()


def get_db_path() -> Path:
    """Return the SQLite DB file path."""
    data_dir = get_app_data_dir()
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "email_to_task.sqlite3"
    except OSError:
        # Fallback for environments where home dir is restricted.
        fallback = Path("/tmp") / "email_to_task"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback / "email_to_task.sqlite3"


def ensure_db_connectivity(db_path: Path | None = None) -> None:
    """Verify the DB path is usable (directory exists and SQLite can open it)."""
    p = db_path or get_db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.close()


def get_sample_data_paths() -> tuple[Path, Path]:
    """Return (csv_path, json_path) for bundled sample email data."""
    root = get_project_root()
    return (
        root / "data" / "sample_emails.csv",
        root / "data" / "sample_emails.json",
    )


def get_default_extractor_method() -> str:
    """
    Return configured default extractor method.

    Uses env var `EMAIL_TO_TASK_EXTRACTOR_METHOD` when set; otherwise defaults to `spacy`.
    """
    method = os.getenv("EMAIL_TO_TASK_EXTRACTOR_METHOD", EXTRACTOR_SPACY).strip().lower()
    if method in EXTRACTOR_OPTIONS:
        return method
    return EXTRACTOR_SPACY

