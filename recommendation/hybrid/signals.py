"""Independent hybrid recommendation signals.

Each function returns a score in [0, 1]. None of them call an LLM.
Collaborative filtering has no interaction log; it uses skill-set Jaccard
as a documented cold-start proxy.
"""

from __future__ import annotations

from recommendation.baselines.content import content_score


def gap_relevance(
    skill_ids: list,
    gaps: dict,
    levels: dict,
) -> float:
    return content_score(skill_ids, gaps, levels)


def prerequisite_fit(
    taught_names: list[str],
    open_gap_names: set[str],
    parents: dict[str, list[str]],
) -> float:
    scores: list[float] = []
    for name in taught_names:
        if name not in open_gap_names:
            continue
        required = parents.get(name, [])
        if not required:
            scores.append(1.0)
            continue
        ready = sum(1 for item in required if item not in open_gap_names)
        scores.append(ready / len(required))
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def difficulty_fit(resource_difficulty: float, learner_level: float) -> float:
    delta = abs(float(resource_difficulty) - float(learner_level))
    return max(0.0, min(1.0, 1.0 - (delta / 4.0)))


def preference_fit(kind: str, resource_format: str | None, formats: list[str]) -> float:
    wanted = {item.lower() for item in formats}
    if not wanted:
        return 0.5
    if kind == "COURSE":
        fmt = (resource_format or "").lower()
        return 1.0 if fmt in wanted else 0.2
    if kind == "PROJECT":
        return 1.0 if "hands-on" in wanted else 0.5
    if "live" in wanted or "hands-on" in wanted:
        return 1.0
    return 0.5


def collaborative_jaccard(
    employee_ids: set[object], resource_ids: set[object]
) -> float:
    if not employee_ids or not resource_ids:
        return 0.0
    inter = len(employee_ids.intersection(resource_ids))
    union = len(employee_ids.union(resource_ids))
    if union == 0:
        return 0.0
    return inter / union


def kg_score(
    taught_names: list[str],
    gap_names: set[str],
    ancestors: dict[str, set[str]],
    related: dict[str, set[str]],
) -> float:
    if not taught_names:
        return 0.0
    best = 0.0
    for name in taught_names:
        if name in gap_names:
            best = max(best, 1.0)
            continue
        if any(name in ancestors.get(gap, set()) for gap in gap_names):
            best = max(best, 0.75)
            continue
        if any(name in related.get(gap, set()) for gap in gap_names):
            best = max(best, 0.4)
    return best


def weighted_score(components: dict[str, float], weights: dict[str, float]) -> float:
    total_w = 0.0
    total = 0.0
    for key, weight in weights.items():
        if weight <= 0:
            continue
        total_w += weight
        total += weight * float(components.get(key, 0.0))
    if total_w <= 0:
        return 0.0
    return total / total_w


def hybrid_reason(
    components: dict[str, float],
    weights: dict[str, float],
    matched_names: list[str],
) -> str:
    names = ", ".join(matched_names[:4]) or "open skill gaps"
    ranked = sorted(
        ((key, weights.get(key, 0.0) * components.get(key, 0.0)) for key in weights),
        key=lambda item: item[1],
        reverse=True,
    )
    top = ", ".join(f"{key} {components.get(key, 0.0):.2f}" for key, _ in ranked[:3])
    return (
        f"Weighted hybrid of seven signals for {names}. "
        f"Strongest: {top}. Collaborative filtering uses skill overlap "
        "(no click log yet)."
    )


__all__ = [
    "collaborative_jaccard",
    "difficulty_fit",
    "gap_relevance",
    "hybrid_reason",
    "kg_score",
    "preference_fit",
    "prerequisite_fit",
    "weighted_score",
]
