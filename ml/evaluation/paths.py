"""Learning-path metrics: violations, coverage, hours, efficiency."""

from __future__ import annotations

import json
from pathlib import Path

from recommendation.path.build import plan_path

from ml.evaluation.metrics import mean_metric


def _edges(prereq_path: Path) -> list[tuple[str, str]]:
    payload = json.loads(prereq_path.read_text(encoding="utf-8"))
    return [(src, dst) for src, dst in payload["prerequisites"]]


def _hours_for_skill(courses: list[dict], skill: str) -> float:
    matches = [
        float(row["duration_hours"])
        for row in courses
        if skill in {item["name"] for item in row["skills"]}
    ]
    return min(matches) if matches else 8.0


def path_metrics(
    eval_path: Path, prereq_path: Path, catalog_path: Path, hours_per_week: float = 10.0
) -> dict[str, float]:
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    if payload.get("synthetic") is not True:
        raise ValueError("path eval set must be labeled synthetic")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    courses = catalog["courses"]
    edges = _edges(prereq_path)
    violations: list[float] = []
    coverage: list[float] = []
    hours: list[float] = []
    efficiency: list[float] = []
    for case in payload["queries"]:
        targets = list(case["target_gaps"])
        missing = set(case["missing"])
        plan = plan_path(targets, edges=edges, missing=missing, gap_names=set(targets))
        violations.append(float(plan.violation_count))
        covered = len(set(plan.ordered) & set(targets))
        coverage.append(covered / len(targets) if targets else 1.0)
        total = sum(_hours_for_skill(courses, skill) for skill in plan.ordered)
        hours.append(total)
        weeks = max(total / hours_per_week, 1.0)
        efficiency.append((covered / len(targets) if targets else 1.0) / weeks)
    return {
        "prerequisite_violations": mean_metric(violations),
        "skill_coverage": mean_metric(coverage),
        "total_learning_hours": mean_metric(hours),
        "path_efficiency": mean_metric(efficiency),
        "queries": float(len(payload["queries"])),
    }
