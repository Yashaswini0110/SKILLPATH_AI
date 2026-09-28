"""Map a raw skill mention to one catalog skill, or leave it unmatched.

The mapper never invents a skill. Colliding aliases resolve to unmatched.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable
from uuid import UUID

from ml.skill_extraction.normalizer import compact_skill_text, normalize_skill_text

EXACT_CONFIDENCE = 1.0
ALIAS_CONFIDENCE = 0.9
UNMATCHED_CONFIDENCE = 0.0


class MatchType(str, Enum):
    EXACT = "exact"
    ALIAS = "alias"
    COLLISION = "collision"
    UNMATCHED = "unmatched"


@dataclass(frozen=True)
class TaxonomyEntry:
    skill_id: UUID
    canonical_name: str
    name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillMatch:
    raw: str
    skill_id: UUID | None
    canonical_name: str | None
    confidence: float
    matched_term: str | None
    match_type: MatchType


@dataclass(frozen=True)
class _Hit:
    skill_id: UUID
    canonical_name: str
    matched_term: str
    match_type: MatchType


class TaxonomyMapper:
    def __init__(self, entries: Iterable[TaxonomyEntry]) -> None:
        self._index: dict[str, list[_Hit]] = {}
        self._surfaces: list[tuple[str, _Hit]] = []
        for entry in entries:
            self._index_term(entry.name, entry, MatchType.EXACT)
            self._add_surface(entry.name, entry, MatchType.EXACT)
            self._index_term(entry.canonical_name, entry, MatchType.EXACT)
            self._add_surface(entry.canonical_name, entry, MatchType.EXACT)
            for alias in entry.aliases:
                self._index_term(alias, entry, MatchType.ALIAS)
                self._add_surface(alias, entry, MatchType.ALIAS)

    def surface_forms(self) -> list[tuple[str, UUID, str, MatchType]]:
        return [
            (term, hit.skill_id, hit.canonical_name, hit.match_type)
            for term, hit in self._surfaces
        ]

    def _add_surface(
        self, term: str, entry: TaxonomyEntry, match_type: MatchType
    ) -> None:
        cleaned = term.strip()
        if not cleaned:
            return
        self._surfaces.append(
            (
                cleaned,
                _Hit(
                    skill_id=entry.skill_id,
                    canonical_name=entry.canonical_name,
                    matched_term=cleaned,
                    match_type=match_type,
                ),
            )
        )

    def resolve(self, raw: str) -> SkillMatch:
        mention = raw.strip()
        if not mention:
            return SkillMatch(
                raw=raw,
                skill_id=None,
                canonical_name=None,
                confidence=UNMATCHED_CONFIDENCE,
                matched_term=None,
                match_type=MatchType.UNMATCHED,
            )

        hits = self._lookup(mention)
        if not hits:
            return SkillMatch(
                raw=raw,
                skill_id=None,
                canonical_name=None,
                confidence=UNMATCHED_CONFIDENCE,
                matched_term=None,
                match_type=MatchType.UNMATCHED,
            )

        skill_ids = {hit.skill_id for hit in hits}
        if len(skill_ids) > 1:
            return SkillMatch(
                raw=raw,
                skill_id=None,
                canonical_name=None,
                confidence=UNMATCHED_CONFIDENCE,
                matched_term=None,
                match_type=MatchType.COLLISION,
            )

        chosen = _prefer_exact(hits)
        confidence = (
            EXACT_CONFIDENCE
            if chosen.match_type is MatchType.EXACT
            else ALIAS_CONFIDENCE
        )
        return SkillMatch(
            raw=raw,
            skill_id=chosen.skill_id,
            canonical_name=chosen.canonical_name,
            confidence=confidence,
            matched_term=chosen.matched_term,
            match_type=chosen.match_type,
        )

    def resolve_many(self, mentions: Iterable[str]) -> list[SkillMatch]:
        return [self.resolve(mention) for mention in mentions]

    def _lookup(self, raw: str) -> list[_Hit]:
        normalized = normalize_skill_text(raw)
        if normalized and normalized in self._index:
            return self._index[normalized]
        compact = compact_skill_text(raw)
        if compact and compact in self._index:
            return self._index[compact]
        return []

    def _index_term(
        self, term: str, entry: TaxonomyEntry, match_type: MatchType
    ) -> None:
        keys = {normalize_skill_text(term), compact_skill_text(term)}
        for key in keys:
            if not key:
                continue
            self._index.setdefault(key, []).append(
                _Hit(
                    skill_id=entry.skill_id,
                    canonical_name=entry.canonical_name,
                    matched_term=term,
                    match_type=match_type,
                )
            )


def _prefer_exact(hits: list[_Hit]) -> _Hit:
    for hit in hits:
        if hit.match_type is MatchType.EXACT:
            return hit
    return hits[0]
