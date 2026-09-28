"""phase 10 hybrid recommendation method

Revision ID: 0008_phase10
Revises: 0007_phase8
Create Date: 2026-09-21
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0008_phase10"
down_revision: Union[str, None] = "0007_phase8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_recommendation_method", "recommendation_results", type_="check"
    )
    op.create_check_constraint(
        "ck_recommendation_method",
        "recommendation_results",
        "method IN ('POPULARITY', 'CONTENT', 'SEMANTIC', 'HYBRID')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_recommendation_method", "recommendation_results", type_="check"
    )
    op.create_check_constraint(
        "ck_recommendation_method",
        "recommendation_results",
        "method IN ('POPULARITY', 'CONTENT', 'SEMANTIC')",
    )
