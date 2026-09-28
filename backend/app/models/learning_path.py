from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.employee import Employee
from app.models.mixins import TimestampMixin
from app.models.resource import Course, Project
from app.models.skill import Skill


class LearningPath(TimestampMixin, Base):
    __tablename__ = "learning_paths"
    __table_args__ = (
        CheckConstraint(
            "prerequisite_violation_count >= 0",
            name="ck_learning_paths_violations",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    method: Mapped[str] = mapped_column(String(32), nullable=False, default="ORTOOLS")
    prerequisite_violation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    hours_violation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    duplicate_resource_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    deadline_weeks: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    total_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_weeks: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    skill_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    path_efficiency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    comparison: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_title: Mapped[str] = mapped_column(String(255), nullable=False)
    skipped_foundations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    adaptations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    employee: Mapped[Employee] = relationship()
    steps: Mapped[list[LearningPathStep]] = relationship(
        back_populates="path", order_by="LearningPathStep.position"
    )


class LearningPathStep(TimestampMixin, Base):
    __tablename__ = "learning_path_steps"
    __table_args__ = (
        CheckConstraint("position >= 1", name="ck_learning_path_steps_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    week_start: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    week_end: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    blocked_by: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    why: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    explanation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    path: Mapped[LearningPath] = relationship(back_populates="steps")
    skill: Mapped[Skill] = relationship()
    course: Mapped[Course | None] = relationship()
    project: Mapped[Project | None] = relationship()
