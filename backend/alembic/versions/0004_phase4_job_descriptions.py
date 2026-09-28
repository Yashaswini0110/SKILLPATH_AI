"""phase 4 job descriptions

Revision ID: 0004_phase4
Revises: 0003_phase3
Create Date: 2026-09-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_phase4"
down_revision: Union[str, None] = "0003_phase3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_descriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=True),
        sa.Column("content_type", sa.String(127), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="processed"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "weight_required",
            sa.Numeric(3, 2),
            nullable=False,
            server_default="1.00",
        ),
        sa.Column(
            "weight_preferred",
            sa.Numeric(3, 2),
            nullable=False,
            server_default="0.60",
        ),
        sa.Column(
            "weight_mentioned",
            sa.Numeric(3, 2),
            nullable=False,
            server_default="0.40",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "source_type IN ('PASTE', 'FILE')", name="ck_job_descriptions_source"
        ),
        sa.CheckConstraint(
            "weight_required >= 0 AND weight_required <= 1",
            name="ck_job_descriptions_weight_required",
        ),
        sa.CheckConstraint(
            "weight_preferred >= 0 AND weight_preferred <= 1",
            name="ck_job_descriptions_weight_preferred",
        ),
        sa.CheckConstraint(
            "weight_mentioned >= 0 AND weight_mentioned <= 1",
            name="ck_job_descriptions_weight_mentioned",
        ),
    )
    op.create_index(
        "ix_job_descriptions_employee_id", "job_descriptions", ["employee_id"]
    )

    op.create_table(
        "job_description_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "job_description_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement", sa.String(16), nullable=False),
        sa.Column("importance", sa.Numeric(3, 2), nullable=False),
        sa.Column("required_level", sa.Integer(), nullable=False),
        sa.Column("match_type", sa.String(32), nullable=False),
        sa.Column("mention_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_description_id"], ["job_descriptions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "job_description_id",
            "skill_id",
            name="uq_job_description_skills_jd_skill",
        ),
        sa.CheckConstraint(
            "requirement IN ('REQUIRED', 'PREFERRED', 'MENTIONED')",
            name="ck_job_description_skills_requirement",
        ),
        sa.CheckConstraint(
            "required_level >= 1 AND required_level <= 5",
            name="ck_job_description_skills_level",
        ),
        sa.CheckConstraint(
            "importance >= 0 AND importance <= 1",
            name="ck_job_description_skills_importance",
        ),
        sa.CheckConstraint(
            "mention_count >= 1", name="ck_job_description_skills_mentions"
        ),
    )
    op.create_index(
        "ix_job_description_skills_job_description_id",
        "job_description_skills",
        ["job_description_id"],
    )
    op.create_index(
        "ix_job_description_skills_skill_id",
        "job_description_skills",
        ["skill_id"],
    )


def downgrade() -> None:
    op.drop_table("job_description_skills")
    op.drop_table("job_descriptions")
