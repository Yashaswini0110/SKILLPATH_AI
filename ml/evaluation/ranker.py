"""Offline course ranker that reuses the product scoring functions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from recommendation.baselines.content import content_score
from recommendation.baselines.popularity import popularity_score
from recommendation.baselines.semantic import (
    HashingEncoder,
    gap_summary,
    resource_text,
    semantic_score,
)
from recommendation.hybrid.graph_data import load_taxonomy_graph
from recommendation.hybrid.signals import (
    collaborative_jaccard,
    difficulty_fit,
    kg_score,
    preference_fit,
    prerequisite_fit,
    weighted_score,
)

METHODS = ("POPULARITY", "CONTENT", "SEMANTIC", "KG", "HYBRID")
HYBRID_KEYS = (
    "semantic",
    "gap",
    "prerequisite",
    "difficulty",
    "preference",
    "collaborative",
    "kg",
)
DEFAULT_WEIGHTS = {key: 1.0 for key in HYBRID_KEYS}


@dataclass(frozen=True)
class RankedCourse:
    title: str
    score: float
    components: dict[str, float]
    skills: list[str]


def load_courses(catalog_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    if payload.get("synthetic") is not True:
        raise ValueError("resource catalog must be labeled synthetic")
    return list(payload["courses"])


def rank_courses(
    courses: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    *,
    method: str,
    graph: dict[str, Any],
    formats: list[str] | None = None,
    known_skills: set[str] | None = None,
    weights: dict[str, float] | None = None,
) -> list[RankedCourse]:
    method = method.upper()
    if method not in METHODS:
        raise ValueError(f"unknown method {method}")
    open_names = {item["name"] for item in gaps}
    skill_order = [item["name"] for item in gaps]
    gap_weights = {item["name"]: float(item["gap"]) for item in gaps}
    candidates = [
        row
        for row in courses
        if open_names.intersection(skill["name"] for skill in row["skills"])
    ]
    encoder = HashingEncoder()
    user_text = gap_summary(
        [(item["name"], float(item["gap"]), item["priority"]) for item in gaps]
    )
    hybrid_w = weights or DEFAULT_WEIGHTS
    known = known_skills or set()
    wanted = formats or []
    ranked: list[RankedCourse] = []
    for row in candidates:
        taught = [item["name"] for item in row["skills"]]
        levels = {item["name"]: float(item["level"]) for item in row["skills"]}
        matched = [item for item in gaps if item["name"] in levels]
        pop = popularity_score(
            rating=float(row["rating"]), skill_count=len(row["skills"]), years=None
        )
        content = content_score(skill_order, gap_weights, levels)
        semantic = semantic_score(
            user_text,
            resource_text(row["title"], row["description"], taught),
            encoder,
        )
        learner = (
            sum(float(item.get("current_level", 0.0)) for item in matched)
            / len(matched)
            if matched
            else 2.5
        )
        parts = {
            "semantic": semantic,
            "gap": content,
            "prerequisite": prerequisite_fit(taught, open_names, graph["parents"]),
            "difficulty": difficulty_fit(float(row["difficulty"]), learner),
            "preference": preference_fit("COURSE", row.get("format"), wanted),
            "collaborative": collaborative_jaccard(known, set(taught)),
            "kg": kg_score(taught, open_names, graph["ancestors"], graph["related"]),
        }
        if method == "POPULARITY":
            score = pop
        elif method == "CONTENT":
            score = content
        elif method == "SEMANTIC":
            score = semantic
        elif method == "KG":
            score = parts["kg"]
        else:
            score = weighted_score(parts, hybrid_w)
        ranked.append(
            RankedCourse(
                title=row["title"],
                score=score,
                components=parts,
                skills=taught,
            )
        )
    ranked.sort(key=lambda item: (-item.score, item.title.lower()))
    return ranked


def taxonomy_graph(path: Path) -> dict[str, Any]:
    return load_taxonomy_graph(str(path))
