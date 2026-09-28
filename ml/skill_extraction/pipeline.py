"""Resume skill extraction pipeline.

Layer 1: taxonomy dictionary matching (authoritative for known catalog terms).
Layer 2: section context (skills / experience / projects) to weight confidence.
Layer 3/4 (semantic + LLM) are intentionally not used as the decision engine.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from ml.skill_extraction.dictionary_extractor import (
    DictionaryHit,
    extract_dictionary_hits,
)
from ml.skill_extraction.proficiency import estimate_proficiency
from ml.skill_extraction.segmenter import segment_resume
from ml.skill_extraction.taxonomy_mapper import (
    ALIAS_CONFIDENCE,
    EXACT_CONFIDENCE,
    MatchType,
    TaxonomyMapper,
)

SECTION_WEIGHT = {
    "skills": 1.0,
    "experience": 0.9,
    "projects": 0.85,
    "certifications": 0.8,
    "education": 0.65,
    "summary": 0.55,
    "other": 0.45,
}


@dataclass(frozen=True)
class ExtractedSkill:
    skill_id: UUID
    canonical_name: str
    matched_term: str
    match_type: str
    proficiency: float
    confidence: float
    evidence_snippet: str
    section: str
    mention_count: int
    inferred: bool = True
    source: str = "RESUME"


def extract_skills_from_text(text: str, mapper: TaxonomyMapper) -> list[ExtractedSkill]:
    sections = segment_resume(text)
    hits = extract_dictionary_hits(text, mapper, sections)
    grouped: dict[UUID, list[DictionaryHit]] = defaultdict(list)
    for hit in hits:
        grouped[hit.skill_id].append(hit)

    results: list[ExtractedSkill] = []
    for skill_id, skill_hits in grouped.items():
        chosen = _best_hit(skill_hits)
        mention_count = len(skill_hits)
        mapping_confidence = (
            EXACT_CONFIDENCE
            if chosen.match_type is MatchType.EXACT
            else ALIAS_CONFIDENCE
        )
        section_weight = SECTION_WEIGHT.get(chosen.section, 0.45)
        frequency_weight = min(1.0, 0.75 + 0.1 * mention_count)
        confidence = round(
            min(1.0, mapping_confidence * section_weight * frequency_weight), 2
        )
        results.append(
            ExtractedSkill(
                skill_id=skill_id,
                canonical_name=chosen.canonical_name,
                matched_term=chosen.matched_term,
                match_type=chosen.match_type.value,
                proficiency=estimate_proficiency(
                    chosen.snippet, chosen.section, mention_count
                ),
                confidence=confidence,
                evidence_snippet=chosen.snippet,
                section=chosen.section,
                mention_count=mention_count,
            )
        )
    results.sort(key=lambda item: (-item.confidence, item.canonical_name.lower()))
    return results


def _best_hit(hits: list[DictionaryHit]) -> DictionaryHit:
    return sorted(
        hits,
        key=lambda hit: (
            SECTION_WEIGHT.get(hit.section, 0),
            1 if hit.match_type is MatchType.EXACT else 0,
            len(hit.matched_term),
        ),
        reverse=True,
    )[0]
