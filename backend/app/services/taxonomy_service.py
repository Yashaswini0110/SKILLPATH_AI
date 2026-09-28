from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.paths import ensure_repo_on_path
from app.models import Skill
from app.schemas.skill import SkillResolveItem, SkillResolveResponse

ensure_repo_on_path()

from ml.skill_extraction.taxonomy_mapper import (  # noqa: E402
    TaxonomyEntry,
    TaxonomyMapper,
)


def mapper_from_db(db: Session) -> TaxonomyMapper:
    rows = db.scalars(select(Skill).options(joinedload(Skill.aliases))).unique().all()
    entries = [
        TaxonomyEntry(
            skill_id=row.id,
            canonical_name=row.canonical_name,
            name=row.name,
            aliases=tuple(alias.alias for alias in row.aliases),
        )
        for row in rows
    ]
    return TaxonomyMapper(entries)


class TaxonomyService:
    def resolve(self, db: Session, mentions: list[str]) -> SkillResolveResponse:
        mapper = mapper_from_db(db)
        results = [
            SkillResolveItem(
                raw=match.raw,
                skill_id=match.skill_id,
                canonical_name=match.canonical_name,
                confidence=match.confidence,
                matched_term=match.matched_term,
                match_type=match.match_type.value,
            )
            for match in mapper.resolve_many(mentions)
        ]
        return SkillResolveResponse(results=results)


taxonomy_service = TaxonomyService()
