"""Upload emails page."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pandas as pd
import streamlit as st

from src.config import EXTRACTOR_OPTIONS, EXTRACTOR_SPACY, get_sample_data_paths
from src.extraction.factory import resolve_extractor_method
from src.ingestion.loaders import load_emails_from_json, load_emails_from_csv, EmailRecord
from src.services.processing_service import process_emails


def _emails_to_preview_df(emails: list[EmailRecord]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": e.id,
                "sender": e.sender,
                "subject": e.subject,
                "received_at": e.received_at,
                "body_preview": (e.body or "")[:120].replace("\n", " ") + ("..." if e.body and len(e.body) > 120 else ""),
            }
            for e in emails
        ]
    )


def _load_sample_dataset() -> list[EmailRecord]:
    csv_path, json_path = get_sample_data_paths()

    emails: list[EmailRecord] = []
    if csv_path.exists():
        emails.extend(load_emails_from_csv(csv_path.read_bytes()))
    if json_path.exists():
        # Merge; JSON and CSV should represent the same set.
        more = load_emails_from_json(json_path.read_bytes())
        by_id = {e.id: e for e in emails}
        for e in more:
            by_id[e.id] = e
        emails = list(by_id.values())
    return emails


def render_upload_page() -> None:
    st.header("Upload Emails")

    st.markdown(
        "Upload a `.csv` or `.json` file, or load the bundled sample dataset to see the app in action."
    )

    uploaded = st.file_uploader("Choose a CSV or JSON file", type=["csv", "json"])

    load_sample = st.button("Load Sample Dataset", type="primary")

    emails: list[EmailRecord] = []
    preview_df: pd.DataFrame | None = None

    if load_sample:
        try:
            emails = _load_sample_dataset()
            preview_df = _emails_to_preview_df(emails)
            st.success(f"Loaded sample dataset: {len(emails)} emails.")
        except Exception as e:  # noqa: BLE001
            st.error(f"Failed to load sample dataset: {e}")

    if uploaded is not None:
        try:
            file_bytes = uploaded.getvalue()
            name = uploaded.name or ""
            if name.lower().endswith(".csv"):
                emails = load_emails_from_csv(file_bytes)
            else:
                emails = load_emails_from_json(file_bytes)
            preview_df = _emails_to_preview_df(emails)
            st.success(f"Loaded upload: {len(emails)} emails.")
        except Exception as e:  # noqa: BLE001
            st.error(str(e))

    selected_method = st.session_state.get("selected_extractor_method", "rule_based")

    if emails:
        st.divider()
        st.subheader("Preview")
        st.dataframe(preview_df, use_container_width=True, hide_index=True)

        st.subheader("Process & Extract Tasks")
        method = st.selectbox(
            "Extraction method",
            options=EXTRACTOR_OPTIONS,
            index=EXTRACTOR_OPTIONS.index(selected_method) if selected_method in EXTRACTOR_OPTIONS else 0,
            format_func=lambda x: "spaCy NLP" if x == EXTRACTOR_SPACY else "Rule-based",
        )
        method = resolve_extractor_method(method)
        if st.button("Process Emails", type="primary"):
            with st.spinner("Extracting tasks and saving to the database..."):
                result = process_emails(emails, extraction_method=method)
            st.success(
                f"Processed {result.emails_processed} emails. Tasks updated in DB."
            )
            if result.errors:
                st.warning("Some rows could not be processed:")
                for err in result.errors[:20]:
                    st.write(err)
                if len(result.errors) > 20:
                    st.caption(f"...and {len(result.errors) - 20} more.")

            st.toast("Done.")
            st.rerun()

    st.divider()
    st.subheader("Submit Individual Email")
    st.caption("Use this quick form so recruiters can test extraction on one email at a time.")

    with st.form("single_email_form", clear_on_submit=False):
        sender = st.text_input(
            "Sender",
            placeholder="e.g. Alex Kim <alex@example.com>",
        )
        subject = st.text_input(
            "Subject",
            placeholder="e.g. Please review proposal by Friday",
        )
        body = st.text_area(
            "Body",
            placeholder="Paste a single email body here...",
            height=180,
        )
        received_at = st.text_input(
            "Received At (optional, ISO datetime)",
            placeholder="e.g. 2026-03-25T09:30:00",
        )
        submitted = st.form_submit_button("Process This Email", type="primary")

    if submitted:
        if not subject.strip() and not body.strip():
            st.error("Please provide at least a subject or body.")
            return

        received_val = received_at.strip() or datetime.utcnow().isoformat()
        email = EmailRecord(
            id=f"manual_{uuid4().hex[:12]}",
            sender=sender.strip() or "manual@local",
            subject=subject.strip() or "(No Subject)",
            body=body.strip() or "",
            received_at=received_val,
        )

        with st.spinner("Processing single email..."):
            result = process_emails([email], extraction_method=resolve_extractor_method(selected_method))

        if result.errors:
            st.error("Could not process this email.")
            for err in result.errors:
                st.write(err)
        else:
            st.success("Email processed and task created. Check Dashboard, Tasks, or Review Queue.")
            st.toast("Single email processed.")
