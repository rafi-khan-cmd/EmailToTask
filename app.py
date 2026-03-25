"""Streamlit entrypoint for the Email-to-Task Automation Dashboard."""

from __future__ import annotations

import streamlit as st

from src.config import EXTRACTOR_OPTIONS, EXTRACTOR_SPACY, get_default_extractor_method
from src.extraction.factory import resolve_extractor_method
from src.extraction.spacy_utils import is_spacy_model_available
from src.ui.dashboard import render_dashboard_page
from src.ui.task_table import render_tasks_page
from src.ui.task_detail import render_task_detail_page
from src.ui.upload_page import render_upload_page
from src.ui.dashboard import render_analytics_page


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

