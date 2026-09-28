from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel


class AnalyticsSkillPublic(ORMModel):
    id: UUID
    canonical_name: str
    category: str


class AnalyticsScopePublic(ORMModel):
    type: str
    label: str


class HeatmapRowPublic(ORMModel):
    skill: AnalyticsSkillPublic
    band_1: int
    band_2: int
    band_3: int
    band_4: int
    band_5: int
    missing_count: int


class GapAggregatePublic(ORMModel):
    skill: AnalyticsSkillPublic
    employees_with_gap: int
    avg_gap: float
    critical_count: int
    high_count: int


class TrainingPriorityPublic(ORMModel):
    skill: AnalyticsSkillPublic
    rank: int
    employees_with_gap: int
    avg_gap: float
    course_count: int
    project_count: int


class LearningProgressPublic(ORMModel):
    employees_with_attempts: int
    total_attempts: int
    pass_rate: float
    employees_with_paths: int
    avg_path_coverage: float


class FrameworkAdoptionPublic(ORMModel):
    role_id: UUID
    title: str
    employees_targeting: int


class DepartmentSlicePublic(ORMModel):
    department: str
    employee_count: int


class AnalyticsSnapshotPublic(ORMModel):
    scope: AnalyticsScopePublic
    disclaimer: str
    employee_count: int
    with_target_role_count: int
    avg_completeness: float
    heatmap: list[HeatmapRowPublic] = Field(default_factory=list)
    top_gaps: list[GapAggregatePublic] = Field(default_factory=list)
    training_priorities: list[TrainingPriorityPublic] = Field(default_factory=list)
    learning_progress: LearningProgressPublic
    frameworks: list[FrameworkAdoptionPublic] = Field(default_factory=list)
    departments: list[DepartmentSlicePublic] = Field(default_factory=list)
    github_collected: bool = False
