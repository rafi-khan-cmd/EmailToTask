"""Analytics computation for the dashboard."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

import pandas as pd

from src.db.repository import get_all_tasks


def _effective_priority(task: dict[str, Any]) -> str:
    if task.get("user_corrected") and task.get("corrected_priority"):
        return str(task["corrected_priority"])
    return str(task.get("priority"))


def _effective_status(task: dict[str, Any]) -> str:
    return str(task.get("status"))


def _effective_normalized_deadline(task: dict[str, Any]) -> str | None:
    if task.get("user_corrected"):
        return task.get("corrected_normalized_deadline")
    return task.get("normalized_deadline")


def tasks_to_dataframe(limit: int = 10_000) -> pd.DataFrame:
    """Convert stored tasks into a DataFrame with effective fields."""
    tasks = get_all_tasks(limit=limit)
    rows: list[dict[str, Any]] = []
    for t in tasks:
        rows.append(
            {
                **t,
                "effective_priority": _effective_priority(t),
                "effective_status": _effective_status(t),
                "effective_normalized_deadline": _effective_normalized_deadline(t),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        # Create expected columns to simplify UI code.
        for col in [
            "created_at",
            "effective_priority",
            "effective_status",
            "sender",
            "effective_normalized_deadline",
        ]:
            if col not in df.columns:
                df[col] = pd.Series(dtype="object")
    return df


def tasks_by_priority(limit: int = 10_000) -> pd.DataFrame:
    df = tasks_to_dataframe(limit=limit)
    if df.empty:
        return pd.DataFrame({"priority": [], "count": []})
    out = df["effective_priority"].value_counts().reset_index()
    out.columns = ["priority", "count"]
    return out


def tasks_by_status(limit: int = 10_000) -> pd.DataFrame:
    df = tasks_to_dataframe(limit=limit)
    if df.empty:
        return pd.DataFrame({"status": [], "count": []})
    out = df["effective_status"].value_counts().reset_index()
    out.columns = ["status", "count"]
    return out


def tasks_by_sender(limit: int = 10_000, top_n: int = 10) -> pd.DataFrame:
    df = tasks_to_dataframe(limit=limit)
    if df.empty:
        return pd.DataFrame({"sender": [], "count": []})
    out = df["sender"].fillna("Unknown").value_counts().reset_index()
    out.columns = ["sender", "count"]
    return out.head(top_n)


def task_creation_trend(limit: int = 10_000, freq: str = "D") -> pd.DataFrame:
    """
    Compute task creation trend by day/week.

    freq: pandas resample frequency ("D" day, "W" week).
    """
    df = tasks_to_dataframe(limit=limit)
    if df.empty or "created_at" not in df.columns:
        return pd.DataFrame({"period": [], "count": []})

    # Parse created_at to datetime; errors become NaT and are ignored.
    created = pd.to_datetime(df["created_at"], errors="coerce", utc=False)
    df2 = df.copy()
    df2["created_at_dt"] = created
    df2 = df2.dropna(subset=["created_at_dt"])
    if df2.empty:
        return pd.DataFrame({"period": [], "count": []})

    grouped = df2.groupby(pd.Grouper(key="created_at_dt", freq=freq)).size().reset_index(name="count")
    grouped["period"] = grouped["created_at_dt"].dt.date.astype(str)
    return grouped[["period", "count"]]

