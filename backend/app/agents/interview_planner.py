"""Interview Planner agent.

Plain-function style mirroring app/agents/jd_analyzer.py and resume_analyzer.py - no
LangGraph, no classes (LangGraph orchestration is Phase 4+, not needed at this codebase
maturity). Difficulty is a static range set once here, not adaptive - the adaptive
per-turn engine is built in Phase 4.
"""

import itertools
import json

from app.llm_adapter import LLMAdapter
from app.prompts import INTERVIEW_PLANNER_PROMPT
from app.utils.json_parsing import parse_llm_json

REQUIRED_KEYS = ("candidate_level", "topic_mix", "difficulty_min", "difficulty_max", "rationale")

# CE-a: how many topic_mix entries get grounded in one of the candidate's own
# resume projects, scaled by format. Deterministic - the LLM never decides
# this - so it degrades predictably to 0 for an unrecognized question_count
# rather than guessing, mirroring clamp_difficulty's "backstop" approach below.
GROUNDED_PROJECT_SLOTS = {5: 1, 8: 2, 12: 3}

# Deterministic backstop on top of the prompt instruction: even if the LLM proposes a
# difficulty range that assumes more seniority than the resume shows, the plan can never
# exceed this ceiling for the inferred candidate_level (CLAUDE.md - Interview Planner
# guardrail: "Plan must stay within candidate's stated experience level").
DIFFICULTY_CEILING = {
    "junior": 3,
    "mid": 4,
    "senior": 5,
    "staff": 5,
    "principal": 5,
}
DEFAULT_CEILING = 4


def clamp_difficulty(candidate_level: str, difficulty_min: int, difficulty_max: int) -> tuple[int, int]:
    ceiling = DIFFICULTY_CEILING.get(candidate_level, DEFAULT_CEILING)
    clamped_max = max(1, min(difficulty_max, ceiling))
    clamped_min = max(1, min(difficulty_min, clamped_max))
    return clamped_min, clamped_max


def _apply_project_grounding(topic_mix: list[dict], projects: list, question_count: int) -> list[dict]:
    """Tag a subset of topic_mix entries as grounded in a specific resume project.

    Carves single-question entries off the largest existing entries (largest
    first, so a 1-question topic never gets wiped out) rather than asking the
    LLM to decide this - CE-a is a content-quality change, not a prompt-trust
    change. Falls back to no grounded entries if the resume lists no projects,
    or if question_count isn't one of the known formats.
    """
    working = [dict(entry) for entry in topic_mix]
    slots = GROUNDED_PROJECT_SLOTS.get(question_count, 0) if projects else 0

    grounded_entries = []
    if slots:
        project_cycle = itertools.cycle(projects)
        for _ in range(slots):
            candidate = max(working, key=lambda t: t.get("question_count", 0), default=None)
            if candidate is None or candidate.get("question_count", 0) <= 0:
                break
            candidate["question_count"] = candidate.get("question_count", 0) - 1
            project = next(project_cycle)
            grounded_entries.append(
                {
                    "topic": f"{project.get('name', 'Project')} — project deep-dive",
                    "question_count": 1,
                    "grounded_in_project": True,
                    "project": {
                        "name": project.get("name"),
                        "description": project.get("description"),
                        "technologies": project.get("technologies", []),
                    },
                }
            )
        working = [entry for entry in working if entry.get("question_count", 0) > 0]

    for entry in working:
        entry.setdefault("grounded_in_project", False)
        entry.setdefault("project", None)

    return working + grounded_entries


def generate_interview_plan(
    llm: LLMAdapter,
    *,
    resume_data: dict,
    jd_data: dict,
    skill_gap: dict,
    question_count: int,
) -> dict:
    prompt = INTERVIEW_PLANNER_PROMPT.format(
        question_count=question_count,
        resume_data=json.dumps(resume_data),
        jd_data=json.dumps(jd_data),
        skill_gap=json.dumps(skill_gap),
    )
    raw = llm.generate(prompt, agent_name="interview_planner", temperature=0.2, max_tokens=1536)
    result = parse_llm_json(raw)

    if not isinstance(result, dict) or not all(k in result for k in REQUIRED_KEYS):
        raise ValueError(f"Malformed interview plan object: {result!r}")

    topic_mix = result["topic_mix"]
    if not isinstance(topic_mix, list) or not topic_mix:
        raise ValueError(f"Malformed interview plan topic_mix: {topic_mix!r}")
    total_questions = sum(topic.get("question_count", 0) for topic in topic_mix)
    if total_questions != question_count:
        raise ValueError(
            f"Interview plan topic_mix sums to {total_questions}, expected {question_count}: {topic_mix!r}"
        )

    topic_mix = _apply_project_grounding(topic_mix, resume_data.get("projects") or [], question_count)

    difficulty_min, difficulty_max = clamp_difficulty(
        result["candidate_level"], result["difficulty_min"], result["difficulty_max"]
    )

    return {
        "candidate_level": result["candidate_level"],
        "topic_mix": topic_mix,
        "difficulty_min": difficulty_min,
        "difficulty_max": difficulty_max,
        "rationale": result["rationale"],
    }
