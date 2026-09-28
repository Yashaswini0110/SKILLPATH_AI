"""Independent mentor-matching signals.

Each function returns a score in [0, 1]. None of them call an LLM.
Workload has no assignment log yet; open slots equal max_mentees.
"""

from __future__ import annotations

from uuid import UUID

from recommendation.hybrid.signals import preference_fit, weighted_score


def skill_overlap(matched: int, top_count: int) -> float:
    if top_count <= 0:
        return 0.0
    return max(0.0, min(1.0, matched / top_count))


def domain_overlap(mentor_domains: list[str], learner_domains: list[str]) -> float:
    if not mentor_domains:
        return 0.5
    wanted = {item.lower() for item in learner_domains if item}
    if not wanted:
        return 0.5
    hits = sum(1 for item in mentor_domains if item.lower() in wanted)
    return hits / len(mentor_domains)


def experience_score(years: int) -> float:
    return max(0.0, min(1.0, float(years) / 15.0))


def availability_score(hours_per_month: int) -> float:
    return max(0.0, min(1.0, float(hours_per_month) / 12.0))


def learning_goals_score(
    mentor_skill_ids: set[UUID],
    role_skill_ids: set[UUID],
    formats: list[str],
) -> float:
    if not role_skill_ids:
        coverage = 0.5
    else:
        coverage = len(mentor_skill_ids.intersection(role_skill_ids)) / len(
            role_skill_ids
        )
    fmt = preference_fit("MENTOR", None, formats)
    return 0.7 * coverage + 0.3 * fmt


def workload_score(open_slots: int, max_mentees: int) -> float:
    if max_mentees <= 0:
        return 0.0
    return max(0.0, min(1.0, open_slots / max_mentees))


def mentor_reason(
    matched_names: list[str],
    top_count: int,
    hours: int,
    open_slots: int,
) -> str:
    count = len(matched_names)
    skills = ", ".join(matched_names[:5])
    overlap = (
        f"{count} of your top {top_count} skill gaps match this mentor's expertise"
    )
    if skills:
        overlap += f" ({skills})"
    return (
        f"{overlap}. {hours} available hours/month and "
        f"{open_slots} open mentee slots."
    )


__all__ = [
    "availability_score",
    "domain_overlap",
    "experience_score",
    "learning_goals_score",
    "mentor_reason",
    "skill_overlap",
    "weighted_score",
    "workload_score",
]
