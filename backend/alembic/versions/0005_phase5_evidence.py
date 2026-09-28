"""phase 5 evidence profile

Revision ID: 0005_phase5
Revises: 0004_phase4
Create Date: 2026-09-21
"""

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0005_phase5"
down_revision: Union[str, None] = "0004_phase4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT employee_id, skill_id, current_level, confidence
            FROM employee_skills es
            WHERE NOT EXISTS (
                SELECT 1 FROM evidence e
                WHERE e.employee_id = es.employee_id
                  AND e.skill_id = es.skill_id
                  AND e.source_type = 'SELF'
            )
            """
        )
    ).mappings()
    for row in rows:
        connection.execute(
            sa.text(
                """
                INSERT INTO evidence (
                    id, employee_id, skill_id, source_type, source_id, raw_text,
                    extracted_level, reliability, recency, strength, inferred,
                    section, match_type, confidence, created_at, updated_at
                ) VALUES (
                    :id, :employee_id, :skill_id, 'SELF', NULL, NULL,
                    :extracted_level, :reliability, 1.00, 1.00, false,
                    NULL, NULL, :confidence, NOW(), NOW()
                )
                """
            ),
            {
                "id": uuid4(),
                "employee_id": row["employee_id"],
                "skill_id": row["skill_id"],
                "extracted_level": row["current_level"],
                "reliability": row["confidence"],
                "confidence": row["confidence"],
            },
        )
    op.create_index(
        "uq_evidence_self_employee_skill",
        "evidence",
        ["employee_id", "skill_id"],
        unique=True,
        postgresql_where=sa.text("source_type = 'SELF'"),
    )


def downgrade() -> None:
    op.drop_index("uq_evidence_self_employee_skill", table_name="evidence")
    op.execute(sa.text("DELETE FROM evidence WHERE source_type = 'SELF'"))
