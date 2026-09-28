from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationAppError
from app.core.paths import ensure_repo_on_path, repo_root
from app.models import RecommendationResult, User
from app.schemas.recommendation import (
    ExplanationPublic,
    MatchedGapSkillPublic,
    RecommendationItemPublic,
    RecommendationListPublic,
)
from app.schemas.resource import CoursePublic, MentorPublic, ProjectPublic
from app.services.gap_service import gap_service
from app.services.profile_service import profile_service
from app.services.resource_service import resource_service

ensure_repo_on_path()

from recommendation.baselines.content import content_score  # noqa: E402
from recommendation.baselines.popularity import popularity_score  # noqa: E402
from recommendation.baselines.semantic import (  # noqa: E402
    gap_summary,
    get_encoder,
    resource_text,
    semantic_score,
)
from recommendation.explain import explain_resource  # noqa: E402
from recommendation.hybrid.graph_data import load_taxonomy_graph  # noqa: E402
from recommendation.hybrid.signals import (  # noqa: E402
    collaborative_jaccard,
    difficulty_fit,
    kg_score,
    preference_fit,
    prerequisite_fit,
    weighted_score,
)

METHODS = {"POPULARITY", "CONTENT", "SEMANTIC", "KG", "HYBRID"}
RESOURCE_TYPES = {"COURSE", "PROJECT", "MENTOR"}
HYBRID_KEYS = (
    "semantic",
    "gap",
    "prerequisite",
    "difficulty",
    "preference",
    "collaborative",
    "kg",
)
ResourceRow = CoursePublic | ProjectPublic | MentorPublic


class RecommendationService:
    def recommend(
        self,
        db: Session,
        user: User,
        *,
        resource_type: str,
        method: str,
        role_id: UUID | None = None,
        job_description_id: UUID | None = None,
        limit: int | None = None,
    ) -> RecommendationListPublic:
        resource_type = resource_type.upper()
        method = method.upper()
        if resource_type not in RESOURCE_TYPES:
            raise ValidationAppError("resource_type must be COURSE, PROJECT, or MENTOR")
        if method not in METHODS:
            raise ValidationAppError(
                "method must be POPULARITY, CONTENT, SEMANTIC, KG, or HYBRID"
            )
        analysis = gap_service.analyze(
            db, user, role_id=role_id, job_description_id=job_description_id
        )
        top_gaps = [item for item in analysis.gaps if item.priority != "NONE"][
            : settings.rec_top_gap_count
        ]
        if not top_gaps:
            raise ValidationAppError("No open skill gaps to recommend against")
        catalog = _load_catalog(db, resource_type)
        gap_ids = {item.skill.id for item in top_gaps}
        skill_order = [item.skill.id for item in top_gaps]
        gap_weights = {item.skill.id: float(item.gap) for item in top_gaps}
        candidates = [row for row in catalog if gap_ids.intersection(_skill_ids(row))]
        employee = profile_service.get_employee_for_user(db, user)
        encoder_name: str | None = None
        encoder = None
        user_text = ""
        if method in {"SEMANTIC", "HYBRID"}:
            encoder = get_encoder(
                settings.rec_semantic_backend, settings.rec_semantic_model
            )
            encoder_name = encoder.name
            user_text = gap_summary(
                [
                    (item.skill.canonical_name, float(item.gap), item.priority)
                    for item in top_gaps
                ]
            )
        hybrid_w = settings.hybrid_weights() if method == "HYBRID" else None
        graph = _taxonomy_graph() if method in {"HYBRID", "KG"} else None
        open_names = {item.skill.canonical_name for item in top_gaps}
        emp_skill_ids = {row.skill_id for row in employee.skills}
        prefs = employee.learning_preferences or {}
        formats = [str(item) for item in prefs.get("formats") or []]
        scored: list[tuple[float, dict[str, Any], ResourceRow]] = []
        for row in candidates:
            levels = _skill_levels(row)
            matched = [item for item in top_gaps if item.skill.id in levels]
            pop = _popularity(row)
            content = content_score(skill_order, gap_weights, levels)
            semantic = 0.0
            if method in {"SEMANTIC", "HYBRID"} and encoder is not None:
                semantic = semantic_score(
                    user_text,
                    resource_text(
                        _title(row),
                        _description(row),
                        [item.skill.canonical_name for item in row.skills],
                    ),
                    encoder,
                )
            components: dict[str, Any] = {
                "popularity": round(pop, 4),
                "content": round(content, 4),
                "semantic": (
                    round(semantic, 4) if method in {"SEMANTIC", "HYBRID"} else None
                ),
            }
            if method == "POPULARITY":
                score = pop
            elif method == "CONTENT":
                score = content
            elif method == "SEMANTIC":
                score = semantic
            elif method == "KG":
                assert graph is not None
                taught = [item.skill.canonical_name for item in row.skills]
                score = kg_score(
                    taught, open_names, graph["ancestors"], graph["related"]
                )
                components["kg"] = round(score, 4)
            else:
                assert hybrid_w is not None and graph is not None
                taught = [item.skill.canonical_name for item in row.skills]
                learner = _learner_level(matched)
                hybrid_parts = {
                    "semantic": semantic,
                    "gap": content,
                    "prerequisite": prerequisite_fit(
                        taught, open_names, graph["parents"]
                    ),
                    "difficulty": difficulty_fit(_resource_difficulty(row), learner),
                    "preference": preference_fit(resource_type, _format(row), formats),
                    "collaborative": collaborative_jaccard(
                        emp_skill_ids, _skill_ids(row)
                    ),
                    "kg": kg_score(
                        taught, open_names, graph["ancestors"], graph["related"]
                    ),
                }
                score = weighted_score(hybrid_parts, hybrid_w)
                for key in HYBRID_KEYS:
                    components[key] = round(hybrid_parts[key], 4)
                components["weights"] = hybrid_w
            components["final"] = round(score, 4)
            scored.append(
                (
                    score,
                    {
                        "components": components,
                        "matched": matched,
                    },
                    row,
                )
            )
        scored.sort(key=lambda item: (-item[0], _title(item[2]).lower()))
        limit = limit or settings.rec_result_limit
        scored = scored[: max(1, min(limit, 50))]
        batch_id = uuid4()
        items: list[RecommendationItemPublic] = []
        for rank, (score, meta, row) in enumerate(scored, start=1):
            matched_payload = [
                MatchedGapSkillPublic(
                    skill=item.skill, gap=item.gap, priority=item.priority
                )
                for item in meta["matched"]
            ]
            explanation = explain_resource(
                rank=rank,
                matched=[
                    (item.skill.canonical_name, item.priority)
                    for item in meta["matched"]
                ],
                components=meta["components"],
                method=method,
                formats=formats,
            )
            explanation_payload = explanation.as_public()
            db.add(
                RecommendationResult(
                    batch_id=batch_id,
                    employee_id=employee.id,
                    resource_type=resource_type,
                    resource_id=row.id,
                    method=method,
                    rank=rank,
                    score=Decimal(str(round(score, 4))),
                    components=meta["components"],
                    matched_skills=[
                        {
                            "skill_id": str(item.skill.id),
                            "canonical_name": item.skill.canonical_name,
                            "gap": str(item.gap),
                            "priority": item.priority,
                        }
                        for item in meta["matched"]
                    ],
                    reason=explanation.verbalization,
                    explanation=explanation_payload,
                    encoder=encoder_name,
                    target_type=analysis.target.type,
                    target_id=analysis.target.id,
                    target_title=analysis.target.title,
                )
            )
            items.append(
                RecommendationItemPublic(
                    rank=rank,
                    score=Decimal(str(round(score, 4))),
                    components=meta["components"],
                    matched_skills=matched_payload,
                    reason=explanation.verbalization,
                    explanation=ExplanationPublic.model_validate(explanation_payload),
                    course=row if isinstance(row, CoursePublic) else None,
                    project=row if isinstance(row, ProjectPublic) else None,
                    mentor=row if isinstance(row, MentorPublic) else None,
                )
            )
        db.commit()
        return RecommendationListPublic(
            batch_id=batch_id,
            method=method,
            resource_type=resource_type,
            encoder=encoder_name,
            target=analysis.target,
            gap_skills=[
                MatchedGapSkillPublic(
                    skill=item.skill, gap=item.gap, priority=item.priority
                )
                for item in top_gaps
            ],
            items=items,
            weights=hybrid_w,
        )


def _load_catalog(db: Session, resource_type: str) -> list[ResourceRow]:
    if resource_type == "COURSE":
        return list(resource_service.list_courses(db))
    if resource_type == "PROJECT":
        return list(resource_service.list_projects(db))
    return list(resource_service.list_mentors(db))


def _skill_ids(row: ResourceRow) -> set[UUID]:
    return {item.skill.id for item in row.skills}


def _skill_levels(row: ResourceRow) -> dict[UUID, float]:
    return {item.skill.id: float(item.level) for item in row.skills}


def _title(row: ResourceRow) -> str:
    if isinstance(row, MentorPublic):
        return row.name
    return row.title


def _description(row: ResourceRow) -> str:
    if isinstance(row, MentorPublic):
        return row.bio
    return row.description


def _format(row: ResourceRow) -> str | None:
    if isinstance(row, CoursePublic):
        return row.format
    return None


def _resource_difficulty(row: ResourceRow) -> float:
    if isinstance(row, CoursePublic | ProjectPublic):
        return float(row.difficulty)
    if not row.skills:
        return 3.0
    return sum(float(item.level) for item in row.skills) / len(row.skills)


def _learner_level(matched: list[Any]) -> float:
    if not matched:
        return 2.5
    return sum(float(item.current_level) for item in matched) / len(matched)


def _popularity(row: ResourceRow) -> float:
    if isinstance(row, CoursePublic):
        return popularity_score(
            rating=float(row.rating), skill_count=len(row.skills), years=None
        )
    if isinstance(row, MentorPublic):
        return popularity_score(
            rating=None, skill_count=len(row.skills), years=row.years_experience
        )
    return popularity_score(rating=None, skill_count=len(row.skills), years=None)


def _taxonomy_graph() -> dict[str, Any]:
    path = repo_root() / "datasets" / "processed" / "skill_prerequisites.json"
    try:
        return load_taxonomy_graph(str(path))
    except OSError:
        return {"parents": {}, "related": {}, "ancestors": {}}


recommendation_service = RecommendationService()
