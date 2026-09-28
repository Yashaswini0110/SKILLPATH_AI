from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import ORMModel
from app.schemas.role import RequirementWeightsPublic
from app.schemas.skill import SkillPublic


class JobDescriptionSkillPublic(ORMModel):
    id: UUID
    skill: SkillPublic
    requirement: str
    importance: Decimal
    required_level: int
    match_type: str
    mention_count: int


class JobDescriptionSummary(ORMModel):
    id: UUID
    title: str
    source_type: str
    original_filename: str | None = None
    status: str
    created_at: datetime
    skill_count: int


class JobDescriptionPublic(JobDescriptionSummary):
    extracted_text: str | None = None
    error_message: str | None = None
    weights: RequirementWeightsPublic
    skills: list[JobDescriptionSkillPublic] = []


class JobDescriptionCreate(ORMModel):
    title: str | None = Field(default=None, max_length=255)
    text: str = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 20:
            raise ValueError("Job description is too short")
        return stripped
