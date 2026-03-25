# Email-to-Task Automation Dashboard

Convert unstructured email text into structured tasks using a modular extraction architecture with two extractor modes:
- `rule_based` (regex + deterministic heuristics)
- `spacy` (spaCy NLP + dateparser normalization)

The app includes persistent task storage, a review queue for human correction, and analytics dashboards for operational visibility.

## Problem Statement
Action items are often buried inside unstructured emails. This project turns email-like text into a usable task workflow with deadlines, priorities, and review flags.

## NLP Upgrade Overview
The extraction engine now supports two interchangeable implementations under a common `BaseExtractor` interface:
- `RuleBasedExtractor`
- `SpacyExtractor`

Both return the same output contract:
```python
{
  "task_title": str | None,
  "deadline_text": str | None,
  "normalized_deadline": str | None,
  "priority": "Low" | "Medium" | "High",
  "extraction_confidence": float,
  "needs_review": bool,
  "extraction_method": str,
}
```

## Why spaCy
- Fast to integrate
- Great sentence/token parsing for heuristic NLP
- Strong production-friendly baseline for non-trained-model extraction
- Keeps architecture modular and easy to extend

## Why dateparser
- Parses human-readable deadline phrases (`tomorrow`, `next Monday`, `by 3 PM`)
- Converts raw deadline text into normalized datetime values when possible
- Works well with deterministic extraction rules

## Key Features
- CSV/JSON email ingestion + bundled sample datasets
- Dual extraction modes (rule-based and spaCy NLP)
- Deadline text capture and date normalization
- Human-in-the-loop review queue (`needs_review`)
- Editable task detail view (corrected title/deadline/priority/status/notes)
- Dashboard metrics and analytics charts
- Task table with search, filters, sorting, overdue flagging
- SQLite persistence with clean repository abstraction

## Architecture Overview
The app keeps extraction decoupled from UI and storage:
- UI does not implement extraction logic
- services orchestrate ingestion → preprocessing → extraction → persistence
- extractor implementations are swappable through a factory

## Folder Structure
```text
project_root/
  app.py
  requirements.txt
  README.md
  env.example
  data/
    sample_emails.csv
    sample_emails.json
  src/
    config.py
    db/
      connection.py
      schema.py
      repository.py
    ingestion/
      loaders.py
      validators.py
    preprocessing/
      cleaner.py
    extraction/
      base.py
      rule_based.py
      spacy_extractor.py
      factory.py
      spacy_patterns.py
      spacy_utils.py
      deadline_utils.py
      priority_utils.py
      task_utils.py
    services/
      processing_service.py
      analytics_service.py
      task_service.py
    ui/
      dashboard.py
      task_table.py
      task_detail.py
      upload_page.py
      components.py
  scripts/
    init_db.py
    seed_data.py
    reset_db.py
    smoke_test_spacy_extractor.py
```

## Tech Stack
- Python
- Streamlit
- pandas
- SQLite
- Plotly
- spaCy (`en_core_web_sm`)
- dateparser

## Local Setup
1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python -m spacy download en_core_web_sm`
5. `python3 scripts/init_db.py`
6. `python3 scripts/seed_data.py`
7. `streamlit run app.py`

## Extraction Modes in App
Use the sidebar selector:
- **Rule-based**
- **spaCy NLP**

If spaCy model is missing, the app shows a clear warning and falls back to `rule_based`.

## Database Initialization
- `scripts/init_db.py` creates schema
- `scripts/seed_data.py` ingests sample emails and extracts tasks
- `scripts/reset_db.py` resets and recreates schema

## Smoke Test for NLP Extractor
Run:
```bash
python3 scripts/smoke_test_spacy_extractor.py
```
This validates plausible outputs for several test cases and confirms `extraction_method="spacy"`.

## Deployment (Streamlit Community Cloud)
- Deploy `app.py` with `requirements.txt`
- Ensure spaCy model is available in the environment:
  - `python -m spacy download en_core_web_sm`
- SQLite storage can be ephemeral depending on cloud restart/redeploy behavior

## Extensibility
To add a future extractor:
1. Implement `BaseExtractor.extract(...)`
2. Return the same output schema
3. Register in `src/extraction/factory.py`

This keeps UI, services, and DB logic unchanged.

## Limitations
- Extraction is heuristic, not model-trained
- Ambiguous deadline phrases may remain unnormalized
- Non-actionable/weak emails can still require manual review
- Multi-action emails currently prioritize one main task phrase

## Resume-ready Bullet Suggestions
- Enhanced an email-to-task automation dashboard with spaCy-based NLP to extract action items, deadlines, and priorities from unstructured email text.
- Integrated date normalization using dateparser to convert human-readable deadline phrases into structured task metadata.
- Designed a modular extractor architecture supporting both rule-based and NLP pipelines through a shared interface.
- Implemented a human-in-the-loop review workflow to validate and correct ambiguous extraction outputs.
- Built analytics and dashboard views to monitor extracted tasks, overdue items, and review-needed cases.

## GitHub Project Description
Deployable Streamlit app that transforms unstructured emails into structured tasks using dual extraction modes (rule-based + spaCy NLP). Includes dateparser-based deadline normalization, review queue corrections, SQLite persistence, and analytics dashboards.

## Portfolio Description
Built an NLP-enhanced productivity dashboard that extracts actionable tasks from email text. The system supports both deterministic and spaCy-powered extraction, normalizes date phrases with dateparser, and includes a human-in-the-loop review workflow for reliable operations.

