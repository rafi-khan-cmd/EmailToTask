"""Task detail/review editor page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.config import (
    PRIORITIES,
    STATUSES,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)
from src.db.repository import update_task
from src.db.repository import TaskFilters
from src.services.task_service import get_task_detail, is_overdue
from src.services.task_service import get_tasks_for_ui
from src.ui.components import render_overdue_badge, render_priority_badge, render_status_badge


def _parse_optional_date_input(value: str | None) -> str | None:
    """
    Normalize a YYYY-MM-DD text input into the same format we store.

    Returns None for empty input.
    """
    if value is None:
        return None
    s = value.strip()
    if not s:
        return None
    # Keep as-is if it looks like YYYY-MM-DD.
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    # Try parsing any ISO date.
    try:
        from datetime import date

        dt = date.fromisoformat(s)
        return dt.isoformat()
    except Exception:
        return s  # store raw; user can correct later


def render_task_detail_editor(task_id: int, *, mode: str = "tasks") -> None:
    """Render the editor UI for a single task."""
    t = get_task_detail(task_id)
    if not t:
        st.error("Task not found.")
        return

    st.subheader(f"Task Review / Editor (ID: {t.get('id')})")

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("### Original Email")
        st.caption(f"Sender: {t.get('sender') or '—'}")
        st.caption(f"Subject: {t.get('subject') or '—'}")
        with st.expander("Show original email body"):
            st.write(t.get("original_body") or "")

    with right:
        st.markdown("### Extraction Summary")
        render_priority_badge(t.get("effective_priority"))
        render_status_badge(t.get("status"))
        render_overdue_badge(is_overdue(t))
        st.write(
            f"Extraction confidence: `{t.get('extraction_confidence')}`"
        )
        st.write(f"Extraction method: `{t.get('extraction_method') or 'unknown'}`")
        st.write(f"Needs Review: `{bool(t.get('needs_review'))}`")

    st.divider()

    st.markdown("### Corrected Values (Human-in-the-loop)")

    extracted_title = t.get("task_title") or ""
    extracted_deadline_text = t.get("deadline_text") or ""
    extracted_normalized_deadline = t.get("normalized_deadline") or ""
    extracted_priority = t.get("priority") or ""

    effective_title = t.get("effective_task_title") or extracted_title

    default_needs_review = True if mode == "review_queue" else bool(t.get("needs_review"))
    mark_reviewed = st.checkbox("Mark as Reviewed", value=not default_needs_review)

    # Status.
    status = st.selectbox(
        "Task Status",
        options=STATUSES,
        index=STATUSES.index(t.get("status")) if t.get("status") in STATUSES else 0,
    )

    corrected_task_title = st.text_input(
        "Corrected Task Title",
        value=t.get("corrected_task_title") if t.get("corrected_task_title") is not None else effective_title,
        placeholder=extracted_title,
    )
    corrected_deadline_text = st.text_input(
        "Corrected Deadline Text (raw)",
        value=t.get("corrected_deadline_text") if t.get("corrected_deadline_text") is not None else (extracted_deadline_text or ""),
        placeholder=extracted_deadline_text,
    )
    corrected_normalized_deadline = st.text_input(
        "Corrected Normalized Deadline (YYYY-MM-DD, optional)",
        value=t.get("corrected_normalized_deadline") if t.get("corrected_normalized_deadline") is not None else (extracted_normalized_deadline or ""),
        placeholder=extracted_normalized_deadline,
    )
    current_priority = (
        t.get("corrected_priority")
        if t.get("corrected_priority") is not None
        else (t.get("effective_priority") or extracted_priority)
    )
    if current_priority not in PRIORITIES:
        current_priority = PRIORITIES[0]

    corrected_priority = st.selectbox(
        "Corrected Priority",
        options=PRIORITIES,
        index=PRIORITIES.index(str(current_priority)),
    )

    notes = st.text_area(
        "Notes",
        value=t.get("notes") or "",
        placeholder="Add context for yourself or the team...",
    )

    extracted_display_block = st.expander("Show extracted fields (original v1 output)")
    with extracted_display_block:
        st.write(f"Task Title (extracted): `{extracted_title}`")
        st.write(f"Deadline Text (extracted): `{extracted_deadline_text or '—'}`")
        st.write(f"Normalized Deadline (extracted): `{extracted_normalized_deadline or '—'}`")
        st.write(f"Priority (extracted): `{extracted_priority or '—'}`")

    save_clicked = st.button("Save Changes", type="primary")
    if save_clicked:
        # Convert empty strings to None so we can clear corrections.
        had_corrections = bool(t.get("user_corrected"))

        raw_title = corrected_task_title.strip()
        raw_deadline_text = corrected_deadline_text.strip()
        raw_norm = _parse_optional_date_input(corrected_normalized_deadline)
        raw_priority = (corrected_priority.strip() if corrected_priority else "").strip() or None

        # Avoid marking `user_corrected` unless the user actually changed something
        # from the current effective/extracted values.
        corrected_title_val = None if raw_title == extracted_title and not had_corrections else (raw_title or None)
        corrected_deadline_val = (
            None if raw_deadline_text == extracted_deadline_text and not had_corrections else (raw_deadline_text or None)
        )
        corrected_norm_val = (
            None if raw_norm == extracted_normalized_deadline and not had_corrections else raw_norm
        )
        corrected_prio_val = (
            None if raw_priority == extracted_priority and not had_corrections else raw_priority
        )

        # Persist updates.
        update_task(
            task_id=int(t["id"]),
            corrected_task_title=corrected_title_val,
            corrected_deadline_text=corrected_deadline_val,
            corrected_normalized_deadline=corrected_norm_val,
            corrected_priority=corrected_prio_val,
            notes=notes.strip() or None,
            status=str(status),
            needs_review=bool(not mark_reviewed),
        )
        st.success("Task updated.")
        st.rerun()


def render_task_detail_page(*, mode: str = "review_queue") -> None:
    """Route-level wrapper for the task detail editor."""
    if mode != "review_queue":
        st.info("This page is currently intended for the review queue.")
        return

    st.header("Review Queue")

    tasks = get_tasks_for_ui(
        TaskFilters(
            search=None,
            priority=None,
            status=None,
            needs_review=True,
            overdue=None,
            sender=None,
        )
    )
    tasks = sorted(tasks, key=lambda t: t.get("extraction_confidence") or 0.0)

    if not tasks:
        st.success("No tasks currently need review. Nice work!")
        return

    ids = [int(t["id"]) for t in tasks if t.get("id") is not None]
    selected = st.selectbox("Open task", options=ids, index=0)
    if selected is not None:
        render_task_detail_editor(task_id=int(selected), mode="review_queue")

