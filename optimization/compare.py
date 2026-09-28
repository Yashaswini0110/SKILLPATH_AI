"""Compare greedy, topological, and OR-Tools selections."""

from __future__ import annotations

from optimization.greedy import greedy_select
from optimization.metrics import MethodScore, score_selection
from optimization.ortools_solver import ortools_select

METHODS = ("ORTOOLS", "GREEDY", "TOPOLOGICAL")


def compare_methods(
    ordered: list[str],
    *,
    durations: dict[str, int],
    edges: list[tuple[str, str]],
    gap_names: set[str],
    hours_per_week: int,
    deadline_weeks: int,
) -> dict[str, MethodScore]:
    weekly = max(1, int(hours_per_week))
    deadline = max(1, int(deadline_weeks))
    capacity = weekly * deadline
    parents: dict[str, list[str]] = {}
    pool = set(ordered)
    for src, dst in edges:
        if dst in pool:
            parents.setdefault(dst, []).append(src)
    greedy = greedy_select(
        ordered, durations=durations, parents=parents, capacity_hours=capacity
    )
    optimized = ortools_select(
        ordered,
        durations=durations,
        parents=parents,
        gap_names=gap_names,
        capacity_hours=capacity,
    )
    scores = {
        "GREEDY": score_selection(
            "GREEDY",
            greedy,
            durations=durations,
            gap_names=gap_names,
            edges=edges,
            hours_per_week=weekly,
            deadline_weeks=deadline,
        ),
        "TOPOLOGICAL": score_selection(
            "TOPOLOGICAL",
            ordered,
            durations=durations,
            gap_names=gap_names,
            edges=edges,
            hours_per_week=weekly,
            deadline_weeks=deadline,
        ),
        "ORTOOLS": score_selection(
            "ORTOOLS",
            optimized,
            durations=durations,
            gap_names=gap_names,
            edges=edges,
            hours_per_week=weekly,
            deadline_weeks=deadline,
        ),
    }
    return scores


def select_names(method: str, scores: dict[str, MethodScore]) -> list[str]:
    key = method.upper()
    if key not in scores:
        key = "ORTOOLS"
    return list(scores[key].selected)
