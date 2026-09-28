from uuid import uuid4

from recommendation.baselines.content import content_score
from recommendation.baselines.popularity import popularity_score
from recommendation.baselines.semantic import HashingEncoder, semantic_score
from recommendation.baselines.vectors import cosine_similarity


def test_cosine_identical_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_content_score_ranks_overlapping_skills() -> None:
    skill_a, skill_b = uuid4(), uuid4()
    order = [skill_a, skill_b]
    gaps = {skill_a: 3.0, skill_b: 0.0}
    match = {skill_a: 4.0, skill_b: 0.0}
    miss = {skill_a: 0.0, skill_b: 5.0}
    assert content_score(order, gaps, match) > content_score(order, gaps, miss)


def test_popularity_uses_rating_or_experience() -> None:
    assert popularity_score(rating=4.0, skill_count=1, years=None) == 0.8
    assert popularity_score(rating=None, skill_count=1, years=15) == 1.0


def test_hashing_semantic_prefers_shared_terms() -> None:
    encoder = HashingEncoder()
    close = semantic_score(
        "Deep Learning gap 3.4 priority CRITICAL",
        "Deep Learning with Neural Nets. Skills: Deep Learning.",
        encoder,
    )
    far = semantic_score(
        "Deep Learning gap 3.4 priority CRITICAL",
        "Git Collaboration. Skills: Git.",
        encoder,
    )
    assert close > far
