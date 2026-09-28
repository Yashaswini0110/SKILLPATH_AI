"""phase 8 recommendation results

Revision ID: 0007_phase8
Revises: 0006_phase7
Create Date: 2026-09-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_phase8"
down_revision: Union[str, None] = "0006_phase7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_type", sa.String(32), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("method", sa.String(32), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(6, 4), nullable=False),
        sa.Column("components", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "matched_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("encoder", sa.String(64), nullable=True),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_title", sa.String(255), nullable=False),
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
            ["employee_id"], ["employees.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "resource_type IN ('COURSE', 'PROJECT', 'MENTOR')",
            name="ck_recommendation_resource_type",
        ),
        sa.CheckConstraint(
            "method IN ('POPULARITY', 'CONTENT', 'SEMANTIC')",
            name="ck_recommendation_method",
        ),
        sa.CheckConstraint("rank >= 1", name="ck_recommendation_rank"),
    )
    op.create_index(
        "ix_recommendation_results_batch_id",
        "recommendation_results",
        ["batch_id"],
    )
    op.create_index(
        "ix_recommendation_results_employee_id",
        "recommendation_results",
        ["employee_id"],
    )
    op.create_index(
        "ix_recommendation_results_resource_id",
        "recommendation_results",
        ["resource_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recommendation_results_resource_id", table_name="recommendation_results"
    )
    op.drop_index(
        "ix_recommendation_results_employee_id", table_name="recommendation_results"
    )
    op.drop_index(
        "ix_recommendation_results_batch_id", table_name="recommendation_results"
    )
    op.drop_table("recommendation_results")
