"""Automated explanation faithfulness. Not a user study."""

from __future__ import annotations

from recommendation.explain import explain_resource


def explanation_is_faithful(
    *,
    rank: int,
    matched: list[tuple[str, str]],
    components: dict[str, float],
    method: str,
) -> bool:
    explanation = explain_resource(
        rank=rank,
        matched=matched,
        components=components,
        method=method,
    )
    if not explanation.facts:
        return False
    keys = {fact.key for fact in explanation.facts}
    if "rank" not in keys:
        return False
    text = " ".join(fact.text for fact in explanation.facts).lower()
    verbal = explanation.verbalization.lower()
    for name, _priority in matched:
        if name.lower() not in text:
            return False
    invented = []
    for token in ("hiring", "guarantee", "will get a job"):
        if token in verbal and token not in text:
            invented.append(token)
    return not invented
