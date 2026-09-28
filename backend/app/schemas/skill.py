from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel


class SkillPublic(ORMModel):
    id: UUID
    name: str
    canonical_name: str
    category: str
    description: str | None = None
    difficulty: int = 3
    aliases: list[str] = Field(default_factory=list)


class SkillResolveRequest(BaseModel):
    mentions: list[str] = Field(min_length=1, max_length=50)

    @field_validator("mentions")
    @classmethod
    def strip_mentions(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("At least one skill mention is required")
        return cleaned


class SkillResolveItem(BaseModel):
    raw: str
    skill_id: UUID | None = None
    canonical_name: str | None = None
    confidence: float = Field(ge=0, le=1)
    matched_term: str | None = None
    match_type: Literal["exact", "alias", "collision", "unmatched"]


class SkillResolveResponse(BaseModel):
    results: list[SkillResolveItem]
