from recommendation.mentors.signals import (
    availability_score,
    domain_overlap,
    experience_score,
    mentor_reason,
    skill_overlap,
    workload_score,
)


def test_mentor_signal_bounds() -> None:
    assert skill_overlap(3, 5) == 0.6
    assert skill_overlap(0, 5) == 0.0
    assert domain_overlap(["AI/ML", "GenAI"], ["AI/ML"]) == 0.5
    assert domain_overlap(["Data"], ["AI/ML"]) == 0.0
    assert experience_score(15) == 1.0
    assert availability_score(6) == 0.5
    assert workload_score(2, 4) == 0.5
    assert workload_score(0, 2) == 0.0


def test_mentor_reason_matches_playbook_shape() -> None:
    text = mentor_reason(["RAG", "LLMs", "Vector Databases"], 5, 10, 4)
    assert text.startswith("3 of your top 5 skill gaps match this mentor's expertise")
    assert "10 available hours/month" in text
    assert "4 open mentee slots" in text
