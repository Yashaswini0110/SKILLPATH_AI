from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.skill import Skill


class Course(TimestampMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint(
            "difficulty >= 1 AND difficulty <= 5", name="ck_courses_difficulty"
        ),
        CheckConstraint("duration_hours >= 0", name="ck_courses_duration"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_courses_rating"),
        CheckConstraint(
            "format IN ('video', 'text', 'hands-on', 'live')",
            name="ck_courses_format",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)

    skills: Mapped[list[CourseSkill]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class CourseSkill(Base):
    __tablename__ = "course_skills"
    __table_args__ = (
        UniqueConstraint("course_id", "skill_id", name="uq_course_skills_course_skill"),
        CheckConstraint("level >= 1 AND level <= 5", name="ck_course_skills_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    course: Mapped[Course] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="course_skills")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint(
            "difficulty >= 1 AND difficulty <= 5", name="ck_projects_difficulty"
        ),
        CheckConstraint("duration_hours >= 0", name="ck_projects_duration"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    technologies: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    deliverables: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    skills: Mapped[list[ProjectSkill]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectSkill(Base):
    __tablename__ = "project_skills"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "skill_id", name="uq_project_skills_project_skill"
        ),
        CheckConstraint("level >= 1 AND level <= 5", name="ck_project_skills_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    project: Mapped[Project] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="project_skills")


class Mentor(TimestampMixin, Base):
    __tablename__ = "mentors"
    __table_args__ = (
        CheckConstraint("years_experience >= 0", name="ck_mentors_experience"),
        CheckConstraint(
            "available_hours_per_month >= 0", name="ck_mentors_availability"
        ),
        CheckConstraint("max_mentees >= 0", name="ck_mentors_max_mentees"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=False)
    years_experience: Mapped[int] = mapped_column(Integer, nullable=False)
    available_hours_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    max_mentees: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    domains: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    skills: Mapped[list[MentorSkill]] = relationship(
        back_populates="mentor", cascade="all, delete-orphan"
    )


class MentorSkill(Base):
    __tablename__ = "mentor_skills"
    __table_args__ = (
        UniqueConstraint("mentor_id", "skill_id", name="uq_mentor_skills_mentor_skill"),
        CheckConstraint("level >= 1 AND level <= 5", name="ck_mentor_skills_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mentor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mentors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    mentor: Mapped[Mentor] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="mentor_skills")
