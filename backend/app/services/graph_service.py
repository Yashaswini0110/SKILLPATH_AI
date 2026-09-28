from __future__ import annotations

import json
from functools import lru_cache
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.exceptions import UnavailableError, ValidationAppError
from app.core.paths import ensure_repo_on_path, repo_root
from app.models import (
    Course,
    CourseSkill,
    Employee,
    EmployeeSkill,
    Mentor,
    MentorSkill,
    Project,
    ProjectSkill,
    RoleSkill,
    Skill,
    TargetRole,
    User,
)
from app.schemas.graph import (
    GraphEdgePublic,
    GraphGapMentorPublic,
    GraphRelatedSkillPublic,
    GraphSkillViewPublic,
    GraphStatusPublic,
)
from app.schemas.skill import SkillPublic
from app.services.catalog_service import catalog_service
from app.services.gap_service import gap_service
from app.services.resource_service import resource_service
from app.services.skill_view import to_skill_public

ensure_repo_on_path()

from knowledge_graph.client import GraphClient  # noqa: E402
from knowledge_graph.cycle import (  # noqa: E402
    ancestor_subgraph,
    assert_acyclic,
    find_cycles,
    topological_chain,
)
from knowledge_graph.queries import (  # noqa: E402
    courses_teaching,
    immediate_prerequisites,
    mentors_for_skill,
    mentors_for_skills,
    node_counts,
    prerequisite_edges,
    projects_practicing,
    related_skills,
)
from knowledge_graph.seed import sync_graph  # noqa: E402

PREREQ_PATH = repo_root() / "datasets" / "processed" / "skill_prerequisites.json"


class GraphService:
    def __init__(self) -> None:
        self._client: GraphClient | None = None

    def client(self) -> GraphClient:
        if self._client is None:
            self._client = GraphClient(
                settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password
            )
        if not self._client.verify():
            raise UnavailableError(
                "Neo4j is not reachable. Start it with docker compose up -d neo4j."
            )
        return self._client

    def sync(self, db: Session) -> GraphStatusPublic:
        client = self.client()
        payload = _build_payload(db)
        sync_graph(client, payload)
        return self.status()

    def status(self) -> GraphStatusPublic:
        client = self.client()
        edges = prerequisite_edges(client)
        cycles = find_cycles(edges)
        return GraphStatusPublic(
            connected=True,
            acyclic=not cycles,
            cycle_count=len(cycles),
            cycles=cycles[:5],
            nodes=node_counts(client),
        )

    def skill_view(self, db: Session, skill_id: UUID) -> GraphSkillViewPublic:
        skill = catalog_service.get_skill(db, skill_id)
        client = self.client()
        key = str(skill_id)
        skills_by_id = _skill_index(db)
        prereqs = [
            skills_by_id[row["id"]]
            for row in immediate_prerequisites(client, key)
            if row["id"] in skills_by_id
        ]
        name_by_id = {str(item.id): item.name for item in skills_by_id.values()}
        id_by_name = {item.name: str(item.id) for item in skills_by_id.values()}
        named_edges = [
            (name_by_id[src], name_by_id[dst])
            for src, dst in prerequisite_edges(client)
            if src in name_by_id and dst in name_by_id
        ]
        chain_names = topological_chain(named_edges, skill.name)
        chain = [
            skills_by_id[id_by_name[name]] for name in chain_names if name in id_by_name
        ]
        layer_names, named_sub_edges = ancestor_subgraph(named_edges, skill.name)
        layers = [
            [skills_by_id[id_by_name[name]] for name in layer if name in id_by_name]
            for layer in layer_names
        ]
        dag_edges = [
            GraphEdgePublic(
                source=skills_by_id[id_by_name[src]],
                target=skills_by_id[id_by_name[dst]],
            )
            for src, dst in named_sub_edges
            if src in id_by_name and dst in id_by_name
        ]
        related = [
            GraphRelatedSkillPublic(
                skill=skills_by_id[row["id"]], relation=row["relation"]
            )
            for row in related_skills(client, key)
            if row["id"] in skills_by_id
        ]
        course_ids = {UUID(row["id"]) for row in courses_teaching(client, key)}
        project_ids = {UUID(row["id"]) for row in projects_practicing(client, key)}
        mentor_ids = {UUID(row["id"]) for row in mentors_for_skill(client, key)}
        return GraphSkillViewPublic(
            skill=skill,
            prerequisites=prereqs,
            chain=chain,
            layers=layers,
            edges=dag_edges,
            related=related,
            courses=[
                item
                for item in resource_service.list_courses(db)
                if item.id in course_ids
            ],
            projects=[
                item
                for item in resource_service.list_projects(db)
                if item.id in project_ids
            ],
            mentors=[
                item
                for item in resource_service.list_mentors(db)
                if item.id in mentor_ids
            ],
        )

    def gap_mentors(
        self,
        db: Session,
        user: User,
        role_id: UUID | None = None,
        job_description_id: UUID | None = None,
    ) -> list[GraphGapMentorPublic]:
        analysis = gap_service.analyze(
            db, user, role_id=role_id, job_description_id=job_description_id
        )
        open_gaps = [item for item in analysis.gaps if item.priority != "NONE"][
            : settings.rec_top_gap_count
        ]
        if not open_gaps:
            raise ValidationAppError("No open skill gaps to match mentors against")
        gap_ids = [str(item.skill.id) for item in open_gaps]
        client = self.client()
        rows = mentors_for_skills(client, gap_ids)
        mentors = {item.id: item for item in resource_service.list_mentors(db)}
        skills_by_id = _skill_index(db)
        results: list[GraphGapMentorPublic] = []
        for row in rows:
            mentor = mentors.get(UUID(row["id"]))
            if mentor is None:
                continue
            matched = [
                skills_by_id[skill_id]
                for skill_id in row["skill_ids"]
                if skill_id in skills_by_id
            ]
            results.append(GraphGapMentorPublic(mentor=mentor, matched_skills=matched))
        return results

    def try_sync(self, db: Session) -> None:
        try:
            self.sync(db)
        except UnavailableError:
            return


graph_service = GraphService()


def _skill_index(db: Session) -> dict[str, SkillPublic]:
    rows = db.scalars(select(Skill).options(joinedload(Skill.aliases))).unique().all()
    return {str(row.id): to_skill_public(row) for row in rows}


def _build_payload(db: Session) -> dict:
    skills = db.scalars(select(Skill).options(joinedload(Skill.aliases))).unique().all()
    by_name = {row.name: row for row in skills}
    spec = _prerequisite_spec()
    prereq_pairs = _named_pairs(by_name, spec["prerequisites"])
    assert_acyclic([(src.name, dst.name) for src, dst in prereq_pairs])

    courses = (
        db.scalars(
            select(Course).options(
                joinedload(Course.skills).joinedload(CourseSkill.skill)
            )
        )
        .unique()
        .all()
    )
    projects = (
        db.scalars(
            select(Project).options(
                joinedload(Project.skills).joinedload(ProjectSkill.skill)
            )
        )
        .unique()
        .all()
    )
    mentors = (
        db.scalars(
            select(Mentor).options(
                joinedload(Mentor.skills).joinedload(MentorSkill.skill)
            )
        )
        .unique()
        .all()
    )
    roles = (
        db.scalars(
            select(TargetRole).options(
                joinedload(TargetRole.role_skills).joinedload(RoleSkill.skill)
            )
        )
        .unique()
        .all()
    )
    employees = (
        db.scalars(
            select(Employee).options(
                joinedload(Employee.user),
                joinedload(Employee.skills).joinedload(EmployeeSkill.skill),
            )
        )
        .unique()
        .all()
    )
    return {
        "skills": [
            {
                "id": str(row.id),
                "name": row.name,
                "canonical_name": row.canonical_name,
                "category": row.category,
                "difficulty": row.difficulty,
            }
            for row in skills
        ],
        "courses": [{"id": str(row.id), "title": row.title} for row in courses],
        "projects": [{"id": str(row.id), "title": row.title} for row in projects],
        "mentors": [{"id": str(row.id), "name": row.name} for row in mentors],
        "roles": [{"id": str(row.id), "title": row.title} for row in roles],
        "employees": [
            {
                "id": str(row.id),
                "user_id": str(row.user_id),
                "full_name": row.user.full_name,
            }
            for row in employees
        ],
        "prerequisites": [_pair(src, dst) for src, dst in prereq_pairs],
        "related": [
            _pair(src, dst) for src, dst in _named_pairs(by_name, spec["related"])
        ],
        "complements": [
            _pair(src, dst) for src, dst in _named_pairs(by_name, spec["complements"])
        ],
        "teaches": [
            _pair_ids(link.course_id, link.skill_id)
            for course in courses
            for link in course.skills
        ],
        "practices": [
            _pair_ids(link.project_id, link.skill_id)
            for project in projects
            for link in project.skills
        ],
        "expert_in": [
            _pair_ids(link.mentor_id, link.skill_id)
            for mentor in mentors
            for link in mentor.skills
        ],
        "requires": [
            _pair_ids(link.role_id, link.skill_id)
            for role in roles
            for link in role.role_skills
        ],
        "has_skill": [
            _pair_ids(link.employee_id, link.skill_id)
            for employee in employees
            for link in employee.skills
        ],
    }


def _pair(src: Skill, dst: Skill) -> dict[str, str]:
    return {"src": str(src.id), "dst": str(dst.id)}


def _pair_ids(src: UUID, dst: UUID) -> dict[str, str]:
    return {"src": str(src), "dst": str(dst)}


def _named_pairs(
    by_name: dict[str, Skill], rows: list[list[str]]
) -> list[tuple[Skill, Skill]]:
    pairs: list[tuple[Skill, Skill]] = []
    for row in rows:
        if len(row) != 2:
            raise ValidationAppError("Prerequisite edges must have two skill names")
        src_name, dst_name = row
        if src_name not in by_name or dst_name not in by_name:
            missing = src_name if src_name not in by_name else dst_name
            raise ValidationAppError(
                f"Prerequisite dataset references unknown skill '{missing}'"
            )
        pairs.append((by_name[src_name], by_name[dst_name]))
    return pairs


@lru_cache(maxsize=1)
def _prerequisite_spec() -> dict:
    payload = json.loads(PREREQ_PATH.read_text(encoding="utf-8"))
    return {
        "prerequisites": payload.get("prerequisites", []),
        "related": payload.get("related", []),
        "complements": payload.get("complements", []),
    }
