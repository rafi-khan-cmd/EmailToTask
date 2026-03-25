"""Initialize the SQLite database schema."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running `python3 scripts/init_db.py` directly by ensuring the repo root is on PYTHONPATH.
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import ensure_db_connectivity, get_db_path
from src.db.connection import connect
from src.db.schema import SCHEMA_SQL


def main() -> None:
    db_path = get_db_path()
    ensure_db_connectivity(db_path)
    conn = connect(db_path)
    with conn:
        conn.executescript(SCHEMA_SQL)
    print(f"Initialized database at: {db_path}")


if __name__ == "__main__":
    main()

