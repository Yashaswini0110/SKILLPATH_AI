"""PRD evidence aggregation: confidence, proficiency, and conflict flags.

C(s) = 1 − Π(1 − r_e × σ_e × ρ_e)
L_cur(s) = Σ(w_e × l_e) / Σ(w_e) where w_e = r_e × σ_e × ρ_e
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import variance


@dataclass(frozen=True)
class EvidenceItem:
    source_type: str
    extracted_level: float
    reliability: float
    strength: float
    recency: float
    inferred: bool = True


@dataclass(frozen=True)
class AggregatedSkill:
    current_level: float
    confidence: float
    conflict: bool
    variance: float
    recommend_assessment: bool
    evidence_count: int


def evidence_weight(item: EvidenceItem) -> float:
    return _clamp(item.reliability * item.strength * item.recency, 0.0, 1.0)


def aggregate_skill(
    items: list[EvidenceItem],
    conflict_variance: float = 1.0,
) -> AggregatedSkill:
    if not items:
        raise ValueError("Cannot aggregate a skill with no evidence")
    weights = [evidence_weight(item) for item in items]
    survival = 1.0
    for weight in weights:
        survival *= 1.0 - weight
    confidence = _clamp(1.0 - survival, 0.0, 1.0)
    weight_sum = sum(weights)
    if weight_sum == 0:
        level = sum(item.extracted_level for item in items) / len(items)
    else:
        level = (
            sum(
                weight * item.extracted_level
                for weight, item in zip(weights, items, strict=True)
            )
            / weight_sum
        )
    levels = [item.extracted_level for item in items]
    spread = float(variance(levels)) if len(levels) >= 2 else 0.0
    conflict = len(items) >= 2 and spread >= conflict_variance
    return AggregatedSkill(
        current_level=_clamp(level, 0.0, 5.0),
        confidence=confidence,
        conflict=conflict,
        variance=spread,
        recommend_assessment=conflict,
        evidence_count=len(items),
    )


def confidence_label(confidence: float, high: float = 0.7, medium: float = 0.4) -> str:
    if confidence >= high:
        return "HIGH"
    if confidence >= medium:
        return "MEDIUM"
    return "LOW"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
