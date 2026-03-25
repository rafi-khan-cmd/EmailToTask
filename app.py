"""Streamlit entrypoint for the Email-to-Task Automation Dashboard."""

from __future__ import annotations

import streamlit as st

from src.config import EXTRACTOR_OPTIONS, EXTRACTOR_SPACY, get_default_extractor_method
from src.db.repository import get_all_tasks
from src.extraction.factory import resolve_extractor_method
from src.extraction.spacy_utils import is_spacy_model_available
from src.ingestion.loaders import load_emails_from_json
from src.services.processing_service import process_emails
from src.ui.dashboard import render_dashboard_page
from src.ui.task_table import render_tasks_page
from src.ui.task_detail import render_task_detail_page
from src.ui.upload_page import render_upload_page
from src.ui.dashboard import render_analytics_page
from src.config import get_sample_data_paths


def _auto_seed_if_empty() -> None:
    if st.session_state.get("_auto_seed_done"):
        return
    st.session_state["_auto_seed_done"] = True
    try:
        existing = get_all_tasks(limit=1)
        if existing:
            return
        _, sample_json_path = get_sample_data_paths()
        if not sample_json_path.exists():
            return
        emails = load_emails_from_json(sample_json_path.read_bytes())
        if not emails:
            return
        process_emails(emails, extraction_method="rule_based")
        st.sidebar.success("Sample data preloaded.")
    except Exception:
        # Keep startup resilient even if sample preloading fails.
        return


def main() -> None:
    st.set_page_config(
        page_title="Email-to-Task Automation Dashboard",
        layout="wide",
    )

    st.title("Email-to-Task Automation Dashboard")
    st.caption("Convert unstructured emails into structured tasks (rule-based + spaCy NLP).")

    configured_default = get_default_extractor_method()
    default_method = resolve_extractor_method(configured_default)
    if "selected_extractor_method" not in st.session_state:
        st.session_state["selected_extractor_method"] = default_method

    method_idx = EXTRACTOR_OPTIONS.index(st.session_state["selected_extractor_method"])
    chosen_method = st.sidebar.selectbox(
        "Extractor Mode",
        options=EXTRACTOR_OPTIONS,
        index=method_idx,
        format_func=lambda x: "spaCy NLP" if x == EXTRACTOR_SPACY else "Rule-based",
        help="Used for new processing runs from Upload Emails. Existing tasks keep their stored method.",
    )
    st.session_state["selected_extractor_method"] = resolve_extractor_method(chosen_method)

    if chosen_method == EXTRACTOR_SPACY and not is_spacy_model_available():
        st.sidebar.warning(
            "spaCy model not found. Falling back to rule_based. Run: "
            "`python -m spacy download en_core_web_sm`"
        )

    _auto_seed_if_empty()

    page = st.sidebar.radio(
        "Navigation",
        options=[
            "Dashboard",
            "Tasks",
            "Review Queue",
            "Upload Emails",
            "Analytics",
        ],
        index=0,
    )

    # A small bit of routing glue: Review Queue and Task Detail share the same editor view.
    if page == "Dashboard":
        render_dashboard_page()
    elif page == "Tasks":
        render_tasks_page()
    elif page == "Review Queue":
        render_task_detail_page(mode="review_queue")
    elif page == "Upload Emails":
        render_upload_page()
    elif page == "Analytics":
        render_analytics_page()


if __name__ == "__main__":
    main()

