"""Greedy unique assignment of one course and one project per major gap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from recommendation.projects.signals import course_prep_fit


@dataclass(frozen=True)
class ScoredResource:
    resource_id: UUID
    score: float
    difficulty: int
    title: str
    components: dict[str, Any]


def assign_pairs(
    gaps: list[UUID],
    projects: dict[UUID, list[ScoredResource]],
    courses: dict[UUID, list[ScoredResource]],
) -> list[tuple[UUID, ScoredResource, ScoredResource]]:
    used_projects: set[UUID] = set()
    used_courses: set[UUID] = set()
    chosen: dict[UUID, tuple[ScoredResource, ScoredResource]] = {}
    ordered = sorted(
        enumerate(gaps),
        key=lambda item: (len(projects.get(item[1], [])), item[0]),
    )
    for _, gap_id in ordered:
        project = _first_unused(
            sorted(projects.get(gap_id, []), key=lambda row: (-row.score, row.title)),
            used_projects,
        )
        if project is None:
            continue
        ranked_courses = sorted(
            (
                _with_prep(row, project.difficulty)
                for row in courses.get(gap_id, [])
                if row.resource_id not in used_courses
            ),
            key=lambda row: (-row.score, row.title),
        )
        if not ranked_courses:
            continue
        course = ranked_courses[0]
        used_projects.add(project.resource_id)
        used_courses.add(course.resource_id)
        chosen[gap_id] = (course, project)
    return [
        (gap_id, chosen[gap_id][0], chosen[gap_id][1])
        for gap_id in gaps
        if gap_id in chosen
    ]


def _with_prep(row: ScoredResource, project_difficulty: int) -> ScoredResource:
    prep = course_prep_fit(row.difficulty, project_difficulty)
    combined = 0.7 * row.score + 0.3 * prep
    components = dict(row.components)
    components["prep"] = round(prep, 4)
    components["final"] = round(combined, 4)
    return ScoredResource(
        resource_id=row.resource_id,
        score=combined,
        difficulty=row.difficulty,
        title=row.title,
        components=components,
    )


def _first_unused(rows: list[ScoredResource], used: set[UUID]) -> ScoredResource | None:
    for row in rows:
        if row.resource_id not in used:
            return row
    return None
