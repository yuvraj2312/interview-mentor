import json

from app.agents.interview_planner import generate_interview_plan
from app.llm_adapter import LLMAdapter

PROJECTS = [
    {"name": "Order Pipeline", "description": "Async order processing service.", "technologies": ["Python", "Kafka"]},
    {"name": "Internal Dashboard", "description": "Ops metrics dashboard.", "technologies": ["React", "TypeScript"]},
]


class _FakeLLM(LLMAdapter):
    def __init__(self, response: dict):
        self._response = response
        self.last_usage = None

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        return json.dumps(self._response)


def _raw_topic_mix(question_count: int) -> list[dict]:
    # Two entries whose question_count sums to exactly question_count, with
    # the first entry large enough to carve every grounded slot from it (the
    # planner never needs to touch the second entry for any tested format).
    second = 2
    first = question_count - second
    return [
        {"topic": "Python fundamentals", "question_count": first},
        {"topic": "PostgreSQL", "question_count": second},
    ]


def _plan(question_count: int, projects: list) -> dict:
    llm = _FakeLLM(
        {
            "candidate_level": "mid",
            "topic_mix": _raw_topic_mix(question_count),
            "difficulty_min": 2,
            "difficulty_max": 3,
            "rationale": "Focused on missing required skills given a mid-level resume.",
        }
    )
    return generate_interview_plan(
        llm,
        resume_data={"skills": [], "experience": [], "education": [], "projects": projects},
        jd_data={},
        skill_gap={},
        question_count=question_count,
    )


def _grounded_entries(topic_mix: list) -> list:
    return [t for t in topic_mix if t["grounded_in_project"]]


def test_quick_format_grounds_exactly_one_entry():
    plan = _plan(5, PROJECTS)
    grounded = _grounded_entries(plan["topic_mix"])
    assert len(grounded) == 1
    assert grounded[0]["project"]["name"] == PROJECTS[0]["name"]
    assert sum(t["question_count"] for t in plan["topic_mix"]) == 5


def test_standard_format_grounds_exactly_two_entries():
    plan = _plan(8, PROJECTS)
    grounded = _grounded_entries(plan["topic_mix"])
    assert len(grounded) == 2
    assert [g["project"]["name"] for g in grounded] == [PROJECTS[0]["name"], PROJECTS[1]["name"]]
    assert sum(t["question_count"] for t in plan["topic_mix"]) == 8


def test_thorough_format_grounds_exactly_three_entries_and_cycles_projects():
    plan = _plan(12, PROJECTS)
    grounded = _grounded_entries(plan["topic_mix"])
    assert len(grounded) == 3
    # Only 2 projects for 3 slots - round-robin cycles back to the first.
    assert [g["project"]["name"] for g in grounded] == [
        PROJECTS[0]["name"],
        PROJECTS[1]["name"],
        PROJECTS[0]["name"],
    ]
    assert sum(t["question_count"] for t in plan["topic_mix"]) == 12


def test_no_projects_falls_back_to_zero_grounded_entries():
    plan = _plan(8, [])
    assert _grounded_entries(plan["topic_mix"]) == []
    assert all(t["grounded_in_project"] is False and t["project"] is None for t in plan["topic_mix"])
    assert sum(t["question_count"] for t in plan["topic_mix"]) == 8


def test_missing_projects_key_falls_back_to_zero_grounded_entries():
    llm = _FakeLLM(
        {
            "candidate_level": "mid",
            "topic_mix": _raw_topic_mix(8),
            "difficulty_min": 2,
            "difficulty_max": 3,
            "rationale": "Focused on missing required skills given a mid-level resume.",
        }
    )
    plan = generate_interview_plan(
        llm,
        resume_data={"skills": [], "experience": [], "education": []},
        jd_data={},
        skill_gap={},
        question_count=8,
    )
    assert _grounded_entries(plan["topic_mix"]) == []


def test_ungrounded_entries_keep_their_original_topic_and_are_tagged_false():
    plan = _plan(5, PROJECTS)
    non_grounded = [t for t in plan["topic_mix"] if not t["grounded_in_project"]]
    original_topics = {t["topic"] for t in _raw_topic_mix(5)}
    assert {t["topic"] for t in non_grounded}.issubset(original_topics)
    assert all(t["project"] is None for t in non_grounded)
