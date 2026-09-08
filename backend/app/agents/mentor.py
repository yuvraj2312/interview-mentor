"""Mentor agent (Phase 6c).

Plain-function style mirroring app/agents/evaluator.py and
interview_planner.py - no LangGraph, this is a one-shot synthesis step run
once at the end of a completed session, not part of the adaptive loop.

Temperature 0.3: lower than question generation (0.7, deliberately
creative) but not as low as the evaluator's 0.2, since this is narrative
synthesis over already-scored turns, not itself a numeric rubric score.
Evidence-groundedness (CLAUDE.md's "specific and evidence-based, not
generic" guardrail) is enforced via the prompt instructions in
app/prompts/mentor_prompts.py, the same anti-genericness pattern the
evaluator prompt uses for its rationale field.
"""

import json

from app.llm_adapter import LLMAdapter
from app.prompts import MENTOR_PROMPT
from app.utils.json_parsing import parse_llm_json

REQUIRED_KEYS = ("summary", "strengths", "growth_areas", "roadmap_items")


def generate_roadmap(
    llm: LLMAdapter,
    *,
    turns: list[dict],
    skill_profile: dict,
    missing_skills: list[str],
) -> dict:
    prompt = MENTOR_PROMPT.format(
        turns=json.dumps(turns),
        skill_profile=json.dumps(skill_profile),
        missing_skills=json.dumps(missing_skills),
    )
    raw = llm.generate(prompt, agent_name="mentor", temperature=0.3, max_tokens=2048)
    result = parse_llm_json(raw)

    if not isinstance(result, dict) or not all(k in result for k in REQUIRED_KEYS):
        raise ValueError(f"Malformed roadmap object: {result!r}")

    roadmap_items = result["roadmap_items"]
    if not isinstance(roadmap_items, list):
        raise ValueError(f"Malformed roadmap_items: {roadmap_items!r}")

    return result
