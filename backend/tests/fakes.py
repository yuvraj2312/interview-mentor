"""Test doubles for LLMAdapter.

Phase 4d cost-cap tests need to exercise the real question_generator/
evaluator agent code (so llm.last_usage actually gets set by a real
generate() call) - unlike the existing pattern elsewhere in this test
suite of patching app.workflows.interview_graph.generate_question/
evaluate_answer directly, which replaces those functions entirely and
never touches llm.generate() at all. FakeLLMAdapter stands in for
AnthropicAdapter so those agent functions run for real against scripted,
zero-network responses with a controllable per-call cost.
"""

from app.llm_adapter import LLMAdapter, LLMCallUsage


class FakeLLMAdapter(LLMAdapter):
    def __init__(self, responses: list[str], *, cost_per_call: float) -> None:
        # Not copied: callers share one list across the multiple
        # FakeLLMAdapter instances a test's fake_llm_factory hands out (one
        # per get_llm_adapter() call, mirroring the real "fresh adapter
        # instance per request" pattern), so responses queued for later
        # turns are consumed in call order across instances.
        self._responses = responses
        self._cost_per_call = cost_per_call
        self.calls: list[dict] = []
        self.last_usage = None

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        self.calls.append({"prompt": prompt, "agent_name": agent_name})
        text = self._responses.pop(0)
        self.last_usage = LLMCallUsage(
            input_tokens=10, output_tokens=10, cost_usd=self._cost_per_call, latency_ms=1
        )
        return text


def fake_llm_factory(responses: list[str], *, cost_per_call: float):
    """A get_llm_adapter(db, *, session_id=None)-compatible callable that
    hands back a fresh FakeLLMAdapter sharing `responses` on every call.
    """

    def factory(db, *, session_id=None):
        return FakeLLMAdapter(responses, cost_per_call=cost_per_call)

    return factory
