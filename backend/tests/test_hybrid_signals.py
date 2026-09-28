from pathlib import Path
from uuid import uuid4

from recommendation.hybrid.graph_data import load_taxonomy_graph
from recommendation.hybrid.signals import (
    collaborative_jaccard,
    difficulty_fit,
    kg_score,
    preference_fit,
    prerequisite_fit,
    weighted_score,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_prerequisite_fit_penalizes_open_parents() -> None:
    parents = {"Deep Learning": ["Machine Learning"]}
    ready = prerequisite_fit(["Deep Learning"], {"Deep Learning"}, parents)
    blocked = prerequisite_fit(
        ["Deep Learning"], {"Deep Learning", "Machine Learning"}, parents
    )
    assert ready == 1.0
    assert blocked == 0.0


def test_difficulty_and_preference_and_jaccard() -> None:
    assert difficulty_fit(3, 3) == 1.0
    assert difficulty_fit(5, 1) == 0.0
    assert preference_fit("COURSE", "video", ["video"]) == 1.0
    assert preference_fit("COURSE", "text", ["video"]) == 0.2
    assert preference_fit("COURSE", "video", []) == 0.5
    assert preference_fit("PROJECT", None, ["hands-on"]) == 1.0
    assert preference_fit("MENTOR", None, ["live"]) == 1.0
    a, b, c = uuid4(), uuid4(), uuid4()
    assert collaborative_jaccard({a, b}, {b, c}) == 1 / 3
    assert collaborative_jaccard(set(), {a}) == 0.0


def test_kg_score_uses_gap_then_ancestor_then_related() -> None:
    ancestors = {"RAG": {"LLMs", "Statistics"}}
    related = {"RAG": {"Vector Databases"}}
    assert kg_score(["RAG"], {"RAG"}, ancestors, related) == 1.0
    assert kg_score(["Statistics"], {"RAG"}, ancestors, related) == 0.75
    assert kg_score(["Vector Databases"], {"RAG"}, ancestors, related) == 0.4
    assert kg_score(["Git"], {"RAG"}, ancestors, related) == 0.0


def test_weighted_score_is_normalized_mean() -> None:
    parts = {"semantic": 1.0, "gap": 0.0}
    weights = {"semantic": 1.0, "gap": 1.0}
    assert weighted_score(parts, weights) == 0.5
    assert weighted_score(parts, {"semantic": 0.0, "gap": 0.0}) == 0.0


def test_taxonomy_graph_loads_rag_ancestors() -> None:
    graph = load_taxonomy_graph(
        str(REPO_ROOT / "datasets" / "processed" / "skill_prerequisites.json")
    )
    assert "Machine Learning" in graph["parents"]["Deep Learning"]
    assert "Statistics" in graph["ancestors"]["RAG"]
    assert "Vector Databases" in graph["related"]["LLMs"]
