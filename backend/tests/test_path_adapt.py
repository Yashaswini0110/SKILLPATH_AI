from recommendation.path.adapt import adapt_path, path_effect, refresher_hours


def test_path_effect_thresholds() -> None:
    assert path_effect(0.54) == "REFRESHER"
    assert path_effect(0.55) is None
    assert path_effect(0.70) is None
    assert path_effect(0.90) == "SKIP"
    assert path_effect(1.0) == "SKIP"


def test_weak_quiz_adds_refresher_hours_and_keeps_skill() -> None:
    adapted = adapt_path(
        ["Python", "FastAPI"],
        {"Python": 0.25},
        gap_names={"Python", "FastAPI"},
        durations={"Python": 28, "FastAPI": 20},
    )
    assert adapted.ordered == ["Python", "FastAPI"]
    assert adapted.extras["Python"] == refresher_hours(28)
    assert adapted.adaptations[0].action == "REFRESHER"
    assert "Python" in adapted.gap_names
    assert adapted.skipped == []


def test_strong_quiz_skips_skill_so_dependents_remain() -> None:
    adapted = adapt_path(
        ["Python", "FastAPI"],
        {"Python": 0.90},
        gap_names={"Python", "FastAPI"},
        durations={"Python": 28, "FastAPI": 20},
    )
    assert adapted.ordered == ["FastAPI"]
    assert adapted.skipped == ["Python"]
    assert "Python" not in adapted.gap_names
    assert adapted.adaptations[0].action == "SKIP"
    assert adapted.extras == {}


def test_strong_quiz_records_skip_when_skill_already_left_the_plan() -> None:
    adapted = adapt_path(
        ["FastAPI"],
        {"Python": 1.0},
        gap_names={"FastAPI"},
        durations={"FastAPI": 20},
    )
    assert adapted.ordered == ["FastAPI"]
    assert adapted.skipped == ["Python"]
    assert adapted.adaptations[0].action == "SKIP"
