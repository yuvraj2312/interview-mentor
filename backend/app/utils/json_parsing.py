"""Shared LLM JSON-response parsing.

Same fence-stripping regex + json.loads logic as app/interview.py's
private _parse_json, extracted here so resume/JD agents can reuse it
without touching interview.py (left untouched - Phase-0-verified).
"""

import json
import re


def parse_llm_json(raw: str) -> dict | list:
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)
