"""Reusable spaCy matcher patterns and lexical constants."""

from __future__ import annotations

from spacy.matcher import Matcher
from spacy.language import Language

ACTION_VERB_LEMMAS = {
    "send",
    "review",
    "fix",
    "update",
    "schedule",
    "complete",
    "finish",
    "prepare",
    "call",
    "reply",
    "submit",
    "confirm",
    "check",
    "follow",
}

URGENCY_TERMS = {
    "urgent",
    "asap",
    "immediately",
    "critical",
    "today",
    "eod",
}

DEADLINE_HINT_TERMS = {
    "today",
    "tomorrow",
    "friday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "saturday",
    "sunday",
    "week",
    "noon",
    "pm",
    "am",
    "eod",
}


def build_spacy_matcher(nlp: Language) -> Matcher:
    """Create and return matcher patterns used by SpacyExtractor."""
    matcher = Matcher(nlp.vocab)

    matcher.add(
        "ACTION_REQUEST",
        [
            [{"LOWER": {"IN": ["please", "kindly"]}}, {"LEMMA": {"IN": list(ACTION_VERB_LEMMAS)}}],
            [{"LOWER": {"IN": ["can", "could", "would"]}}, {"LOWER": "you"}, {"LEMMA": {"IN": list(ACTION_VERB_LEMMAS)}}],
            [{"LOWER": "let"}, {"ORTH": "'s"}, {"LEMMA": {"IN": list(ACTION_VERB_LEMMAS)}}],
            [{"LEMMA": {"IN": list(ACTION_VERB_LEMMAS)}}],
        ],
    )

    matcher.add(
        "DEADLINE_CUE",
        [
            [{"LOWER": {"IN": ["by", "before"]}}, {"IS_ALPHA": True, "OP": "+"}],
            [{"LOWER": "next"}, {"LOWER": {"IN": ["week", "monday", "tuesday", "wednesday", "thursday", "friday"]}}],
            [{"LOWER": {"IN": ["today", "tomorrow"]}}],
            [{"LOWER": "end"}, {"LOWER": "of"}, {"LOWER": {"IN": ["day", "week"]}}],
        ],
    )

    matcher.add(
        "URGENCY_CUE",
        [[{"LOWER": {"IN": list(URGENCY_TERMS)}}]],
    )
    return matcher

