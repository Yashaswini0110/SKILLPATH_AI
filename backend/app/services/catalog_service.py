from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.core.requirements import configured_jd_weights, requirement_from_importance
from app.models import RoleSkill, Skill, TargetRole
from app.schemas.role import (
    RequirementWeightsPublic,
    RoleSkillPublic,
    TargetRolePublic,
    TargetRoleSummary,
)
from app.schemas.skill import SkillPublic
from app.services.skill_view import to_skill_public

REQUIREMENT_ORDER = {"REQUIRED": 0, "PREFERRED": 1, "MENTIONED": 2}


class CatalogService:
    def list_skills(
        self, db: Session, category: str | None = None
    ) -> list[SkillPublic]:
        stmt = (
            select(Skill)
            .options(joinedload(Skill.aliases))
            .order_by(Skill.category, Skill.canonical_name)
        )
        if category:
            stmt = stmt.where(Skill.category == category)
        rows = db.scalars(stmt).unique().all()
        return [to_skill_public(row) for row in rows]

    def get_skill(self, db: Session, skill_id: UUID) -> SkillPublic:
        skill = (
            db.scalars(
                select(Skill)
                .options(joinedload(Skill.aliases))
                .where(Skill.id == skill_id)
            )
            .unique()
            .one_or_none()
        )
        if skill is None:
            raise NotFoundError("Skill not found")
        return to_skill_public(skill)

    def list_roles(self, db: Session) -> list[TargetRoleSummary]:
        rows = db.scalars(select(TargetRole).order_by(TargetRole.title)).all()
        return [TargetRoleSummary.model_validate(row) for row in rows]

    def get_role(self, db: Session, role_id: UUID) -> TargetRolePublic:
        role = (
            db.scalars(
                select(TargetRole)
                .options(
                    joinedload(TargetRole.role_skills)
                    .joinedload(RoleSkill.skill)
                    .joinedload(Skill.aliases)
                )
                .where(TargetRole.id == role_id)
            )
            .unique()
            .one_or_none()
        )
        if role is None:
            raise NotFoundError("Target role not found")
        weights = configured_jd_weights()
        skills = [
            RoleSkillPublic(
                skill=to_skill_public(rs.skill),
                required_level=rs.required_level,
                importance=rs.importance,
                criticality=rs.criticality,
                requirement=requirement_from_importance(rs.importance).value,
            )
            for rs in role.role_skills
        ]
        skills.sort(
            key=lambda item: (
                REQUIREMENT_ORDER.get(item.requirement, 9),
                -item.required_level,
                item.skill.canonical_name.lower(),
            )
        )
        return TargetRolePublic(
            id=role.id,
            title=role.title,
            category=role.category,
            description=role.description,
            weights=RequirementWeightsPublic(
                required=Decimal(str(weights.required)),
                preferred=Decimal(str(weights.preferred)),
                mentioned=Decimal(str(weights.mentioned)),
            ),
            skills=skills,
        )


catalog_service = CatalogService()
