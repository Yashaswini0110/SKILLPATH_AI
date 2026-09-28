"""Turn a job description into a taxonomy-mapped competency profile.

Requirement classes follow the PRD starting weights:
Required = 1.0, Preferred = 0.6, Mentioned = 0.4.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from ml.skill_extraction.dictionary_extractor import (
    DictionaryHit,
    extract_dictionary_hits,
)
from ml.skill_extraction.segmenter import ResumeSection, segment_resume
from ml.skill_extraction.taxonomy_mapper import MatchType, TaxonomyMapper

REQUIRED_CUES = re.compile(
    r"\b(required|must|mandatory|need(?:s|ed)?|minimum|essential|expect(?:ed)?)\b",
    re.I,
)
PREFERRED_CUES = re.compile(
    r"\b(preferred|nice to have|bonus|plus|desired|optional)\b",
    re.I,
)
EXPERT_CUES = re.compile(r"\b(expert|senior|advanced|lead|principal)\b", re.I)
BEGINNER_CUES = re.compile(r"\b(familiar|basic|exposure|beginner)\b", re.I)

REQUIREMENT_RANK = {"REQUIRED": 3, "PREFERRED": 2, "MENTIONED": 1}


class RequirementType(str, Enum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"
    MENTIONED = "MENTIONED"


@dataclass(frozen=True)
class RequirementWeights:
    required: float = 1.0
    preferred: float = 0.6
    mentioned: float = 0.4


@dataclass(frozen=True)
class JDSkill:
    skill_id: UUID
    canonical_name: str
    requirement: RequirementType
    importance: float
    required_level: int
    match_type: str
    mention_count: int


def extract_jd_skills(
    text: str,
    mapper: TaxonomyMapper,
    weights: RequirementWeights | None = None,
) -> list[JDSkill]:
    weights = weights or RequirementWeights()
    sections = segment_resume(text)
    hits = extract_dictionary_hits(text, mapper, sections)
    grouped: dict[UUID, list[tuple[DictionaryHit, RequirementType]]] = defaultdict(list)
    for hit in hits:
        grouped[hit.skill_id].append((hit, _classify(hit, sections)))

    results: list[JDSkill] = []
    for skill_id, skill_hits in grouped.items():
        chosen_hit, requirement = max(
            skill_hits,
            key=lambda item: (
                REQUIREMENT_RANK[item[1].value],
                1 if item[0].match_type is MatchType.EXACT else 0,
            ),
        )
        importance = {
            RequirementType.REQUIRED: weights.required,
            RequirementType.PREFERRED: weights.preferred,
            RequirementType.MENTIONED: weights.mentioned,
        }[requirement]
        results.append(
            JDSkill(
                skill_id=skill_id,
                canonical_name=chosen_hit.canonical_name,
                requirement=requirement,
                importance=importance,
                required_level=_required_level(chosen_hit, requirement, sections),
                match_type=chosen_hit.match_type.value,
                mention_count=len(skill_hits),
            )
        )
    results.sort(
        key=lambda item: (
            -REQUIREMENT_RANK[item.requirement.value],
            -item.required_level,
            item.canonical_name.lower(),
        )
    )
    return results


def _classify(hit: DictionaryHit, sections: list[ResumeSection]) -> RequirementType:
    if hit.section == "preferred":
        return RequirementType.PREFERRED
    if hit.section in {"required", "responsibilities", "skills"}:
        return RequirementType.REQUIRED
    window = _section_window(hit, sections, 90)
    if PREFERRED_CUES.search(window):
        return RequirementType.PREFERRED
    if REQUIRED_CUES.search(window):
        return RequirementType.REQUIRED
    return RequirementType.MENTIONED


def _required_level(
    hit: DictionaryHit,
    requirement: RequirementType,
    sections: list[ResumeSection],
) -> int:
    base = {
        RequirementType.REQUIRED: 4,
        RequirementType.PREFERRED: 3,
        RequirementType.MENTIONED: 2,
    }[requirement]
    window = _section_window(hit, sections, 80)
    if EXPERT_CUES.search(window):
        base = min(5, base + 1)
    if BEGINNER_CUES.search(window):
        base = max(1, base - 1)
    return base


def _section_window(
    hit: DictionaryHit, sections: list[ResumeSection], radius: int
) -> str:
    section = next(
        (item for item in sections if item.start <= hit.start < item.end),
        None,
    )
    if section is None:
        return ""
    local_start = hit.start - section.start
    local_end = hit.end - section.start
    left = max(0, local_start - radius)
    right = min(len(section.text), local_end + radius)
    return section.text[left:right]
