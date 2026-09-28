"""phase 13 topological learning paths

Revision ID: 0011_phase13
Revises: 0010_phase12
Create Date: 2026-09-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_phase13"
down_revision: Union[str, Sequence[str], None] = "0010_phase12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learning_paths",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("method", sa.String(32), nullable=False),
        sa.Column("prerequisite_violation_count", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_title", sa.String(255), nullable=False),
        sa.Column(
            "skipped_foundations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
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
            "prerequisite_violation_count >= 0",
            name="ck_learning_paths_violations",
        ),
    )
    op.create_index(
        "ix_learning_paths_employee_id", "learning_paths", ["employee_id"]
    )
    op.create_table(
        "learning_path_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("path_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("blocked_by", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("why", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
            ["path_id"], ["learning_paths.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.CheckConstraint("position >= 1", name="ck_learning_path_steps_position"),
    )
    op.create_index(
        "ix_learning_path_steps_path_id", "learning_path_steps", ["path_id"]
    )
    op.create_index(
        "ix_learning_path_steps_skill_id", "learning_path_steps", ["skill_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_learning_path_steps_skill_id", table_name="learning_path_steps")
    op.drop_index("ix_learning_path_steps_path_id", table_name="learning_path_steps")
    op.drop_table("learning_path_steps")
    op.drop_index("ix_learning_paths_employee_id", table_name="learning_paths")
    op.drop_table("learning_paths")
