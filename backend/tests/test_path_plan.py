from knowledge_graph.cycle import (
    ancestor_set,
    prerequisite_violation_count,
    topological_order,
)
from recommendation.path.build import plan_path


def _edges() -> list[tuple[str, str]]:
    return [
        ("Statistics", "Machine Learning"),
        ("Python", "Machine Learning"),
        ("Machine Learning", "Deep Learning"),
        ("Deep Learning", "Transformers"),
        ("Transformers", "LLMs"),
        ("LLMs", "RAG"),
        ("Vector Databases", "RAG"),
    ]


def test_plan_path_orders_foundations_before_rag() -> None:
    missing = {
        "Statistics",
        "Python",
        "Machine Learning",
        "Deep Learning",
        "Transformers",
        "LLMs",
        "RAG",
        "Vector Databases",
    }
    plan = plan_path(
        ["RAG"],
        edges=_edges(),
        missing=missing,
        gap_names={"RAG"},
    )
    assert plan.violation_count == 0
    order = {name: index for index, name in enumerate(plan.ordered)}
    assert order["Statistics"] < order["Machine Learning"]
    assert order["Machine Learning"] < order["Deep Learning"]
    assert order["Deep Learning"] < order["Transformers"]
    assert order["Transformers"] < order["LLMs"]
    assert order["LLMs"] < order["RAG"]
    assert plan.kinds["Statistics"] == "FOUNDATION"
    assert plan.kinds["RAG"] == "GAP"


def test_skipped_foundation_does_not_create_a_violation() -> None:
    missing = {
        "Machine Learning",
        "Deep Learning",
        "Transformers",
        "LLMs",
        "RAG",
    }
    plan = plan_path(
        ["RAG"],
        edges=_edges(),
        missing=missing,
        gap_names={"RAG"},
    )
    assert "Statistics" in plan.skipped
    assert "Statistics" not in plan.ordered
    assert plan.ordered[0] == "Machine Learning"
    assert plan.violation_count == 0


def test_reversed_order_is_a_violation() -> None:
    reversed_order = ["RAG", "LLMs", "Transformers"]
    count = prerequisite_violation_count(reversed_order, _edges())
    assert count >= 2


def test_union_of_targets_stays_acyclic() -> None:
    nodes = ancestor_set(_edges(), ["RAG", "Python"])
    ordered = topological_order(_edges(), nodes)
    assert prerequisite_violation_count(ordered, _edges()) == 0
    assert ordered.index("Python") < ordered.index("Machine Learning")
