"""Process uploaded emails into stored tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config import STATUS_PENDING
from src.db.repository import insert_email, upsert_task_for_email
from src.extraction.factory import get_extractor
from src.ingestion.loaders import EmailRecord
from src.preprocessing.cleaner import clean_email_text


@dataclass(frozen=True)
class ProcessingResult:
    emails_processed: int
    tasks_created: int
    tasks_updated: int
    errors: list[str]


def process_emails(
    emails: list[EmailRecord],
    *,
    extraction_method: str = "rule_based",
) -> ProcessingResult:
    """Ingest email records, extract tasks, and persist them to SQLite."""
    extractor = get_extractor(extraction_method)

    errors: list[str] = []
    tasks_created = 0
    tasks_updated = 0

    for idx, email in enumerate(emails, start=1):
        try:
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

            # v1: upsert by email_id (replace tasks for this email).
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
                status=STATUS_PENDING,
                extraction_confidence=float(extraction["extraction_confidence"]),
                needs_review=bool(extraction["needs_review"]),
                extraction_method=str(extraction["extraction_method"]),
            )

            tasks_created += 1
            tasks_updated += 1
        except Exception as e:  # noqa: BLE001 - user-facing errors
            errors.append(f"Row {idx} ({email.id}): {e}")

    return ProcessingResult(
        emails_processed=len(emails),
        tasks_created=tasks_created,
        tasks_updated=tasks_updated,
        errors=errors,
    )

