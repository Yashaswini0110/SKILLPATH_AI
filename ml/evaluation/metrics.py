"""Ranking and set metrics used by Phase 27. No LLM."""

from __future__ import annotations

import math


def precision_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top = ranked[:k]
    if not top:
        return 0.0
    return len(set(top) & relevant) / len(top)


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 1.0
    return len(set(ranked[:k]) & relevant) / len(relevant)


def average_precision_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if not relevant or k <= 0:
        return 0.0
    hits = 0.0
    total = 0.0
    for index, item in enumerate(ranked[:k], start=1):
        if item not in relevant:
            continue
        hits += 1
        total += hits / index
    return total / min(len(relevant), k)


def dcg_at_k(gains: list[float], k: int) -> float:
    score = 0.0
    for index, gain in enumerate(gains[:k], start=1):
        score += gain / math.log2(index + 1)
    return score


def ndcg_at_k(ranked: list[str], relevance: dict[str, float], k: int) -> float:
    gains = [float(relevance.get(item, 0.0)) for item in ranked[:k]]
    ideal = sorted(relevance.values(), reverse=True)
    normalizer = dcg_at_k(ideal, k)
    if normalizer <= 0:
        return 0.0
    return dcg_at_k(gains, k) / normalizer


def mean_metric(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def coverage(recommended: list[set[str]], catalog: set[str]) -> float:
    if not catalog:
        return 0.0
    shown: set[str] = set()
    for bag in recommended:
        shown.update(bag)
    return len(shown) / len(catalog)


def intra_list_diversity(skill_sets: list[set[str]]) -> float:
    if len(skill_sets) < 2:
        return 0.0
    pairs = 0
    distance = 0.0
    for i, left in enumerate(skill_sets):
        for right in skill_sets[i + 1 :]:
            union = left | right
            if not union:
                continue
            pairs += 1
            distance += 1.0 - (len(left & right) / len(union))
    if pairs == 0:
        return 0.0
    return distance / pairs


def f1_score(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
