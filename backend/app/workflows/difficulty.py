"""Deterministic adaptive-difficulty rule for the Phase 4a interview loop.

Difficulty is never LLM-decided (CLAUDE.md - Question Generator guardrail:
"difficulty bounded by adaptive engine output"). This function is the sole
authority on the next turn's difficulty: it is a pure function of the current
difficulty, the last answer's scores, and the plan's bounds, so it can be
unit-tested exhaustively without a DB, an LLM, or HTTP.
"""

STRONG_THRESHOLD = 7.5
WEAK_THRESHOLD = 4.0


def compute_next_difficulty(
    current_difficulty: int,
    technical_score: float,
    communication_score: float,
    completeness_score: float,
    difficulty_min: int,
    difficulty_max: int,
    strong_threshold: float = STRONG_THRESHOLD,
    weak_threshold: float = WEAK_THRESHOLD,
) -> int:
    composite = (technical_score + communication_score + completeness_score) / 3

    if composite >= strong_threshold:
        next_difficulty = current_difficulty + 1
    elif composite <= weak_threshold:
        next_difficulty = current_difficulty - 1
    else:
        next_difficulty = current_difficulty

    return max(difficulty_min, min(next_difficulty, difficulty_max))
