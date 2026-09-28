"""Map a skill on the path to one catalog course and optional project."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID


@dataclass(frozen=True)
class ResourceCandidate:
    resource_id: UUID
    title: str
    taught_level: float
    duration_hours: int
    difficulty: int


T = TypeVar("T")


def pick_resource(
    candidates: list[ResourceCandidate], used: set[UUID]
) -> ResourceCandidate | None:
    available = [item for item in candidates if item.resource_id not in used]
    if not available:
        return None
    available.sort(
        key=lambda item: (-item.taught_level, item.duration_hours, item.title.lower())
    )
    return available[0]
