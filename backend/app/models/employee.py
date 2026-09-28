from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.education import Education
    from app.models.employee_skill import EmployeeSkill
    from app.models.evidence import Evidence
    from app.models.job_description import JobDescription
    from app.models.resume import Resume
    from app.models.target_role import TargetRole
    from app.models.user import User
    from app.models.work_experience import WorkExperience


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("user_id", name="uq_employees_user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    years_experience: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )
    available_hours_per_week: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10
    )
    learning_preferences: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    target_role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user: Mapped[User] = relationship("User", back_populates="employee")
    target_role: Mapped[TargetRole | None] = relationship(
        "TargetRole", back_populates="employees"
    )
    education: Mapped[list[Education]] = relationship(
        "Education", back_populates="employee", cascade="all, delete-orphan"
    )
    experience: Mapped[list[WorkExperience]] = relationship(
        "WorkExperience", back_populates="employee", cascade="all, delete-orphan"
    )
    skills: Mapped[list[EmployeeSkill]] = relationship(
        "EmployeeSkill", back_populates="employee", cascade="all, delete-orphan"
    )
    resumes: Mapped[list[Resume]] = relationship(
        "Resume", back_populates="employee", cascade="all, delete-orphan"
    )
    evidence: Mapped[list[Evidence]] = relationship(
        "Evidence", back_populates="employee", cascade="all, delete-orphan"
    )
    job_descriptions: Mapped[list[JobDescription]] = relationship(
        "JobDescription", back_populates="employee", cascade="all, delete-orphan"
    )
