"""Skill-extraction Precision / Recall / F1 on the labeled synthetic set."""

from __future__ import annotations

import json
from pathlib import Path

from ml.evaluation.metrics import f1_score, mean_metric
from ml.skill_extraction.catalog_loader import load_taxonomy_mapper
from ml.skill_extraction.pipeline import extract_skills_from_text


def extraction_scores(eval_path: Path, taxonomy_path: Path) -> dict[str, float]:
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    if payload.get("synthetic") is not True:
        raise ValueError("extraction eval set must be labeled synthetic")
    mapper = load_taxonomy_mapper(taxonomy_path)
    precisions: list[float] = []
    recalls: list[float] = []
    f1s: list[float] = []
    for case in payload["cases"]:
        predicted = {
            item.canonical_name
            for item in extract_skills_from_text(case["text"], mapper)
        }
        gold = set(case["gold_canonical_names"])
        if not predicted and not gold:
            precision = recall = 1.0
        elif not predicted or not gold:
            precision = recall = 0.0
        else:
            overlap = predicted & gold
            precision = len(overlap) / len(predicted)
            recall = len(overlap) / len(gold)
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1_score(precision, recall))
    return {
        "precision": mean_metric(precisions),
        "recall": mean_metric(recalls),
        "f1": mean_metric(f1s),
        "cases": float(len(payload["cases"])),
    }
