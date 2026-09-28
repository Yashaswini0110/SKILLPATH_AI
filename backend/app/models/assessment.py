from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.skill import Skill


class Assessment(TimestampMixin, Base):
    __tablename__ = "assessments"
    __table_args__ = (
        CheckConstraint(
            "assessment_type IN ('MCQ', 'CONCEPTUAL', 'CODING', 'PRACTICAL')",
            name="ck_assessments_type",
        ),
        CheckConstraint(
            "pass_score >= 0 AND pass_score <= 1", name="ck_assessments_pass_score"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="MCQ"
    )
    pass_score: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.70")
    )

    skill: Mapped[Skill] = relationship()
    questions: Mapped[list[AssessmentQuestion]] = relationship(
        back_populates="assessment",
        order_by="AssessmentQuestion.position",
        cascade="all, delete-orphan",
    )
    attempts: Mapped[list[AssessmentAttempt]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentQuestion(TimestampMixin, Base):
    __tablename__ = "assessment_questions"
    __table_args__ = (
        CheckConstraint("position >= 1", name="ck_assessment_questions_position"),
        CheckConstraint(
            "correct_index >= 0", name="ck_assessment_questions_correct_index"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    choices: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    assessment: Mapped[Assessment] = relationship(back_populates="questions")


class AssessmentAttempt(TimestampMixin, Base):
    __tablename__ = "assessment_attempts"
    __table_args__ = (
        CheckConstraint(
            "percent >= 0 AND percent <= 1", name="ck_assessment_attempts_percent"
        ),
        CheckConstraint(
            "extracted_level >= 0 AND extracted_level <= 5",
            name="ck_assessment_attempts_level",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    percent: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    extracted_level: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)

    assessment: Mapped[Assessment] = relationship(back_populates="attempts")
    answers: Mapped[list[AssessmentAnswer]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="AssessmentAnswer.position",
    )


class AssessmentAnswer(TimestampMixin, Base):
    __tablename__ = "assessment_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)

    attempt: Mapped[AssessmentAttempt] = relationship(back_populates="answers")
    question: Mapped[AssessmentQuestion] = relationship()
