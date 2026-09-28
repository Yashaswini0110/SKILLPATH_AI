from __future__ import annotations

from decimal import Decimal
from statistics import mean
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationAppError
from app.core.paths import ensure_repo_on_path
from app.models import User
from app.schemas.gap import GapAnalysisPublic, GapItemPublic, GapTargetPublic
from app.schemas.job_description import JobDescriptionPublic
from app.schemas.role import TargetRolePublic
from app.schemas.skill_profile import AggregatedSkillPublic
from app.services.catalog_service import catalog_service
from app.services.job_description_service import job_description_service
from app.services.profile_service import profile_service
from app.services.skill_profile_service import skill_profile_service

ensure_repo_on_path()

from ml.evidence.aggregation import EvidenceItem, evidence_weight  # noqa: E402
from ml.gap.engine import GapThresholds, GapWeights, compute_gap  # noqa: E402

PRIORITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "NONE": 4,
}


class GapService:
    def analyze(
        self,
        db: Session,
        user: User,
        role_id: UUID | None = None,
        job_description_id: UUID | None = None,
    ) -> GapAnalysisPublic:
        if role_id is not None and job_description_id is not None:
            raise ValidationAppError(
                "Provide a catalog role or a job description, not both"
            )
        employee = profile_service.get_employee_for_user(db, user)
        if job_description_id is not None:
            jd = job_description_service.get_job_description(
                db, user, job_description_id
            )
            target = GapTargetPublic(type="JOB_DESCRIPTION", id=jd.id, title=jd.title)
            requirements = _jd_requirements(jd)
        else:
            selected_role_id = role_id or employee.target_role_id
            if selected_role_id is None:
                raise ValidationAppError(
                    "Select a target role or analyze a job description first"
                )
            role = catalog_service.get_role(db, selected_role_id)
            target = GapTargetPublic(type="ROLE", id=role.id, title=role.title)
            requirements = _role_requirements(role)

        current = {
            item.skill.id: item
            for item in skill_profile_service.get_profile(db, user).skills
        }
        weights = GapWeights(
            importance=settings.gap_weight_importance,
            confidence=settings.gap_weight_confidence,
            criticality=settings.gap_weight_criticality,
            evidence=settings.gap_weight_evidence,
        )
        thresholds = GapThresholds(
            critical=settings.gap_critical_threshold,
            high=settings.gap_high_threshold,
            medium=settings.gap_medium_threshold,
        )
        gaps: list[GapItemPublic] = []
        for item in requirements:
            profile = current.get(item["skill"].id)
            current_level, confidence, evidence_strength, inferred_only, conflict = (
                _current_state(profile)
            )
            score = compute_gap(
                required_level=float(item["required_level"]),
                current_level=current_level,
                importance=float(item["importance"]),
                confidence=confidence,
                criticality=float(item["criticality"]),
                evidence_strength=evidence_strength,
                weights=weights,
                thresholds=thresholds,
            )
            gaps.append(
                GapItemPublic(
                    skill=item["skill"],
                    required_level=Decimal(str(item["required_level"])),
                    current_level=Decimal(str(current_level)).quantize(Decimal("0.1")),
                    gap_basic=Decimal(str(round(score.gap_basic, 2))),
                    gap=Decimal(str(round(score.gap, 2))),
                    priority=score.priority,
                    importance=item["importance"],
                    criticality=item["criticality"],
                    confidence=Decimal(str(round(confidence, 2))),
                    evidence_strength=Decimal(str(round(evidence_strength, 2))),
                    requirement=item["requirement"],
                    inferred_only=inferred_only,
                    conflict=conflict,
                )
            )
        gaps.sort(
            key=lambda row: (
                PRIORITY_ORDER.get(row.priority, 9),
                -float(row.gap),
                row.skill.canonical_name.lower(),
            )
        )
        return GapAnalysisPublic(
            target=target,
            gap_count=sum(1 for row in gaps if row.priority != "NONE"),
            critical_count=sum(1 for row in gaps if row.priority == "CRITICAL"),
            high_count=sum(1 for row in gaps if row.priority == "HIGH"),
            medium_count=sum(1 for row in gaps if row.priority == "MEDIUM"),
            low_count=sum(1 for row in gaps if row.priority == "LOW"),
            none_count=sum(1 for row in gaps if row.priority == "NONE"),
            gaps=gaps,
        )


def _role_requirements(role: TargetRolePublic) -> list[dict]:
    return [
        {
            "skill": item.skill,
            "required_level": item.required_level,
            "importance": item.importance,
            "criticality": item.criticality,
            "requirement": item.requirement,
        }
        for item in role.skills
    ]


def _jd_requirements(jd: JobDescriptionPublic) -> list[dict]:
    return [
        {
            "skill": item.skill,
            "required_level": item.required_level,
            "importance": item.importance,
            "criticality": item.importance,
            "requirement": item.requirement,
        }
        for item in jd.skills
    ]


def _current_state(
    profile: AggregatedSkillPublic | None,
) -> tuple[float, float, float, bool, bool]:
    if profile is None:
        # Unknown skills count as 0. C=0 or E=0 would hide missing required skills.
        return 0.0, 1.0, 1.0, False, False
    weights = [
        evidence_weight(
            EvidenceItem(
                source_type=row.source_type,
                extracted_level=float(row.extracted_level),
                reliability=float(row.reliability),
                strength=float(row.strength),
                recency=float(row.recency),
                inferred=row.inferred,
            )
        )
        for row in profile.evidence
    ]
    evidence_strength = mean(weights) if weights else 1.0
    return (
        float(profile.current_level),
        float(profile.confidence),
        float(evidence_strength),
        profile.inferred_only,
        profile.conflict,
    )


gap_service = GapService()
