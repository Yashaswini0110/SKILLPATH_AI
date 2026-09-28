from decimal import Decimal
from uuid import UUID

from app.schemas.common import ORMModel
from app.schemas.skill import SkillPublic


class GapTargetPublic(ORMModel):
    type: str
    id: UUID
    title: str


class GapItemPublic(ORMModel):
    skill: SkillPublic
    required_level: Decimal
    current_level: Decimal
    gap_basic: Decimal
    gap: Decimal
    priority: str
    importance: Decimal
    criticality: Decimal
    confidence: Decimal
    evidence_strength: Decimal
    requirement: str
    inferred_only: bool
    conflict: bool


class GapAnalysisPublic(ORMModel):
    target: GapTargetPublic
    gap_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    none_count: int
    gaps: list[GapItemPublic] = []
