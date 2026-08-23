from app.workflows.difficulty import compute_next_difficulty


def test_strong_answer_increases_difficulty():
    assert compute_next_difficulty(3, 9, 9, 9, difficulty_min=1, difficulty_max=5) == 4


def test_weak_answer_decreases_difficulty():
    assert compute_next_difficulty(3, 2, 2, 2, difficulty_min=1, difficulty_max=5) == 2


def test_mid_range_answer_keeps_difficulty_unchanged():
    assert compute_next_difficulty(3, 6, 6, 6, difficulty_min=1, difficulty_max=5) == 3


def test_strong_answer_at_max_stays_clamped_at_max():
    assert compute_next_difficulty(5, 10, 10, 10, difficulty_min=1, difficulty_max=5) == 5


def test_weak_answer_at_min_stays_clamped_at_min():
    assert compute_next_difficulty(1, 0, 0, 0, difficulty_min=1, difficulty_max=5) == 1


def test_strong_answer_respects_a_narrower_plan_range():
    assert compute_next_difficulty(3, 9, 9, 9, difficulty_min=2, difficulty_max=3) == 3


def test_exact_strong_threshold_boundary_increases_difficulty():
    # composite == strong_threshold (7.5) should count as strong (>=)
    assert compute_next_difficulty(3, 7.5, 7.5, 7.5, difficulty_min=1, difficulty_max=5) == 4


def test_exact_weak_threshold_boundary_decreases_difficulty():
    # composite == weak_threshold (4.0) should count as weak (<=)
    assert compute_next_difficulty(3, 4.0, 4.0, 4.0, difficulty_min=1, difficulty_max=5) == 2


def test_just_above_weak_threshold_keeps_difficulty_unchanged():
    assert compute_next_difficulty(3, 4.1, 4.1, 4.1, difficulty_min=1, difficulty_max=5) == 3


def test_just_below_strong_threshold_keeps_difficulty_unchanged():
    assert compute_next_difficulty(3, 7.4, 7.4, 7.4, difficulty_min=1, difficulty_max=5) == 3


def test_mixed_scores_use_composite_average():
    # composite = (10 + 10 + 2) / 3 = 7.33, below the 7.5 strong threshold
    assert compute_next_difficulty(3, 10, 10, 2, difficulty_min=1, difficulty_max=5) == 3
