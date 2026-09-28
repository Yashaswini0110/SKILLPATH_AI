"""Skill-gap ranking NDCG@10 against graded synthetic labels."""

from __future__ import annotations

import json
from pathlib import Path

from ml.evaluation.metrics import mean_metric, ndcg_at_k
from ml.gap.engine import compute_gap


def gap_ranking_ndcg(eval_path: Path, k: int = 10) -> dict[str, float]:
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    if payload.get("synthetic") is not True:
        raise ValueError("gap ranking eval set must be labeled synthetic")
    scores: list[float] = []
    for case in payload["queries"]:
        ranked: list[tuple[float, str]] = []
        for item in case["skills"]:
            score = compute_gap(
                required_level=float(item["required"]),
                current_level=float(item["current"]),
                importance=float(item["importance"]),
                confidence=float(item["confidence"]),
                criticality=float(item["criticality"]),
                evidence_strength=float(item["evidence"]),
            )
            ranked.append((score.gap, item["name"]))
        ranked.sort(key=lambda row: (-row[0], row[1]))
        order = [name for _, name in ranked]
        relevance = {name: float(gain) for name, gain in case["relevance"].items()}
        scores.append(ndcg_at_k(order, relevance, k))
    return {
        "ndcg_at_10": mean_metric(scores),
        "queries": float(len(payload["queries"])),
    }
