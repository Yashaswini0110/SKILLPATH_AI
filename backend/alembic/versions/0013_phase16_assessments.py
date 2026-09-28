"""phase 16 assessments

Revision ID: 0013_phase16
Revises: 0012_phase14
Create Date: 2026-09-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_phase16"
down_revision: Union[str, Sequence[str], None] = "0012_phase14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("evidence_source_id_fkey", "evidence", type_="foreignkey")
    op.create_table(
        "assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("assessment_type", sa.String(32), nullable=False),
        sa.Column("pass_score", sa.Numeric(3, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_id"),
        sa.CheckConstraint(
            "assessment_type IN ('MCQ', 'CONCEPTUAL', 'CODING', 'PRACTICAL')",
            name="ck_assessments_type",
        ),
        sa.CheckConstraint(
            "pass_score >= 0 AND pass_score <= 1", name="ck_assessments_pass_score"
        ),
    )
    op.create_index("ix_assessments_skill_id", "assessments", ["skill_id"])
    op.create_table(
        "assessment_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("choices", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("position >= 1", name="ck_assessment_questions_position"),
        sa.CheckConstraint(
            "correct_index >= 0", name="ck_assessment_questions_correct_index"
        ),
    )
    op.create_index(
        "ix_assessment_questions_assessment_id",
        "assessment_questions",
        ["assessment_id"],
    )
    op.create_table(
        "assessment_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("percent", sa.Numeric(4, 3), nullable=False),
        sa.Column("extracted_level", sa.Numeric(3, 1), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "percent >= 0 AND percent <= 1", name="ck_assessment_attempts_percent"
        ),
        sa.CheckConstraint(
            "extracted_level >= 0 AND extracted_level <= 5",
            name="ck_assessment_attempts_level",
        ),
    )
    op.create_index(
        "ix_assessment_attempts_assessment_id", "assessment_attempts", ["assessment_id"]
    )
    op.create_index(
        "ix_assessment_attempts_employee_id", "assessment_attempts", ["employee_id"]
    )
    op.create_table(
        "assessment_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("selected_index", sa.Integer(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["assessment_attempts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["assessment_questions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assessment_answers_attempt_id", "assessment_answers", ["attempt_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_assessment_answers_attempt_id", table_name="assessment_answers")
    op.drop_table("assessment_answers")
    op.drop_index(
        "ix_assessment_attempts_employee_id", table_name="assessment_attempts"
    )
    op.drop_index(
        "ix_assessment_attempts_assessment_id", table_name="assessment_attempts"
    )
    op.drop_table("assessment_attempts")
    op.drop_index(
        "ix_assessment_questions_assessment_id", table_name="assessment_questions"
    )
    op.drop_table("assessment_questions")
    op.drop_index("ix_assessments_skill_id", table_name="assessments")
    op.drop_table("assessments")
    op.create_foreign_key(
        "evidence_source_id_fkey",
        "evidence",
        "resumes",
        ["source_id"],
        ["id"],
        ondelete="CASCADE",
    )
