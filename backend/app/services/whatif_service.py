"""Compare catalog roles against the current skill profile.

This is not a hiring or employment predictor. It only reports stored
coverage, missing skills, estimated learning effort, mapped projects,
and mentor overlap. It does not change the saved target role or path.
GitHub evidence is not required.
"""

from __future__ import annotations

import math
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationAppError
from app.core.paths import ensure_repo_on_path
from app.models import User
from app.schemas.gap import GapItemPublic, GapTargetPublic
from app.schemas.role import TargetRoleSummary
from app.schemas.whatif import (
    WhatIfMissingSkillPublic,
    WhatIfScenarioPublic,
    WhatIfSimulationPublic,
)
from app.services.catalog_service import catalog_service
from app.services.gap_service import gap_service
from app.services.mentor_service import _teaches
from app.services.path_service import _map_all, _prerequisite_edges
from app.services.profile_service import profile_service
from app.services.resource_service import resource_service
from app.services.skill_profile_service import skill_profile_service

ensure_repo_on_path()

from knowledge_graph.cycle import ancestor_set  # noqa: E402
from recommendation.path.build import plan_path  # noqa: E402

DISCLAIMER = (
    "This compares skill coverage and estimated learning effort for catalog "
    "roles. It is not a hiring or employment prediction."
)


class WhatIfService:
    def compare(
        self, db: Session, user: User, role_ids: list[UUID]
    ) -> WhatIfSimulationPublic:
        unique: list[UUID] = []
        for role_id in role_ids:
            if role_id not in unique:
                unique.append(role_id)
        if not unique:
            raise ValidationAppError("Select at least one catalog role to compare")
        if len(unique) > 4:
            raise ValidationAppError("Compare at most four catalog roles")
        employee = profile_service.get_employee_for_user(db, user)
        hours = employee.available_hours_per_week or 10
        current = None
        if employee.target_role is not None:
            current = employee.target_role
        scenarios = [
            _scenario(db, user, role_id, hours, current.id if current else None)
            for role_id in unique
        ]
        current_target = None
        if current is not None:
            current_target = GapTargetPublic(
                type="ROLE", id=current.id, title=current.title
            )
        return WhatIfSimulationPublic(
            current_target=current_target,
            hours_per_week=hours,
            disclaimer=DISCLAIMER,
            scenarios=scenarios,
        )


whatif_service = WhatIfService()


def _scenario(
    db: Session,
    user: User,
    role_id: UUID,
    hours_per_week: int,
    current_id: UUID | None,
) -> WhatIfScenarioPublic:
    role = catalog_service.get_role(db, role_id)
    analysis = gap_service.analyze(db, user, role_id=role_id)
    skills = analysis.gaps
    covered = [item for item in skills if item.priority == "NONE"]
    missing = [item for item in skills if item.priority != "NONE"]
    coverage = 0.0 if not skills else round(len(covered) / len(skills), 4)
    path_skills, hours, projects = _effort(db, user, missing, hours_per_week)
    weeks = 0 if hours == 0 else max(1, math.ceil(hours / hours_per_week))
    mentor_names = _mentor_names(db, missing)
    return WhatIfScenarioPublic(
        role=TargetRoleSummary.model_validate(role),
        is_current=current_id is not None and current_id == role.id,
        skill_count=len(skills),
        covered_count=len(covered),
        coverage=coverage,
        open_gap_count=len(missing),
        missing_skills=[
            WhatIfMissingSkillPublic(
                skill=item.skill.canonical_name,
                priority=item.priority,
                current_level=float(item.current_level),
                required_level=float(item.required_level),
            )
            for item in missing[:8]
        ],
        estimated_hours=hours,
        estimated_weeks=weeks,
        path_skills=path_skills,
        required_projects=projects,
        mentor_count=len(mentor_names),
        mentor_names=mentor_names[:3],
    )


def _effort(
    db: Session,
    user: User,
    missing: list[GapItemPublic],
    hours_per_week: int,
) -> tuple[list[str], int, list[str]]:
    del hours_per_week
    if not missing:
        return [], 0, []
    edges = _prerequisite_edges()
    skills = {item.name: item for item in catalog_service.list_skills(db)}
    profile = {
        item.skill.name: float(item.current_level)
        for item in skill_profile_service.get_profile(db, user).skills
    }
    gap_by_name = {item.skill.name: item for item in missing}
    targets = [item.skill.name for item in missing[: settings.rec_top_gap_count]]
    found: set[str] = set()
    for name in ancestor_set(edges, targets):
        if name not in skills:
            continue
        if name in gap_by_name:
            found.add(name)
        elif profile.get(name, 0.0) < settings.rec_path_foundation_level:
            found.add(name)
    plan = plan_path(targets, edges=edges, missing=found, gap_names=set(targets))
    if not plan.ordered:
        return [], 0, []
    mapped = _map_all(
        plan.ordered,
        skills,
        resource_service.list_courses(db),
        resource_service.list_projects(db),
        plan,
        gap_by_name,
    )
    names = list(plan.ordered[:8])
    hours = 0
    projects: list[str] = []
    for name in names:
        row = mapped.get(name)
        if row is None:
            continue
        hours += int(row["duration_hours"])
        project = row["project"]
        if project is not None and project.title not in projects:
            projects.append(project.title)
    return names, hours, projects[:6]


def _mentor_names(db: Session, missing: list[GapItemPublic]) -> list[str]:
    top = missing[: settings.rec_top_gap_count]
    if not top:
        return []
    names: list[str] = []
    for mentor in resource_service.list_mentors(db):
        if any(_teaches(mentor, item.skill.id) for item in top):
            names.append(mentor.name)
    return names
