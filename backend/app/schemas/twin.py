from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common import ORMModel
from app.schemas.gap import GapTargetPublic
from app.schemas.skill import SkillPublic


class TwinEvidenceSourcePublic(ORMModel):
    source_type: str
    present: bool
    level: Decimal | None = None
    inferred: bool = False


class TwinHistoryPointPublic(ORMModel):
    at: datetime
    source_type: str
    level: Decimal
    inferred: bool


class TwinSkillPublic(ORMModel):
    skill: SkillPublic
    current_level: Decimal
    required_level: Decimal | None = None
    gap_basic: Decimal | None = None
    gap: Decimal | None = None
    priority: str | None = None
    requirement: str | None = None
    confidence: Decimal
    confidence_label: str
    conflict: bool
    inferred_only: bool
    recommend_assessment: bool
    in_target: bool
    evidence_sources: list[TwinEvidenceSourcePublic] = Field(default_factory=list)
    history: list[TwinHistoryPointPublic] = Field(default_factory=list)
    trend: str


class TwinSnapshotPublic(ORMModel):
    target: GapTargetPublic
    disclaimer: str
    skill_count: int
    open_gap_count: int
    conflict_count: int
    github_collected: bool
    skills: list[TwinSkillPublic] = Field(default_factory=list)
