from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationAppError
from app.core.paths import ensure_repo_on_path
from app.models import PracticePairing, User
from app.schemas.gap import GapItemPublic
from app.schemas.recommendation import (
    ExplanationPublic,
    PracticePairListPublic,
    PracticePairPublic,
)
from app.schemas.resource import CoursePublic, ProjectPublic
from app.services.gap_service import gap_service
from app.services.profile_service import profile_service
from app.services.resource_service import resource_service

ensure_repo_on_path()

from recommendation.explain import explain_practice  # noqa: E402
from recommendation.hybrid.signals import difficulty_fit  # noqa: E402
from recommendation.projects.pairing import (  # noqa: E402
    ScoredResource,
    assign_pairs,
)
from recommendation.projects.signals import (  # noqa: E402
    duration_fit,
    gap_priority_score,
    proficiency_fit,
    role_fit,
    skills_addressed,
    technology_fit,
    weighted_score,
)

MAJOR_PRIORITIES = {"CRITICAL", "HIGH"}
FALLBACK_PRIORITIES = {"CRITICAL", "HIGH", "MEDIUM"}


class PracticeService:
    def pair(
        self,
        db: Session,
        user: User,
        *,
        role_id: UUID | None = None,
        job_description_id: UUID | None = None,
        limit: int | None = None,
    ) -> PracticePairListPublic:
        analysis = gap_service.analyze(
            db, user, role_id=role_id, job_description_id=job_description_id
        )
        gaps = _major_gaps(analysis.gaps, limit or settings.rec_pair_limit)
        if not gaps:
            raise ValidationAppError("No major skill gaps to pair a project against")
        employee = profile_service.get_employee_for_user(db, user)
        hours = employee.available_hours_per_week or 10
        role_ids = {item.skill.id for item in analysis.gaps}
        known_names = [row.skill.canonical_name for row in employee.skills]
        known_names.extend(item.skill.canonical_name for item in analysis.gaps)
        weights = settings.practice_weights()
        courses = resource_service.list_courses(db)
        projects = resource_service.list_projects(db)
        course_by_id = {row.id: row for row in courses}
        project_by_id = {row.id: row for row in projects}
        gap_by_id = {item.skill.id: item for item in gaps}
        project_scores: dict[UUID, list[ScoredResource]] = {}
        course_scores: dict[UUID, list[ScoredResource]] = {}
        for gap in gaps:
            scored_projects: list[ScoredResource] = []
            for project_item in projects:
                scored = _score_project(
                    project_item, gap, hours, known_names, role_ids, weights
                )
                if scored is not None:
                    scored_projects.append(scored)
            scored_courses: list[ScoredResource] = []
            for course_item in courses:
                scored = _score_course(course_item, gap, hours)
                if scored is not None:
                    scored_courses.append(scored)
            project_scores[gap.skill.id] = scored_projects
            course_scores[gap.skill.id] = scored_courses
        assigned = assign_pairs(
            [item.skill.id for item in gaps], project_scores, course_scores
        )
        if not assigned:
            raise ValidationAppError(
                "No catalog course and project both teach a major skill gap"
            )
        batch_id = uuid4()
        items: list[PracticePairPublic] = []
        for rank, (skill_id, course_row, project_row) in enumerate(assigned, start=1):
            gap = gap_by_id[skill_id]
            course = course_by_id[course_row.resource_id]
            project = project_by_id[project_row.resource_id]
            components = {
                "project": project_row.components,
                "course": course_row.components,
                "final": round(project_row.score, 4),
            }
            explanation = explain_practice(
                rank=rank,
                skill=gap.skill.canonical_name,
                priority=gap.priority,
                course_title=course.title,
                project_title=project.title,
                current_level=float(gap.current_level),
                required_level=float(gap.required_level),
            )
            explanation_payload = explanation.as_public()
            reason = explanation.verbalization
            db.add(
                PracticePairing(
                    batch_id=batch_id,
                    employee_id=employee.id,
                    skill_id=skill_id,
                    course_id=course.id,
                    project_id=project.id,
                    rank=rank,
                    score=Decimal(str(round(project_row.score, 4))),
                    components=components,
                    reason=reason,
                    explanation=explanation_payload,
                    target_type=analysis.target.type,
                    target_id=analysis.target.id,
                    target_title=analysis.target.title,
                )
            )
            items.append(
                PracticePairPublic(
                    rank=rank,
                    score=Decimal(str(round(project_row.score, 4))),
                    skill=gap.skill,
                    gap=gap.gap,
                    priority=gap.priority,
                    current_level=gap.current_level,
                    required_level=gap.required_level,
                    course=course,
                    project=project,
                    components=components,
                    reason=reason,
                    explanation=ExplanationPublic.model_validate(explanation_payload),
                )
            )
        db.commit()
        return PracticePairListPublic(
            batch_id=batch_id,
            target=analysis.target,
            weights=weights,
            items=items,
        )


def _major_gaps(gaps: list[GapItemPublic], limit: int) -> list[GapItemPublic]:
    major = [item for item in gaps if item.priority in MAJOR_PRIORITIES]
    if not major:
        major = [item for item in gaps if item.priority in FALLBACK_PRIORITIES]
    return major[: max(1, min(limit, 20))]


def _taught(row: CoursePublic | ProjectPublic, skill_id: UUID) -> float | None:
    for link in row.skills:
        if link.skill.id == skill_id:
            return float(link.level)
    return None


def _score_project(
    row: ProjectPublic,
    gap: GapItemPublic,
    hours: int,
    known_names: list[str],
    role_ids: set[UUID],
    weights: dict[str, float],
) -> ScoredResource | None:
    taught = _taught(row, gap.skill.id)
    if taught is None:
        return None
    current = float(gap.current_level)
    parts = {
        "skills_addressed": skills_addressed(taught),
        "gap_priority": gap_priority_score(gap.priority),
        "difficulty": difficulty_fit(row.difficulty, current if current else 2.5),
        "proficiency": proficiency_fit(taught, current),
        "duration": duration_fit(row.duration_hours, hours),
        "technologies": technology_fit(row.technologies, known_names),
        "role": role_fit({link.skill.id for link in row.skills}, role_ids),
    }
    score = weighted_score(parts, weights)
    return ScoredResource(
        resource_id=row.id,
        score=score,
        difficulty=row.difficulty,
        title=row.title,
        components={key: round(value, 4) for key, value in parts.items()}
        | {"final": round(score, 4)},
    )


def _score_course(
    row: CoursePublic, gap: GapItemPublic, hours: int
) -> ScoredResource | None:
    taught = _taught(row, gap.skill.id)
    if taught is None:
        return None
    current = float(gap.current_level) or 2.5
    parts = {
        "skills_addressed": skills_addressed(taught),
        "difficulty": difficulty_fit(row.difficulty, current),
        "duration": duration_fit(row.duration_hours, hours),
    }
    score = weighted_score(
        parts,
        {"skills_addressed": 2.0, "difficulty": 0.5, "duration": 0.5},
    )
    return ScoredResource(
        resource_id=row.id,
        score=score,
        difficulty=row.difficulty,
        title=row.title,
        components={key: round(value, 4) for key, value in parts.items()}
        | {"final": round(score, 4)},
    )


practice_service = PracticeService()
