"""phase 12 mentor matches

Revision ID: 0010_phase12
Revises: 0009_phase11
Create Date: 2026-09-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_phase12"
down_revision: Union[str, None] = "0009_phase11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mentor_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mentor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(6, 4), nullable=False),
        sa.Column("components", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("why", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mentor_id"], ["mentors.id"], ondelete="CASCADE"),
        sa.CheckConstraint("rank >= 1", name="ck_mentor_matches_rank"),
    )
    op.create_index("ix_mentor_matches_batch_id", "mentor_matches", ["batch_id"])
    op.create_index("ix_mentor_matches_employee_id", "mentor_matches", ["employee_id"])
    op.create_index("ix_mentor_matches_mentor_id", "mentor_matches", ["mentor_id"])


def downgrade() -> None:
    op.drop_index("ix_mentor_matches_mentor_id", table_name="mentor_matches")
    op.drop_index("ix_mentor_matches_employee_id", table_name="mentor_matches")
    op.drop_index("ix_mentor_matches_batch_id", table_name="mentor_matches")
    op.drop_table("mentor_matches")
