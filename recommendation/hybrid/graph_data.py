"""Load the catalog DAG used by hybrid prerequisite and KG signals."""

from __future__ import annotations

import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import TypedDict


class TaxonomyGraph(TypedDict):
    parents: dict[str, list[str]]
    related: dict[str, set[str]]
    ancestors: dict[str, set[str]]


@lru_cache(maxsize=1)
def load_taxonomy_graph(path: str) -> TaxonomyGraph:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    parents: dict[str, list[str]] = defaultdict(list)
    children: dict[str, list[str]] = defaultdict(list)
    for src, dst in payload.get("prerequisites", []):
        parents[dst].append(src)
        children[src].append(dst)
    related: dict[str, set[str]] = defaultdict(set)
    for src, dst in payload.get("related", []) + payload.get("complements", []):
        related[src].add(dst)
        related[dst].add(src)
    ancestors: dict[str, set[str]] = {}

    def walk(node: str, seen: set[str]) -> set[str]:
        if node in ancestors:
            return ancestors[node]
        bag: set[str] = set()
        for parent in parents.get(node, []):
            if parent in seen:
                continue
            bag.add(parent)
            bag.update(walk(parent, seen | {parent}))
        ancestors[node] = bag
        return bag

    for node in set(parents) | set(children):
        walk(node, {node})
    return {
        "parents": dict(parents),
        "related": dict(related),
        "ancestors": ancestors,
    }
