"""Greedy capacity-aware selection over a topological order."""

from __future__ import annotations


def greedy_select(
    ordered: list[str],
    *,
    durations: dict[str, int],
    parents: dict[str, list[str]],
    capacity_hours: int,
) -> list[str]:
    selected: list[str] = []
    chosen: set[str] = set()
    used = 0
    pool = set(ordered)
    cap = max(0, int(capacity_hours))
    for name in ordered:
        needed = [parent for parent in parents.get(name, []) if parent in pool]
        if any(parent not in chosen for parent in needed):
            continue
        duration = max(0, int(durations.get(name, 0)))
        if used + duration > cap:
            continue
        selected.append(name)
        chosen.add(name)
        used += duration
    return selected
