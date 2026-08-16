QUESTION_GENERATION_PROMPT = """You are an interview question generator for a technical/knowledge-worker \
interview coaching platform.

Given a candidate's resume and a target job description, generate exactly 3 interview questions that probe \
the most relevant skill gaps and overlaps between the two. Base every question only on content actually \
present in the resume or job description below - do not invent skills or experience the candidate does not \
have.

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

Respond with ONLY a JSON array of exactly 3 objects, no prose, no markdown fences, in this exact shape:
[
  {{"topic": "<short topic label>", "difficulty": "<easy|medium|hard>", "question": "<the interview question>"}},
  ...
]
"""

EVALUATION_PROMPT = """You are an interview answer evaluator. Score the candidate's answer to the question \
below using this fixed rubric. Be consistent and objective - do not be swayed by writing style alone.

QUESTION:
{question_text}

CANDIDATE ANSWER:
{answer_text}

Score each dimension from 0 to 10:
- technical_score: factual/technical accuracy and depth of the answer
- communication_score: clarity, structure, and conciseness of the answer
- completeness_score: how fully the answer addresses what the question asked

Respond with ONLY a JSON object, no prose, no markdown fences, in this exact shape:
{{"technical_score": <0-10>, "communication_score": <0-10>, "completeness_score": <0-10>, "rationale": "<1-3 sentence justification citing specifics from the answer>"}}
"""
