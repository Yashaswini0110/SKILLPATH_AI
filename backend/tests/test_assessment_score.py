from ml.assessment.score import level_from_percent, score_mcq


def test_perfect_score_is_level_five_and_passes() -> None:
    result = score_mcq([1, 0, 2, 1], [1, 0, 2, 1], pass_score=0.7)
    assert result.correct_count == 4
    assert result.percent == 1.0
    assert result.extracted_level == 5.0
    assert result.passed is True


def test_zero_score_is_level_one_and_fails() -> None:
    result = score_mcq([0, 0, 0, 0], [1, 1, 1, 1], pass_score=0.7)
    assert result.percent == 0.0
    assert result.extracted_level == 1.0
    assert result.passed is False


def test_blank_answers_count_as_wrong() -> None:
    result = score_mcq([None, 1, None], [0, 1, 2], pass_score=0.7)
    assert result.correct_count == 1
    assert result.extracted_level == 2.3


def test_level_from_percent_is_linear() -> None:
    assert level_from_percent(0.0) == 1.0
    assert level_from_percent(0.5) == 3.0
    assert level_from_percent(1.0) == 5.0
