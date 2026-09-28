from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.schemas.common import ORMModel
from app.schemas.skill import SkillPublic


class ExtractedSkillPublic(ORMModel):
    id: UUID
    skill: SkillPublic
    extracted_level: Decimal
    confidence: Decimal
    reliability: Decimal
    strength: Decimal
    source_type: str
    inferred: bool
    evidence_snippet: str | None = None
    section: str | None = None
    match_type: str | None = None


class ResumeSummary(ORMModel):
    id: UUID
    original_filename: str
    content_type: str
    status: str
    created_at: datetime
    skill_count: int


class ResumePublic(ResumeSummary):
    extracted_text: str | None = None
    error_message: str | None = None
    skills: list[ExtractedSkillPublic] = []
