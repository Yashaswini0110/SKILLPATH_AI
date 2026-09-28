"""Privacy-safe team and org aggregates.

Department is the team scope. The snapshot never includes names, emails,
user IDs, resume text, or raw evidence. GitHub is not collected.
"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.enums import SkillSourceType, UserRole
from app.core.exceptions import ForbiddenError, ValidationAppError
from app.core.paths import ensure_repo_on_path
from app.models import (
    AssessmentAttempt,
    CourseSkill,
    Employee,
    EmployeeSkill,
    Evidence,
    LearningPath,
    ProjectSkill,
    RoleSkill,
    Skill,
    TargetRole,
    User,
)
from app.schemas.analytics import (
    AnalyticsScopePublic,
    AnalyticsSkillPublic,
    AnalyticsSnapshotPublic,
    DepartmentSlicePublic,
    FrameworkAdoptionPublic,
    GapAggregatePublic,
    HeatmapRowPublic,
    LearningProgressPublic,
    TrainingPriorityPublic,
)
from app.services.profile_service import profile_service

ensure_repo_on_path()

from ml.evidence.aggregation import EvidenceItem, aggregate_skill  # noqa: E402

DISCLAIMER = (
    "Aggregates only. Individual names, emails, and evidence text are not "
    "included. GitHub is not collected. This is not a hiring or employment "
    "prediction."
)

ANALYTICS_ROLES = {
    UserRole.MANAGER.value,
    UserRole.HR_ADMIN.value,
    UserRole.SYSTEM_ADMIN.value,
}
HR_ROLES = {UserRole.HR_ADMIN.value, UserRole.SYSTEM_ADMIN.value}
HEATMAP_LIMIT = 12
GAP_LIMIT = 8


class AnalyticsService:
    def snapshot(
        self,
        db: Session,
        user: User,
        department: str | None = None,
    ) -> AnalyticsSnapshotPublic:
        if user.role not in ANALYTICS_ROLES:
            raise ForbiddenError("Manager or HR role required")
        viewer = profile_service.get_employee_for_user(db, user)
        requested = (department or "").strip()
        if user.role == UserRole.MANAGER.value:
            label = (viewer.department or "").strip()
            if not label:
                raise ValidationAppError(
                    "Set a department on your profile to see team aggregates"
                )
            if requested and requested.casefold() != label.casefold():
                raise ForbiddenError("Managers can only view their own department")
            employees = _employees_in_department(db, label)
            scope = AnalyticsScopePublic(type="DEPARTMENT", label=label)
        elif requested:
            employees = _employees_in_department(db, requested)
            scope = AnalyticsScopePublic(type="DEPARTMENT", label=requested)
        else:
            employees = _all_employees(db)
            scope = AnalyticsScopePublic(type="ORG", label="Organization")

        ids = [row.id for row in employees]
        skills = {item.id: item for item in db.scalars(select(Skill)).all()}
        levels = _levels_by_employee(db, ids)
        requirements = _role_requirements(db)
        heatmap = _heatmap(employees, levels, requirements, skills)
        gaps = _gaps(employees, levels, requirements, skills)
        courses, projects = _resource_counts(db)
        priorities = [
            TrainingPriorityPublic(
                skill=item.skill,
                rank=index,
                employees_with_gap=item.employees_with_gap,
                avg_gap=item.avg_gap,
                course_count=courses.get(item.skill.id, 0),
                project_count=projects.get(item.skill.id, 0),
            )
            for index, item in enumerate(gaps[:GAP_LIMIT], start=1)
        ]
        departments: list[DepartmentSlicePublic] = []
        if user.role in HR_ROLES and scope.type == "ORG":
            departments = _department_slices(employees)
        return AnalyticsSnapshotPublic(
            scope=scope,
            disclaimer=DISCLAIMER,
            employee_count=len(employees),
            with_target_role_count=sum(
                1 for row in employees if row.target_role_id is not None
            ),
            avg_completeness=_avg_completeness(employees),
            heatmap=heatmap,
            top_gaps=gaps[:GAP_LIMIT],
            training_priorities=priorities,
            learning_progress=_progress(db, ids),
            frameworks=_frameworks(db, employees),
            departments=departments,
            github_collected=False,
        )


analytics_service = AnalyticsService()


def _all_employees(db: Session) -> list[Employee]:
    return list(
        db.scalars(
            select(Employee).options(
                joinedload(Employee.education),
                joinedload(Employee.experience),
                joinedload(Employee.skills),
            )
        )
        .unique()
        .all()
    )


def _employees_in_department(db: Session, department: str) -> list[Employee]:
    return [
        row
        for row in _all_employees(db)
        if (row.department or "").strip().casefold() == department.casefold()
    ]


def _levels_by_employee(
    db: Session, employee_ids: list[UUID]
) -> dict[UUID, dict[UUID, float]]:
    if not employee_ids:
        return {}
    evidence_rows = db.scalars(
        select(Evidence).where(Evidence.employee_id.in_(employee_ids))
    ).all()
    declared = db.scalars(
        select(EmployeeSkill).where(EmployeeSkill.employee_id.in_(employee_ids))
    ).all()
    grouped: dict[UUID, dict[UUID, list[EvidenceItem]]] = defaultdict(
        lambda: defaultdict(list)
    )
    self_present: dict[UUID, set[UUID]] = defaultdict(set)
    for row in evidence_rows:
        grouped[row.employee_id][row.skill_id].append(
            EvidenceItem(
                source_type=row.source_type,
                extracted_level=float(row.extracted_level),
                reliability=float(row.reliability),
                strength=float(row.strength),
                recency=float(row.recency),
                inferred=row.inferred,
            )
        )
        if row.source_type == SkillSourceType.SELF.value:
            self_present[row.employee_id].add(row.skill_id)
    for row in declared:
        if row.skill_id in self_present[row.employee_id]:
            continue
        grouped[row.employee_id][row.skill_id].append(
            EvidenceItem(
                source_type=SkillSourceType.SELF.value,
                extracted_level=float(row.current_level),
                reliability=settings.self_declaration_reliability,
                strength=1.0,
                recency=1.0,
                inferred=False,
            )
        )
    levels: dict[UUID, dict[UUID, float]] = {}
    for employee_id, by_skill in grouped.items():
        levels[employee_id] = {
            skill_id: aggregate_skill(
                items, conflict_variance=settings.evidence_conflict_variance
            ).current_level
            for skill_id, items in by_skill.items()
        }
    return levels


def _role_requirements(db: Session) -> dict[UUID, list[RoleSkill]]:
    rows = db.scalars(select(RoleSkill)).all()
    grouped: dict[UUID, list[RoleSkill]] = defaultdict(list)
    for row in rows:
        grouped[row.role_id].append(row)
    return grouped


def _skill_public(skill: Skill) -> AnalyticsSkillPublic:
    return AnalyticsSkillPublic(
        id=skill.id,
        canonical_name=skill.canonical_name,
        category=skill.category,
    )


def _band(level: float) -> int:
    return max(1, min(5, int(level)))


def _heatmap(
    employees: list[Employee],
    levels: dict[UUID, dict[UUID, float]],
    requirements: dict[UUID, list[RoleSkill]],
    skills: dict[UUID, Skill],
) -> list[HeatmapRowPublic]:
    skill_ids: set[UUID] = set()
    for employee in employees:
        skill_ids.update(levels.get(employee.id, {}))
        if employee.target_role_id:
            skill_ids.update(
                item.skill_id for item in requirements.get(employee.target_role_id, [])
            )
    rows: list[HeatmapRowPublic] = []
    for skill_id in skill_ids:
        skill = skills.get(skill_id)
        if skill is None:
            continue
        bands = [0, 0, 0, 0, 0]
        missing = 0
        for employee in employees:
            level = levels.get(employee.id, {}).get(skill_id)
            if level is None:
                missing += 1
            else:
                bands[_band(level) - 1] += 1
        rows.append(
            HeatmapRowPublic(
                skill=_skill_public(skill),
                band_1=bands[0],
                band_2=bands[1],
                band_3=bands[2],
                band_4=bands[3],
                band_5=bands[4],
                missing_count=missing,
            )
        )
    rows.sort(
        key=lambda item: (
            -item.missing_count,
            item.skill.canonical_name.lower(),
        )
    )
    return rows[:HEATMAP_LIMIT]


def _gaps(
    employees: list[Employee],
    levels: dict[UUID, dict[UUID, float]],
    requirements: dict[UUID, list[RoleSkill]],
    skills: dict[UUID, Skill],
) -> list[GapAggregatePublic]:
    totals: dict[UUID, list[float]] = defaultdict(list)
    critical: dict[UUID, int] = defaultdict(int)
    high: dict[UUID, int] = defaultdict(int)
    for employee in employees:
        if employee.target_role_id is None:
            continue
        current = levels.get(employee.id, {})
        for item in requirements.get(employee.target_role_id, []):
            gap = max(0.0, float(item.required_level) - current.get(item.skill_id, 0.0))
            if gap <= 0:
                continue
            totals[item.skill_id].append(gap)
            if gap >= 2.0:
                critical[item.skill_id] += 1
            elif gap >= 1.0:
                high[item.skill_id] += 1
    rows: list[GapAggregatePublic] = []
    for skill_id, values in totals.items():
        skill = skills.get(skill_id)
        if skill is None:
            continue
        rows.append(
            GapAggregatePublic(
                skill=_skill_public(skill),
                employees_with_gap=len(values),
                avg_gap=round(sum(values) / len(values), 2),
                critical_count=critical[skill_id],
                high_count=high[skill_id],
            )
        )
    rows.sort(
        key=lambda item: (
            -item.employees_with_gap,
            -item.avg_gap,
            item.skill.canonical_name.lower(),
        )
    )
    return rows


def _resource_counts(db: Session) -> tuple[dict[UUID, int], dict[UUID, int]]:
    courses = {
        skill_id: count
        for skill_id, count in db.execute(
            select(CourseSkill.skill_id, func.count()).group_by(CourseSkill.skill_id)
        )
    }
    projects = {
        skill_id: count
        for skill_id, count in db.execute(
            select(ProjectSkill.skill_id, func.count()).group_by(ProjectSkill.skill_id)
        )
    }
    return courses, projects


def _progress(db: Session, employee_ids: list[UUID]) -> LearningProgressPublic:
    if not employee_ids:
        return LearningProgressPublic(
            employees_with_attempts=0,
            total_attempts=0,
            pass_rate=0.0,
            employees_with_paths=0,
            avg_path_coverage=0.0,
        )
    attempts = db.scalars(
        select(AssessmentAttempt).where(AssessmentAttempt.employee_id.in_(employee_ids))
    ).all()
    paths = db.scalars(
        select(LearningPath).where(LearningPath.employee_id.in_(employee_ids))
    ).all()
    passed = sum(1 for item in attempts if item.passed)
    coverages = [float(item.skill_coverage) for item in paths]
    return LearningProgressPublic(
        employees_with_attempts=len({item.employee_id for item in attempts}),
        total_attempts=len(attempts),
        pass_rate=round(passed / len(attempts), 2) if attempts else 0.0,
        employees_with_paths=len({item.employee_id for item in paths}),
        avg_path_coverage=(
            round(sum(coverages) / len(coverages), 2) if coverages else 0.0
        ),
    )


def _frameworks(
    db: Session, employees: list[Employee]
) -> list[FrameworkAdoptionPublic]:
    roles = {row.id: row for row in db.scalars(select(TargetRole)).all()}
    counts: dict[UUID, int] = defaultdict(int)
    for employee in employees:
        if employee.target_role_id is not None:
            counts[employee.target_role_id] += 1
    rows = [
        FrameworkAdoptionPublic(
            role_id=role_id,
            title=roles[role_id].title,
            employees_targeting=count,
        )
        for role_id, count in counts.items()
        if role_id in roles
    ]
    rows.sort(key=lambda item: (-item.employees_targeting, item.title.lower()))
    return rows


def _department_slices(employees: list[Employee]) -> list[DepartmentSlicePublic]:
    counts: dict[str, int] = defaultdict(int)
    for employee in employees:
        label = (employee.department or "").strip() or "Unspecified"
        counts[label] += 1
    rows = [
        DepartmentSlicePublic(department=name, employee_count=count)
        for name, count in counts.items()
    ]
    rows.sort(key=lambda item: (-item.employee_count, item.department.lower()))
    return rows


def _avg_completeness(employees: list[Employee]) -> float:
    if not employees:
        return 0.0
    scores = [profile_service.completeness(row).score for row in employees]
    return round(sum(scores) / len(scores), 2)
