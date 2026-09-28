from decimal import Decimal
from uuid import UUID

from app.schemas.common import ORMModel
from app.schemas.skill import SkillPublic


class ResourceSkillPublic(ORMModel):
    skill: SkillPublic
    level: int


class CoursePublic(ORMModel):
    id: UUID
    title: str
    provider: str
    description: str
    difficulty: int
    duration_hours: int
    format: str
    url: str
    rating: Decimal
    skills: list[ResourceSkillPublic] = []


class ProjectPublic(ORMModel):
    id: UUID
    title: str
    description: str
    difficulty: int
    duration_hours: int
    technologies: list[str] = []
    deliverables: list[str] = []
    skills: list[ResourceSkillPublic] = []


class MentorPublic(ORMModel):
    id: UUID
    name: str
    title: str
    bio: str
    years_experience: int
    available_hours_per_month: int
    max_mentees: int
    domains: list[str] = []
    skills: list[ResourceSkillPublic] = []
