"""Path metrics for greedy vs topological vs OR-Tools."""

from __future__ import annotations

import math
from dataclasses import dataclass

from knowledge_graph.cycle import prerequisite_violation_count


@dataclass(frozen=True)
class MethodScore:
    method: str
    selected: list[str]
    total_hours: int
    estimated_weeks: int
    skill_coverage: float
    prerequisite_violation_count: int
    hours_violation_count: int
    path_efficiency: float

    def as_public(self) -> dict[str, object]:
        return {
            "method": self.method,
            "selected_count": len(self.selected),
            "total_hours": self.total_hours,
            "estimated_weeks": self.estimated_weeks,
            "skill_coverage": self.skill_coverage,
            "prerequisite_violation_count": self.prerequisite_violation_count,
            "hours_violation_count": self.hours_violation_count,
            "path_efficiency": self.path_efficiency,
        }


def score_selection(
    method: str,
    selected: list[str],
    *,
    durations: dict[str, int],
    gap_names: set[str],
    edges: list[tuple[str, str]],
    hours_per_week: int,
    deadline_weeks: int,
) -> MethodScore:
    weekly = max(1, int(hours_per_week))
    deadline = max(1, int(deadline_weeks))
    capacity = weekly * deadline
    total = sum(max(0, int(durations.get(name, 0))) for name in selected)
    coverage = (
        0.0
        if not gap_names
        else len([name for name in selected if name in gap_names]) / len(gap_names)
    )
    weeks = 1 if total == 0 else max(1, math.ceil(total / weekly))
    return MethodScore(
        method=method,
        selected=list(selected),
        total_hours=total,
        estimated_weeks=weeks,
        skill_coverage=round(coverage, 4),
        prerequisite_violation_count=prerequisite_violation_count(selected, edges),
        hours_violation_count=1 if total > capacity else 0,
        path_efficiency=round(coverage / weeks, 4),
    )
