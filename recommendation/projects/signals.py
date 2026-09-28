"""Independent project-ranking signals for course → project pairing.

Each function returns a score in [0, 1]. None of them call an LLM.
"""

from __future__ import annotations

from recommendation.hybrid.signals import difficulty_fit, weighted_score

PRIORITY_WEIGHT = {
    "CRITICAL": 1.0,
    "HIGH": 0.8,
    "MEDIUM": 0.5,
    "LOW": 0.25,
    "NONE": 0.0,
}


def skills_addressed(taught_level: float | None) -> float:
    if taught_level is None:
        return 0.0
    return max(0.0, min(1.0, float(taught_level) / 5.0))


def gap_priority_score(priority: str) -> float:
    return PRIORITY_WEIGHT.get(priority.upper(), 0.0)


def proficiency_fit(project_level: float, current_level: float) -> float:
    target = min(5.0, float(current_level) + 1.0)
    return max(0.0, min(1.0, 1.0 - abs(float(project_level) - target) / 4.0))


def duration_fit(duration_hours: int, hours_per_week: int) -> float:
    weekly = max(1, int(hours_per_week))
    weeks = float(duration_hours) / weekly
    if weeks <= 2:
        return 1.0
    if weeks <= 4:
        return 0.75
    if weeks <= 8:
        return 0.5
    return 0.25


def technology_fit(technologies: list[str], known_names: list[str]) -> float:
    if not technologies:
        return 0.5
    known = [name.lower() for name in known_names if name]
    if not known:
        return 0.5
    hits = 0
    for tech in technologies:
        token = tech.lower()
        if any(item in token or token in item for item in known):
            hits += 1
    return hits / len(technologies)


def role_fit(project_skill_ids: set, role_skill_ids: set) -> float:
    if not project_skill_ids:
        return 0.0
    return len(project_skill_ids.intersection(role_skill_ids)) / len(project_skill_ids)


def course_prep_fit(course_difficulty: float, project_difficulty: float) -> float:
    if float(course_difficulty) <= float(project_difficulty):
        return 1.0
    return 0.5


__all__ = [
    "PRIORITY_WEIGHT",
    "course_prep_fit",
    "difficulty_fit",
    "duration_fit",
    "gap_priority_score",
    "proficiency_fit",
    "role_fit",
    "skills_addressed",
    "technology_fit",
    "weighted_score",
]
