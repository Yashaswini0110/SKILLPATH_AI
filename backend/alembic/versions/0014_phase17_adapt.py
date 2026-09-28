"""phase 17 adaptive path adaptations

Revision ID: 0014_phase17
Revises: 0013_phase16
Create Date: 2026-09-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_phase17"
down_revision: Union[str, Sequence[str], None] = "0013_phase16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "learning_paths",
        sa.Column(
            "adaptations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.alter_column("learning_paths", "adaptations", server_default=None)


def downgrade() -> None:
    op.drop_column("learning_paths", "adaptations")
