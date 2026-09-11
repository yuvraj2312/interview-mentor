import json

from app.agents.interviewer import answer_clarification
from app.llm_adapter import LLMAdapter


class _RecordingLLM(LLMAdapter):
    def __init__(self):
        self.last_usage = None
        self.last_prompt = None
        self.last_agent_name = None

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        self.last_prompt = prompt
        self.last_agent_name = agent_name
        return json.dumps({"clarification_text": "The request refers to an HTTP request from the client."})


def test_prompt_grounds_in_the_specific_question_and_forbids_revealing_the_answer():
    llm = _RecordingLLM()
    answer_clarification(
        llm,
        topic="Full-stack web development",
        question_text="Walk me through how a request flows through the system.",
        difficulty=3,
        clarifying_question="What do you mean by 'request'?",
    )

    assert "Full-stack web development" in llm.last_prompt
    assert "Walk me through how a request flows through the system." in llm.last_prompt
    assert "What do you mean by 'request'?" in llm.last_prompt
    assert "Do NOT reveal the answer" in llm.last_prompt
    assert llm.last_agent_name == "interviewer"


def test_result_requires_clarification_text_key():
    llm = _RecordingLLM()
    result = answer_clarification(
        llm,
        topic="Databases",
        question_text="How would you design a schema for this?",
        difficulty=2,
        clarifying_question="Do you mean a relational or NoSQL schema?",
    )
    assert result == {"clarification_text": "The request refers to an HTTP request from the client."}


def test_malformed_llm_output_raises_value_error():
    class _BadLLM(LLMAdapter):
        last_usage = None

        def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
            return json.dumps({"unexpected_key": "oops"})

    try:
        answer_clarification(
            _BadLLM(),
            topic="Databases",
            question_text="How would you design a schema for this?",
            difficulty=2,
            clarifying_question="What kind of schema?",
        )
        assert False, "expected ValueError"
    except ValueError:
        pass
