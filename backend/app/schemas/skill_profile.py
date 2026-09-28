from decimal import Decimal
from uuid import UUID

from app.schemas.common import ORMModel
from app.schemas.skill import SkillPublic


class EvidencePublic(ORMModel):
    id: UUID | None = None
    source_type: str
    extracted_level: Decimal
    reliability: Decimal
    strength: Decimal
    recency: Decimal
    inferred: bool


class AggregatedSkillPublic(ORMModel):
    skill: SkillPublic
    current_level: Decimal
    confidence: Decimal
    confidence_label: str
    conflict: bool
    variance: Decimal
    recommend_assessment: bool
    inferred_only: bool
    evidence: list[EvidencePublic] = []


class SkillProfilePublic(ORMModel):
    skill_count: int
    conflict_count: int
    conflict_variance_threshold: Decimal
    source_reliability: dict[str, float]
    skills: list[AggregatedSkillPublic] = []
