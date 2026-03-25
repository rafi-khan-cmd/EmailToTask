"""Tasks list/table page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.db.repository import TaskFilters
from src.services.task_service import get_tasks_for_ui
from src.ui.task_detail import render_task_detail_editor


def _extract_unique_senders(tasks: list[dict[str, Any]]) -> list[str]:
    senders = sorted({(t.get("sender") or "").strip() for t in tasks if t.get("sender")})
    return senders


def render_tasks_page() -> None:
    st.header("Tasks")

    # Filters.
    tasks_for_filters = get_tasks_for_ui(
        TaskFilters(search=None, priority=None, status=None, needs_review=None, overdue=None, sender=None)
    )
    senders = _extract_unique_senders(tasks_for_filters)

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        search = st.text_input("Search", placeholder="Sender, subject, or task title")
    with col_f2:
        priority = st.selectbox("Priority", options=["All", "Low", "Medium", "High"], index=0)
    with col_f3:
        status = st.selectbox(
            "Status", options=["All", "Pending", "In Progress", "Completed", "Archived"], index=0
        )
    with col_f4:
        needs_review = st.selectbox("Needs Review", options=["Any", "Yes", "No"], index=0)

    col_f5, col_f6 = st.columns(2)
    with col_f5:
        sender = st.selectbox("Sender", options=["All"] + senders, index=0)
    with col_f6:
        overdue_only = st.toggle("Overdue only", value=False)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        sort_by = st.selectbox("Sort by", options=["created_at", "normalized_deadline"], index=0)
    with col_s2:
        sort_desc = st.toggle("Newest first", value=True)

    filters = TaskFilters(
        search=search.strip() or None,
        priority=None if priority == "All" else priority,
        status=None if status == "All" else status,
        needs_review=None if needs_review == "Any" else (needs_review == "Yes"),
        overdue=None,  # apply after effective deadline selection
        sender=None if sender == "All" else sender,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    tasks = get_tasks_for_ui(filters)
    if overdue_only:
        tasks = [t for t in tasks if t.get("overdue") is True]

    st.divider()

    if not tasks:
        st.info("No tasks match the selected filters.")
        return

    # Show table.
    show = [
        {
            "id": t.get("id"),
            "Sender": t.get("sender") or "",
            "Subject": t.get("subject") or "",
            "Task Title": t.get("effective_task_title") or "",
            "Priority": t.get("effective_priority") or "",
            "Deadline": t.get("effective_deadline_text") or "",
            "Status": t.get("status") or "",
            "Method": t.get("extraction_method") or "",
            "Needs Review": bool(t.get("needs_review")),
            "Overdue": bool(t.get("overdue")),
            "Confidence": t.get("extraction_confidence"),
            "Created": t.get("created_at"),
        }
        for t in tasks
    ]
    st.dataframe(show, use_container_width=True, hide_index=True)

    # Select a task to edit.
    ids = [int(t["id"]) for t in tasks if t.get("id") is not None]
    selected = st.selectbox("Open task", options=ids, index=0, key="tasks_selected_id")

    if selected is not None:
        render_task_detail_editor(task_id=int(selected), mode="tasks")

