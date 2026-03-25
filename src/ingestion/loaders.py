"""Load email datasets from CSV/JSON into internal records."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.ingestion.validators import validate_email_columns, validate_email_row
from src.utils.datetime_utils import parse_received_at


@dataclass(frozen=True)
class EmailRecord:
    id: str
    sender: str | None
    subject: str | None
    body: str | None
    received_at: str | None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "EmailRecord":
        return EmailRecord(
            id=str(d.get("id")),
            sender=d.get("sender"),
            subject=d.get("subject"),
            body=d.get("body"),
            received_at=parse_received_at(d.get("received_at")),
        )


def _read_csv_bytes(file_bytes: bytes) -> list[EmailRecord]:
    df = pd.read_csv(io.BytesIO(file_bytes))
    columns_result = validate_email_columns(df.columns)
    if not columns_result.ok:
        raise ValueError("; ".join(columns_result.errors))

    emails: list[EmailRecord] = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
        row_validation = validate_email_row(row_dict)
        if not row_validation.ok:
            # Skip invalid row but surface at least one helpful error.
            continue
        emails.append(EmailRecord.from_dict(row_dict))
    return emails


def load_emails_from_csv(file_bytes: bytes) -> list[EmailRecord]:
    if not file_bytes:
        raise ValueError("Uploaded CSV is empty.")
    return _read_csv_bytes(file_bytes)


def load_emails_from_json(file_bytes: bytes) -> list[EmailRecord]:
    if not file_bytes:
        raise ValueError("Uploaded JSON is empty.")
    payload = json.loads(file_bytes.decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("JSON must be an array of email objects.")

    emails: list[EmailRecord] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        validation = validate_email_row(item)
        if not validation.ok:
            continue
        # Normalize optional fields.
        if "received_at" in item:
            item = dict(item)
            item["received_at"] = parse_received_at(item.get("received_at"))
        emails.append(EmailRecord.from_dict(item))
    return emails


def load_emails_from_uploaded_payload(
    file_name: str, file_bytes: bytes
) -> list[EmailRecord]:
    name = (file_name or "").lower()
    if name.endswith(".csv"):
        return load_emails_from_csv(file_bytes)
    if name.endswith(".json"):
        return load_emails_from_json(file_bytes)
    raise ValueError("Unsupported file type. Please upload a `.csv` or `.json` file.")

