"""PRD skill-gap engine.

Gap_basic = max(0, L_req − L_cur)
Gap = Gap_basic × I × C × R × E × configurable weights (default 1.0)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GapWeights:
    importance: float = 1.0
    confidence: float = 1.0
    criticality: float = 1.0
    evidence: float = 1.0


@dataclass(frozen=True)
class GapThresholds:
    critical: float = 2.0
    high: float = 1.0
    medium: float = 0.5


@dataclass(frozen=True)
class GapScore:
    gap_basic: float
    gap: float
    priority: str


def compute_gap(
    *,
    required_level: float,
    current_level: float,
    importance: float,
    confidence: float,
    criticality: float,
    evidence_strength: float,
    weights: GapWeights | None = None,
    thresholds: GapThresholds | None = None,
) -> GapScore:
    weights = weights or GapWeights()
    thresholds = thresholds or GapThresholds()
    basic = max(0.0, required_level - current_level)
    gap = (
        basic
        * _clamp(importance, 0.0, 1.0)
        * _clamp(confidence, 0.0, 1.0)
        * _clamp(criticality, 0.0, 1.0)
        * _clamp(evidence_strength, 0.0, 1.0)
        * weights.importance
        * weights.confidence
        * weights.criticality
        * weights.evidence
    )
    return GapScore(
        gap_basic=basic,
        gap=max(0.0, gap),
        priority=priority_band(gap, thresholds),
    )


def priority_band(gap: float, thresholds: GapThresholds | None = None) -> str:
    thresholds = thresholds or GapThresholds()
    if gap <= 0:
        return "NONE"
    if gap <= thresholds.medium:
        return "LOW"
    if gap <= thresholds.high:
        return "MEDIUM"
    if gap <= thresholds.critical:
        return "HIGH"
    return "CRITICAL"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
