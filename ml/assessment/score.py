"""Map MCQ results to a 1–5 proficiency level.

extracted_level = 1 + 4 × (correct / total)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class McqScore:
    correct_count: int
    total: int
    percent: float
    extracted_level: float
    passed: bool
    strength: float


def score_mcq(
    selected: list[int | None],
    correct: list[int],
    pass_score: float = 0.7,
) -> McqScore:
    if not correct or len(selected) != len(correct):
        raise ValueError("Answer count must match the question count")
    hits = sum(
        1
        for choice, expected in zip(selected, correct, strict=True)
        if choice is not None and int(choice) == int(expected)
    )
    percent = hits / len(correct)
    return McqScore(
        correct_count=hits,
        total=len(correct),
        percent=percent,
        extracted_level=level_from_percent(percent),
        passed=percent + 1e-9 >= float(pass_score),
        strength=_clamp(0.5 + 0.5 * percent, 0.0, 1.0),
    )


def level_from_percent(percent: float) -> float:
    return round(1.0 + 4.0 * _clamp(float(percent), 0.0, 1.0), 1)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
