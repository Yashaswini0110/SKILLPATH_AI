"""phase 3 resume extraction

Revision ID: 0003_phase3
Revises: 0002_phase2
Create Date: 2026-09-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_phase3"
down_revision: Union[str, None] = "0002_phase2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(127), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="processed"),
        sa.Column("error_message", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_resumes_employee_id", "resumes", ["employee_id"])

    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("extracted_level", sa.Numeric(3, 1), nullable=False),
        sa.Column("reliability", sa.Numeric(3, 2), nullable=False),
        sa.Column("recency", sa.Numeric(3, 2), nullable=False, server_default="1.00"),
        sa.Column("strength", sa.Numeric(3, 2), nullable=False),
        sa.Column("inferred", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("section", sa.String(50), nullable=True),
        sa.Column("match_type", sa.String(32), nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False),
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
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "extracted_level >= 0 AND extracted_level <= 5", name="ck_evidence_level"
        ),
        sa.CheckConstraint(
            "reliability >= 0 AND reliability <= 1", name="ck_evidence_reliability"
        ),
        sa.CheckConstraint("recency >= 0 AND recency <= 1", name="ck_evidence_recency"),
        sa.CheckConstraint("strength >= 0 AND strength <= 1", name="ck_evidence_strength"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_evidence_confidence"),
    )
    op.create_index("ix_evidence_employee_id", "evidence", ["employee_id"])
    op.create_index("ix_evidence_skill_id", "evidence", ["skill_id"])
    op.create_index("ix_evidence_source_type", "evidence", ["source_type"])
    op.create_index("ix_evidence_source_id", "evidence", ["source_id"])


def downgrade() -> None:
    op.drop_table("evidence")
    op.drop_table("resumes")
