"""Expand top gaps through the DAG, then emit a topological sequence.

The LLM is not used. A prerequisite never appears after a skill that
depends on it. Known skills are skipped; missing foundations stay.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from knowledge_graph.cycle import (
    ancestor_set,
    prerequisite_violation_count,
    topological_order,
)


@dataclass(frozen=True)
class PathPlan:
    ordered: list[str]
    skipped: list[str]
    kinds: dict[str, str]
    reasons: dict[str, str]
    blocked_by: dict[str, list[str]]
    violation_count: int
    edges: list[tuple[str, str]] = field(default_factory=list)


def plan_path(
    top_gap_names: list[str],
    *,
    edges: list[tuple[str, str]],
    missing: set[str],
    gap_names: set[str] | None = None,
) -> PathPlan:
    targets = [name for name in top_gap_names if name]
    if not targets:
        return PathPlan(
            ordered=[],
            skipped=[],
            kinds={},
            reasons={},
            blocked_by={},
            violation_count=0,
            edges=[],
        )
    nodes = ancestor_set(edges, targets)
    full_order = topological_order(edges, nodes)
    ordered = [name for name in full_order if name in missing]
    skipped = [name for name in full_order if name not in missing]
    gaps = gap_names if gap_names is not None else set(targets)
    parents: dict[str, list[str]] = {}
    children: dict[str, list[str]] = {}
    for src, dst in edges:
        parents.setdefault(dst, []).append(src)
        children.setdefault(src, []).append(dst)
    kinds = {name: "GAP" if name in gaps else "FOUNDATION" for name in ordered}
    in_path = set(ordered)
    blocked_by = {
        name: sorted(parent for parent in parents.get(name, []) if parent in in_path)
        for name in ordered
    }
    subgraph = [(src, dst) for src, dst in edges if src in in_path and dst in in_path]
    reasons = {
        name: _reason(
            name,
            kinds[name],
            blocked_by[name],
            _supported_gaps(name, children, gaps),
        )
        for name in ordered
    }
    return PathPlan(
        ordered=ordered,
        skipped=skipped,
        kinds=kinds,
        reasons=reasons,
        blocked_by=blocked_by,
        violation_count=prerequisite_violation_count(ordered, edges),
        edges=subgraph,
    )


def _supported_gaps(
    name: str, children: dict[str, list[str]], gaps: set[str]
) -> list[str]:
    seen: set[str] = set()
    stack = list(children.get(name, []))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(children.get(node, []))
    hits = [item for item in sorted(seen) if item in gaps]
    if name in gaps and name not in hits:
        hits.append(name)
    return hits


def _reason(name: str, kind: str, parents: list[str], supported: list[str]) -> str:
    if kind == "GAP":
        text = f"{name} is an open skill gap"
    else:
        targets = [item for item in supported if item != name][:3]
        if targets:
            text = f"{name} is a missing foundation for {', '.join(targets)}"
        else:
            text = f"{name} is a missing foundation on the path"
    if parents:
        text += f". Learn after {', '.join(parents)}"
    return f"{text}."
