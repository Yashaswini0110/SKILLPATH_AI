"""phase 2 skill taxonomy

Revision ID: 0002_phase2
Revises: 0001_phase1
Create Date: 2026-09-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase2"
down_revision: Union[str, None] = "0001_phase1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "skills",
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="3"),
    )
    op.create_check_constraint(
        "ck_skills_difficulty",
        "skills",
        "difficulty >= 1 AND difficulty <= 5",
    )
    op.create_unique_constraint("uq_skills_canonical_name", "skills", ["canonical_name"])

    op.create_table(
        "skill_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alias", sa.String(255), nullable=False),
        sa.Column("normalized_alias", sa.String(255), nullable=False),
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
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("normalized_alias", name="uq_skill_aliases_normalized"),
    )
    op.create_index("ix_skill_aliases_skill_id", "skill_aliases", ["skill_id"])
    op.create_index(
        "ix_skill_aliases_normalized_alias", "skill_aliases", ["normalized_alias"]
    )


def downgrade() -> None:
    op.drop_index("ix_skill_aliases_normalized_alias", table_name="skill_aliases")
    op.drop_index("ix_skill_aliases_skill_id", table_name="skill_aliases")
    op.drop_table("skill_aliases")
    op.drop_constraint("uq_skills_canonical_name", "skills", type_="unique")
    op.drop_constraint("ck_skills_difficulty", "skills", type_="check")
    op.drop_column("skills", "difficulty")
