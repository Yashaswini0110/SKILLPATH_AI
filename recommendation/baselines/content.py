"""Content-based baseline: cosine of gap vector vs resource skill vector."""

from __future__ import annotations

from uuid import UUID

from recommendation.baselines.vectors import cosine_similarity


def gap_vector(
    skill_ids: list[UUID],
    gaps: dict[UUID, float],
) -> list[float]:
    return [max(0.0, float(gaps.get(skill_id, 0.0))) for skill_id in skill_ids]


def resource_vector(
    skill_ids: list[UUID],
    levels: dict[UUID, float],
) -> list[float]:
    return [
        max(0.0, min(1.0, float(levels.get(skill_id, 0.0)) / 5.0))
        for skill_id in skill_ids
    ]


def content_score(
    skill_ids: list[UUID],
    gaps: dict[UUID, float],
    levels: dict[UUID, float],
) -> float:
    return cosine_similarity(
        gap_vector(skill_ids, gaps), resource_vector(skill_ids, levels)
    )
