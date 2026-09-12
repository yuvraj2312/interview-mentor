QUESTION_GENERATOR_PROMPT = """You are an interview question generator for a technical/knowledge-worker \
interview coaching platform, generating one question at a time in an adaptive interview.

Generate exactly one interview question on the topic below, calibrated to the exact difficulty level given. \
The difficulty level is fixed by the adaptive engine, not up to you - do not soften or escalate it.

TOPIC: {topic}
DIFFICULTY: {difficulty} (on a 1-5 scale, where 1 is entry-level/basic and 5 is expert-level/advanced)
CANDIDATE LEVEL: {candidate_level}
{project_context}
{followup_context}
Do not repeat or closely paraphrase any of these questions already asked in this session:
{asked_questions}

Respond with ONLY a JSON object, no prose, no markdown fences, in this exact shape:
{{"question_text": "<the interview question>"}}
"""

# CE-a: interpolated into {project_context} above only for a topic_mix slot
# tagged grounded_in_project; left as "" otherwise so an ungrounded slot's
# prompt is byte-identical to the pre-CE-a prompt.
PROJECT_GROUNDING_INSTRUCTION = """
This question MUST concretely reference the candidate's own project below - name it explicitly and ask \
something that requires reasoning about a real decision, tradeoff, or detail from it, not a generic question \
about the topic in isolation.

PROJECT NAME: {name}
PROJECT DESCRIPTION: {description}
TECHNOLOGIES USED: {technologies}
"""

# CE-c: interpolated into {followup_context} above only when generating a
# same-topic follow-up; left as "" otherwise so a non-follow-up prompt is
# byte-identical to the pre-CE-c prompt.
FOLLOWUP_INSTRUCTION = """
This is a FOLLOW-UP question, not a fresh question - the candidate already attempted the question below, and \
their answer left a specific, nameable gap. Ask a targeted follow-up that concretely addresses that gap - do not \
ask a generic "can you elaborate" question, and do not simply repeat the original question.

ORIGINAL QUESTION: {original_question}
CANDIDATE'S ANSWER: {original_answer}
SPECIFIC GAP TO PROBE: {followup_reason}
"""
