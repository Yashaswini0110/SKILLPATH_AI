"""phase 27 knowledge-graph ranking method

Revision ID: 0017_phase27
Revises: 0016_phase19
Create Date: 2026-09-23
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0017_phase27"
down_revision: Union[str, Sequence[str], None] = "0016_phase19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_recommendation_method", "recommendation_results", type_="check"
    )
    op.create_check_constraint(
        "ck_recommendation_method",
        "recommendation_results",
        "method IN ('POPULARITY', 'CONTENT', 'SEMANTIC', 'KG', 'HYBRID')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_recommendation_method", "recommendation_results", type_="check"
    )
    op.create_check_constraint(
        "ck_recommendation_method",
        "recommendation_results",
        "method IN ('POPULARITY', 'CONTENT', 'SEMANTIC', 'HYBRID')",
    )
