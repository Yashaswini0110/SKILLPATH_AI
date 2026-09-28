from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.models import (
    Course,
    CourseSkill,
    Mentor,
    MentorSkill,
    Project,
    ProjectSkill,
    Skill,
)
from app.schemas.resource import (
    CoursePublic,
    MentorPublic,
    ProjectPublic,
    ResourceSkillPublic,
)
from app.services.skill_view import to_skill_public


class ResourceService:
    def list_courses(
        self, db: Session, skill_id: UUID | None = None
    ) -> list[CoursePublic]:
        stmt = (
            select(Course)
            .options(
                joinedload(Course.skills)
                .joinedload(CourseSkill.skill)
                .joinedload(Skill.aliases)
            )
            .order_by(Course.title)
        )
        if skill_id is not None:
            stmt = stmt.where(Course.skills.any(CourseSkill.skill_id == skill_id))
        rows = db.scalars(stmt).unique().all()
        return [_course_public(row) for row in rows]

    def get_course(self, db: Session, course_id: UUID) -> CoursePublic:
        row = _one_course(db, course_id)
        if row is None:
            raise NotFoundError("Course not found")
        return _course_public(row)

    def list_projects(
        self, db: Session, skill_id: UUID | None = None
    ) -> list[ProjectPublic]:
        stmt = (
            select(Project)
            .options(
                joinedload(Project.skills)
                .joinedload(ProjectSkill.skill)
                .joinedload(Skill.aliases)
            )
            .order_by(Project.title)
        )
        if skill_id is not None:
            stmt = stmt.where(Project.skills.any(ProjectSkill.skill_id == skill_id))
        rows = db.scalars(stmt).unique().all()
        return [_project_public(row) for row in rows]

    def get_project(self, db: Session, project_id: UUID) -> ProjectPublic:
        row = _one_project(db, project_id)
        if row is None:
            raise NotFoundError("Project not found")
        return _project_public(row)

    def list_mentors(
        self, db: Session, skill_id: UUID | None = None
    ) -> list[MentorPublic]:
        stmt = (
            select(Mentor)
            .options(
                joinedload(Mentor.skills)
                .joinedload(MentorSkill.skill)
                .joinedload(Skill.aliases)
            )
            .order_by(Mentor.name)
        )
        if skill_id is not None:
            stmt = stmt.where(Mentor.skills.any(MentorSkill.skill_id == skill_id))
        rows = db.scalars(stmt).unique().all()
        return [_mentor_public(row) for row in rows]

    def get_mentor(self, db: Session, mentor_id: UUID) -> MentorPublic:
        row = _one_mentor(db, mentor_id)
        if row is None:
            raise NotFoundError("Mentor not found")
        return _mentor_public(row)


def _one_course(db: Session, course_id: UUID) -> Course | None:
    return (
        db.scalars(
            select(Course)
            .options(
                joinedload(Course.skills)
                .joinedload(CourseSkill.skill)
                .joinedload(Skill.aliases)
            )
            .where(Course.id == course_id)
        )
        .unique()
        .one_or_none()
    )


def _one_project(db: Session, project_id: UUID) -> Project | None:
    return (
        db.scalars(
            select(Project)
            .options(
                joinedload(Project.skills)
                .joinedload(ProjectSkill.skill)
                .joinedload(Skill.aliases)
            )
            .where(Project.id == project_id)
        )
        .unique()
        .one_or_none()
    )


def _one_mentor(db: Session, mentor_id: UUID) -> Mentor | None:
    return (
        db.scalars(
            select(Mentor)
            .options(
                joinedload(Mentor.skills)
                .joinedload(MentorSkill.skill)
                .joinedload(Skill.aliases)
            )
            .where(Mentor.id == mentor_id)
        )
        .unique()
        .one_or_none()
    )


def _skill_links(rows: list) -> list[ResourceSkillPublic]:
    items = [
        ResourceSkillPublic(skill=to_skill_public(row.skill), level=row.level)
        for row in rows
    ]
    items.sort(key=lambda item: (-item.level, item.skill.canonical_name.lower()))
    return items


def _course_public(row: Course) -> CoursePublic:
    return CoursePublic(
        id=row.id,
        title=row.title,
        provider=row.provider,
        description=row.description,
        difficulty=row.difficulty,
        duration_hours=row.duration_hours,
        format=row.format,
        url=row.url,
        rating=row.rating,
        skills=_skill_links(row.skills),
    )


def _project_public(row: Project) -> ProjectPublic:
    return ProjectPublic(
        id=row.id,
        title=row.title,
        description=row.description,
        difficulty=row.difficulty,
        duration_hours=row.duration_hours,
        technologies=list(row.technologies or []),
        deliverables=list(row.deliverables or []),
        skills=_skill_links(row.skills),
    )


def _mentor_public(row: Mentor) -> MentorPublic:
    return MentorPublic(
        id=row.id,
        name=row.name,
        title=row.title,
        bio=row.bio,
        years_experience=row.years_experience,
        available_hours_per_month=row.available_hours_per_month,
        max_mentees=row.max_mentees,
        domains=list(row.domains or []),
        skills=_skill_links(row.skills),
    )


resource_service = ResourceService()
