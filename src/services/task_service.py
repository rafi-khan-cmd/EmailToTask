"""Task-specific helpers for the UI."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from src.config import STATUS_ARCHIVED, STATUS_COMPLETED
from src.db.repository import get_task_by_id, filter_tasks, TaskFilters


def effective_task_title(task: dict[str, Any]) -> str | None:
    if task.get("user_corrected") and task.get("corrected_task_title") is not None:
        return task.get("corrected_task_title")
    return task.get("task_title")


def effective_deadline_text(task: dict[str, Any]) -> str | None:
    if task.get("user_corrected") and task.get("corrected_deadline_text") is not None:
        return task.get("corrected_deadline_text")
    return task.get("deadline_text")


def effective_normalized_deadline(task: dict[str, Any]) -> str | None:
    if task.get("user_corrected"):
        return task.get("corrected_normalized_deadline")
    return task.get("normalized_deadline")


def effective_priority(task: dict[str, Any]) -> str | None:
    if task.get("user_corrected") and task.get("corrected_priority") is not None:
        return task.get("corrected_priority")
    return task.get("priority")


def is_overdue(task: dict[str, Any]) -> bool:
    status = task.get("status")
    if status in (STATUS_COMPLETED, STATUS_ARCHIVED):
        return False
    norm = effective_normalized_deadline(task)
    if not norm:
        return False
    try:
        d = datetime.fromisoformat(norm).date()
    except ValueError:
        return False
    return d < date.today()


def get_tasks_for_ui(filters: TaskFilters) -> list[dict[str, Any]]:
    """Return tasks augmented with effective fields for UI rendering."""
    tasks = filter_tasks(filters)
    out: list[dict[str, Any]] = []
    for t in tasks:
        out.append(
            {
                **t,
                "effective_task_title": effective_task_title(t),
                "effective_deadline_text": effective_deadline_text(t),
                "effective_normalized_deadline": effective_normalized_deadline(t),
                "effective_priority": effective_priority(t),
                "overdue": is_overdue(t),
            }
        )
    return out


def get_task_detail(task_id: int) -> dict[str, Any] | None:
    """Fetch a task and add computed effective fields."""
    t = get_task_by_id(task_id)
    if not t:
        return None
    return {
        **t,
        "effective_task_title": effective_task_title(t),
        "effective_deadline_text": effective_deadline_text(t),
        "effective_normalized_deadline": effective_normalized_deadline(t),
        "effective_priority": effective_priority(t),
        "overdue": is_overdue(t),
    }

