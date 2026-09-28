from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationAppError
from app.core.paths import ensure_repo_on_path
from app.models import MentorMatch, User
from app.schemas.recommendation import (
    ExplanationPublic,
    MatchedGapSkillPublic,
    MentorMatchListPublic,
    MentorMatchPublic,
    MentorWhyPublic,
)
from app.schemas.resource import MentorPublic
from app.services.catalog_service import catalog_service
from app.services.gap_service import gap_service
from app.services.profile_service import profile_service
from app.services.resource_service import resource_service

ensure_repo_on_path()

from recommendation.explain import explain_mentor  # noqa: E402
from recommendation.mentors.signals import (  # noqa: E402
    availability_score,
    domain_overlap,
    experience_score,
    learning_goals_score,
    skill_overlap,
    weighted_score,
    workload_score,
)


class MentorService:
    def match(
        self,
        db: Session,
        user: User,
        *,
        role_id: UUID | None = None,
        job_description_id: UUID | None = None,
        limit: int | None = None,
    ) -> MentorMatchListPublic:
        analysis = gap_service.analyze(
            db, user, role_id=role_id, job_description_id=job_description_id
        )
        top_gaps = [item for item in analysis.gaps if item.priority != "NONE"][
            : settings.rec_top_gap_count
        ]
        if not top_gaps:
            raise ValidationAppError("No open skill gaps to match a mentor against")
        employee = profile_service.get_employee_for_user(db, user)
        prefs = employee.learning_preferences or {}
        formats = [str(item) for item in prefs.get("formats") or []]
        learner_domains = _learner_domains(db, analysis.target.type, analysis.target.id)
        if employee.department:
            learner_domains.append(employee.department)
        role_ids = {item.skill.id for item in analysis.gaps}
        weights = settings.mentor_weights()
        scored: list[tuple[float, MentorPublic, dict, MentorWhyPublic, list[str]]] = []
        for mentor in resource_service.list_mentors(db):
            matched = [item for item in top_gaps if _teaches(mentor, item.skill.id)]
            if not matched:
                continue
            mentor_ids = {link.skill.id for link in mentor.skills}
            open_slots = mentor.max_mentees
            parts = {
                "skill_overlap": skill_overlap(len(matched), len(top_gaps)),
                "domain_overlap": domain_overlap(mentor.domains, learner_domains),
                "experience": experience_score(mentor.years_experience),
                "availability": availability_score(mentor.available_hours_per_month),
                "learning_goals": learning_goals_score(mentor_ids, role_ids, formats),
                "workload": workload_score(open_slots, mentor.max_mentees),
            }
            score = weighted_score(parts, weights)
            why = MentorWhyPublic(
                matched_gap_count=len(matched),
                top_gap_count=len(top_gaps),
                matched_skills=[item.skill for item in matched],
                available_hours_per_month=mentor.available_hours_per_month,
                open_mentee_slots=open_slots,
                domains=list(mentor.domains),
            )
            components = {key: round(value, 4) for key, value in parts.items()}
            components["final"] = round(score, 4)
            scored.append(
                (
                    score,
                    mentor,
                    components,
                    why,
                    [item.skill.canonical_name for item in matched],
                )
            )
        if not scored:
            raise ValidationAppError("No catalog mentor covers your current top gaps")
        scored.sort(key=lambda row: (-row[0], row[1].name.lower()))
        limit = limit or settings.rec_mentor_limit
        scored = scored[: max(1, min(limit, 20))]
        batch_id = uuid4()
        items: list[MentorMatchPublic] = []
        for rank, (score, mentor, components, why, matched_names) in enumerate(
            scored, start=1
        ):
            explanation = explain_mentor(
                rank=rank,
                matched_names=matched_names,
                top_count=len(top_gaps),
                hours=mentor.available_hours_per_month,
                open_slots=why.open_mentee_slots,
                domains=list(why.domains),
            )
            explanation_payload = explanation.as_public()
            db.add(
                MentorMatch(
                    batch_id=batch_id,
                    employee_id=employee.id,
                    mentor_id=mentor.id,
                    rank=rank,
                    score=Decimal(str(round(score, 4))),
                    components=components,
                    why=why.model_dump(mode="json"),
                    reason=explanation.verbalization,
                    explanation=explanation_payload,
                    target_type=analysis.target.type,
                    target_id=analysis.target.id,
                    target_title=analysis.target.title,
                )
            )
            items.append(
                MentorMatchPublic(
                    rank=rank,
                    score=Decimal(str(round(score, 4))),
                    mentor=mentor,
                    components=components,
                    why=why,
                    reason=explanation.verbalization,
                    explanation=ExplanationPublic.model_validate(explanation_payload),
                )
            )
        db.commit()
        return MentorMatchListPublic(
            batch_id=batch_id,
            target=analysis.target,
            weights=weights,
            gap_skills=[
                MatchedGapSkillPublic(
                    skill=item.skill, gap=item.gap, priority=item.priority
                )
                for item in top_gaps
            ],
            items=items,
        )


def _teaches(mentor: MentorPublic, skill_id: UUID) -> bool:
    return any(link.skill.id == skill_id for link in mentor.skills)


def _learner_domains(db: Session, target_type: str, target_id: UUID) -> list[str]:
    if target_type != "ROLE":
        return []
    role = catalog_service.get_role(db, target_id)
    return [role.category] if role.category else []


mentor_service = MentorService()
