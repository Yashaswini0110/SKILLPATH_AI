from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.enums import SkillSourceType
from app.core.evidence import configured_source_reliabilities, source_reliability
from app.core.exceptions import NotFoundError
from app.core.paths import ensure_repo_on_path
from app.models import Employee, EmployeeSkill, Evidence, Skill, User
from app.schemas.skill_profile import (
    AggregatedSkillPublic,
    EvidencePublic,
    SkillProfilePublic,
)
from app.services.skill_view import to_skill_public

ensure_repo_on_path()

from ml.evidence.aggregation import (  # noqa: E402
    EvidenceItem,
    aggregate_skill,
    confidence_label,
)


class SkillProfileService:
    def get_profile(self, db: Session, user: User) -> SkillProfilePublic:
        employee = db.scalar(select(Employee).where(Employee.user_id == user.id))
        if employee is None:
            raise NotFoundError("Employee profile not found")

        evidence_rows = (
            db.scalars(
                select(Evidence)
                .options(joinedload(Evidence.skill).joinedload(Skill.aliases))
                .where(Evidence.employee_id == employee.id)
            )
            .unique()
            .all()
        )
        declared = (
            db.scalars(
                select(EmployeeSkill)
                .options(joinedload(EmployeeSkill.skill).joinedload(Skill.aliases))
                .where(EmployeeSkill.employee_id == employee.id)
            )
            .unique()
            .all()
        )

        grouped: dict[UUID, list[Evidence]] = defaultdict(list)
        skills: dict[UUID, Skill] = {}
        persisted_ids: set[UUID] = set()
        for evidence_row in evidence_rows:
            grouped[evidence_row.skill_id].append(evidence_row)
            skills[evidence_row.skill_id] = evidence_row.skill
            persisted_ids.add(evidence_row.id)

        for declared_row in declared:
            skills[declared_row.skill_id] = declared_row.skill
            has_self = any(
                item.source_type == SkillSourceType.SELF.value
                for item in grouped[declared_row.skill_id]
            )
            if not has_self:
                grouped[declared_row.skill_id].append(
                    _virtual_self_evidence(employee.id, declared_row)
                )

        aggregated: list[AggregatedSkillPublic] = []
        for skill_id, rows in grouped.items():
            items = [
                EvidenceItem(
                    source_type=row.source_type,
                    extracted_level=float(row.extracted_level),
                    reliability=float(row.reliability),
                    strength=float(row.strength),
                    recency=float(row.recency),
                    inferred=row.inferred,
                )
                for row in rows
            ]
            result = aggregate_skill(
                items, conflict_variance=settings.evidence_conflict_variance
            )
            inferred_only = all(item.inferred for item in items)
            aggregated.append(
                AggregatedSkillPublic(
                    skill=to_skill_public(skills[skill_id]),
                    current_level=Decimal(str(result.current_level)).quantize(
                        Decimal("0.1")
                    ),
                    confidence=Decimal(str(round(result.confidence, 2))),
                    confidence_label=confidence_label(
                        result.confidence,
                        high=settings.evidence_confidence_high,
                        medium=settings.evidence_confidence_medium,
                    ),
                    conflict=result.conflict,
                    variance=Decimal(str(round(result.variance, 2))),
                    recommend_assessment=result.recommend_assessment,
                    inferred_only=inferred_only,
                    evidence=[
                        EvidencePublic(
                            id=row.id if row.id in persisted_ids else None,
                            source_type=row.source_type,
                            extracted_level=row.extracted_level,
                            reliability=row.reliability,
                            strength=row.strength,
                            recency=row.recency,
                            inferred=row.inferred,
                        )
                        for row in rows
                    ],
                )
            )
        aggregated.sort(
            key=lambda item: (
                not item.conflict,
                -float(item.confidence),
                item.skill.canonical_name.lower(),
            )
        )
        return SkillProfilePublic(
            skill_count=len(aggregated),
            conflict_count=sum(1 for item in aggregated if item.conflict),
            conflict_variance_threshold=Decimal(
                str(settings.evidence_conflict_variance)
            ),
            source_reliability=configured_source_reliabilities(),
            skills=aggregated,
        )


def _virtual_self_evidence(employee_id: UUID, row: EmployeeSkill) -> Evidence:
    return Evidence(
        employee_id=employee_id,
        skill_id=row.skill_id,
        source_type=SkillSourceType.SELF.value,
        source_id=None,
        raw_text=None,
        extracted_level=row.current_level,
        reliability=Decimal(str(source_reliability(SkillSourceType.SELF.value))),
        recency=Decimal("1.00"),
        strength=Decimal("1.00"),
        inferred=False,
        section=None,
        match_type=None,
        confidence=row.confidence,
    )


skill_profile_service = SkillProfileService()
