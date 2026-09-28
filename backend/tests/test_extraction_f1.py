import json
from pathlib import Path

from ml.skill_extraction.catalog_loader import load_taxonomy_mapper
from ml.skill_extraction.pipeline import extract_skills_from_text

REPO = Path(__file__).resolve().parents[2]
TAXONOMY = REPO / "datasets" / "processed" / "skill_taxonomy.json"
EVAL_SET = REPO / "datasets" / "synthetic" / "resume_extraction_eval.json"


def _prf(predicted: set[str], gold: set[str]) -> tuple[float, float, float]:
    if not predicted and not gold:
        return 1.0, 1.0, 1.0
    if not predicted or not gold:
        return 0.0, 0.0, 0.0
    overlap = predicted & gold
    precision = len(overlap) / len(predicted)
    recall = len(overlap) / len(gold)
    if precision + recall == 0:
        return 0.0, 0.0, 0.0
    f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def test_dictionary_extraction_f1_meets_mvp_target() -> None:
    mapper = load_taxonomy_mapper(TAXONOMY)
    payload = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    assert payload["synthetic"] is True
    scores = []
    for case in payload["cases"]:
        extracted = extract_skills_from_text(case["text"], mapper)
        predicted = {item.canonical_name for item in extracted}
        gold = set(case["gold_canonical_names"])
        _precision, _recall, f1 = _prf(predicted, gold)
        scores.append(f1)
        missing = gold - predicted
        extra = predicted - gold
        assert not missing, f"{case['id']} missed {missing}; extra {extra}"
    mean_f1 = sum(scores) / len(scores)
    assert mean_f1 >= 0.85
