"""Estimate a 1–5 proficiency from local resume context. This is not ground truth."""

from __future__ import annotations

import re

EXPERT_TERMS = (
    "expert",
    "senior",
    "lead",
    "principal",
    "architect",
    "advanced",
)
BEGINNER_TERMS = (
    "familiar",
    "beginner",
    "basic",
    "exposure",
    "introductory",
    "novice",
)
YEAR_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs)\b", re.I)

SECTION_DEFAULT = {
    "skills": 3.0,
    "experience": 3.5,
    "projects": 3.0,
    "education": 2.5,
    "certifications": 3.0,
    "summary": 3.0,
    "other": 2.5,
}


def estimate_proficiency(snippet: str, section: str, mention_count: int) -> float:
    text = snippet.lower()
    level = SECTION_DEFAULT.get(section, 2.5)
    if any(term in text for term in EXPERT_TERMS):
        level = max(level, 4.5)
    if any(term in text for term in BEGINNER_TERMS):
        level = min(level, 2.0)
    years = _years(text)
    if years is not None:
        if years >= 7:
            level = max(level, 5.0)
        elif years >= 4:
            level = max(level, 4.0)
        elif years >= 2:
            level = max(level, 3.0)
        elif years >= 1:
            level = max(level, 2.5)
    if mention_count >= 3:
        level = min(5.0, level + 0.5)
    return round(min(5.0, max(1.0, level)), 1)


def _years(text: str) -> float | None:
    match = YEAR_PATTERN.search(text)
    if not match:
        return None
    return float(match.group(1))
