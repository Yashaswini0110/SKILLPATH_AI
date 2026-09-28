from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.resume import Resume
    from app.models.skill import Skill


class Evidence(TimestampMixin, Base):
    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint(
            "extracted_level >= 0 AND extracted_level <= 5",
            name="ck_evidence_level",
        ),
        CheckConstraint(
            "reliability >= 0 AND reliability <= 1", name="ck_evidence_reliability"
        ),
        CheckConstraint("recency >= 0 AND recency <= 1", name="ck_evidence_recency"),
        CheckConstraint("strength >= 0 AND strength <= 1", name="ck_evidence_strength"),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_evidence_confidence"
        ),
        Index(
            "uq_evidence_self_employee_skill",
            "employee_id",
            "skill_id",
            unique=True,
            postgresql_where=text("source_type = 'SELF'"),
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
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_level: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    reliability: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    recency: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("1.00")
    )
    strength: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    inferred: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    section: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)

    employee: Mapped[Employee] = relationship(back_populates="evidence")
    skill: Mapped[Skill] = relationship()
    resume: Mapped[Resume | None] = relationship(
        back_populates="evidence",
        primaryjoin="foreign(Evidence.source_id) == Resume.id",
        viewonly=True,
    )
