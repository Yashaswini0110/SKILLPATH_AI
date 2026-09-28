from recommendation.path.stages import assign_stages, group_stages

PLAYBOOK = [
    "Statistics",
    "Machine Learning",
    "Deep Learning",
    "Transformers",
    "LLMs",
    "RAG",
]


def _chain_blocked() -> dict[str, list[str]]:
    blocked: dict[str, list[str]] = {PLAYBOOK[0]: []}
    for earlier, later in zip(PLAYBOOK, PLAYBOOK[1:], strict=False):
        blocked[later] = [earlier]
    return blocked


def test_playbook_chain_is_foundation_core_advanced() -> None:
    stages = assign_stages(PLAYBOOK, _chain_blocked())
    assert stages["Statistics"] == "FOUNDATION"
    assert stages["RAG"] == "ADVANCED"
    assert stages["Machine Learning"] == "CORE"
    assert stages["Deep Learning"] == "CORE"
    assert stages["Transformers"] == "CORE"
    assert stages["LLMs"] == "CORE"
    groups = group_stages(PLAYBOOK, stages)
    assert [name for name, _items in groups] == ["FOUNDATION", "CORE", "ADVANCED"]
    assert groups[0][1] == ["Statistics"]
    assert groups[-1][1] == ["RAG"]


def test_single_skill_is_core_unless_marked_foundation() -> None:
    assert assign_stages(["RAG"], {"RAG": []}) == {"RAG": "CORE"}
    assert assign_stages(
        ["Statistics"],
        {"Statistics": []},
        {"Statistics": "FOUNDATION"},
    ) == {"Statistics": "FOUNDATION"}


def test_deeper_foundation_kind_stays_core() -> None:
    ordered = ["Statistics", "Machine Learning"]
    stages = assign_stages(
        ordered,
        {"Statistics": [], "Machine Learning": ["Statistics"]},
        {"Statistics": "FOUNDATION", "Machine Learning": "FOUNDATION"},
    )
    assert stages == {
        "Statistics": "FOUNDATION",
        "Machine Learning": "CORE",
    }


def test_two_depths_have_no_advanced() -> None:
    ordered = ["Python", "FastAPI"]
    stages = assign_stages(ordered, {"Python": [], "FastAPI": ["Python"]})
    assert stages == {"Python": "FOUNDATION", "FastAPI": "CORE"}


def test_parents_outside_the_selected_path_do_not_raise_depth() -> None:
    ordered = ["Machine Learning", "Deep Learning"]
    stages = assign_stages(
        ordered,
        {
            "Machine Learning": ["Statistics"],
            "Deep Learning": ["Machine Learning"],
        },
    )
    assert stages["Machine Learning"] == "FOUNDATION"
    assert stages["Deep Learning"] == "CORE"


def test_group_stages_splits_when_stage_changes() -> None:
    ordered = ["A", "B", "C", "D"]
    stages = {
        "A": "FOUNDATION",
        "B": "FOUNDATION",
        "C": "CORE",
        "D": "ADVANCED",
    }
    assert group_stages(ordered, stages) == [
        ("FOUNDATION", ["A", "B"]),
        ("CORE", ["C"]),
        ("ADVANCED", ["D"]),
    ]


def test_independent_skill_after_core_is_later() -> None:
    ordered = ["Python", "REST APIs", "FastAPI", "PostgreSQL"]
    stages = assign_stages(
        ordered,
        {
            "Python": [],
            "REST APIs": [],
            "FastAPI": ["Python", "REST APIs"],
            "PostgreSQL": [],
        },
    )
    assert stages == {
        "Python": "FOUNDATION",
        "REST APIs": "FOUNDATION",
        "FastAPI": "CORE",
        "PostgreSQL": "ADVANCED",
    }


def test_empty_path_has_no_stages() -> None:
    assert assign_stages([], {}) == {}
    assert group_stages([], {}) == []
