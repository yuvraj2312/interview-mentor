"""Question Generator agent (Phase 4a).

Plain-function style mirroring app/agents/jd_analyzer.py and resume_analyzer.py.
Difficulty and topic are inputs the LLM must honor, never outputs it controls -
the adaptive engine (app/workflows/difficulty.py) is the sole authority on
difficulty (CLAUDE.md - Question Generator guardrail: "difficulty bounded by
adaptive engine output").
"""

from app.llm_adapter import LLMAdapter
from app.prompts import PROJECT_GROUNDING_INSTRUCTION, QUESTION_GENERATOR_PROMPT
from app.utils.json_parsing import parse_llm_json

REQUIRED_KEYS = ("question_text",)


def generate_question(
    llm: LLMAdapter,
    *,
    topic: str,
    difficulty: int,
    candidate_level: str,
    asked_questions: list[str],
    project: dict | None = None,
) -> dict:
    project_context = (
        PROJECT_GROUNDING_INSTRUCTION.format(
            name=project.get("name") or "the project",
            description=project.get("description") or "(no description given)",
            technologies=", ".join(project.get("technologies") or []) or "not specified",
        )
        if project
        else ""
    )
    prompt = QUESTION_GENERATOR_PROMPT.format(
        topic=topic,
        difficulty=difficulty,
        candidate_level=candidate_level,
        project_context=project_context,
        asked_questions="\n".join(f"- {q}" for q in asked_questions) or "(none yet)",
    )
    raw = llm.generate(prompt, agent_name="question_generator", temperature=0.7, max_tokens=512)
    result = parse_llm_json(raw)

    if not isinstance(result, dict) or not all(k in result for k in REQUIRED_KEYS):
        raise ValueError(f"Malformed question generator object: {result!r}")
    return result
