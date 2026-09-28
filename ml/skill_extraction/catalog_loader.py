from __future__ import annotations

import json
import uuid
from pathlib import Path

from ml.skill_extraction.taxonomy_mapper import TaxonomyEntry, TaxonomyMapper

SKILL_NS = uuid.UUID("11111111-1111-1111-1111-111111111111")


def catalog_skill_id(name: str) -> uuid.UUID:
    return uuid.uuid5(SKILL_NS, name)


def load_taxonomy_entries(path: str | Path) -> list[TaxonomyEntry]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    entries: list[TaxonomyEntry] = []
    for item in payload.get("skills", []):
        name = str(item["name"])
        entries.append(
            TaxonomyEntry(
                skill_id=catalog_skill_id(name),
                canonical_name=str(item["canonical_name"]),
                name=name,
                aliases=tuple(str(alias) for alias in item.get("aliases") or []),
            )
        )
    return entries


def load_taxonomy_mapper(path: str | Path) -> TaxonomyMapper:
    return TaxonomyMapper(load_taxonomy_entries(path))
