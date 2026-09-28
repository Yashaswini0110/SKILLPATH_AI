from ml.gap.engine import GapThresholds, GapWeights, compute_gap, priority_band


def test_basic_gap_is_clamped() -> None:
    score = compute_gap(
        required_level=4,
        current_level=5,
        importance=1.0,
        confidence=1.0,
        criticality=1.0,
        evidence_strength=1.0,
    )
    assert score.gap_basic == 0
    assert score.gap == 0
    assert score.priority == "NONE"


def test_enhanced_gap_multiplies_components() -> None:
    score = compute_gap(
        required_level=4,
        current_level=0,
        importance=1.0,
        confidence=1.0,
        criticality=0.85,
        evidence_strength=1.0,
    )
    assert score.gap_basic == 4
    assert score.gap == 3.4
    assert score.priority == "CRITICAL"


def test_gap_weights_are_configurable() -> None:
    score = compute_gap(
        required_level=4,
        current_level=0,
        importance=1.0,
        confidence=1.0,
        criticality=1.0,
        evidence_strength=1.0,
        weights=GapWeights(importance=0.5),
    )
    assert score.gap == 2.0
    assert score.priority == "HIGH"


def test_priority_bands_match_prd() -> None:
    thresholds = GapThresholds()
    assert priority_band(0, thresholds) == "NONE"
    assert priority_band(0.5, thresholds) == "LOW"
    assert priority_band(1.0, thresholds) == "MEDIUM"
    assert priority_band(2.0, thresholds) == "HIGH"
    assert priority_band(2.1, thresholds) == "CRITICAL"


def test_components_are_clamped() -> None:
    score = compute_gap(
        required_level=2,
        current_level=0,
        importance=2.0,
        confidence=2.0,
        criticality=2.0,
        evidence_strength=2.0,
    )
    assert score.gap == 2.0
    assert score.priority == "HIGH"
