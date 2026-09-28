from ml.skill_extraction.normalizer import compact_skill_text, normalize_skill_text


def test_normalize_lowercases_and_strips() -> None:
    assert normalize_skill_text("  Machine Learning  ") == "machine learning"


def test_normalize_punctuation_and_hyphens() -> None:
    assert normalize_skill_text("machine-learning") == "machine learning"
    assert normalize_skill_text("CI/CD") == "ci cd"


def test_normalize_camel_case() -> None:
    assert normalize_skill_text("MachineLearning") == "machine learning"


def test_compact_removes_spaces() -> None:
    assert compact_skill_text("machine-learning") == "machinelearning"
    assert compact_skill_text("K8s") == "k8s"
