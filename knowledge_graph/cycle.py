"""In-memory cycle detection and topological chains for the skill DAG."""

from __future__ import annotations

from collections import defaultdict, deque


def find_cycles(edges: list[tuple[str, str]]) -> list[list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    nodes: set[str] = set()
    for src, dst in edges:
        graph[src].append(dst)
        nodes.add(src)
        nodes.add(dst)

    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> None:
        visiting.add(node)
        stack.append(node)
        for nxt in graph[node]:
            if nxt in visiting:
                start = stack.index(nxt)
                cycles.append(stack[start:] + [nxt])
            elif nxt not in visited:
                dfs(nxt)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(nodes):
        if node not in visited:
            dfs(node)
    return cycles


def assert_acyclic(edges: list[tuple[str, str]]) -> None:
    cycles = find_cycles(edges)
    if cycles:
        sample = " -> ".join(cycles[0])
        raise ValueError(f"Prerequisite graph contains a cycle: {sample}")


def topological_chain(edges: list[tuple[str, str]], target: str) -> list[str]:
    reverse: dict[str, list[str]] = defaultdict(list)
    nodes: set[str] = {target}
    for src, dst in edges:
        reverse[dst].append(src)
        nodes.add(src)
        nodes.add(dst)

    ancestors: set[str] = set()

    def walk(node: str) -> None:
        if node in ancestors:
            return
        ancestors.add(node)
        for parent in reverse[node]:
            walk(parent)

    walk(target)
    subgraph = [
        (src, dst) for src, dst in edges if src in ancestors and dst in ancestors
    ]
    incoming: dict[str, int] = {node: 0 for node in ancestors}
    forward: dict[str, list[str]] = defaultdict(list)
    for src, dst in subgraph:
        forward[src].append(dst)
        incoming[dst] = incoming.get(dst, 0) + 1
        incoming.setdefault(src, incoming.get(src, 0))
    queue = deque(sorted(node for node, count in incoming.items() if count == 0))
    ordered: list[str] = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for nxt in sorted(forward[node]):
            incoming[nxt] -= 1
            if incoming[nxt] == 0:
                queue.append(nxt)
    if target not in ordered:
        ordered.append(target)
    return ordered


def ancestor_subgraph(
    edges: list[tuple[str, str]], target: str
) -> tuple[list[list[str]], list[tuple[str, str]]]:
    reverse: dict[str, list[str]] = defaultdict(list)
    for src, dst in edges:
        reverse[dst].append(src)

    ancestors: set[str] = set()

    def walk(node: str) -> None:
        if node in ancestors:
            return
        ancestors.add(node)
        for parent in reverse[node]:
            walk(parent)

    walk(target)
    subgraph = [
        (src, dst) for src, dst in edges if src in ancestors and dst in ancestors
    ]
    forward: dict[str, list[str]] = defaultdict(list)
    for src, dst in subgraph:
        forward[src].append(dst)
    dist: dict[str, int] = {target: 0}

    def dist_to_target(node: str) -> int:
        if node in dist:
            return dist[node]
        children = forward.get(node, [])
        dist[node] = 1 + max((dist_to_target(child) for child in children), default=0)
        return dist[node]

    for node in ancestors:
        dist_to_target(node)
    max_dist = max(dist.values(), default=0)
    layers: list[list[str]] = [[] for _ in range(max_dist + 1)]
    for node, value in sorted(dist.items()):
        layers[max_dist - value].append(node)
    return layers, subgraph


def ancestor_set(edges: list[tuple[str, str]], targets: list[str]) -> set[str]:
    reverse: dict[str, list[str]] = defaultdict(list)
    for src, dst in edges:
        reverse[dst].append(src)
    seen: set[str] = set()

    def walk(node: str) -> None:
        if node in seen:
            return
        seen.add(node)
        for parent in reverse.get(node, []):
            walk(parent)

    for target in targets:
        walk(target)
    return seen


def topological_order(edges: list[tuple[str, str]], nodes: set[str]) -> list[str]:
    incoming: dict[str, int] = {node: 0 for node in nodes}
    forward: dict[str, list[str]] = defaultdict(list)
    for src, dst in edges:
        if src not in nodes or dst not in nodes:
            continue
        forward[src].append(dst)
        incoming[dst] += 1
    queue = deque(sorted(node for node, count in incoming.items() if count == 0))
    ordered: list[str] = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for nxt in sorted(forward[node]):
            incoming[nxt] -= 1
            if incoming[nxt] == 0:
                queue.append(nxt)
    leftover = sorted(nodes.difference(ordered))
    ordered.extend(leftover)
    return ordered


def prerequisite_violation_count(order: list[str], edges: list[tuple[str, str]]) -> int:
    index = {name: position for position, name in enumerate(order)}
    count = 0
    for src, dst in edges:
        if src not in index or dst not in index:
            continue
        if index[src] >= index[dst]:
            count += 1
    return count
