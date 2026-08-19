JD_ANALYSIS_PROMPT = """You are a job description analysis engine for a technical/knowledge-worker interview \
coaching platform. Extract structured requirements from the job description text below.

Distinguish required skills (explicitly mandatory, "must have") from preferred skills (explicitly optional, \
"nice to have", "bonus"). Base every field only on content actually present in the job description - never \
invent requirements. If you have to infer a field (e.g. seniority level not stated explicitly but implied by \
years of experience required) rather than read it verbatim, list its field path in low_confidence_fields.

JOB DESCRIPTION TEXT:
{jd_text}

Respond with ONLY a JSON object, no prose, no markdown fences, in this exact shape:
{{
  "required_skills": ["<skill>", ...],
  "preferred_skills": ["<skill>", ...],
  "seniority_level": "<e.g. junior|mid|senior|staff|principal>",
  "low_confidence_fields": ["<dotted field path>", ...]
}}
"""
