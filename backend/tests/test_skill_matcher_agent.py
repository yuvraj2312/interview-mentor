import json

from app.agents.skill_matcher import llm_fallback_match
from app.llm_adapter import LLMAdapter


class _RecordingLLM(LLMAdapter):
    def __init__(self, response: dict):
        self.last_usage = None
        self.last_prompt = None
        self.last_kwargs = None
        self._response = response

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        self.last_prompt = prompt
        self.last_kwargs = {"agent_name": agent_name, "temperature": temperature, "max_tokens": max_tokens}
        return json.dumps(self._response)


def test_prompt_contains_both_phrases_and_anti_superficial_similarity_guidance():
    llm = _RecordingLLM({"is_match": True, "rationale": "canned"})
    llm_fallback_match(llm, jd_skill="rating agency criteria knowledge", resume_skill="S&P ratings methodology exposure")

    assert "rating agency criteria knowledge" in llm.last_prompt
    assert "S&P ratings methodology exposure" in llm.last_prompt
    # anti-superficial-similarity guidance, not just a bare comparison prompt
    assert "Java" in llm.last_prompt and "JavaScript" in llm.last_prompt
    assert "Accounts Payable" in llm.last_prompt and "Accounts Receivable" in llm.last_prompt
    assert "is_match" in llm.last_prompt


def test_uses_deterministic_low_temperature_and_small_max_tokens():
    llm = _RecordingLLM({"is_match": True, "rationale": "canned"})
    llm_fallback_match(llm, jd_skill="AP", resume_skill="Accounts Payable")

    assert llm.last_kwargs["agent_name"] == "skill_matcher"
    assert llm.last_kwargs["temperature"] == 0.0
    assert llm.last_kwargs["max_tokens"] <= 200


def test_true_verdict_parses_to_true():
    llm = _RecordingLLM({"is_match": True, "rationale": "same skill, different phrasing"})
    assert llm_fallback_match(llm, jd_skill="AP", resume_skill="Accounts Payable") is True


def test_false_verdict_parses_to_false():
    llm = _RecordingLLM({"is_match": False, "rationale": "different accounting functions"})
    assert llm_fallback_match(llm, jd_skill="Accounts Payable", resume_skill="Accounts Receivable") is False


def test_malformed_output_missing_required_keys_raises_value_error():
    class _IncompleteLLM(LLMAdapter):
        last_usage = None

        def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
            return json.dumps({"is_match": True})

    try:
        llm_fallback_match(_IncompleteLLM(), jd_skill="AP", resume_skill="Accounts Payable")
        assert False, "expected ValueError"
    except ValueError:
        pass
