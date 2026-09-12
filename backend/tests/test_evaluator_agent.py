import json

from app.agents.evaluator import evaluate_answer
from app.llm_adapter import LLMAdapter


class _RecordingLLM(LLMAdapter):
    def __init__(self):
        self.last_usage = None
        self.last_prompt = None

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        self.last_prompt = prompt
        return json.dumps(
            {
                "technical_score": 7.0,
                "communication_score": 7.0,
                "completeness_score": 7.0,
                "rationale": "canned",
                "needs_followup": False,
                "followup_reason": "",
            }
        )


def test_prompt_contains_anti_genericness_followup_instruction():
    llm = _RecordingLLM()
    evaluate_answer(llm, question_text="Explain X", answer_text="Y", difficulty=3)

    assert "specific, nameable gap" in llm.last_prompt.lower()
    assert "could be more detailed" in llm.last_prompt
    assert "needs_followup" in llm.last_prompt
    assert "followup_reason" in llm.last_prompt


def test_result_requires_needs_followup_and_followup_reason_keys():
    llm = _RecordingLLM()
    result = evaluate_answer(llm, question_text="Explain X", answer_text="Y", difficulty=3)
    assert result["needs_followup"] is False
    assert result["followup_reason"] == ""


def test_malformed_output_missing_followup_keys_raises_value_error():
    class _IncompleteLLM(LLMAdapter):
        last_usage = None

        def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
            return json.dumps(
                {
                    "technical_score": 7.0,
                    "communication_score": 7.0,
                    "completeness_score": 7.0,
                    "rationale": "canned",
                }
            )

    try:
        evaluate_answer(_IncompleteLLM(), question_text="Explain X", answer_text="Y", difficulty=3)
        assert False, "expected ValueError"
    except ValueError:
        pass
