from __future__ import annotations

import json
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.paths import repo_root
from app.models import (
    Assessment,
    AssessmentQuestion,
    Course,
    CourseSkill,
    Mentor,
    MentorSkill,
    Project,
    ProjectSkill,
    RoleSkill,
    Skill,
    SkillAlias,
    TargetRole,
)

logger = get_logger()

SKILL_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")
ROLE_NS = uuid.UUID("22222222-2222-2222-2222-222222222222")
COURSE_NS = uuid.UUID("33333333-3333-3333-3333-333333333333")
PROJECT_NS = uuid.UUID("44444444-4444-4444-4444-444444444444")
MENTOR_NS = uuid.UUID("55555555-5555-5555-5555-555555555555")
ASSESSMENT_NS = uuid.UUID("66666666-6666-6666-6666-666666666666")
QUESTION_NS = uuid.UUID("77777777-7777-7777-7777-777777777777")
TAXONOMY_PATH = repo_root() / "datasets" / "processed" / "skill_taxonomy.json"
RESOURCE_PATH = repo_root() / "datasets" / "processed" / "resource_catalog.json"
ASSESSMENT_PATH = repo_root() / "datasets" / "processed" / "assessments.json"


def catalog_skill_id(name: str) -> uuid.UUID:
    return uuid.uuid5(SKILL_NS, name)


def catalog_role_id(title: str) -> uuid.UUID:
    return uuid.uuid5(ROLE_NS, title)


def catalog_mentor_id(name: str) -> uuid.UUID:
    return uuid.uuid5(MENTOR_NS, name)


def catalog_course_id(title: str) -> uuid.UUID:
    return uuid.uuid5(COURSE_NS, title)


def catalog_project_id(title: str) -> uuid.UUID:
    return uuid.uuid5(PROJECT_NS, title)


def catalog_assessment_id(skill_name: str) -> uuid.UUID:
    return uuid.uuid5(ASSESSMENT_NS, skill_name)


def catalog_question_id(skill_name: str, position: int) -> uuid.UUID:
    return uuid.uuid5(QUESTION_NS, f"{skill_name}:{position}")


def load_taxonomy(path: Path | None = None) -> list[dict[str, Any]]:
    taxonomy_path = path or TAXONOMY_PATH
    payload = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    skills = payload.get("skills")
    if not isinstance(skills, list) or not skills:
        raise ValueError(f"Taxonomy file has no skills: {taxonomy_path}")
    return skills


def load_resource_catalog(path: Path | None = None) -> dict[str, Any]:
    catalog_path = path or RESOURCE_PATH
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Resource catalog is not an object: {catalog_path}")
    return payload


ROLES: list[tuple[str, str, str]] = [
    (
        "Software Engineer",
        "Software Engineering",
        "Builds and maintains software systems.",
    ),
    (
        "Backend Engineer",
        "Software Engineering",
        "Designs server-side services and APIs.",
    ),
    ("Data Analyst", "Data", "Analyzes data to support decisions."),
    ("Data Engineer", "Data", "Builds data pipelines and warehouses."),
    ("Data Scientist", "AI/ML", "Applies statistics and ML to business problems."),
    ("ML Engineer", "AI/ML", "Productionizes machine learning systems."),
    ("AI Engineer", "AI/ML", "Builds applied AI products."),
    ("NLP Engineer", "AI/ML", "Specializes in language technologies."),
    ("GenAI Engineer", "AI/ML", "Builds generative AI and RAG systems."),
    ("MLOps Engineer", "AI/ML", "Operates ML infrastructure and deployment."),
]

# importance 1.0 = required, 0.6 = preferred (PRD §6.3 starting values)
ROLE_SKILLS: dict[str, list[tuple[str, int, str, str]]] = {
    "Software Engineer": [
        ("Python", 4, "1.00", "0.90"),
        ("Git", 4, "1.00", "0.80"),
        ("SQL", 3, "0.60", "0.50"),
        ("REST APIs", 4, "1.00", "0.80"),
        ("System Design", 3, "0.60", "0.70"),
    ],
    "Backend Engineer": [
        ("Python", 4, "1.00", "0.90"),
        ("FastAPI", 4, "1.00", "0.80"),
        ("PostgreSQL", 4, "1.00", "0.85"),
        ("REST APIs", 4, "1.00", "0.80"),
        ("Docker", 3, "0.60", "0.60"),
    ],
    "Data Analyst": [
        ("SQL", 4, "1.00", "0.95"),
        ("Data Analysis", 4, "1.00", "0.90"),
        ("Statistics", 3, "1.00", "0.80"),
        ("Data Visualization", 4, "1.00", "0.70"),
        ("Python", 3, "0.60", "0.50"),
    ],
    "Data Engineer": [
        ("Python", 4, "1.00", "0.85"),
        ("SQL", 4, "1.00", "0.90"),
        ("PostgreSQL", 4, "1.00", "0.80"),
        ("Docker", 3, "0.60", "0.60"),
        ("AWS", 3, "0.60", "0.70"),
    ],
    "Data Scientist": [
        ("Python", 4, "1.00", "0.90"),
        ("Statistics", 4, "1.00", "0.95"),
        ("Machine Learning", 4, "1.00", "0.90"),
        ("Pandas", 4, "1.00", "0.70"),
        ("Data Visualization", 3, "0.60", "0.50"),
    ],
    "ML Engineer": [
        ("Python", 4, "1.00", "0.95"),
        ("Machine Learning", 4, "1.00", "0.95"),
        ("Deep Learning", 4, "1.00", "0.85"),
        ("MLOps", 3, "0.60", "0.80"),
        ("Docker", 3, "0.60", "0.60"),
        ("Statistics", 3, "0.60", "0.70"),
    ],
    "AI Engineer": [
        ("Python", 4, "1.00", "0.90"),
        ("Machine Learning", 4, "1.00", "0.85"),
        ("LLMs", 4, "1.00", "0.90"),
        ("RAG", 3, "0.60", "0.80"),
        ("REST APIs", 3, "0.60", "0.50"),
    ],
    "NLP Engineer": [
        ("Python", 4, "1.00", "0.90"),
        ("NLP", 4, "1.00", "0.95"),
        ("Transformers", 4, "1.00", "0.90"),
        ("LLMs", 4, "1.00", "0.85"),
        ("Machine Learning", 3, "0.60", "0.70"),
    ],
    "GenAI Engineer": [
        ("Python", 4, "1.00", "0.90"),
        ("LLMs", 4, "1.00", "0.95"),
        ("RAG", 4, "1.00", "0.95"),
        ("Vector Databases", 4, "1.00", "0.85"),
        ("Prompt Engineering", 4, "1.00", "0.70"),
        ("Transformers", 3, "0.60", "0.80"),
    ],
    "MLOps Engineer": [
        ("Python", 4, "1.00", "0.80"),
        ("MLOps", 4, "1.00", "0.95"),
        ("Docker", 4, "1.00", "0.85"),
        ("Kubernetes", 4, "1.00", "0.80"),
        ("CI/CD", 4, "1.00", "0.80"),
        ("Model Deployment", 4, "1.00", "0.90"),
    ],
}


def seed_catalog(db: Session) -> None:
    from app.core.paths import ensure_repo_on_path

    ensure_repo_on_path()
    from ml.skill_extraction.normalizer import normalize_skill_text

    skill_map: dict[str, Skill] = {}
    claimed_aliases: dict[str, str] = {}

    for item in load_taxonomy():
        name = str(item["name"])
        canonical_name = str(item["canonical_name"])
        category = str(item["category"])
        description = item.get("description")
        difficulty = int(item.get("difficulty") or 3)
        aliases = [str(alias) for alias in item.get("aliases") or []]

        skill = db.scalar(select(Skill).where(Skill.name == name))
        if skill is None:
            skill = Skill(
                id=catalog_skill_id(name),
                name=name,
                canonical_name=canonical_name,
                category=category,
                description=description,
                difficulty=difficulty,
            )
            db.add(skill)
            db.flush()
        else:
            skill.canonical_name = canonical_name
            skill.category = category
            skill.description = description
            skill.difficulty = difficulty

        skill_map[name] = skill

        existing_normalized = {
            row.normalized_alias: row
            for row in db.scalars(
                select(SkillAlias).where(SkillAlias.skill_id == skill.id)
            ).all()
        }
        for alias in aliases:
            normalized = normalize_skill_text(alias)
            if not normalized or normalized in claimed_aliases:
                continue
            claimed_aliases[normalized] = name
            if normalized in existing_normalized:
                existing_normalized[normalized].alias = alias
                continue
            taken = db.scalar(
                select(SkillAlias).where(SkillAlias.normalized_alias == normalized)
            )
            if taken is not None:
                if taken.skill_id != skill.id:
                    logger.warning(
                        "skipping persisted alias collision %s for %s", alias, name
                    )
                continue
            db.add(
                SkillAlias(
                    skill_id=skill.id,
                    alias=alias,
                    normalized_alias=normalized,
                )
            )

    db.flush()

    for title, category, description in ROLES:
        role = db.scalar(select(TargetRole).where(TargetRole.title == title))
        if role is None:
            role = TargetRole(
                id=catalog_role_id(title),
                title=title,
                category=category,
                description=description,
            )
            db.add(role)
            db.flush()
        for skill_name, level, importance, criticality in ROLE_SKILLS.get(title, []):
            skill = skill_map[skill_name]
            existing = db.scalar(
                select(RoleSkill).where(
                    RoleSkill.role_id == role.id, RoleSkill.skill_id == skill.id
                )
            )
            if existing is None:
                db.add(
                    RoleSkill(
                        role_id=role.id,
                        skill_id=skill.id,
                        required_level=level,
                        importance=Decimal(importance),
                        criticality=Decimal(criticality),
                    )
                )

    seed_resources(db, skill_map)
    seed_assessments(db, skill_map)


def seed_resources(db: Session, skill_map: dict[str, Skill]) -> None:
    catalog = load_resource_catalog()
    for item in catalog.get("courses") or []:
        _upsert_course(db, skill_map, item)
    for item in catalog.get("projects") or []:
        _upsert_project(db, skill_map, item)
    for item in catalog.get("mentors") or []:
        _upsert_mentor(db, skill_map, item)


def _skill_rows(
    skill_map: dict[str, Skill], items: list[dict[str, Any]], owner: str
) -> list[tuple[Skill, int]]:
    rows: list[tuple[Skill, int]] = []
    seen: set[str] = set()
    for raw in items:
        name = str(raw.get("name") or "")
        if not name or name in seen:
            continue
        skill = skill_map.get(name)
        if skill is None:
            logger.warning("skipping unknown catalog skill %s on %s", name, owner)
            continue
        seen.add(name)
        level = int(raw.get("level") or 3)
        rows.append((skill, max(1, min(5, level))))
    return rows


def _upsert_course(
    db: Session, skill_map: dict[str, Skill], item: dict[str, Any]
) -> None:
    title = str(item["title"])
    course = db.scalar(select(Course).where(Course.title == title))
    if course is None:
        course = Course(id=catalog_course_id(title), title=title)
        db.add(course)
    course.provider = str(item["provider"])
    course.description = str(item["description"])
    course.difficulty = int(item["difficulty"])
    course.duration_hours = int(item["duration_hours"])
    course.format = str(item["format"])
    course.url = str(item["url"])
    course.rating = Decimal(str(item["rating"]))
    db.flush()
    db.execute(delete(CourseSkill).where(CourseSkill.course_id == course.id))
    for skill, level in _skill_rows(skill_map, item.get("skills") or [], title):
        db.add(CourseSkill(course_id=course.id, skill_id=skill.id, level=level))


def _upsert_project(
    db: Session, skill_map: dict[str, Skill], item: dict[str, Any]
) -> None:
    title = str(item["title"])
    project = db.scalar(select(Project).where(Project.title == title))
    if project is None:
        project = Project(id=catalog_project_id(title), title=title)
        db.add(project)
    project.description = str(item["description"])
    project.difficulty = int(item["difficulty"])
    project.duration_hours = int(item["duration_hours"])
    project.technologies = list(item.get("technologies") or [])
    project.deliverables = list(item.get("deliverables") or [])
    db.flush()
    db.execute(delete(ProjectSkill).where(ProjectSkill.project_id == project.id))
    for skill, level in _skill_rows(skill_map, item.get("skills") or [], title):
        db.add(ProjectSkill(project_id=project.id, skill_id=skill.id, level=level))


def _upsert_mentor(
    db: Session, skill_map: dict[str, Skill], item: dict[str, Any]
) -> None:
    name = str(item["name"])
    mentor = db.scalar(select(Mentor).where(Mentor.name == name))
    if mentor is None:
        mentor = Mentor(id=catalog_mentor_id(name), name=name)
        db.add(mentor)
    mentor.title = str(item["title"])
    mentor.bio = str(item["bio"])
    mentor.years_experience = int(item["years_experience"])
    mentor.available_hours_per_month = int(item["available_hours_per_month"])
    mentor.max_mentees = int(item.get("max_mentees") or 2)
    mentor.domains = list(item.get("domains") or [])
    db.flush()
    db.execute(delete(MentorSkill).where(MentorSkill.mentor_id == mentor.id))
    for skill, level in _skill_rows(skill_map, item.get("skills") or [], name):
        db.add(MentorSkill(mentor_id=mentor.id, skill_id=skill.id, level=level))


def load_assessments(path: Path | None = None) -> list[dict[str, Any]]:
    assessment_path = path or ASSESSMENT_PATH
    payload = json.loads(assessment_path.read_text(encoding="utf-8"))
    rows = payload.get("assessments")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"Assessment file has no quizzes: {assessment_path}")
    return rows


def seed_assessments(db: Session, skill_map: dict[str, Skill]) -> None:
    from app.core.config import settings

    for item in load_assessments():
        skill_name = str(item.get("skill") or "")
        skill = skill_map.get(skill_name)
        if skill is None:
            logger.warning("skipping assessment for unknown skill %s", skill_name)
            continue
        quiz = db.scalar(select(Assessment).where(Assessment.skill_id == skill.id))
        if quiz is None:
            quiz = Assessment(id=catalog_assessment_id(skill_name), skill_id=skill.id)
            db.add(quiz)
        quiz.title = str(item.get("title") or f"{skill.canonical_name} quiz")
        quiz.assessment_type = str(item.get("type") or "MCQ")
        quiz.pass_score = Decimal(
            str(item.get("pass_score") or settings.assessment_pass_score)
        )
        db.flush()
        db.execute(
            delete(AssessmentQuestion).where(
                AssessmentQuestion.assessment_id == quiz.id
            )
        )
        for position, question in enumerate(item.get("questions") or [], start=1):
            choices = [str(choice) for choice in question.get("choices") or []]
            correct_index = int(question["correct_index"])
            if not choices or correct_index < 0 or correct_index >= len(choices):
                logger.warning("skipping bad question %s #%s", skill_name, position)
                continue
            db.add(
                AssessmentQuestion(
                    id=catalog_question_id(skill_name, position),
                    assessment_id=quiz.id,
                    position=position,
                    prompt=str(question["prompt"]),
                    choices=choices,
                    correct_index=correct_index,
                    explanation=question.get("explanation"),
                )
            )
