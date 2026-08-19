RESUME_ANALYSIS_PROMPT = """You are a resume analysis engine for a technical/knowledge-worker interview \
coaching platform. Extract structured data from the resume text below.

Base every field only on content actually present in the resume - never invent skills, employers, dates, \
or experience the candidate does not have. If you have to infer a field (e.g. an end date written as \
"present", or a skill implied but not explicitly named) rather than read it verbatim, list its field path \
in low_confidence_fields.

RESUME TEXT:
{resume_text}

Respond with ONLY a JSON object, no prose, no markdown fences, in this exact shape:
{{
  "skills": ["<skill>", ...],
  "experience": [
    {{"title": "<job title>", "company": "<company>", "start_date": "<string>", "end_date": "<string>", \
"description": "<1-2 sentence summary>"}}, ...
  ],
  "education": [
    {{"institution": "<name>", "degree": "<degree>", "field_of_study": "<field>", "graduation_date": "<string>"}}, ...
  ],
  "projects": [
    {{"name": "<project name>", "description": "<1-2 sentence summary>", "technologies": ["<tech>", ...]}}, ...
  ],
  "low_confidence_fields": ["<dotted field path>", ...]
}}
"""
