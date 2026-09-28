from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import SkillSourceType
from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.skill import Skill


class EmployeeSkill(TimestampMixin, Base):
    __tablename__ = "employee_skills"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "skill_id", name="uq_employee_skills_employee_skill"
        ),
        CheckConstraint(
            "current_level >= 0 AND current_level <= 5", name="ck_employee_skills_level"
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_employee_skills_confidence"
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
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_level: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SkillSourceType.SELF.value
    )

    employee: Mapped[Employee] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="employee_skills")
