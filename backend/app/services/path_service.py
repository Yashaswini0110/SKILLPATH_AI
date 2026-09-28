from __future__ import annotations

import json
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationAppError
from app.core.paths import ensure_repo_on_path, repo_root
from app.models import LearningPath, LearningPathStep, User
from app.schemas.gap import GapItemPublic
from app.schemas.learning_path import (
    LearningPathPublic,
    LearningPathStepPublic,
    PathAdaptationPublic,
    PathGapSkillPublic,
    PathMethodScorePublic,
)
from app.schemas.recommendation import ExplanationPublic
from app.schemas.resource import CoursePublic, ProjectPublic
from app.schemas.skill import SkillPublic
from app.services.assessment_service import assessment_service
from app.services.catalog_service import catalog_service
from app.services.gap_service import gap_service
from app.services.profile_service import profile_service
from app.services.resource_service import resource_service
from app.services.skill_profile_service import skill_profile_service

ensure_repo_on_path()

from knowledge_graph.cycle import ancestor_set  # noqa: E402
from optimization.compare import compare_methods, select_names  # noqa: E402
from optimization.metrics import MethodScore  # noqa: E402
from optimization.schedule import pack_weeks  # noqa: E402
from recommendation.explain import explain_path_step  # noqa: E402
from recommendation.path.adapt import AdaptedPath, adapt_path  # noqa: E402
from recommendation.path.build import PathPlan, plan_path  # noqa: E402
from recommendation.path.resources import ResourceCandidate, pick_resource  # noqa: E402
from recommendation.path.stages import assign_stages  # noqa: E402

PathMethod = Literal["ORTOOLS", "GREEDY", "TOPOLOGICAL"]


class PathService:
    def build(
        self,
        db: Session,
        user: User,
        *,
        role_id: UUID | None = None,
        job_description_id: UUID | None = None,
        method: PathMethod = "ORTOOLS",
        deadline_weeks: int | None = None,
    ) -> LearningPathPublic:
        analysis = gap_service.analyze(
            db, user, role_id=role_id, job_description_id=job_description_id
        )
        top_gaps = [item for item in analysis.gaps if item.priority != "NONE"][
            : settings.rec_top_gap_count
        ]
        if not top_gaps:
            raise ValidationAppError("No open skill gaps to build a learning path from")
        edges = _prerequisite_edges()
        skills = {item.name: item for item in catalog_service.list_skills(db)}
        profile = {
            item.skill.name: float(item.current_level)
            for item in skill_profile_service.get_profile(db, user).skills
        }
        gap_by_name = {item.skill.name: item for item in analysis.gaps}
        targets = [item.skill.name for item in top_gaps]
        missing: set[str] = set()
        for name in ancestor_set(edges, targets):
            if name not in skills:
                continue
            if name in gap_by_name:
                if gap_by_name[name].priority != "NONE":
                    missing.add(name)
            elif profile.get(name, 0.0) < settings.rec_path_foundation_level:
                missing.add(name)
        plan = plan_path(targets, edges=edges, missing=missing, gap_names=set(targets))
        if not plan.ordered:
            raise ValidationAppError(
                "No missing skills remain after expanding prerequisites"
            )
        employee = profile_service.get_employee_for_user(db, user)
        hours_per_week = employee.available_hours_per_week or 10
        deadline = deadline_weeks or settings.rec_path_deadline_weeks
        courses = resource_service.list_courses(db)
        projects = resource_service.list_projects(db)
        mapped = _map_all(plan.ordered, skills, courses, projects, plan, gap_by_name)
        percents = assessment_service.latest_percent_by_skill_name(db, employee.id)
        durations = {name: int(item["duration_hours"]) for name, item in mapped.items()}
        adapted = adapt_path(
            plan.ordered,
            percents,
            gap_names=set(targets),
            durations=durations,
            weak=settings.assessment_weak_score,
            strong=settings.assessment_strong_score,
        )
        _apply_refreshers(mapped, adapted)
        if not adapted.ordered:
            raise ValidationAppError("No missing skills remain after quiz adaptations")
        durations = {
            name: int(mapped[name]["duration_hours"]) for name in adapted.ordered
        }
        scores = compare_methods(
            adapted.ordered,
            durations=durations,
            edges=edges,
            gap_names=adapted.gap_names,
            hours_per_week=hours_per_week,
            deadline_weeks=deadline,
        )
        chosen = select_names(method, scores)
        chosen_rows = [mapped[name] for name in chosen if name in mapped]
        stages = assign_stages(
            [row["skill"].name for row in chosen_rows],
            {row["skill"].name: list(row["blocked_by"]) for row in chosen_rows},
            {row["skill"].name: str(row["kind"]) for row in chosen_rows},
        )
        progress = assessment_service.progress_by_skill(db, employee.id)
        quiz_ids = assessment_service.ids_by_skill(db)
        spans = pack_weeks(
            [int(row["duration_hours"]) for row in chosen_rows], hours_per_week
        )
        chosen_score = scores[method if method in scores else "ORTOOLS"]
        duplicates = _duplicate_resource_count(chosen_rows)
        comparison = [
            PathMethodScorePublic(**scores[key].as_public())
            for key in ("ORTOOLS", "GREEDY", "TOPOLOGICAL")
        ]
        skipped_foundations = list(dict.fromkeys([*plan.skipped, *adapted.skipped]))
        adaptations_payload = [item.as_public() for item in adapted.adaptations]
        path = LearningPath(
            employee_id=employee.id,
            method=chosen_score.method,
            prerequisite_violation_count=chosen_score.prerequisite_violation_count,
            hours_violation_count=chosen_score.hours_violation_count,
            duplicate_resource_count=duplicates,
            hours_per_week=hours_per_week,
            deadline_weeks=deadline,
            total_hours=chosen_score.total_hours,
            estimated_weeks=chosen_score.estimated_weeks,
            skill_coverage=chosen_score.skill_coverage,
            path_efficiency=chosen_score.path_efficiency,
            comparison=[item.model_dump() for item in comparison],
            target_type=analysis.target.type,
            target_id=analysis.target.id,
            target_title=analysis.target.title,
            skipped_foundations=skipped_foundations,
            adaptations=adaptations_payload,
            reason=_reason(chosen_score, hours_per_week, deadline, duplicates),
        )
        db.add(path)
        db.flush()
        public_steps: list[LearningPathStepPublic] = []
        for position, (row, span) in enumerate(
            zip(chosen_rows, spans, strict=True), start=1
        ):
            why = dict(row["why"])
            why["duration_hours"] = row["duration_hours"]
            why["week_start"] = span.week_start
            why["week_end"] = span.week_end
            course = row["course"]
            project = row["project"]
            skill = row["skill"]
            stage = stages.get(skill.name, "CORE")
            difficulty = _step_difficulty(course, project, skill)
            status = progress.get(skill.id, "NOT_STARTED")
            quiz_id = quiz_ids.get(skill.id)
            why["stage"] = stage
            why["status"] = status
            why["difficulty"] = difficulty
            if quiz_id is not None:
                why["assessment_id"] = str(quiz_id)
            extra = why.get("extra_hours")
            quiz_percent = why.get("quiz_percent")
            priority = why.get("priority")
            explanation = explain_path_step(
                skill=skill.canonical_name,
                kind=str(row["kind"]),
                blocked_by=list(row["blocked_by"]),
                duration_hours=int(row["duration_hours"]),
                week_start=span.week_start,
                week_end=span.week_end,
                open_gap=bool(why.get("open_gap")),
                position=position,
                course_title=None if course is None else course.title,
                project_title=None if project is None else project.title,
                extra_hours=None if extra is None else int(extra),
                quiz_percent=(None if quiz_percent is None else float(quiz_percent)),
                priority=None if priority is None else str(priority),
            )
            explanation_payload = explanation.as_public()
            why["explanation"] = explanation_payload
            db.add(
                LearningPathStep(
                    path_id=path.id,
                    position=position,
                    skill_id=skill.id,
                    course_id=None if course is None else course.id,
                    project_id=None if project is None else project.id,
                    kind=row["kind"],
                    reason=row["reason"],
                    duration_hours=row["duration_hours"],
                    week_start=span.week_start,
                    week_end=span.week_end,
                    blocked_by=row["blocked_by"],
                    why=why,
                    explanation=explanation_payload,
                )
            )
            public_steps.append(
                LearningPathStepPublic(
                    position=position,
                    skill=skill,
                    kind=row["kind"],
                    stage=stage,
                    status=status,
                    difficulty=difficulty,
                    reason=row["reason"],
                    blocked_by=row["blocked_by"],
                    course=course,
                    project=project,
                    duration_hours=row["duration_hours"],
                    week_start=span.week_start,
                    week_end=span.week_end,
                    assessment_id=quiz_id,
                    why=why,
                    explanation=ExplanationPublic.model_validate(explanation_payload),
                )
            )
        db.commit()
        return LearningPathPublic(
            id=path.id,
            method=path.method,
            prerequisite_violation_count=path.prerequisite_violation_count,
            hours_violation_count=path.hours_violation_count,
            duplicate_resource_count=path.duplicate_resource_count,
            hours_per_week=path.hours_per_week,
            deadline_weeks=path.deadline_weeks,
            capacity_hours=hours_per_week * deadline,
            total_hours=path.total_hours,
            estimated_weeks=path.estimated_weeks,
            skill_coverage=path.skill_coverage,
            path_efficiency=path.path_efficiency,
            target=analysis.target,
            gap_skills=[
                PathGapSkillPublic(
                    skill=item.skill, gap=item.gap, priority=item.priority
                )
                for item in top_gaps
            ],
            skipped_foundations=skipped_foundations,
            adaptations=[
                PathAdaptationPublic.model_validate(item)
                for item in adaptations_payload
            ],
            comparison=comparison,
            reason=path.reason,
            steps=public_steps,
            edges=[list(pair) for pair in plan.edges],
        )


def _apply_refreshers(mapped: dict[str, dict], adapted: AdaptedPath) -> None:
    notes = {item.skill: item for item in adapted.adaptations}
    for name, extra in adapted.extras.items():
        row = mapped[name]
        row["duration_hours"] = int(row["duration_hours"]) + extra
        row["kind"] = "REFRESHER"
        note = notes[name]
        row["reason"] = note.reason
        why = dict(row["why"])
        why["kind"] = "REFRESHER"
        why["extra_hours"] = extra
        why["quiz_percent"] = note.percent
        row["why"] = why


def _reason(
    score: MethodScore, hours_per_week: int, deadline: int, duplicates: int
) -> str:
    return (
        f"{score.method} path of {len(score.selected)} skills in "
        f"{score.total_hours}h over {score.estimated_weeks} week(s) "
        f"({hours_per_week}h/week, {deadline}-week deadline). "
        f"prerequisite_violation_count = {score.prerequisite_violation_count}, "
        f"hours_violation_count = {score.hours_violation_count}, "
        f"duplicate_resource_count = {duplicates}."
    )


def _map_all(
    ordered: list[str],
    skills: dict[str, SkillPublic],
    courses: list[CoursePublic],
    projects: list[ProjectPublic],
    plan: PathPlan,
    gap_by_name: dict[str, GapItemPublic],
) -> dict[str, dict]:
    used_courses: set[UUID] = set()
    used_projects: set[UUID] = set()
    mapped: dict[str, dict] = {}
    for name in ordered:
        skill = skills[name]
        course = _map_course(skill.id, courses, used_courses)
        project = _map_project(skill.id, projects, used_projects)
        if course is not None:
            used_courses.add(course.id)
        if project is not None:
            used_projects.add(project.id)
        duration = (0 if course is None else course.duration_hours) + (
            0 if project is None else project.duration_hours
        )
        mapped[name] = {
            "skill": skill,
            "kind": plan.kinds[name],
            "reason": plan.reasons[name],
            "blocked_by": plan.blocked_by[name],
            "course": course,
            "project": project,
            "duration_hours": duration,
            "why": {
                "kind": plan.kinds[name],
                "blocked_by": plan.blocked_by[name],
                "open_gap": name in gap_by_name
                and gap_by_name[name].priority != "NONE",
                "priority": (
                    None if name not in gap_by_name else gap_by_name[name].priority
                ),
            },
        }
    return mapped


def _duplicate_resource_count(rows: list[dict]) -> int:
    courses = [row["course"].id for row in rows if row["course"] is not None]
    projects = [row["project"].id for row in rows if row["project"] is not None]
    return (len(courses) - len(set(courses))) + (len(projects) - len(set(projects)))


def _prerequisite_edges() -> list[tuple[str, str]]:
    path = repo_root() / "datasets" / "processed" / "skill_prerequisites.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [(str(src), str(dst)) for src, dst in payload.get("prerequisites", [])]


def _map_course(
    skill_id: UUID, courses: list[CoursePublic], used: set[UUID]
) -> CoursePublic | None:
    picked = pick_resource(_course_candidates(skill_id, courses), used)
    if picked is None:
        return None
    return next(item for item in courses if item.id == picked.resource_id)


def _map_project(
    skill_id: UUID, projects: list[ProjectPublic], used: set[UUID]
) -> ProjectPublic | None:
    picked = pick_resource(_project_candidates(skill_id, projects), used)
    if picked is None:
        return None
    return next(item for item in projects if item.id == picked.resource_id)


def _course_candidates(
    skill_id: UUID, courses: list[CoursePublic]
) -> list[ResourceCandidate]:
    found: list[ResourceCandidate] = []
    for row in courses:
        taught = _taught(row, skill_id)
        if taught is None:
            continue
        found.append(
            ResourceCandidate(
                resource_id=row.id,
                title=row.title,
                taught_level=taught,
                duration_hours=row.duration_hours,
                difficulty=row.difficulty,
            )
        )
    return found


def _project_candidates(
    skill_id: UUID, projects: list[ProjectPublic]
) -> list[ResourceCandidate]:
    found: list[ResourceCandidate] = []
    for row in projects:
        taught = _taught(row, skill_id)
        if taught is None:
            continue
        found.append(
            ResourceCandidate(
                resource_id=row.id,
                title=row.title,
                taught_level=taught,
                duration_hours=row.duration_hours,
                difficulty=row.difficulty,
            )
        )
    return found


def _taught(row: CoursePublic | ProjectPublic, skill_id: UUID) -> float | None:
    for link in row.skills:
        if link.skill.id == skill_id:
            return float(link.level)
    return None


def _step_difficulty(
    course: CoursePublic | None,
    project: ProjectPublic | None,
    skill: SkillPublic,
) -> int:
    if course is not None:
        return int(course.difficulty)
    if project is not None:
        return int(project.difficulty)
    return int(skill.difficulty)


path_service = PathService()
