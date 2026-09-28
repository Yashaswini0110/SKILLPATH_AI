"""Phase 26 hop-by-hop integration of the learner pipeline."""

import pytest
from fastapi.testclient import TestClient

from tests.pipeline import (
    assessed_skills,
    gap_analysis,
    learning_path,
    open_gap_names,
    path_skill_names,
    profile_names,
    rec_matched_names,
    recommend_courses,
    set_target_role,
    skill_profile,
    start_learner,
    submit_quiz,
    upload_sample_resume,
)

pytestmark = pytest.mark.integration


def test_resume_feeds_skill_profile(client: TestClient, unique_email: str) -> None:
    headers = start_learner(client, unique_email)
    upload = upload_sample_resume(client, headers)
    extracted = {item["skill"]["canonical_name"] for item in upload["skills"]}
    assert {"Python", "Machine Learning", "Docker"} <= extracted
    assert all(item["source_type"] == "RESUME" for item in upload["skills"])

    profile = skill_profile(client, headers)
    names = profile_names(profile)
    assert {"Python", "Machine Learning", "Docker"} <= names
    python = next(
        item
        for item in profile["skills"]
        if item["skill"]["canonical_name"] == "Python"
    )
    sources = {row["source_type"] for row in python["evidence"]}
    assert "RESUME" in sources
    assert python["inferred_only"] is True


def test_skill_profile_feeds_gap_analysis(
    client: TestClient, unique_email: str
) -> None:
    headers = start_learner(client, unique_email)
    upload_sample_resume(client, headers)
    set_target_role(client, headers)

    profile = skill_profile(client, headers)
    gaps = gap_analysis(client, headers)
    assert gaps["target"]["title"] == "ML Engineer"

    current = {
        item["skill"]["canonical_name"]: float(item["current_level"])
        for item in profile["skills"]
    }
    by_gap = {item["skill"]["canonical_name"]: item for item in gaps["gaps"]}
    assert float(by_gap["Python"]["current_level"]) == current["Python"]
    assert float(by_gap["Python"]["current_level"]) > 0
    assert float(by_gap["Machine Learning"]["current_level"]) > 0
    assert "MLOps" in open_gap_names(gaps)
    assert float(by_gap["MLOps"]["current_level"]) == 0
    assert by_gap["MLOps"]["priority"] != "NONE"


def test_gaps_feed_course_recommendations(
    client: TestClient, unique_email: str
) -> None:
    headers = start_learner(client, unique_email)
    upload_sample_resume(client, headers)
    set_target_role(client, headers)

    open_names = open_gap_names(gap_analysis(client, headers))
    recs = recommend_courses(client, headers)
    assert recs["items"]
    assert recs["target"]["title"] == "ML Engineer"
    assert rec_matched_names(recs) & open_names
    listed_gaps = {item["skill"]["canonical_name"] for item in recs["gap_skills"]}
    assert listed_gaps <= open_names or listed_gaps & open_names


def test_recommendations_align_with_learning_path(
    client: TestClient, unique_email: str
) -> None:
    headers = start_learner(client, unique_email)
    upload_sample_resume(client, headers)
    set_target_role(client, headers)

    recs = recommend_courses(client, headers)
    path = learning_path(client, headers)
    assert path["prerequisite_violation_count"] == 0
    assert path["steps"]
    path_names = set(path_skill_names(path))
    assert rec_matched_names(recs) & path_names
    assert path_names & open_gap_names(gap_analysis(client, headers))


def test_assessment_updates_skill_profile(
    client: TestClient, unique_email: str
) -> None:
    headers = start_learner(client, unique_email)
    upload_sample_resume(client, headers)
    set_target_role(client, headers)

    before = skill_profile(client, headers)
    before_stats = next(
        (
            item
            for item in before["skills"]
            if item["skill"]["canonical_name"] == "Statistics"
        ),
        None,
    )
    before_level = float(before_stats["current_level"]) if before_stats else 0.0

    result = submit_quiz(client, headers, "Statistics", correct=True)
    assert result["passed"] is True
    assert result["percent"] == 1.0

    after = skill_profile(client, headers)
    stats = next(
        item
        for item in after["skills"]
        if item["skill"]["canonical_name"] == "Statistics"
    )
    sources = {row["source_type"] for row in stats["evidence"]}
    assert "ASSESSMENT" in sources
    assert float(stats["current_level"]) > before_level


def test_profile_update_reoptimizes_path(client: TestClient, unique_email: str) -> None:
    headers = start_learner(client, unique_email)
    upload_sample_resume(client, headers)
    set_target_role(client, headers)

    before = learning_path(client, headers)
    quiz_skill = next(
        name for name in path_skill_names(before) if name in assessed_skills()
    )
    submit_quiz(client, headers, quiz_skill, correct=True)

    after = learning_path(client, headers)
    assert after["prerequisite_violation_count"] == 0
    adaptation = next(
        (item for item in after["adaptations"] if item["skill"] == quiz_skill),
        None,
    )
    names = path_skill_names(after)
    if adaptation is not None:
        assert adaptation["action"] in {"SKIP", "REFRESHER"}
    if quiz_skill in names:
        step = next(
            item for item in after["steps"] if item["skill"]["name"] == quiz_skill
        )
        assert step["status"] in {"COMPLETED", "IN_PROGRESS"}
    else:
        assert adaptation is not None and adaptation["action"] == "SKIP"
