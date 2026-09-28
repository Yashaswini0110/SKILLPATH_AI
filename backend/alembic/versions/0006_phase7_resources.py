"""phase 7 resource catalogs

Revision ID: 0006_phase7
Revises: 0005_phase5
Create Date: 2026-09-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_phase7"
down_revision: Union[str, None] = "0005_phase5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("duration_hours", sa.Integer(), nullable=False),
        sa.Column("format", sa.String(32), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("rating", sa.Numeric(3, 2), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("title", name="uq_courses_title"),
        sa.CheckConstraint(
            "difficulty >= 1 AND difficulty <= 5", name="ck_courses_difficulty"
        ),
        sa.CheckConstraint("duration_hours >= 0", name="ck_courses_duration"),
        sa.CheckConstraint("rating >= 0 AND rating <= 5", name="ck_courses_rating"),
        sa.CheckConstraint(
            "format IN ('video', 'text', 'hands-on', 'live')",
            name="ck_courses_format",
        ),
    )
    op.create_index("ix_courses_title", "courses", ["title"])

    op.create_table(
        "course_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "course_id", "skill_id", name="uq_course_skills_course_skill"
        ),
        sa.CheckConstraint(
            "level >= 1 AND level <= 5", name="ck_course_skills_level"
        ),
    )
    op.create_index("ix_course_skills_course_id", "course_skills", ["course_id"])
    op.create_index("ix_course_skills_skill_id", "course_skills", ["skill_id"])

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("duration_hours", sa.Integer(), nullable=False),
        sa.Column(
            "technologies",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "deliverables",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        *_timestamps(),
        sa.UniqueConstraint("title", name="uq_projects_title"),
        sa.CheckConstraint(
            "difficulty >= 1 AND difficulty <= 5", name="ck_projects_difficulty"
        ),
        sa.CheckConstraint("duration_hours >= 0", name="ck_projects_duration"),
    )
    op.create_index("ix_projects_title", "projects", ["title"])

    op.create_table(
        "project_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "project_id", "skill_id", name="uq_project_skills_project_skill"
        ),
        sa.CheckConstraint(
            "level >= 1 AND level <= 5", name="ck_project_skills_level"
        ),
    )
    op.create_index("ix_project_skills_project_id", "project_skills", ["project_id"])
    op.create_index("ix_project_skills_skill_id", "project_skills", ["skill_id"])

    op.create_table(
        "mentors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=False),
        sa.Column("years_experience", sa.Integer(), nullable=False),
        sa.Column("available_hours_per_month", sa.Integer(), nullable=False),
        sa.Column("max_mentees", sa.Integer(), nullable=False, server_default="2"),
        sa.Column(
            "domains",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        *_timestamps(),
        sa.UniqueConstraint("name", name="uq_mentors_name"),
        sa.CheckConstraint("years_experience >= 0", name="ck_mentors_experience"),
        sa.CheckConstraint(
            "available_hours_per_month >= 0", name="ck_mentors_availability"
        ),
        sa.CheckConstraint("max_mentees >= 0", name="ck_mentors_max_mentees"),
    )

    op.create_table(
        "mentor_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("mentor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["mentor_id"], ["mentors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "mentor_id", "skill_id", name="uq_mentor_skills_mentor_skill"
        ),
        sa.CheckConstraint(
            "level >= 1 AND level <= 5", name="ck_mentor_skills_level"
        ),
    )
    op.create_index("ix_mentor_skills_mentor_id", "mentor_skills", ["mentor_id"])
    op.create_index("ix_mentor_skills_skill_id", "mentor_skills", ["skill_id"])


def downgrade() -> None:
    op.drop_index("ix_mentor_skills_skill_id", table_name="mentor_skills")
    op.drop_index("ix_mentor_skills_mentor_id", table_name="mentor_skills")
    op.drop_table("mentor_skills")
    op.drop_table("mentors")
    op.drop_index("ix_project_skills_skill_id", table_name="project_skills")
    op.drop_index("ix_project_skills_project_id", table_name="project_skills")
    op.drop_table("project_skills")
    op.drop_index("ix_projects_title", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_course_skills_skill_id", table_name="course_skills")
    op.drop_index("ix_course_skills_course_id", table_name="course_skills")
    op.drop_table("course_skills")
    op.drop_index("ix_courses_title", table_name="courses")
    op.drop_table("courses")
