from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.exceptions import ValidationAppError
from app.core.paths import ensure_repo_on_path
from app.models import (
    AssistantTurn,
    Course,
    LearningPath,
    LearningPathStep,
    Mentor,
    PracticePairing,
    Project,
    RecommendationResult,
    Skill,
    User,
)
from app.schemas.assistant import AssistantAnswerPublic, AssistantSourcePublic
from app.services.assessment_service import assessment_service
from app.services.catalog_service import catalog_service
from app.services.gap_service import gap_service
from app.services.profile_service import profile_service
from app.services.resource_service import resource_service
from app.services.skill_profile_service import skill_profile_service

ensure_repo_on_path()

from llm.assistant import answer as grounded_answer  # noqa: E402
from llm.client import complete, grounded_prompt  # noqa: E402
from llm.retrieve import Chunk  # noqa: E402

# Chunk.facts drive plain-language answers; retrieve.py lives outside backend/.
# Reload this module after llm/assistant.py or .env LLM changes.
# NIM gpt-oss-20b often needs a 60s complete() timeout.


class AssistantService:
    def ask(self, db: Session, user: User, question: str) -> AssistantAnswerPublic:
        cleaned = question.strip()
        if len(cleaned) < 3:
            raise ValidationAppError("Enter a question with at least 3 characters")
        employee = profile_service.get_employee_for_user(db, user)
        chunks = _context_chunks(db, user)
        result = grounded_answer(cleaned, chunks)
        used_llm = False
        if settings.llm_enabled and settings.llm_api_key and not result.unavailable:
            prompt = grounded_prompt(
                cleaned,
                [item.text for item in result.sources if item.text],
                draft=result.text,
            )
            rewritten = complete(
                prompt,
                enabled=True,
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                timeout=settings.llm_timeout_seconds,
            )
            if rewritten and _stays_grounded(
                rewritten, result.sources, draft=result.text
            ):
                result.text = rewritten.strip()
                result.used_llm = True
                used_llm = True
        sources_payload = [
            {
                "source_type": item.source_type,
                "title": item.title,
                "text": item.text,
                "source_id": item.source_id,
            }
            for item in result.sources
        ]
        row = AssistantTurn(
            employee_id=employee.id,
            question=cleaned,
            answer=result.text,
            sources=sources_payload,
            used_llm=used_llm,
            unavailable=result.unavailable,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _to_public(row)

    def list_turns(
        self, db: Session, user: User, limit: int = 20
    ) -> list[AssistantAnswerPublic]:
        employee = profile_service.get_employee_for_user(db, user)
        rows = db.scalars(
            select(AssistantTurn)
            .where(AssistantTurn.employee_id == employee.id)
            .order_by(AssistantTurn.created_at.desc())
            .limit(max(1, min(limit, 50)))
        ).all()
        return [_to_public(row) for row in reversed(list(rows))]


assistant_service = AssistantService()


def _context_chunks(db: Session, user: User) -> list[Chunk]:
    chunks: list[Chunk] = []
    chunks.extend(_profile_chunks(db, user))
    chunks.extend(_skill_chunks(db, user))
    chunks.extend(_gap_chunks(db, user))
    chunks.extend(_path_chunks(db, user))
    chunks.extend(_assessment_chunks(db, user))
    chunks.extend(_recommendation_chunks(db, user))
    chunks.extend(_practice_chunks(db, user))
    chunks.extend(_catalog_chunks(db))
    return chunks


def _profile_chunks(db: Session, user: User) -> list[Chunk]:
    employee = profile_service.get_employee_for_user(db, user)
    role = employee.target_role.title if employee.target_role is not None else None
    hours = str(employee.available_hours_per_week)
    if role is None:
        text = "No target role is selected."
        facts = _compact(hours=hours)
    else:
        text = (
            f"Target role is {role}. "
            f"Weekly learning hours = {employee.available_hours_per_week}."
        )
        facts = _compact(target=role, hours=hours)
    return [
        Chunk(source_type="PROFILE", title="Learner profile", text=text, facts=facts)
    ]


def _skill_chunks(db: Session, user: User) -> list[Chunk]:
    profile = skill_profile_service.get_profile(db, user)
    chunks: list[Chunk] = []
    for item in profile.skills:
        text = (
            f"{item.skill.canonical_name} estimated level "
            f"{float(item.current_level):.1f}/5, confidence "
            f"{float(item.confidence):.2f}."
        )
        chunks.append(
            Chunk(
                source_type="PROFICIENCY",
                title=item.skill.canonical_name,
                text=text,
                source_id=str(item.skill.id),
                facts=_compact(
                    skill=item.skill.canonical_name,
                    current=f"{float(item.current_level):.1f}",
                    confidence=f"{float(item.confidence):.2f}",
                ),
            )
        )
    return chunks


def _gap_chunks(db: Session, user: User) -> list[Chunk]:
    try:
        analysis = gap_service.analyze(db, user)
    except ValidationAppError:
        return []
    open_gaps = [item for item in analysis.gaps if item.priority != "NONE"]
    if not open_gaps:
        return [
            Chunk(
                source_type="GAP",
                title=analysis.target.title,
                text=f"No open skill gaps for {analysis.target.title}.",
            )
        ]
    chunks: list[Chunk] = []
    summary = ", ".join(
        f"{item.skill.canonical_name} ({item.priority.lower()})"
        for item in open_gaps[:5]
    )
    chunks.append(
        Chunk(
            source_type="GAP",
            title=analysis.target.title,
            text=f"Open skill gaps for {analysis.target.title}: {summary}.",
            facts=_compact(role=analysis.target.title, summary=summary),
        )
    )
    for item in open_gaps:
        skill_name = item.skill.canonical_name
        current = f"{float(item.current_level):.1f}"
        required = f"{float(item.required_level):.0f}"
        priority = item.priority.title()
        chunks.append(
            Chunk(
                source_type="GAP",
                title=skill_name,
                text=(
                    f"{skill_name} is an open skill gap for "
                    f"{analysis.target.title}. Current "
                    f"{current}/5, required {required}/5, priority {priority}."
                ),
                source_id=str(item.skill.id),
                facts=_compact(
                    skill=skill_name,
                    role=analysis.target.title,
                    current=current,
                    required=required,
                    priority=priority,
                ),
            )
        )
    return chunks


def _path_chunks(db: Session, user: User) -> list[Chunk]:
    employee = profile_service.get_employee_for_user(db, user)
    path = (
        db.scalars(
            select(LearningPath)
            .options(
                joinedload(LearningPath.steps)
                .joinedload(LearningPathStep.skill)
                .joinedload(Skill.aliases),
                joinedload(LearningPath.steps).joinedload(LearningPathStep.course),
                joinedload(LearningPath.steps).joinedload(LearningPathStep.project),
            )
            .where(LearningPath.employee_id == employee.id)
            .order_by(LearningPath.created_at.desc())
        )
        .unique()
        .first()
    )
    if path is None:
        return []
    steps = sorted(path.steps, key=lambda item: item.position)
    if not steps:
        return []
    names = [step.skill.canonical_name for step in steps]
    start = names[0]
    sequence = " → ".join(names[:8])
    hours = str(path.hours_per_week)
    weeks = str(path.estimated_weeks)
    overview_text = (
        f"Stored learning path for {path.target_title} starts with {start}. "
        f"Sequence: {sequence}. "
        f"{hours} hours/week for about {weeks} weeks."
    )
    chunks = [
        Chunk(
            source_type="PATH_OVERVIEW",
            title="Learning path",
            text=overview_text,
            source_id=str(path.id),
            facts=_compact(
                target=path.target_title,
                start=start,
                sequence=sequence,
                hours_per_week=hours,
                weeks=weeks,
            ),
        )
    ]
    for step in steps[:8]:
        skill_name = step.skill.canonical_name
        course = None if step.course is None else step.course.title
        project = None if step.project is None else step.project.title
        weeks_label = _weeks_label(step.week_start, step.week_end)
        hours_label = f"{step.duration_hours} hours" if step.duration_hours else ""
        extra = f" Course: {course}." if course else ""
        extra += f" Project: {project}." if project else ""
        chunks.append(
            Chunk(
                source_type="PATH",
                title=skill_name,
                text=(
                    f"Position {step.position}: {skill_name}. " f"{step.reason}{extra}"
                ),
                source_id=str(step.id),
                facts=_compact(
                    skill=skill_name,
                    reason=step.reason,
                    course=course,
                    project=project,
                    weeks=weeks_label,
                    hours=hours_label,
                    position=str(step.position),
                ),
            )
        )
    return chunks


def _assessment_chunks(db: Session, user: User) -> list[Chunk]:
    chunks: list[Chunk] = []
    for item in assessment_service.list_for_user(db, user):
        if item.latest_percent is None:
            continue
        percent = round(item.latest_percent * 100)
        result = "passed" if item.latest_passed else "not passed"
        chunks.append(
            Chunk(
                source_type="ASSESSMENT",
                title=item.skill.canonical_name,
                text=f"{item.skill.canonical_name} quiz {percent}% ({result}).",
                source_id=str(item.id),
                facts=_compact(
                    skill=item.skill.canonical_name,
                    percent=str(percent),
                    result=result,
                ),
            )
        )
    return chunks


def _recommendation_chunks(db: Session, user: User) -> list[Chunk]:
    employee = profile_service.get_employee_for_user(db, user)
    latest = db.scalars(
        select(RecommendationResult)
        .where(RecommendationResult.employee_id == employee.id)
        .order_by(RecommendationResult.created_at.desc())
        .limit(1)
    ).first()
    if latest is None:
        return []
    rows = db.scalars(
        select(RecommendationResult)
        .where(
            RecommendationResult.employee_id == employee.id,
            RecommendationResult.batch_id == latest.batch_id,
        )
        .order_by(RecommendationResult.rank)
    ).all()
    chunks: list[Chunk] = []
    for row in rows:
        title = _resource_title(db, row.resource_type, row.resource_id)
        mapped = _explanation_facts(row.explanation)
        if title:
            mapped["title"] = title
        mapped["rank"] = mapped.get("rank") or str(row.rank)
        verbalization = mapped.get("verbalization") or row.reason
        gap = mapped.get("gap")
        priority = mapped.get("priority")
        if title and gap:
            text = (
                f"{title} is stored at rank {mapped['rank']} because it "
                f"addresses the {gap} gap"
            )
            if priority:
                text += f" ({priority.lower()})"
            text += "."
        else:
            text = f"{title}: {verbalization}" if title else verbalization
        chunks.append(
            Chunk(
                source_type="RECOMMENDATION",
                title=title or row.reason[:80],
                text=text,
                source_id=str(row.id),
                facts=_compact(**mapped),
            )
        )
    return chunks


def _practice_chunks(db: Session, user: User) -> list[Chunk]:
    employee = profile_service.get_employee_for_user(db, user)
    latest = db.scalars(
        select(PracticePairing)
        .where(PracticePairing.employee_id == employee.id)
        .order_by(PracticePairing.created_at.desc())
        .limit(1)
    ).first()
    if latest is None:
        return []
    rows = (
        db.scalars(
            select(PracticePairing)
            .options(
                joinedload(PracticePairing.skill),
                joinedload(PracticePairing.course),
                joinedload(PracticePairing.project),
            )
            .where(
                PracticePairing.employee_id == employee.id,
                PracticePairing.batch_id == latest.batch_id,
            )
            .order_by(PracticePairing.rank)
        )
        .unique()
        .all()
    )
    chunks: list[Chunk] = []
    for row in rows:
        project_title = row.project.title
        description = row.project.description
        chunks.append(
            Chunk(
                source_type="PRACTICE",
                title=row.skill.canonical_name,
                text=(
                    f"Learn {row.course.title}, then practice {project_title} "
                    f"for {row.skill.canonical_name}."
                ),
                source_id=str(row.id),
                facts=_compact(
                    skill=row.skill.canonical_name,
                    course=row.course.title,
                    title=project_title,
                    project=project_title,
                    description=description,
                ),
            )
        )
    return chunks


def _catalog_chunks(db: Session) -> list[Chunk]:
    chunks: list[Chunk] = []
    for skill in catalog_service.list_skills(db):
        aliases = ", ".join(skill.aliases[:4])
        alias_bit = f" Also called {aliases}." if aliases else ""
        description = skill.description or "No catalog description."
        facts = _compact(
            name=skill.canonical_name,
            canonical=skill.canonical_name,
            description=description,
            aliases=aliases,
        )
        titles = [skill.canonical_name]
        if skill.name not in titles:
            titles.append(skill.name)
        for alias in skill.aliases[:4]:
            if alias not in titles:
                titles.append(alias)
        for title in titles:
            chunks.append(
                Chunk(
                    source_type="SKILL",
                    title=title,
                    text=f"{skill.canonical_name}: {description}{alias_bit}",
                    source_id=str(skill.id),
                    facts=facts,
                )
            )
    for course in resource_service.list_courses(db):
        skills = ", ".join(item.skill.canonical_name for item in course.skills[:4])
        chunks.append(
            Chunk(
                source_type="COURSE",
                title=course.title,
                text=f"{course.title}: {course.description} Skills: {skills}.",
                source_id=str(course.id),
                facts=_compact(
                    title=course.title,
                    description=course.description,
                    skills=skills,
                ),
            )
        )
    for project in resource_service.list_projects(db):
        skills = ", ".join(item.skill.canonical_name for item in project.skills[:4])
        chunks.append(
            Chunk(
                source_type="PROJECT",
                title=project.title,
                text=f"{project.title}: {project.description} Skills: {skills}.",
                source_id=str(project.id),
                facts=_compact(
                    title=project.title,
                    description=project.description,
                    skills=skills,
                ),
            )
        )
    return chunks


def _resource_title(db: Session, resource_type: str, resource_id: UUID) -> str:
    if resource_type == "COURSE":
        row = db.get(Course, resource_id)
        return "" if row is None else row.title
    if resource_type == "PROJECT":
        row = db.get(Project, resource_id)
        return "" if row is None else row.title
    if resource_type == "MENTOR":
        row = db.get(Mentor, resource_id)
        return "" if row is None else row.name
    return ""


def _stays_grounded(text: str, sources: list[Chunk], draft: str = "") -> bool:
    allowed_parts = [draft]
    for item in sources:
        allowed_parts.append(item.title)
        allowed_parts.append(item.text)
        allowed_parts.extend(item.facts.values())
    allowed = " ".join(allowed_parts).lower()
    tokens = [
        token for token in text.lower().replace(".", " ").split() if len(token) > 4
    ]
    if not tokens:
        return True
    hits = sum(1 for token in tokens if token in allowed)
    return hits / len(tokens) >= 0.6


def _compact(**values: object) -> dict[str, str]:
    packed: dict[str, str] = {}
    for key, value in values.items():
        if value is None:
            continue
        text = str(value).strip()
        if text:
            packed[key] = text
    return packed


def _weeks_label(start: int, end: int) -> str:
    if start == end:
        return f"week {start}"
    return f"weeks {start}–{end}"


def _explanation_facts(explanation: object) -> dict[str, str]:
    if not isinstance(explanation, dict):
        return {}
    mapped: dict[str, str] = {}
    verbal = explanation.get("verbalization")
    if verbal:
        mapped["verbalization"] = str(verbal)
    rows = explanation.get("facts")
    if not isinstance(rows, list):
        return mapped
    for item in rows:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        if not key:
            continue
        value = item.get("value")
        text = str(item.get("text") or "").strip()
        if key == "semantic":
            try:
                if float(value) < 0.2:
                    continue
            except (TypeError, ValueError):
                continue
        if key == "preference" and "format fit" in text.lower():
            continue
        if key in {"gap", "priority", "rank"} and value is not None:
            mapped[key] = str(value)
        elif text:
            mapped[key] = text
    return mapped


def _to_public(row: AssistantTurn) -> AssistantAnswerPublic:
    sources = [
        AssistantSourcePublic.model_validate(item)
        for item in (row.sources or [])
        if isinstance(item, dict)
    ]
    return AssistantAnswerPublic(
        id=row.id,
        question=row.question,
        answer=row.answer,
        sources=sources,
        used_llm=row.used_llm,
        unavailable=row.unavailable,
    )
