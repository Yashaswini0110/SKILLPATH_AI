from __future__ import annotations

from pydantic import Field

from app.schemas.common import ORMModel
from app.schemas.resource import CoursePublic, MentorPublic, ProjectPublic
from app.schemas.skill import SkillPublic


class GraphRelatedSkillPublic(ORMModel):
    skill: SkillPublic
    relation: str


class GraphEdgePublic(ORMModel):
    source: SkillPublic
    target: SkillPublic


class GraphSkillViewPublic(ORMModel):
    skill: SkillPublic
    prerequisites: list[SkillPublic] = Field(default_factory=list)
    chain: list[SkillPublic] = Field(default_factory=list)
    layers: list[list[SkillPublic]] = Field(default_factory=list)
    edges: list[GraphEdgePublic] = Field(default_factory=list)
    related: list[GraphRelatedSkillPublic] = Field(default_factory=list)
    courses: list[CoursePublic] = Field(default_factory=list)
    projects: list[ProjectPublic] = Field(default_factory=list)
    mentors: list[MentorPublic] = Field(default_factory=list)


class GraphGapMentorPublic(ORMModel):
    mentor: MentorPublic
    matched_skills: list[SkillPublic] = Field(default_factory=list)


class GraphStatusPublic(ORMModel):
    connected: bool
    acyclic: bool
    cycle_count: int
    cycles: list[list[str]] = Field(default_factory=list)
    nodes: dict[str, int] = Field(default_factory=dict)
