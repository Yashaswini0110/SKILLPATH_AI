from llm.verbalize import verbalize
from recommendation.explain import explain_mentor, explain_practice, explain_resource


def test_resource_facts_use_only_provided_skills() -> None:
    explanation = explain_resource(
        rank=1,
        matched=[("Deep Learning", "CRITICAL")],
        components={
            "semantic": 0.89,
            "prerequisite": 1.0,
            "difficulty": 0.85,
            "preference": 1.0,
        },
        method="HYBRID",
        formats=["video"],
    )
    texts = " ".join(item.text for item in explanation.facts)
    assert "Deep Learning" in texts
    assert "Python" not in texts
    assert "Gap priority = Critical." in texts
    assert "Semantic similarity = 0.89." in texts
    assert "Prerequisites are satisfied." in texts
    assert "Difficulty matches learner level." in texts
    assert "Learner prefers video." in texts
    assert explanation.verbalization.startswith("Addresses Deep Learning gap.")
    assert "I think" not in explanation.verbalization.lower()


def test_verbalize_does_not_invent_when_llm_flag_is_on() -> None:
    explanation = explain_practice(
        rank=2,
        skill="RAG",
        priority="HIGH",
        course_title="RAG Fundamentals",
        project_title="Document Q&A",
        current_level=2.0,
        required_level=4.0,
    )
    from recommendation.explain import ExplanationFact

    facts = [
        ExplanationFact("gap", "Addresses RAG gap.", "RAG"),
        ExplanationFact("priority", "Gap priority = High.", "HIGH"),
    ]
    text = verbalize(facts, use_llm=True)
    assert text == "Addresses RAG gap. Gap priority = High."
    assert "Document Q&A" not in text
    assert "learn" in explanation.verbalization.lower()
    assert "practice" in explanation.verbalization.lower()


def test_mentor_explanation_counts_overlap() -> None:
    explanation = explain_mentor(
        rank=1,
        matched_names=["RAG", "LLMs", "Vector Databases"],
        top_count=5,
        hours=10,
        open_slots=4,
        domains=["AI/ML"],
    )
    assert explanation.facts[0].text.startswith(
        "3 of your top 5 skill gaps match this mentor's expertise"
    )
    assert "10 available hours/month" in explanation.verbalization
    assert "4 open mentee slots" in explanation.verbalization
