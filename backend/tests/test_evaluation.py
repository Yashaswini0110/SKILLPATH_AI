"""Phase 27 research evaluation on labeled synthetic sets."""

from __future__ import annotations

from pathlib import Path

import pytest
from ml.evaluation.explain import explanation_is_faithful
from ml.evaluation.metrics import (
    average_precision_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from ml.evaluation.run import evaluate

pytestmark = pytest.mark.evaluation

REPO = Path(__file__).resolve().parents[2]


def test_ranking_metrics_are_well_behaved() -> None:
    ranked = ["a", "b", "c", "d"]
    relevant = {"a", "c"}
    assert precision_at_k(ranked, relevant, 2) == 0.5
    assert recall_at_k(ranked, relevant, 2) == 0.5
    assert average_precision_at_k(ranked, relevant, 4) > 0
    perfect = ndcg_at_k(["a", "c"], {"a": 3, "c": 2}, 2)
    inverted = ndcg_at_k(["x", "y"], {"a": 3, "c": 2}, 2)
    assert perfect == 1.0
    assert inverted == 0.0


def test_synthetic_evaluation_report() -> None:
    report = evaluate(REPO)
    assert report["synthetic"] is True
    assert "do not represent" in report["disclaimer"]
    methods = report["methods"]
    assert set(methods) == {"POPULARITY", "CONTENT", "SEMANTIC", "KG", "HYBRID"}
    for row in methods.values():
        assert 0.0 <= row["precision_at_5"] <= 1.0
        assert 0.0 <= row["ndcg_at_5"] <= 1.0
        assert 0.0 <= row["coverage"] <= 1.0
    assert methods["HYBRID"]["ndcg_at_5"] >= 0.8
    assert methods["CONTENT"]["ndcg_at_5"] > 0
    assert methods["KG"]["ndcg_at_5"] > 0
    assert methods["POPULARITY"]["ndcg_at_5"] > 0

    ablation = report["ablation"]
    assert "full" in ablation
    for key in (
        "semantic",
        "gap",
        "prerequisite",
        "difficulty",
        "preference",
        "collaborative",
        "kg",
    ):
        assert f"minus_{key}" in ablation
        assert "ndcg_delta" in ablation[f"minus_{key}"]

    assert report["extraction"]["f1"] >= 0.85
    assert report["gap_ranking"]["ndcg_at_10"] >= 0.7
    assert report["learning_path"]["prerequisite_violations"] == 0
    assert report["learning_path"]["skill_coverage"] > 0


def test_eval_sets_are_labeled_synthetic() -> None:
    folder = REPO / "datasets" / "synthetic"
    for name in (
        "recommendation_eval.json",
        "gap_ranking_eval.json",
        "path_eval.json",
        "resume_extraction_eval.json",
    ):
        text = (folder / name).read_text(encoding="utf-8")
        assert '"synthetic": true' in text


def test_explanation_stays_on_stored_facts() -> None:
    assert explanation_is_faithful(
        rank=1,
        matched=[("Deep Learning", "CRITICAL")],
        components={
            "semantic": 0.8,
            "gap": 0.9,
            "prerequisite": 1.0,
            "difficulty": 0.75,
            "final": 0.82,
        },
        method="HYBRID",
    )
