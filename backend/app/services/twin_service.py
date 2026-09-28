"""Read-only per-skill competency snapshot.

Joins the stored skill profile, gap analysis for the saved target (or an
optional catalog role / job description), and persisted evidence history.
Does not change the target role, path, or evidence. GitHub is listed as a
source type but is not collected.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import SkillSourceType
from app.models import Evidence, User
from app.schemas.gap import GapItemPublic
from app.schemas.skill_profile import AggregatedSkillPublic, EvidencePublic
from app.schemas.twin import (
    TwinEvidenceSourcePublic,
    TwinHistoryPointPublic,
    TwinSkillPublic,
    TwinSnapshotPublic,
)
from app.services.gap_service import gap_service
from app.services.profile_service import profile_service
from app.services.skill_profile_service import skill_profile_service

DISCLAIMER = (
    "Estimated from stored evidence. GitHub is not collected. "
    "This is not a hiring or employment prediction."
)

DISPLAY_SOURCES = (
    SkillSourceType.SELF,
    SkillSourceType.RESUME,
    SkillSourceType.ASSESSMENT,
    SkillSourceType.GITHUB,
    SkillSourceType.PROJECT,
    SkillSourceType.COURSE,
    SkillSourceType.CERT,
    SkillSourceType.WORK,
)
SOURCE_ORDER = {source.value: index for index, source in enumerate(DISPLAY_SOURCES)}

TREND_DELTA = Decimal("0.5")


class TwinService:
    def snapshot(
        self,
        db: Session,
        user: User,
        role_id: UUID | None = None,
        job_description_id: UUID | None = None,
    ) -> TwinSnapshotPublic:
        employee = profile_service.get_employee_for_user(db, user)
        profile = skill_profile_service.get_profile(db, user)
        analysis = gap_service.analyze(
            db, user, role_id=role_id, job_description_id=job_description_id
        )
        history_by_skill = _load_history(db, employee.id)
        profile_by_id = {item.skill.id: item for item in profile.skills}
        gap_by_id = {item.skill.id: item for item in analysis.gaps}

        ordered_ids: list[UUID] = [item.skill.id for item in analysis.gaps]
        for item in profile.skills:
            if item.skill.id not in gap_by_id:
                ordered_ids.append(item.skill.id)

        skills = [
            _row(
                skill_id,
                profile_by_id.get(skill_id),
                gap_by_id.get(skill_id),
                history_by_skill.get(skill_id, []),
            )
            for skill_id in ordered_ids
        ]
        github_collected = any(
            source.present
            for item in skills
            for source in item.evidence_sources
            if source.source_type == SkillSourceType.GITHUB.value
        )
        return TwinSnapshotPublic(
            target=analysis.target,
            disclaimer=DISCLAIMER,
            skill_count=len(skills),
            open_gap_count=sum(
                1 for item in skills if item.priority not in (None, "NONE")
            ),
            conflict_count=sum(1 for item in skills if item.conflict),
            github_collected=github_collected,
            skills=skills,
        )


twin_service = TwinService()


def _load_history(
    db: Session, employee_id: UUID
) -> dict[UUID, list[TwinHistoryPointPublic]]:
    rows = list(
        db.scalars(select(Evidence).where(Evidence.employee_id == employee_id)).all()
    )
    rows.sort(
        key=lambda row: (
            row.created_at,
            SOURCE_ORDER.get(row.source_type, 99),
            str(row.id),
        )
    )
    grouped: dict[UUID, list[TwinHistoryPointPublic]] = defaultdict(list)
    for row in rows:
        grouped[row.skill_id].append(
            TwinHistoryPointPublic(
                at=row.created_at,
                source_type=row.source_type,
                level=row.extracted_level,
                inferred=row.inferred,
            )
        )
    return {skill_id: points[-8:] for skill_id, points in grouped.items()}


def _row(
    skill_id: UUID,
    profile: AggregatedSkillPublic | None,
    gap: GapItemPublic | None,
    history: list[TwinHistoryPointPublic],
) -> TwinSkillPublic:
    del skill_id
    if gap is not None:
        skill = gap.skill
    elif profile is not None:
        skill = profile.skill
    else:
        raise RuntimeError("twin row is missing a catalog skill")
    evidence = list(profile.evidence) if profile is not None else []
    current = profile.current_level if profile is not None else Decimal("0.0")
    confidence = profile.confidence if profile is not None else Decimal("0.00")
    label = profile.confidence_label if profile is not None else "LOW"
    return TwinSkillPublic(
        skill=skill,
        current_level=current,
        required_level=gap.required_level if gap is not None else None,
        gap_basic=gap.gap_basic if gap is not None else None,
        gap=gap.gap if gap is not None else None,
        priority=gap.priority if gap is not None else None,
        requirement=gap.requirement if gap is not None else None,
        confidence=confidence,
        confidence_label=label,
        conflict=profile.conflict if profile is not None else False,
        inferred_only=profile.inferred_only if profile is not None else False,
        recommend_assessment=(
            profile.recommend_assessment if profile is not None else False
        ),
        in_target=gap is not None,
        evidence_sources=_sources(evidence),
        history=history,
        trend=_trend(history),
    )


def _sources(evidence: list[EvidencePublic]) -> list[TwinEvidenceSourcePublic]:
    latest: dict[str, TwinEvidenceSourcePublic] = {}
    for item in evidence:
        latest[item.source_type] = TwinEvidenceSourcePublic(
            source_type=item.source_type,
            present=True,
            level=item.extracted_level,
            inferred=item.inferred,
        )
    return [
        latest.get(
            source.value,
            TwinEvidenceSourcePublic(source_type=source.value, present=False),
        )
        for source in DISPLAY_SOURCES
    ]


def _trend(history: list[TwinHistoryPointPublic]) -> str:
    if len(history) < 2:
        return "INSUFFICIENT_DATA"
    first = Decimal(str(history[0].level))
    last = Decimal(str(history[-1].level))
    delta = last - first
    if delta >= TREND_DELTA:
        return "IMPROVING"
    if delta <= -TREND_DELTA:
        return "DECLINING"
    return "STABLE"
