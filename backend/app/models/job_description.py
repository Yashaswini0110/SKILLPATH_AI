from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.skill import Skill


class JobDescription(TimestampMixin, Base):
    __tablename__ = "job_descriptions"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('PASTE', 'FILE')", name="ck_job_descriptions_source"
        ),
        CheckConstraint(
            "weight_required >= 0 AND weight_required <= 1",
            name="ck_job_descriptions_weight_required",
        ),
        CheckConstraint(
            "weight_preferred >= 0 AND weight_preferred <= 1",
            name="ck_job_descriptions_weight_preferred",
        ),
        CheckConstraint(
            "weight_mentioned >= 0 AND weight_mentioned <= 1",
            name="ck_job_descriptions_weight_mentioned",
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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str] = mapped_column(String(127), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="processed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight_required: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("1.00")
    )
    weight_preferred: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.60")
    )
    weight_mentioned: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.40")
    )

    employee: Mapped[Employee] = relationship(back_populates="job_descriptions")
    skills: Mapped[list[JobDescriptionSkill]] = relationship(
        back_populates="job_description", cascade="all, delete-orphan"
    )


class JobDescriptionSkill(TimestampMixin, Base):
    __tablename__ = "job_description_skills"
    __table_args__ = (
        UniqueConstraint(
            "job_description_id",
            "skill_id",
            name="uq_job_description_skills_jd_skill",
        ),
        CheckConstraint(
            "requirement IN ('REQUIRED', 'PREFERRED', 'MENTIONED')",
            name="ck_job_description_skills_requirement",
        ),
        CheckConstraint(
            "required_level >= 1 AND required_level <= 5",
            name="ck_job_description_skills_level",
        ),
        CheckConstraint(
            "importance >= 0 AND importance <= 1",
            name="ck_job_description_skills_importance",
        ),
        CheckConstraint(
            "mention_count >= 1", name="ck_job_description_skills_mentions"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requirement: Mapped[str] = mapped_column(String(16), nullable=False)
    importance: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)
    match_type: Mapped[str] = mapped_column(String(32), nullable=False)
    mention_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    job_description: Mapped[JobDescription] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="job_description_skills")
