import json
from pathlib import Path

from app.db.seed import (
    RESOURCE_PATH,
    TAXONOMY_PATH,
    load_resource_catalog,
    load_taxonomy,
)


def test_resource_catalog_is_synthetic_and_mapped() -> None:
    taxonomy_names = {item["name"] for item in load_taxonomy(TAXONOMY_PATH)}
    catalog = load_resource_catalog(RESOURCE_PATH)
    assert catalog["synthetic"] is True
    assert catalog.get("courses")
    assert catalog.get("projects")
    assert catalog.get("mentors")

    used: set[str] = set()
    for group in ("courses", "projects", "mentors"):
        for item in catalog[group]:
            for skill in item["skills"]:
                name = skill["name"]
                assert name in taxonomy_names, f"{name} is not in the taxonomy"
                used.add(name)
                assert 1 <= int(skill["level"]) <= 5
    assert used == taxonomy_names


def test_resource_catalog_file_is_valid_json() -> None:
    payload = json.loads(Path(RESOURCE_PATH).read_text(encoding="utf-8"))
    titles = [row["title"] for row in payload["courses"]]
    assert len(titles) == len(set(titles))
    names = [row["name"] for row in payload["mentors"]]
    assert len(names) == len(set(names))
