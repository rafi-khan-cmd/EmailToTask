"""Reset database: drop tables and recreate on next init."""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.db.repository import reset_database
from src.db.schema import SCHEMA_SQL
from src.db.connection import connect
from src.config import get_db_path


def main() -> None:
    db_path = get_db_path()
    conn = connect(db_path)
    reset_database()
    # Recreate schema right away to keep developer flow simple.
    with conn:
        conn.executescript(SCHEMA_SQL)
    print(f"Reset database at: {db_path}")


if __name__ == "__main__":
    main()

