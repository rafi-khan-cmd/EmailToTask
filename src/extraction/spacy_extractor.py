"""spaCy-powered extractor for v2 NLP-enhanced task extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

import dateparser

from src.extraction.base import BaseExtractor, EmailForExtraction, ExtractorOutput
from src.extraction.spacy_patterns import (
    ACTION_VERB_LEMMAS,
    build_spacy_matcher,
)
from src.extraction.spacy_utils import get_nlp_model


DEADLINE_REGEX = re.compile(
    r"\b("
    r"today|tomorrow|next\s+(?:monday|tuesday|wednesday|thursday|friday|week)|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"end of day|end of week|before noon|by noon|by eod|"
    r"by\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)"
    r")\b",
    flags=re.IGNORECASE,
)

HIGH_URGENCY_PHRASES = (
    "urgent",
    "asap",
    "immediately",
    "as soon as possible",
    "today",
    "end of day",
    "by eod",
    "critical",
)


@dataclass
class _SpacySignals:
    action_verb_found: bool = False
    object_phrase_found: bool = False
    deadline_found: bool = False
    deadline_normalized: bool = False
    urgency_found: bool = False
    fallback_used: bool = False
    generic_fallback_used: bool = False


class SpacyExtractor(BaseExtractor):
    """spaCy-based extractor with deterministic NLP heuristics."""

    def __init__(self) -> None:
        self.nlp = get_nlp_model()
        self.matcher = build_spacy_matcher(self.nlp)

    @staticmethod
    def _combine_text(email: EmailForExtraction) -> str:
        subject = (email.get("subject") or "").strip()
        body = (email.get("body") or "").strip()
        cleaned = (email.get("cleaned_text") or "").strip()
        if cleaned:
            return cleaned
        return "\n\n".join([x for x in [subject, body] if x]).strip()

    @staticmethod
    def _light_clean(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _rank_sentences(self, doc) -> list:
        ranked: list[tuple[float, object]] = []
        for sent in doc.sents:
            score = 0.0
            lower = sent.text.lower()
            lemmas = {t.lemma_.lower() for t in sent if t.is_alpha}

            if lemmas.intersection(ACTION_VERB_LEMMAS):
                score += 2.0
            if any(term in lower for term in HIGH_URGENCY_PHRASES):
                score += 1.5
            if DEADLINE_REGEX.search(lower):
                score += 1.5
            if any(t in lower for t in ("please", "can you", "could you", "let's", "reminder")):
                score += 0.8
            if len(sent.text.strip()) <= 180:
                score += 0.2
            ranked.append((score, sent))

        ranked.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in ranked if x[0] > 0]

    @staticmethod
    def _titleize(text: str) -> str:
        s = re.sub(r"\s+", " ", text).strip(" .,:;")
        if not s:
            return s
        return s[0].upper() + s[1:]

    def _extract_task_title(self, doc, candidate_sentences: list) -> tuple[str | None, _SpacySignals]:
        signals = _SpacySignals()

        def from_sentence(sent) -> tuple[str | None, bool]:
            for tok in sent:
                lemma = tok.lemma_.lower()
                if tok.pos_ in {"VERB", "AUX"} and lemma in ACTION_VERB_LEMMAS:
                    signals.action_verb_found = True
                    # Grab direct object-ish phrase after the verb.
                    phrase_tokens = [tok.text]
                    for child in tok.children:
                        if child.dep_ in {"dobj", "obj", "pobj", "attr"}:
                            subtree = [t for t in child.subtree if t.i >= tok.i and t.i < tok.i + 10]
                            if subtree:
                                signals.object_phrase_found = True
                                phrase_tokens = [tok.text] + [t.text for t in subtree]
                                break

                    # fallback: take next few non-punct tokens after verb.
                    if not signals.object_phrase_found:
                        tail = [t.text for t in sent if t.i > tok.i and not t.is_punct][:4]
                        if tail:
                            phrase_tokens = [tok.text] + tail

                    text = " ".join(phrase_tokens)
                    text = re.split(
                        r"\b(by|before|tomorrow|today|next week|end of day|end of week|asap|urgent|immediately)\b",
                        text,
                        flags=re.IGNORECASE,
                    )[0]
                    return self._titleize(text), True
            return None, False

        for sent in candidate_sentences:
            title, ok = from_sentence(sent)
            if ok and title:
                return title, signals

        # Secondary: matcher-based fallback.
        matches = self.matcher(doc)
        for _, start, end in matches:
            span = doc[start:end]
            if span.text and any(t.lemma_.lower() in ACTION_VERB_LEMMAS for t in span):
                signals.fallback_used = True
                return self._titleize(span.text), signals

        # Subject fallback.
        subject = (doc[: min(len(doc), 16)].text or "").strip()
        if subject:
            signals.fallback_used = True
            return self._titleize(" ".join(subject.split()[:6])) or None, signals

        signals.fallback_used = True
        signals.generic_fallback_used = True
        return "Review email request", signals

    def _extract_deadline_text(self, doc, candidate_sentences: list) -> str | None:
        for sent in candidate_sentences:
            m = DEADLINE_REGEX.search(sent.text)
            if m:
                return m.group(0).strip()
        m = DEADLINE_REGEX.search(doc.text)
        if m:
            return m.group(0).strip()
        return None

    @staticmethod
    def _normalize_deadline(deadline_text: str | None, base_dt: datetime) -> str | None:
        if not deadline_text:
            return None
        parsed = dateparser.parse(
            deadline_text,
            settings={
                "PREFER_DATES_FROM": "future",
                "RELATIVE_BASE": base_dt,
                "RETURN_AS_TIMEZONE_AWARE": False,
            },
        )
        if not parsed:
            return None
        return parsed.isoformat()

    @staticmethod
    def _extract_priority(text: str, deadline_exists: bool) -> tuple[str, bool]:
        lower = text.lower()
        if any(x in lower for x in HIGH_URGENCY_PHRASES):
            return "High", True
        if deadline_exists or any(x in lower for x in ("reminder", "follow up", "follow-up")):
            return "Medium", False
        return "Low", False

    @staticmethod
    def _confidence(signals: _SpacySignals) -> float:
        score = 0.0
        if signals.action_verb_found:
            score += 0.35
        if signals.object_phrase_found:
            score += 0.20
        if signals.deadline_found:
            score += 0.15
        if signals.deadline_normalized:
            score += 0.10
        if signals.urgency_found:
            score += 0.05
        if signals.fallback_used:
            score -= 0.15
        if signals.generic_fallback_used:
            score -= 0.20
        score = max(0.0, min(score, 1.0))
        return round(score, 3)

    def extract(self, email: EmailForExtraction) -> ExtractorOutput:
        text = self._light_clean(self._combine_text(email))
        if not text:
            return {
                "task_title": "Review email request",
                "deadline_text": None,
                "normalized_deadline": None,
                "priority": "Low",
                "extraction_confidence": 0.0,
                "needs_review": True,
                "extraction_method": "spacy",
            }

        doc = self.nlp(text)
        candidate_sentences = self._rank_sentences(doc)
        if not candidate_sentences:
            candidate_sentences = list(doc.sents)

        task_title, signals = self._extract_task_title(doc, candidate_sentences)

        deadline_text = self._extract_deadline_text(doc, candidate_sentences)
        signals.deadline_found = deadline_text is not None

        ref_dt = datetime.utcnow()
        if email.get("received_at"):
            try:
                ref_dt = datetime.fromisoformat(str(email["received_at"]))
            except ValueError:
                pass
        normalized_deadline = self._normalize_deadline(deadline_text, ref_dt)
        signals.deadline_normalized = normalized_deadline is not None

        priority, urgency = self._extract_priority(text, deadline_exists=signals.deadline_found)
        signals.urgency_found = urgency

        confidence = self._confidence(signals)
        needs_review = bool(
            confidence < 0.50
            or not task_title
            or signals.fallback_used
            or (signals.deadline_found and not signals.deadline_normalized)
        )

        return {
            "task_title": task_title,
            "deadline_text": deadline_text,
            "normalized_deadline": normalized_deadline,
            "priority": priority,
            "extraction_confidence": confidence,
            "needs_review": needs_review,
            "extraction_method": "spacy",
        }

