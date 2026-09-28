"""Phase 26 end-to-end learner story from the playbook."""

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

pytestmark = pytest.mark.e2e


def test_register_resume_role_gap_recommend_path_assess_reoptimize(
    client: TestClient, unique_email: str
) -> None:
    headers = start_learner(client, unique_email)

    extracted = {
        item["skill"]["canonical_name"]
        for item in upload_sample_resume(client, headers)["skills"]
    }
    assert {"Python", "Machine Learning", "Kubernetes"} <= extracted

    profile_after_role = set_target_role(client, headers)
    assert profile_after_role["target_role"]["title"] == "ML Engineer"

    profile = skill_profile(client, headers)
    assert {"Python", "Machine Learning"} <= profile_names(profile)

    gaps = gap_analysis(client, headers)
    assert gaps["target"]["title"] == "ML Engineer"
    open_names = open_gap_names(gaps)
    assert "MLOps" in open_names
    assert gaps["critical_count"] + gaps["high_count"] >= 1

    recs = recommend_courses(client, headers)
    assert recs["items"]
    assert recs["items"][0]["rank"] == 1
    assert recs["items"][0]["explanation"]["facts"]
    assert rec_matched_names(recs) & open_names

    before_path = learning_path(client, headers)
    assert before_path["prerequisite_violation_count"] == 0
    assert before_path["steps"]
    quiz_skill = next(
        name for name in path_skill_names(before_path) if name in assessed_skills()
    )

    result = submit_quiz(client, headers, quiz_skill, correct=True)
    assert result["passed"] is True
    assert result["path_effect"] in {None, "SKIP"}

    after_profile = skill_profile(client, headers)
    assessed = next(
        item
        for item in after_profile["skills"]
        if item["skill"]["name"] == quiz_skill
        or item["skill"]["canonical_name"] == quiz_skill
    )
    assert "ASSESSMENT" in {row["source_type"] for row in assessed["evidence"]}

    after_path = learning_path(client, headers)
    assert after_path["prerequisite_violation_count"] == 0
    adaptation = next(
        (item for item in after_path["adaptations"] if item["skill"] == quiz_skill),
        None,
    )
    names = path_skill_names(after_path)
    if quiz_skill in names:
        step = next(
            item for item in after_path["steps"] if item["skill"]["name"] == quiz_skill
        )
        assert step["status"] in {"COMPLETED", "IN_PROGRESS"}
    else:
        assert adaptation is not None
        assert adaptation["action"] == "SKIP"
