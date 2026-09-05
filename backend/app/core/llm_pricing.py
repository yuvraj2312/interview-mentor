"""Per-model $/token pricing used to compute LLM call cost.

Anthropic's API returns exact input/output token counts per call
(response.usage), so cost is a pure lookup-and-multiply - no local
tokenizer is needed. The figures below are a best-effort snapshot and
should be verified against Anthropic's current pricing page before being
relied on for real budgeting; they're accurate enough as-is to drive
relative cost comparisons and the interview session cost cap either way.
"""

# USD per 1,000,000 tokens.
_PRICING_USD_PER_MILLION_TOKENS: dict[str, dict[str, float]] = {
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
}
_DEFAULT_PRICING = {"input": 1.00, "output": 5.00}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = _PRICING_USD_PER_MILLION_TOKENS.get(model, _DEFAULT_PRICING)
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
