"""phase 18 store explanation facts

Revision ID: 0015_phase18
Revises: 0014_phase17
Create Date: 2026-09-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_phase18"
down_revision: Union[str, Sequence[str], None] = "0014_phase17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in (
        "recommendation_results",
        "practice_pairings",
        "mentor_matches",
        "learning_path_steps",
    ):
        op.add_column(
            table,
            sa.Column(
                "explanation",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
        )


def downgrade() -> None:
    for table in (
        "learning_path_steps",
        "mentor_matches",
        "practice_pairings",
        "recommendation_results",
    ):
        op.drop_column(table, "explanation")
