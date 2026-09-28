"""CP-SAT subset selection with prerequisite and hour-budget constraints."""

from __future__ import annotations

from ortools.sat.python import cp_model

from optimization.greedy import greedy_select


def ortools_select(
    ordered: list[str],
    *,
    durations: dict[str, int],
    parents: dict[str, list[str]],
    gap_names: set[str],
    capacity_hours: int,
    time_limit_seconds: float = 2.0,
) -> list[str]:
    if not ordered:
        return []
    cap = max(0, int(capacity_hours))
    fallback = greedy_select(
        ordered, durations=durations, parents=parents, capacity_hours=cap
    )
    index = {name: position for position, name in enumerate(ordered)}
    model = cp_model.CpModel()
    selected = [model.NewBoolVar(f"sel_{i}") for i in range(len(ordered))]
    pool = set(ordered)
    for position, name in enumerate(ordered):
        for parent in parents.get(name, []):
            if parent not in pool:
                continue
            model.Add(selected[position] <= selected[index[parent]])
    hours = [max(0, int(durations.get(name, 0))) for name in ordered]
    model.Add(sum(selected[i] * hours[i] for i in range(len(ordered))) <= cap)
    model.Maximize(
        sum(
            selected[i] * ((10000 if ordered[i] in gap_names else 10) - hours[i])
            for i in range(len(ordered))
        )
    )
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.num_search_workers = 1
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return fallback
    chosen = [name for i, name in enumerate(ordered) if solver.Value(selected[i]) == 1]
    return chosen
