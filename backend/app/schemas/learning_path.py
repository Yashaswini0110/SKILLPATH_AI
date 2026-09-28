from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel
from app.schemas.gap import GapTargetPublic
from app.schemas.recommendation import ExplanationPublic
from app.schemas.resource import CoursePublic, ProjectPublic
from app.schemas.skill import SkillPublic


class PathGapSkillPublic(ORMModel):
    skill: SkillPublic
    gap: Decimal | None = None
    priority: str


class LearningPathStepPublic(ORMModel):
    position: int
    skill: SkillPublic
    kind: str
    stage: str = "CORE"
    status: str = "NOT_STARTED"
    difficulty: int = 3
    reason: str
    blocked_by: list[str] = Field(default_factory=list)
    course: CoursePublic | None = None
    project: ProjectPublic | None = None
    duration_hours: int = 0
    week_start: int = 1
    week_end: int = 1
    assessment_id: UUID | None = None
    why: dict[str, object] = Field(default_factory=dict)
    explanation: ExplanationPublic


class PathAdaptationPublic(ORMModel):
    skill: str
    action: str
    percent: float
    extra_hours: int = 0
    reason: str


class PathMethodScorePublic(ORMModel):
    method: str
    selected_count: int
    total_hours: int
    estimated_weeks: int
    skill_coverage: float
    prerequisite_violation_count: int
    hours_violation_count: int
    path_efficiency: float


class LearningPathPublic(ORMModel):
    id: UUID
    method: str
    prerequisite_violation_count: int
    hours_violation_count: int = 0
    duplicate_resource_count: int = 0
    hours_per_week: int = 10
    deadline_weeks: int = 12
    capacity_hours: int = 120
    total_hours: int = 0
    estimated_weeks: int = 1
    skill_coverage: float = 0.0
    path_efficiency: float = 0.0
    target: GapTargetPublic
    gap_skills: list[PathGapSkillPublic] = Field(default_factory=list)
    skipped_foundations: list[str] = Field(default_factory=list)
    adaptations: list[PathAdaptationPublic] = Field(default_factory=list)
    comparison: list[PathMethodScorePublic] = Field(default_factory=list)
    reason: str
    steps: list[LearningPathStepPublic] = Field(default_factory=list)
    edges: list[list[str]] = Field(default_factory=list)
