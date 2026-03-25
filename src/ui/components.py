"""Reusable Streamlit UI components."""

from __future__ import annotations

import streamlit as st

from src.config import (
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    STATUS_ARCHIVED,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)


def _badge_style(color: str) -> str:
    return (
        "display:inline-block;"
        f"background-color:{color};"
        "color:white;"
        "padding:2px 8px;"
        "border-radius:999px;"
        "font-size:12px;"
        "line-height:18px;"
    )


def render_priority_badge(priority: str | None) -> None:
    if not priority:
        st.write("")
        return

    p = str(priority)
    if p == PRIORITY_HIGH:
        color = "#d7263d"
    elif p == PRIORITY_MEDIUM:
        color = "#f77f00"
    else:
        color = "#2a9d8f"

    st.markdown(f"<span style='{_badge_style(color)}'>{p}</span>", unsafe_allow_html=True)


def render_status_badge(status: str | None) -> None:
    if not status:
        st.write("")
        return

    s = str(status)
    if s == STATUS_COMPLETED:
        color = "#1b998b"
    elif s == STATUS_ARCHIVED:
        color = "#6c757d"
    elif s == STATUS_IN_PROGRESS:
        color = "#3a86ff"
    else:
        color = "#444444"

    st.markdown(f"<span style='{_badge_style(color)}'>{s}</span>", unsafe_allow_html=True)


def render_overdue_badge(is_overdue: bool) -> None:
    if not is_overdue:
        return
    st.markdown(
        f"<span style='{_badge_style('#b00020')}'>&#9888; Overdue</span>",
        unsafe_allow_html=True,
    )


def empty_state(message: str) -> None:
    st.info(message)

