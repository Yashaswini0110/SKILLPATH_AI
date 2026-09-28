from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel
from app.schemas.gap import GapTargetPublic
from app.schemas.role import TargetRoleSummary


class WhatIfMissingSkillPublic(ORMModel):
    skill: str
    priority: str
    current_level: float
    required_level: float


class WhatIfScenarioPublic(ORMModel):
    role: TargetRoleSummary
    is_current: bool
    skill_count: int
    covered_count: int
    coverage: float
    open_gap_count: int
    missing_skills: list[WhatIfMissingSkillPublic] = Field(default_factory=list)
    estimated_hours: int
    estimated_weeks: int
    path_skills: list[str] = Field(default_factory=list)
    required_projects: list[str] = Field(default_factory=list)
    mentor_count: int
    mentor_names: list[str] = Field(default_factory=list)


class WhatIfSimulationPublic(ORMModel):
    current_target: GapTargetPublic | None = None
    hours_per_week: int
    disclaimer: str
    scenarios: list[WhatIfScenarioPublic] = Field(default_factory=list)


class WhatIfRequest(ORMModel):
    role_ids: list[UUID] = Field(min_length=1, max_length=4)
