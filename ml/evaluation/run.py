"""Run the Phase 27 evaluation suite and return a report dict."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ml.evaluation.extraction import extraction_scores
from ml.evaluation.gaps import gap_ranking_ndcg
from ml.evaluation.metrics import (
    average_precision_at_k,
    coverage,
    intra_list_diversity,
    mean_metric,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from ml.evaluation.paths import path_metrics
from ml.evaluation.ranker import (
    DEFAULT_WEIGHTS,
    HYBRID_KEYS,
    METHODS,
    load_courses,
    rank_courses,
    taxonomy_graph,
)

K = 5


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _binary_relevance(titles: list[str]) -> dict[str, float]:
    return {title: 1.0 for title in titles}


def _method_metrics(
    queries: list[dict[str, Any]],
    courses: list[dict[str, Any]],
    graph: dict[str, Any],
    method: str,
    weights: dict[str, float] | None = None,
) -> dict[str, float]:
    precisions: list[float] = []
    recalls: list[float] = []
    ndcgs: list[float] = []
    maps: list[float] = []
    recommended: list[set[str]] = []
    diversity: list[float] = []
    catalog = {row["title"] for row in courses}
    for query in queries:
        ranked = rank_courses(
            courses,
            query["open_gaps"],
            method=method,
            graph=graph,
            formats=query.get("formats") or [],
            known_skills=set(query.get("known_skills") or []),
            weights=weights,
        )
        titles = [item.title for item in ranked]
        relevant = set(query["relevant_courses"])
        precisions.append(precision_at_k(titles, relevant, K))
        recalls.append(recall_at_k(titles, relevant, K))
        ndcgs.append(ndcg_at_k(titles, _binary_relevance(list(relevant)), K))
        maps.append(average_precision_at_k(titles, relevant, K))
        top = ranked[:K]
        recommended.append({item.title for item in top})
        diversity.append(intra_list_diversity([set(item.skills) for item in top]))
    return {
        "precision_at_5": mean_metric(precisions),
        "recall_at_5": mean_metric(recalls),
        "ndcg_at_5": mean_metric(ndcgs),
        "map_at_5": mean_metric(maps),
        "coverage": coverage(recommended, catalog),
        "diversity": mean_metric(diversity),
    }


def evaluate(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    rec_eval = _load_json(root / "datasets" / "synthetic" / "recommendation_eval.json")
    courses = load_courses(root / "datasets" / "processed" / "resource_catalog.json")
    graph = taxonomy_graph(root / "datasets" / "processed" / "skill_prerequisites.json")
    queries = rec_eval["queries"]
    methods = {
        method: _method_metrics(queries, courses, graph, method) for method in METHODS
    }
    full = _method_metrics(queries, courses, graph, "HYBRID", DEFAULT_WEIGHTS)
    ablations: dict[str, Any] = {"full": full}
    for key in HYBRID_KEYS:
        dropped = dict(DEFAULT_WEIGHTS)
        dropped[key] = 0.0
        variant = _method_metrics(queries, courses, graph, "HYBRID", dropped)
        ablations[f"minus_{key}"] = {
            **variant,
            "ndcg_delta": variant["ndcg_at_5"] - full["ndcg_at_5"],
        }
    return {
        "synthetic": True,
        "disclaimer": (
            "Synthetic labeled evaluation. Results do not represent "
            "real-world employee behavior."
        ),
        "methods": methods,
        "ablation": ablations,
        "extraction": extraction_scores(
            root / "datasets" / "synthetic" / "resume_extraction_eval.json",
            root / "datasets" / "processed" / "skill_taxonomy.json",
        ),
        "gap_ranking": gap_ranking_ndcg(
            root / "datasets" / "synthetic" / "gap_ranking_eval.json"
        ),
        "learning_path": path_metrics(
            root / "datasets" / "synthetic" / "path_eval.json",
            root / "datasets" / "processed" / "skill_prerequisites.json",
            root / "datasets" / "processed" / "resource_catalog.json",
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Evaluation results",
        "",
        report["disclaimer"],
        "",
        "All input sets are labeled `synthetic: true`.",
        "",
        "## Recommendation methods @5",
        "",
        "| Method | P@5 | R@5 | NDCG@5 | MAP@5 | Coverage | Diversity |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for method, row in report["methods"].items():
        lines.append(
            "| {method} | {precision_at_5:.3f} | {recall_at_5:.3f} | "
            "{ndcg_at_5:.3f} | {map_at_5:.3f} | {coverage:.3f} | "
            "{diversity:.3f} |".format(method=method, **row)
        )
    lines.extend(
        [
            "",
            "## Hybrid ablation (NDCG@5 delta vs full)",
            "",
            "| Variant | NDCG@5 | delta |",
            "| --- | --- | --- |",
            "| full | {ndcg_at_5:.3f} | 0.000 |".format(**report["ablation"]["full"]),
        ]
    )
    for key, row in report["ablation"].items():
        if key == "full":
            continue
        lines.append(f"| {key} | {row['ndcg_at_5']:.3f} | {row['ndcg_delta']:+.3f} |")
    ext = report["extraction"]
    gap = report["gap_ranking"]
    path = report["learning_path"]
    lines.extend(
        [
            "",
            "## Extraction",
            "",
            f"Precision {ext['precision']:.3f}, recall {ext['recall']:.3f}, "
            f"F1 {ext['f1']:.3f} on {int(ext['cases'])} synthetic resumes.",
            "",
            "## Skill-gap ranking",
            "",
            f"NDCG@10 {gap['ndcg_at_10']:.3f} on {int(gap['queries'])} "
            "synthetic personas.",
            "",
            "## Learning path",
            "",
            f"Prerequisite violations {path['prerequisite_violations']:.3f}, "
            f"coverage {path['skill_coverage']:.3f}, "
            f"hours {path['total_learning_hours']:.1f}, "
            f"efficiency {path['path_efficiency']:.3f}.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("synthetic") is not True:
        raise ValueError(f"{path} must be labeled synthetic")
    return payload
