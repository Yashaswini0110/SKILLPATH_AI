from decimal import Decimal
from uuid import UUID

from app.schemas.common import ORMModel
from app.schemas.skill import SkillPublic


class RequirementWeightsPublic(ORMModel):
    required: Decimal
    preferred: Decimal
    mentioned: Decimal


class RoleSkillPublic(ORMModel):
    skill: SkillPublic
    required_level: int
    importance: Decimal
    criticality: Decimal
    requirement: str


class TargetRoleSummary(ORMModel):
    id: UUID
    title: str
    category: str
    description: str | None = None


class TargetRolePublic(TargetRoleSummary):
    weights: RequirementWeightsPublic
    skills: list[RoleSkillPublic] = []
