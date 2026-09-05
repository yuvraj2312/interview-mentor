"""Shared LLM JSON-response parsing.

Same fence-stripping regex + json.loads logic as app/interview.py's
private _parse_json, extracted here so resume/JD agents can reuse it
without touching interview.py (left untouched - Phase-0-verified).
"""

import json
import re


def parse_llm_json(raw: str) -> dict | list:
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    # raw_decode (rather than json.loads) parses just the leading JSON document and
    # ignores anything after it, since models occasionally trail the closing fence
    # with stray characters (e.g. an extra quote) that would otherwise raise on
    # otherwise-well-formed output.
    obj, _ = json.JSONDecoder().raw_decode(cleaned)
    return obj
