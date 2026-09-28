from optimization.compare import compare_methods
from optimization.greedy import greedy_select
from optimization.ortools_solver import ortools_select
from optimization.schedule import pack_weeks


def test_greedy_stops_at_capacity() -> None:
    ordered = ["A", "B", "C"]
    durations = {"A": 10, "B": 10, "C": 10}
    parents = {"B": ["A"], "C": ["B"]}
    selected = greedy_select(
        ordered, durations=durations, parents=parents, capacity_hours=20
    )
    assert selected == ["A", "B"]


def test_ortools_prefers_cheaper_equal_coverage() -> None:
    ordered = ["A", "B", "C"]
    durations = {"A": 10, "B": 2, "C": 2}
    parents = {"C": ["B"]}
    chosen = ortools_select(
        ordered,
        durations=durations,
        parents=parents,
        gap_names={"A", "C"},
        capacity_hours=12,
    )
    assert chosen == ["B", "C"]


def test_compare_methods_flags_topo_over_budget() -> None:
    scores = compare_methods(
        ["A", "B", "C"],
        durations={"A": 10, "B": 10, "C": 10},
        edges=[("A", "B"), ("B", "C")],
        gap_names={"A", "B", "C"},
        hours_per_week=10,
        deadline_weeks=2,
    )
    assert scores["TOPOLOGICAL"].hours_violation_count == 1
    assert scores["GREEDY"].hours_violation_count == 0
    assert scores["ORTOOLS"].hours_violation_count == 0
    assert scores["ORTOOLS"].prerequisite_violation_count == 0
    assert scores["GREEDY"].total_hours <= 20
    assert scores["ORTOOLS"].total_hours <= 20


def test_pack_weeks_splits_across_weeks() -> None:
    spans = pack_weeks([6, 6], hours_per_week=10)
    assert spans[0].week_start == 1
    assert spans[0].week_end == 1
    assert spans[1].week_start == 1
    assert spans[1].week_end == 2
