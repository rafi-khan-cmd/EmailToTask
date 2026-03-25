"""Seed the database with bundled sample emails.

This is used by both local development and by the Streamlit UI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_sample_data_paths, get_db_path
from src.db.connection import connect
from src.db.schema import SCHEMA_SQL
from src.db.repository import upsert_task_for_email, insert_email
from src.extraction.factory import get_extractor
from src.ingestion.loaders import EmailRecord
from src.preprocessing.cleaner import clean_email_text


def _load_sample_emails() -> list[EmailRecord]:
    csv_path, json_path = get_sample_data_paths()
    emails: list[EmailRecord] = []
    # For v1 we can load from JSON (preferred because it keeps all fields).
    if json_path.exists():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        for item in payload:
            emails.append(
                EmailRecord(
                    id=str(item.get("id")),
                    sender=item.get("sender"),
                    subject=item.get("subject"),
                    body=item.get("body"),
                    received_at=item.get("received_at"),
                )
            )
    elif csv_path.exists():
        import pandas as pd

        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            emails.append(
                EmailRecord(
                    id=str(row.get("id")),
                    sender=row.get("sender"),
                    subject=row.get("subject"),
                    body=row.get("body"),
                    received_at=row.get("received_at"),
                )
            )
    return emails


def seed_sample_emails_and_tasks(*, extraction_method: str = "rule_based") -> None:
    """Load sample emails and store extracted tasks."""
    # Ensure schema exists.
    db_path = get_db_path()
    conn = connect(db_path)
    with conn:
        conn.executescript(SCHEMA_SQL)

    emails = _load_sample_emails()
    extractor = get_extractor(extraction_method)

    # Some sample tasks start with non-Pending states to make the dashboard more informative.
    status_by_email_id: dict[str, str] = {
        "email_003": "Completed",
        "email_011": "Completed",
        "email_016": "Completed",
        "email_006": "Archived",
        "email_024": "Archived",
        "email_015": "In Progress",
    }

    # Deterministic: replace tasks for each email id.
    for email in emails:
        cleaned_text = clean_email_text(email.subject, email.body)
        insert_email(
            email_id=email.id,
            sender=email.sender,
            subject=email.subject,
            body=email.body,
            received_at=email.received_at,
        )
        extraction = extractor.extract(
            {
                "id": email.id,
                "sender": email.sender,
                "subject": email.subject,
                "body": email.body,
                "received_at": email.received_at,
                "cleaned_text": cleaned_text,
            }
        )
        status = status_by_email_id.get(email.id, "Pending")
        needs_review = bool(extraction["needs_review"])
        if status in {"Completed", "Archived"}:
            needs_review = False

        upsert_task_for_email(
            email_id=email.id,
            sender=email.sender,
            subject=email.subject,
            original_body=email.body,
            cleaned_text=cleaned_text,
            task_title=extraction["task_title"],
            deadline_text=extraction["deadline_text"],
            normalized_deadline=extraction["normalized_deadline"],
            priority=extraction["priority"],
            status=status,
            extraction_confidence=float(extraction["extraction_confidence"]),
            needs_review=needs_review,
            extraction_method=str(extraction["extraction_method"]),
        )

    print(f"Seeded {len(emails)} sample emails/tasks into {db_path}")


if __name__ == "__main__":
    seed_sample_emails_and_tasks()

