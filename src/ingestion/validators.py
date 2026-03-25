"""Validation helpers for uploaded email datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from src.utils.datetime_utils import parse_received_at


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]


REQUIRED_COLUMNS = ["id"]
OPTIONAL_COLUMNS = ["sender", "subject", "body", "received_at"]


def validate_email_columns(columns: Iterable[str]) -> ValidationResult:
    cols = {c.strip() for c in columns if c is not None}
    errors: list[str] = []
    for req in REQUIRED_COLUMNS:
        if req not in cols:
            errors.append(f"Missing required column: `{req}`")
    return ValidationResult(ok=(len(errors) == 0), errors=errors)


def validate_email_row(row: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    email_id = row.get("id")
    if email_id is None or str(email_id).strip() == "":
        errors.append("Email `id` must be a non-empty value.")

    # received_at is optional but if present must parse.
    if "received_at" in row and row.get("received_at") not in (None, ""):
        parsed = parse_received_at(row.get("received_at"))
        if parsed is None:
            errors.append("`received_at` could not be parsed. Use ISO date/time or common formats.")

    return ValidationResult(ok=(len(errors) == 0), errors=errors)

