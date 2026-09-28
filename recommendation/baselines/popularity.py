"""Popularity baseline.

No interaction log exists yet. Score is a catalog proxy in [0, 1]:
courses use rating/5, projects use mapped-skill coverage, mentors use
years of experience capped at 15.
"""

from __future__ import annotations


def popularity_score(
    *, rating: float | None, skill_count: int, years: int | None
) -> float:
    if rating is not None:
        return max(0.0, min(1.0, rating / 5.0))
    if years is not None:
        return max(0.0, min(1.0, years / 15.0))
    return max(0.0, min(1.0, skill_count / 6.0))
