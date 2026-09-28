from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee_skill import EmployeeSkill
    from app.models.job_description import JobDescriptionSkill
    from app.models.resource import CourseSkill, MentorSkill, ProjectSkill
    from app.models.skill_alias import SkillAlias
    from app.models.target_role import RoleSkill


class Skill(TimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint(
            "difficulty >= 1 AND difficulty <= 5", name="ck_skills_difficulty"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    canonical_name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    aliases: Mapped[list[SkillAlias]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
    employee_skills: Mapped[list[EmployeeSkill]] = relationship(back_populates="skill")
    role_skills: Mapped[list[RoleSkill]] = relationship(back_populates="skill")
    job_description_skills: Mapped[list[JobDescriptionSkill]] = relationship(
        back_populates="skill"
    )
    course_skills: Mapped[list[CourseSkill]] = relationship(back_populates="skill")
    project_skills: Mapped[list[ProjectSkill]] = relationship(back_populates="skill")
    mentor_skills: Mapped[list[MentorSkill]] = relationship(back_populates="skill")
