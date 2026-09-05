from app.core.llm_pricing import estimate_cost_usd


def test_known_model_uses_its_own_rate():
    assert estimate_cost_usd("claude-haiku-4-5", input_tokens=1_000_000, output_tokens=0) == 1.00
    assert estimate_cost_usd("claude-haiku-4-5", input_tokens=0, output_tokens=1_000_000) == 5.00


def test_unknown_model_falls_back_to_default_pricing():
    assert estimate_cost_usd("some-future-model", input_tokens=1_000_000, output_tokens=1_000_000) == 6.00


def test_zero_tokens_costs_nothing():
    assert estimate_cost_usd("claude-haiku-4-5", input_tokens=0, output_tokens=0) == 0.0


def test_cost_scales_linearly_with_tokens():
    half = estimate_cost_usd("claude-haiku-4-5", input_tokens=500_000, output_tokens=0)
    full = estimate_cost_usd("claude-haiku-4-5", input_tokens=1_000_000, output_tokens=0)
    assert full == half * 2
