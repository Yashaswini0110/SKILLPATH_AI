from uuid import UUID, uuid4

from recommendation.projects.pairing import ScoredResource, assign_pairs
from recommendation.projects.signals import (
    duration_fit,
    gap_priority_score,
    proficiency_fit,
    role_fit,
    skills_addressed,
    technology_fit,
)


def test_project_signal_bounds() -> None:
    assert skills_addressed(5) == 1.0
    assert skills_addressed(None) == 0.0
    assert gap_priority_score("CRITICAL") == 1.0
    assert gap_priority_score("HIGH") == 0.8
    assert proficiency_fit(4, 3) == 1.0
    assert duration_fit(10, 10) == 1.0
    assert duration_fit(90, 10) == 0.25
    assert technology_fit(["Python", "scikit-learn"], ["Python", "RAG"]) == 0.5
    first, second = uuid4(), uuid4()
    assert role_fit({first, second}, {first}) == 0.5


def _resource(
    resource_id: UUID, title: str, score: float, difficulty: int = 3
) -> ScoredResource:
    return ScoredResource(
        resource_id=resource_id,
        score=score,
        difficulty=difficulty,
        title=title,
        components={},
    )


def test_assign_pairs_uses_each_resource_once() -> None:
    g1, g2 = uuid4(), uuid4()
    c1, c2 = uuid4(), uuid4()
    p1, p2 = uuid4(), uuid4()
    pairs = assign_pairs(
        [g1, g2],
        {
            g1: [_resource(p1, "A", 0.9, 4), _resource(p2, "B", 0.1, 4)],
            g2: [_resource(p1, "A", 0.8, 4), _resource(p2, "B", 0.7, 4)],
        },
        {
            g1: [_resource(c1, "C1", 1.0)],
            g2: [_resource(c2, "C2", 1.0), _resource(c1, "C1", 1.0)],
        },
    )
    assert [gap for gap, _, _ in pairs] == [g1, g2]
    assert pairs[0][2].resource_id == p1
    assert pairs[1][2].resource_id == p2
    assert {pairs[0][1].resource_id, pairs[1][1].resource_id} == {c1, c2}


def test_assign_pairs_gives_scarce_projects_first() -> None:
    g1, g2 = uuid4(), uuid4()
    c1, c2 = uuid4(), uuid4()
    p_shared, p_other = uuid4(), uuid4()
    pairs = assign_pairs(
        [g1, g2],
        {
            g1: [
                _resource(p_shared, "Shared", 0.9, 4),
                _resource(p_other, "Other", 0.8, 4),
            ],
            g2: [_resource(p_shared, "Shared", 0.85, 4)],
        },
        {
            g1: [_resource(c1, "C1", 1.0)],
            g2: [_resource(c2, "C2", 1.0)],
        },
    )
    by_gap = {gap: project.resource_id for gap, _, project in pairs}
    assert by_gap[g2] == p_shared
    assert by_gap[g1] == p_other
