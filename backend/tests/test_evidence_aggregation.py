import pytest
from ml.evidence.aggregation import EvidenceItem, aggregate_skill, confidence_label


def test_single_self_declaration_confidence() -> None:
    result = aggregate_skill(
        [
            EvidenceItem(
                source_type="SELF",
                extracted_level=4.0,
                reliability=0.3,
                strength=1.0,
                recency=1.0,
                inferred=False,
            )
        ]
    )
    assert result.confidence == pytest.approx(0.3)
    assert result.current_level == 4.0
    assert result.conflict is False
    assert result.recommend_assessment is False
    assert confidence_label(result.confidence) == "LOW"


def test_self_and_resume_weighted_level() -> None:
    result = aggregate_skill(
        [
            EvidenceItem("SELF", 4.0, 0.3, 1.0, 1.0, False),
            EvidenceItem("RESUME", 2.0, 0.6, 0.6, 1.0, True),
        ]
    )
    # w_self = 0.3, w_resume = 0.36
    # C = 1 - (0.7 * 0.64) = 0.552
    # L = (0.3*4 + 0.36*2) / 0.66 = 2.909...
    assert result.confidence == pytest.approx(0.552)
    assert result.current_level == pytest.approx(2.909, abs=0.001)
    assert result.conflict is True
    assert result.recommend_assessment is True


def test_matching_levels_are_not_conflicts() -> None:
    result = aggregate_skill(
        [
            EvidenceItem("SELF", 4.0, 0.3, 1.0, 1.0, False),
            EvidenceItem("RESUME", 4.0, 0.6, 1.0, 1.0, True),
        ]
    )
    assert result.conflict is False
    assert result.current_level == 4.0


def test_conflict_threshold_is_configurable() -> None:
    items = [
        EvidenceItem("SELF", 4.0, 0.3, 1.0, 1.0, False),
        EvidenceItem("RESUME", 2.0, 0.6, 1.0, 1.0, True),
    ]
    flagged = aggregate_skill(items, conflict_variance=1.0)
    ignored = aggregate_skill(items, conflict_variance=5.0)
    assert flagged.conflict is True
    assert ignored.conflict is False
