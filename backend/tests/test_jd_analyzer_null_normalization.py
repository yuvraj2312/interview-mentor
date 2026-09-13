"""Regression test for the JD-analyzer half of the empty-array display bug
(2026-09-13 investigation): a genuinely empty section (e.g. no preferred
skills listed) must come back as [], never None - every downstream consumer
(this system's own API responses, the frontend, skill_gap_service's
.get(key, []) calls, which only default on a MISSING key, not an explicit
None) treats a present empty list as "no data" and a null as an error
condition. See test_resume_analyzer_bullet_capture.py for the sibling
resume_analyzer test of the same fix.
"""

import json

from app.agents.jd_analyzer import analyze_job_description
from app.llm_adapter import LLMAdapter


class _NullSectionsLLM(LLMAdapter):
    def __init__(self):
        self.last_usage = None

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        return json.dumps(
            {
                "required_skills": None,
                "preferred_skills": None,
                "seniority_level": "mid",
                "low_confidence_fields": None,
            }
        )


def test_null_sections_are_normalized_to_empty_lists_not_left_as_none():
    llm = _NullSectionsLLM()

    result = analyze_job_description(llm, "irrelevant - the fake LLM ignores the prompt")

    assert result["required_skills"] == []
    assert result["preferred_skills"] == []
    assert result["low_confidence_fields"] == []
