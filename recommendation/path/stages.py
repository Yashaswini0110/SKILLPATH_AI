"""Split an ordered path into foundation → core → advanced.

Stages follow depth in the selected DAG. They do not reorder skills.
"""

from __future__ import annotations

STAGES = ("FOUNDATION", "CORE", "ADVANCED")


def assign_stages(
    ordered: list[str],
    blocked_by: dict[str, list[str]],
    kinds: dict[str, str] | None = None,
) -> dict[str, str]:
    selected = set(ordered)
    depth: dict[str, int] = {}

    def get_depth(name: str) -> int:
        if name in depth:
            return depth[name]
        parents = [item for item in blocked_by.get(name, []) if item in selected]
        depth[name] = 0 if not parents else 1 + max(get_depth(item) for item in parents)
        return depth[name]

    for name in ordered:
        get_depth(name)
    max_depth = max(depth.values(), default=0)
    kinds = kinds or {}
    stages: dict[str, str] = {}
    for name in ordered:
        current_depth = depth[name]
        if current_depth == 0 and (max_depth >= 1 or kinds.get(name) == "FOUNDATION"):
            stages[name] = "FOUNDATION"
        elif max_depth >= 2 and current_depth == max_depth:
            stages[name] = "ADVANCED"
        else:
            stages[name] = "CORE"
    if max_depth < 2:
        first_core = next(
            (index for index, name in enumerate(ordered) if stages[name] == "CORE"),
            None,
        )
        if first_core is not None:
            for index, name in enumerate(ordered):
                if stages[name] == "FOUNDATION" and index > first_core:
                    stages[name] = "ADVANCED"
    return stages


def group_stages(
    ordered: list[str], stages: dict[str, str]
) -> list[tuple[str, list[str]]]:
    groups: list[tuple[str, list[str]]] = []
    for name in ordered:
        stage = stages.get(name, "CORE")
        if not groups or groups[-1][0] != stage:
            groups.append((stage, [name]))
        else:
            groups[-1][1].append(name)
    return groups
