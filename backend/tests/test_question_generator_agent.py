import json

from app.agents.question_generator import generate_question
from app.llm_adapter import LLMAdapter

PROJECT = {
    "name": "Order Pipeline",
    "description": "Async order processing service.",
    "technologies": ["Python", "Kafka"],
}


class _RecordingLLM(LLMAdapter):
    def __init__(self):
        self.last_usage = None
        self.last_prompt = None

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        self.last_prompt = prompt
        return json.dumps({"question_text": "generated question"})


def _generate(llm, project=None):
    return generate_question(
        llm,
        topic="Full-stack web development",
        difficulty=3,
        candidate_level="mid",
        asked_questions=[],
        project=project,
    )


def test_prompt_references_project_name_description_and_technologies_when_grounded():
    llm = _RecordingLLM()
    _generate(llm, project=PROJECT)

    assert PROJECT["name"] in llm.last_prompt
    assert PROJECT["description"] in llm.last_prompt
    assert "Python" in llm.last_prompt
    assert "Kafka" in llm.last_prompt
    assert "MUST concretely reference" in llm.last_prompt


def test_prompt_omits_grounding_instruction_without_project():
    llm = _RecordingLLM()
    _generate(llm, project=None)

    assert "MUST concretely reference" not in llm.last_prompt
    assert PROJECT["name"] not in llm.last_prompt


def test_prompt_without_project_is_unchanged_from_pre_ce_a_shape():
    from app.prompts import QUESTION_GENERATOR_PROMPT

    llm = _RecordingLLM()
    _generate(llm, project=None)

    expected = QUESTION_GENERATOR_PROMPT.format(
        topic="Full-stack web development",
        difficulty=3,
        candidate_level="mid",
        project_context="",
        asked_questions="(none yet)",
    )
    assert llm.last_prompt == expected


def test_result_still_requires_question_text_key():
    llm = _RecordingLLM()
    result = _generate(llm, project=PROJECT)
    assert result == {"question_text": "generated question"}
