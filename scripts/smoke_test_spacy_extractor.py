"""Lightweight smoke checks for the spaCy extractor."""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.extraction.spacy_utils import SpacyModelLoadError


CASES = [
    "Please send the report by Friday.",
    "Can you review the proposal tomorrow?",
    "Finish the slides ASAP.",
    "Let's schedule a meeting next Monday.",
    "FYI, the draft was shared last week.",
    "Please update the spreadsheet before noon.",
]


def main() -> None:
    try:
        from src.extraction.spacy_extractor import SpacyExtractor
    except ImportError as exc:
        print("Missing NLP dependencies. Run: pip install -r requirements.txt")
        raise SystemExit(1) from exc

    try:
        extractor = SpacyExtractor()
    except SpacyModelLoadError as exc:
        print(exc)
        raise SystemExit(1) from exc

    for text in CASES:
        out = extractor.extract(
            {
                "id": "demo",
                "sender": "demo@example.com",
                "subject": "Demo subject",
                "body": text,
                "received_at": "2026-03-25T09:00:00",
            }
        )
        assert out["extraction_method"] == "spacy"
        assert out["priority"] in {"Low", "Medium", "High"}
        assert out["task_title"] is None or isinstance(out["task_title"], str)
        print(f"Input: {text}")
        print(f" -> {out}")
        print("-" * 60)

    print("spaCy extractor smoke test passed.")


if __name__ == "__main__":
    main()

