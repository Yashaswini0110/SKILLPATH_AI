from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel
from app.schemas.gap import GapTargetPublic
from app.schemas.resource import CoursePublic, MentorPublic, ProjectPublic
from app.schemas.skill import SkillPublic


class ExplanationFactPublic(ORMModel):
    key: str
    text: str
    value: str | float | int | None = None


class ExplanationPublic(ORMModel):
    facts: list[ExplanationFactPublic] = Field(default_factory=list)
    verbalization: str = ""


class MatchedGapSkillPublic(ORMModel):
    skill: SkillPublic
    gap: Decimal
    priority: str


class RecommendationItemPublic(ORMModel):
    rank: int
    score: Decimal
    components: dict[str, Any]
    matched_skills: list[MatchedGapSkillPublic] = Field(default_factory=list)
    reason: str
    explanation: ExplanationPublic
    course: CoursePublic | None = None
    project: ProjectPublic | None = None
    mentor: MentorPublic | None = None


class RecommendationListPublic(ORMModel):
    batch_id: UUID
    method: str
    resource_type: str
    encoder: str | None = None
    target: GapTargetPublic
    gap_skills: list[MatchedGapSkillPublic] = Field(default_factory=list)
    items: list[RecommendationItemPublic] = Field(default_factory=list)
    weights: dict[str, float] | None = None


class PracticePairPublic(ORMModel):
    rank: int
    score: Decimal
    skill: SkillPublic
    gap: Decimal
    priority: str
    current_level: Decimal
    required_level: Decimal
    course: CoursePublic
    project: ProjectPublic
    components: dict[str, Any]
    reason: str
    explanation: ExplanationPublic


class PracticePairListPublic(ORMModel):
    batch_id: UUID
    target: GapTargetPublic
    weights: dict[str, float]
    items: list[PracticePairPublic] = Field(default_factory=list)


class MentorWhyPublic(ORMModel):
    matched_gap_count: int
    top_gap_count: int
    matched_skills: list[SkillPublic] = Field(default_factory=list)
    available_hours_per_month: int
    open_mentee_slots: int
    domains: list[str] = Field(default_factory=list)


class MentorMatchPublic(ORMModel):
    rank: int
    score: Decimal
    mentor: MentorPublic
    components: dict[str, Any]
    why: MentorWhyPublic
    reason: str
    explanation: ExplanationPublic


class MentorMatchListPublic(ORMModel):
    batch_id: UUID
    target: GapTargetPublic
    weights: dict[str, float]
    gap_skills: list[MatchedGapSkillPublic] = Field(default_factory=list)
    items: list[MentorMatchPublic] = Field(default_factory=list)
