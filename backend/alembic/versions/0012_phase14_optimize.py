"""phase 14 path optimization metrics

Revision ID: 0012_phase14
Revises: 0011_phase13
Create Date: 2026-09-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_phase14"
down_revision: Union[str, Sequence[str], None] = "0011_phase13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "learning_paths",
        sa.Column("hours_violation_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "learning_paths",
        sa.Column(
            "duplicate_resource_count", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "learning_paths",
        sa.Column("hours_per_week", sa.Integer(), nullable=False, server_default="10"),
    )
    op.add_column(
        "learning_paths",
        sa.Column("deadline_weeks", sa.Integer(), nullable=False, server_default="12"),
    )
    op.add_column(
        "learning_paths",
        sa.Column("total_hours", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "learning_paths",
        sa.Column("estimated_weeks", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "learning_paths",
        sa.Column("skill_coverage", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "learning_paths",
        sa.Column("path_efficiency", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "learning_paths",
        sa.Column(
            "comparison",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "learning_path_steps",
        sa.Column("duration_hours", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "learning_path_steps",
        sa.Column("week_start", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "learning_path_steps",
        sa.Column("week_end", sa.Integer(), nullable=False, server_default="1"),
    )
    op.alter_column("learning_paths", "hours_violation_count", server_default=None)
    op.alter_column("learning_paths", "duplicate_resource_count", server_default=None)
    op.alter_column("learning_paths", "hours_per_week", server_default=None)
    op.alter_column("learning_paths", "deadline_weeks", server_default=None)
    op.alter_column("learning_paths", "total_hours", server_default=None)
    op.alter_column("learning_paths", "estimated_weeks", server_default=None)
    op.alter_column("learning_paths", "skill_coverage", server_default=None)
    op.alter_column("learning_paths", "path_efficiency", server_default=None)
    op.alter_column("learning_paths", "comparison", server_default=None)
    op.alter_column("learning_path_steps", "duration_hours", server_default=None)
    op.alter_column("learning_path_steps", "week_start", server_default=None)
    op.alter_column("learning_path_steps", "week_end", server_default=None)


def downgrade() -> None:
    op.drop_column("learning_path_steps", "week_end")
    op.drop_column("learning_path_steps", "week_start")
    op.drop_column("learning_path_steps", "duration_hours")
    op.drop_column("learning_paths", "comparison")
    op.drop_column("learning_paths", "path_efficiency")
    op.drop_column("learning_paths", "skill_coverage")
    op.drop_column("learning_paths", "estimated_weeks")
    op.drop_column("learning_paths", "total_hours")
    op.drop_column("learning_paths", "deadline_weeks")
    op.drop_column("learning_paths", "hours_per_week")
    op.drop_column("learning_paths", "duplicate_resource_count")
    op.drop_column("learning_paths", "hours_violation_count")
