SKILL_MATCH_PROMPT = """You are assessing whether two skill or experience phrases, one from a candidate's \
resume and one from a job description, refer to the SAME underlying professional skill or competency - not \
whether the phrases share words or look similar. These phrases can come from any professional field \
(technology, finance, healthcare, law, or any other), phrased very differently by different people.

Judge by real-world professional meaning, not surface wording:
- Two phrases can share words, or one can look like a variant of the other, and still be DIFFERENT skills \
(e.g. "Java" and "JavaScript" are different programming languages despite the shared prefix; "Accounts \
Payable" and "Accounts Receivable" are different accounting functions despite sharing "Accounts"; \
"Registered Nurse" and "Registered Dietitian" are different professions despite sharing "Registered").
- Two phrases can use completely different words and still refer to the SAME skill (e.g. "S&P ratings \
methodology exposure" and "rating agency criteria knowledge" both describe familiarity with credit rating \
agency methodology).

JD PHRASE: {jd_skill}
RESUME PHRASE: {resume_skill}

Respond with ONLY a JSON object, no prose, no markdown fences, in this exact shape:
{{"is_match": <true|false>, "rationale": "<one sentence on the actual professional meaning, not the wording>"}}
"""
