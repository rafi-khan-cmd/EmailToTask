"""Repository abstraction for database access."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable

from src.db.connection import connect


@dataclass(frozen=True)
class TaskFilters:
    """Optional filters for listing tasks."""

    search: str | None = None
    priority: str | None = None
    status: str | None = None
    needs_review: bool | None = None
    overdue: bool | None = None
    sender: str | None = None

    sort_by: str = "created_at"
    sort_desc: bool = True


def insert_email(
    email_id: str,
    sender: str | None,
    subject: str | None,
    body: str | None,
    received_at: str | None,
) -> None:
    """Insert or replace an email record."""
    created_at = datetime.utcnow().isoformat()
    conn = connect()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO emails (id, sender, subject, body, received_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (email_id, sender, subject, body, received_at, created_at),
        )


def insert_task(
    *,
    email_id: str,
    sender: str | None,
    subject: str | None,
    original_body: str | None,
    cleaned_text: str | None,
    task_title: str | None,
    deadline_text: str | None,
    normalized_deadline: str | None,
    priority: str,
    status: str,
    extraction_confidence: float,
    needs_review: bool,
    extraction_method: str,
) -> int:
    """Insert a new task for the given email_id."""
    conn = connect()
    now = datetime.utcnow().isoformat()
    completed_at = now if status == "Completed" else None
    with conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (
              email_id,
              sender,
              subject,
              original_body,
              cleaned_text,
              task_title,
              deadline_text,
              normalized_deadline,
              priority,
              status,
              extraction_confidence,
              needs_review,
              extraction_method,
              user_corrected,
              corrected_task_title,
              corrected_deadline_text,
              corrected_normalized_deadline,
              corrected_priority,
              notes,
              created_at,
              updated_at,
              completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email_id,
                sender,
                subject,
                original_body,
                cleaned_text,
                task_title,
                deadline_text,
                normalized_deadline,
                priority,
                status,
                float(extraction_confidence),
                1 if needs_review else 0,
                extraction_method,
                0,  # user_corrected
                None,
                None,
                None,
                None,
                None,  # notes
                now,  # created_at
                now,  # updated_at
                completed_at,  # completed_at
            ),
        )
        return int(cur.lastrowid)


def upsert_task_for_email(
    *,
    email_id: str,
    sender: str | None,
    subject: str | None,
    original_body: str | None,
    cleaned_text: str | None,
    task_title: str | None,
    deadline_text: str | None,
    normalized_deadline: str | None,
    priority: str,
    status: str,
    extraction_confidence: float,
    needs_review: bool,
    extraction_method: str,
) -> None:
    """
    Replace existing tasks for an email and insert a new one.

    v1 behavior keeps it simple and deterministic for repeated processing.
    """
    conn = connect()
    now = datetime.utcnow().isoformat()
    completed_at = now if status == "Completed" else None
    with conn:
        conn.execute("DELETE FROM tasks WHERE email_id = ?", (email_id,))
        conn.execute(
            """
            INSERT INTO tasks (
              email_id,
              sender,
              subject,
              original_body,
              cleaned_text,
              task_title,
              deadline_text,
              normalized_deadline,
              priority,
              status,
              extraction_confidence,
              needs_review,
              extraction_method,
              user_corrected,
              corrected_task_title,
              corrected_deadline_text,
              corrected_normalized_deadline,
              corrected_priority,
              notes,
              created_at,
              updated_at,
              completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email_id,
                sender,
                subject,
                original_body,
                cleaned_text,
                task_title,
                deadline_text,
                normalized_deadline,
                priority,
                status,
                float(extraction_confidence),
                1 if needs_review else 0,
                extraction_method,
                0,
                None,
                None,
                None,
                None,
                None,
                now,
                now,
                completed_at,
            ),
        )


def get_all_tasks(limit: int = 200) -> list[dict[str, Any]]:
    """Return tasks ordered by created_at (newest first)."""
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
        (int(limit),),
    ).fetchall()
    return [dict(r) for r in rows]


def get_task_by_id(task_id: int) -> dict[str, Any] | None:
    """Fetch a single task by its integer id."""
    conn = connect()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (int(task_id),)).fetchone()
    return dict(row) if row else None


def update_task(
    task_id: int,
    *,
    corrected_task_title: str | None,
    corrected_deadline_text: str | None,
    corrected_normalized_deadline: str | None,
    corrected_priority: str | None,
    notes: str | None,
    status: str,
    needs_review: bool,
) -> None:
    """Update user-corrected fields and status."""
    conn = connect()
    now = datetime.utcnow().isoformat()

    # Mark user_corrected when any corrected field is set.
    user_corrected = int(
        corrected_task_title is not None
        or corrected_deadline_text is not None
        or corrected_normalized_deadline is not None
        or corrected_priority is not None
    )

    completed_at = None
    if status == "Completed":
        completed_at_row = conn.execute(
            "SELECT completed_at FROM tasks WHERE id = ?", (int(task_id),)
        ).fetchone()
        completed_at = completed_at_row["completed_at"] if completed_at_row else None
        if not completed_at:
            completed_at = now

    with conn:
        conn.execute(
            """
            UPDATE tasks
            SET
              corrected_task_title = ?,
              corrected_deadline_text = ?,
              corrected_normalized_deadline = ?,
              corrected_priority = ?,
              notes = ?,
              status = ?,
              needs_review = ?,
              user_corrected = ?,
              updated_at = ?,
              completed_at = COALESCE(?, completed_at)
            WHERE id = ?
            """,
            (
                corrected_task_title,
                corrected_deadline_text,
                corrected_normalized_deadline,
                corrected_priority,
                notes,
                status,
                1 if needs_review else 0,
                user_corrected,
                now,
                completed_at,
                int(task_id),
            ),
        )


def reset_database() -> None:
    """Delete all stored emails and tasks."""
    conn = connect()
    from src.db.schema import RESET_SQL

    with conn:
        conn.executescript(RESET_SQL)


def seed_sample_data() -> None:
    """Seed sample data using the scripts module for convenience."""
    from scripts.seed_data import seed_sample_emails_and_tasks

    seed_sample_emails_and_tasks()


def filter_tasks(filters: TaskFilters) -> list[dict[str, Any]]:
    """
    Fetch tasks and apply filters in Python for readability.

    v1 uses moderate datasets so this stays fast and maintainable.
    """
    tasks = get_all_tasks(limit=1000)

    def pick_priority(t: dict[str, Any]) -> str:
        return t["corrected_priority"] if t.get("user_corrected") else t.get("priority")

    def pick_task_title(t: dict[str, Any]) -> str | None:
        if t.get("user_corrected") and t.get("corrected_task_title") is not None:
            return t.get("corrected_task_title")
        return t.get("task_title")

    def pick_deadline_text(t: dict[str, Any]) -> str | None:
        if t.get("user_corrected") and t.get("corrected_deadline_text") is not None:
            return t.get("corrected_deadline_text")
        return t.get("deadline_text")

    def is_overdue(t: dict[str, Any]) -> bool:
        # Overdue means:
        # - status not Completed/Archived
        # - normalized deadline exists and is before today
        status = t.get("status")
        if status in ("Completed", "Archived"):
            return False
        norm = (
            t.get("corrected_normalized_deadline")
            if t.get("user_corrected")
            else t.get("normalized_deadline")
        )
        if not norm:
            return False
        try:
            d = datetime.fromisoformat(norm).date()
        except ValueError:
            return False
        return d < date.today()

    priority = filters.priority
    status = filters.status

    out: list[dict[str, Any]] = []
    for t in tasks:
        if filters.search:
            s = filters.search.lower()
            hay = " ".join(
                str(x)
                for x in [
                    t.get("sender"),
                    t.get("subject"),
                    pick_task_title(t),
                    pick_deadline_text(t),
                ]
                if x is not None
            ).lower()
            if s not in hay:
                continue

        if priority and pick_priority(t) != priority:
            continue

        if status and t.get("status") != status:
            continue

        if filters.needs_review is not None:
            if bool(t.get("needs_review")) != bool(filters.needs_review):
                continue

        if filters.sender and (t.get("sender") or "").lower() != filters.sender.lower():
            continue

        if filters.overdue is not None:
            if bool(filters.overdue) != is_overdue(t):
                continue

        out.append(t)

    # Sorting.
    sort_key = filters.sort_by
    reverse = filters.sort_desc
    out.sort(key=lambda x: x.get(sort_key) or "", reverse=reverse)
    return out


def get_dashboard_metrics() -> dict[str, Any]:
    """Compute dashboard metrics in Python for correctness and clarity."""
    tasks = get_all_tasks(limit=10_000)

    def pick_effective_priority(t: dict[str, Any]) -> str:
        return t["corrected_priority"] if t.get("user_corrected") else t.get("priority")

    def pick_effective_deadline(t: dict[str, Any]) -> str | None:
        if t.get("user_corrected"):
            return t.get("corrected_normalized_deadline")
        return t.get("normalized_deadline")

    today = date.today()

    total = len(tasks)
    pending = sum(1 for t in tasks if t.get("status") == "Pending")
    completed = sum(1 for t in tasks if t.get("status") == "Completed")
    high_priority = sum(
        1 for t in tasks if pick_effective_priority(t) == "High"
    )
    overdue = 0
    needs_review = 0

    for t in tasks:
        if bool(t.get("needs_review")):
            needs_review += 1
        d = pick_effective_deadline(t)
        status = t.get("status")
        if status in ("Completed", "Archived"):
            continue
        if d:
            try:
                dd = datetime.fromisoformat(d).date()
                if dd < today:
                    overdue += 1
            except ValueError:
                pass

    return {
        "total_tasks": total,
        "pending_tasks": pending,
        "completed_tasks": completed,
        "high_priority_tasks": high_priority,
        "overdue_tasks": overdue,
        "needs_review_tasks": needs_review,
    }

