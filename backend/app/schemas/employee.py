from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.enums import LearningFormat
from app.schemas.common import ORMModel
from app.schemas.profile import EducationPublic, ExperiencePublic
from app.schemas.role import TargetRoleSummary
from app.schemas.skill import SkillPublic


class LearningPreferences(BaseModel):
    formats: list[LearningFormat] = Field(default_factory=list)
    pace: str | None = Field(default=None, max_length=50)


class EmployeeUpdate(BaseModel):
    job_title: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    years_experience: Decimal | None = Field(default=None, ge=0, le=60)
    available_hours_per_week: int | None = Field(default=None, ge=1, le=80)
    learning_preferences: LearningPreferences | None = None
    target_role_id: UUID | None = None


class EmployeeSkillCreate(BaseModel):
    skill_id: UUID
    current_level: Decimal = Field(ge=1, le=5)

    @field_validator("current_level")
    @classmethod
    def one_decimal(cls, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.1"))


class EmployeeSkillUpdate(BaseModel):
    current_level: Decimal = Field(ge=1, le=5)

    @field_validator("current_level")
    @classmethod
    def one_decimal(cls, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.1"))


class EmployeeSkillPublic(ORMModel):
    id: UUID
    current_level: Decimal
    confidence: Decimal
    source_type: str
    inferred: bool = False
    skill: SkillPublic


class CompletenessBreakdown(BaseModel):
    job_title: bool
    department: bool
    years_experience: bool
    education: bool
    experience: bool
    skills: bool
    target_role: bool
    learning_preferences: bool


class CompletenessScore(BaseModel):
    score: float = Field(ge=0, le=1)
    completed_items: int
    total_items: int
    breakdown: CompletenessBreakdown


class EmployeePublic(ORMModel):
    id: UUID
    user_id: UUID
    full_name: str
    email: str
    role: str
    job_title: str | None = None
    department: str | None = None
    years_experience: Decimal | None = None
    available_hours_per_week: int
    learning_preferences: dict | None = None
    target_role: TargetRoleSummary | None = None
    completeness: CompletenessScore
    education: list[EducationPublic] = []
    experience: list[ExperiencePublic] = []
    skills: list[EmployeeSkillPublic] = []
