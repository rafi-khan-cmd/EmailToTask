"""Streamlit dashboard page."""

from __future__ import annotations

from typing import Any

import plotly.express as px
import streamlit as st

from src.db.repository import get_all_tasks, get_dashboard_metrics
from src.services.analytics_service import (
    task_creation_trend,
    tasks_by_priority,
    tasks_by_sender,
    tasks_by_status,
)
from src.services.task_service import (
    effective_deadline_text,
    effective_normalized_deadline,
    effective_task_title,
    is_overdue,
)
from src.ui.components import render_overdue_badge, render_priority_badge, render_status_badge


def _recent_tasks_view(limit: int = 10) -> list[dict[str, Any]]:
    tasks = get_all_tasks(limit=200)
    tasks_sorted = sorted(tasks, key=lambda t: t.get("created_at") or "", reverse=True)
    return tasks_sorted[:limit]


def _tasks_for_display(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in tasks:
        out.append(
            {
                "Task ID": t.get("id"),
                "Sender": t.get("sender") or "",
                "Subject": t.get("subject") or "",
                "Task Title": effective_task_title(t) or "",
                "Deadline": effective_deadline_text(t) or "",
                "Priority": (t.get("corrected_priority") if t.get("user_corrected") else t.get("priority")),
                "Status": t.get("status"),
                "Needs Review": bool(t.get("needs_review")),
                "Overdue": is_overdue(t),
            }
        )
    return out


def render_dashboard_page() -> None:
    metrics = get_dashboard_metrics()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Tasks", metrics["total_tasks"])
    c2.metric("Pending", metrics["pending_tasks"])
    c3.metric("Completed", metrics["completed_tasks"])
    c4.metric("High Priority", metrics["high_priority_tasks"])
    c5.metric("Overdue", metrics["overdue_tasks"])

    st.divider()

    # Charts.
    col_a, col_b = st.columns(2)
    with col_a:
        pri_df = tasks_by_priority()
        if not pri_df.empty:
            fig = px.bar(pri_df, x="priority", y="count", title="Tasks by Priority")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tasks yet. Upload emails to generate tasks.")

    with col_b:
        status_df = tasks_by_status()
        if not status_df.empty:
            fig = px.bar(status_df, x="status", y="count", title="Tasks by Status")
            st.plotly_chart(fig, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        trend = task_creation_trend(freq="D")
        if not trend.empty:
            fig = px.line(trend, x="period", y="count", title="Task Creation Trend (Daily)")
            st.plotly_chart(fig, use_container_width=True)

    with col_d:
        sender_df = tasks_by_sender()
        if not sender_df.empty:
            fig = px.bar(sender_df, x="count", y="sender", orientation="h", title="Top Senders")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    all_tasks = get_all_tasks(limit=500)
    needs_review = [t for t in all_tasks if bool(t.get("needs_review"))]
    overdue = [t for t in all_tasks if is_overdue(t)]
    recent = _recent_tasks_view(8)

    left, right = st.columns(2)
    with left:
        st.subheader("Recent Tasks")
        display = _tasks_for_display(recent)
        st.dataframe(display, use_container_width=True, hide_index=True)
        if display:
            st.caption("Use the `Tasks` page to open and edit a task.")

    with right:
        st.subheader("Tasks Needing Review")
        if not needs_review:
            st.success("No tasks are currently flagged for review.")
        else:
            top = sorted(needs_review, key=lambda t: t.get("extraction_confidence") or 0)[:5]
            for t in top:
                st.write(f"Task #{t.get('id')}: {effective_task_title(t) or '(untitled)'}")
                render_priority_badge(
                    t.get("corrected_priority") if t.get("user_corrected") else t.get("priority")
                )
                render_status_badge(t.get("status"))
                render_overdue_badge(is_overdue(t))
                st.caption(f"Deadline: {effective_deadline_text(t) or '—'}")

    if overdue:
        st.divider()
        st.subheader("Overdue")
        top_overdue = sorted(
            overdue,
            key=lambda t: effective_normalized_deadline(t) or t.get("normalized_deadline") or "",
        )[:5]
        for t in top_overdue:
            st.write(f"Task #{t.get('id')}: {effective_task_title(t) or '(untitled)'}")
            render_overdue_badge(True)
            render_status_badge(t.get("status"))
            st.caption(f"Deadline: {effective_deadline_text(t) or '—'}")


def render_analytics_page() -> None:
    """Analytics page uses the same charts as dashboard with extra focus."""
    st.header("Analytics")
    st.write("Key metrics and trends across tasks. Corrections are reflected where applicable.")

    col_a, col_b = st.columns(2)
    with col_a:
        pri_df = tasks_by_priority()
        if not pri_df.empty:
            st.plotly_chart(px.bar(pri_df, x="priority", y="count", title="Tasks by Priority"), use_container_width=True)
    with col_b:
        status_df = tasks_by_status()
        if not status_df.empty:
            st.plotly_chart(px.bar(status_df, x="status", y="count", title="Tasks by Status"), use_container_width=True)

    st.subheader("Task Creation Trend")
    trend = task_creation_trend(freq="W")
    if trend.empty:
        st.info("Not enough data yet.")
    else:
        st.plotly_chart(px.line(trend, x="period", y="count", title="Task Creation Trend (Weekly)"), use_container_width=True)

    st.subheader("Top Senders")
    sender_df = tasks_by_sender(top_n=15)
    if sender_df.empty:
        st.info("No sender data available.")
    else:
        st.plotly_chart(px.bar(sender_df, x="count", y="sender", orientation="h", title="Top Senders"), use_container_width=True)

