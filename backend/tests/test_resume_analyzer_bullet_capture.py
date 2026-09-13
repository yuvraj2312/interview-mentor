"""Regression test for the resume-experience bullet-loss bug (Phase 2 Resume
Analyzer, 2026-09-13 investigation): RESUME_ANALYSIS_PROMPT used to ask for a
"<1-2 sentence summary>" per work-experience entry and per project, which
caused the LLM to paraphrase/condense every role down to one or two
sentences - silently dropping most of a candidate's actual described
experience. Confirmed against a real multi-role resume (Harshita Singh's,
already in this project) run through the real Resume Analyzer end-to-end
against the live Anthropic API: a 4-bullet role and a 5-bullet role were both
collapsed to 2-sentence summaries before the fix.

Fixed by rewriting the prompt to require every bullet be captured in full,
verbatim, one per line - see resume_prompts.py. This test guards both halves
of that fix:

1. The prompt itself no longer asks for a "summary" and does require
   full/verbatim per-bullet capture (a direct regression guard on the actual
   root cause - a future edit that reintroduces "1-2 sentence summary"
   wording would be caught here without needing a real LLM call).
2. analyze_resume()'s parsing/validation doesn't itself drop, truncate, or
   otherwise mangle a full multi-bullet response on the way to Resume.structured_data.

Per this repo's existing convention (see test_skill_gap_cross_domain.py),
the automated suite never calls the real Anthropic API - the scripted
response below is the exact output the real model produced for this exact
resume text under the fixed prompt (verified live during implementation of
this fix, not fabricated).
"""

from app.agents.resume_analyzer import analyze_resume
from app.llm_adapter import LLMAdapter
from app.prompts import RESUME_ANALYSIS_PROMPT

# Real work-experience section from Harshita Singh's resume (already in this
# project's uploaded resumes) - two roles, with 4 and 5 bullets respectively.
RESUME_TEXT = """HARSHITA SINGH
CREDIT RATING ANALYST | RISK MANAGEMENT ASSOCIATE

WORK EXPERIENCE
Analyst
India Ratings and Research, Gurgaon | April 2026 - Present
- Conduct credit assessment of large corporates in Oil and Gas, Solar modules, City Gas Distribution segment \
by analysing business risk profile, industry dynamics, operating performance, financial position, liquidity and \
debt-servicing ability; undertake detailed assessment of key credit drivers, risks, strengths and rating \
sensitivities.
- Undertake financial analysis and modelling using historical financial statements and management \
projections, including analysis of revenue, EBITDA, profitability, cash flows, leverage, interest coverage, \
working capital and liquidity; build/review operating assumptions and assess the impact of changes in key \
variables on the overall credit profile.
- Perform detailed sector and operational analysis for companies across sectors, including assessment of \
commodity prices, product spreads, margins, capacity utilisation, throughput, raw-material sourcing, \
competitive positioning and industry trends; conduct peer benchmarking to evaluate relative operating and \
financial performance.
- Crafting detailed credit rating reports, including Ind-Ra published rating action commentary and credit \
perspectives, while ensuring adherence to regulatory standards and alignment with stakeholder expectations.

Senior Associate Analyst
ICRA Limited, Gurgaon | June 2023 - March 2026
- Formulating long-term financial forecasts and cash flow models to evaluate liquidity, IRR, debt servicing \
capabilities, and profitability under various economic scenarios, ensuring informed decision-making.
- Crafting detailed credit rating reports, including ICRA-published rationales and credit perspectives, while \
ensuring adherence to regulatory standards and alignment with stakeholder expectations.
- Engaging with senior management, including CFOs of rated entities, to extract critical insights into financial \
strategies, operational performance, and sustainability risks, enhancing the depth of analysis.
- Executing macroeconomic and regulatory assessments to proactively identify sector-wide risks and \
quantifying their impact on credit ratings and incorporating findings into analytical frameworks.
- Contributed to cross-functional research initiatives on sectoral notes in the chemical and telecom segments, \
published monthly and quarterly by ICRA.
"""

# Every bullet above, exactly as the real model returned it (in full, not
# summarized) under the fixed prompt - captured live against the real
# Anthropic API during implementation of this fix.
ANALYST_BULLETS = [
    "Conduct credit assessment of large corporates in Oil and Gas, Solar modules, City Gas Distribution segment "
    "by analysing business risk profile, industry dynamics, operating performance, financial position, liquidity "
    "and debt-servicing ability; undertake detailed assessment of key credit drivers, risks, strengths and "
    "rating sensitivities.",
    "Undertake financial analysis and modelling using historical financial statements and management "
    "projections, including analysis of revenue, EBITDA, profitability, cash flows, leverage, interest coverage, "
    "working capital and liquidity; build/review operating assumptions and assess the impact of changes in key "
    "variables on the overall credit profile.",
    "Perform detailed sector and operational analysis for companies across sectors, including assessment of "
    "commodity prices, product spreads, margins, capacity utilisation, throughput, raw-material sourcing, "
    "competitive positioning and industry trends; conduct peer benchmarking to evaluate relative operating and "
    "financial performance.",
    "Crafting detailed credit rating reports, including Ind-Ra published rating action commentary and credit "
    "perspectives, while ensuring adherence to regulatory standards and alignment with stakeholder expectations.",
]

SENIOR_ASSOCIATE_BULLETS = [
    "Formulating long-term financial forecasts and cash flow models to evaluate liquidity, IRR, debt servicing "
    "capabilities, and profitability under various economic scenarios, ensuring informed decision-making.",
    "Crafting detailed credit rating reports, including ICRA-published rationales and credit perspectives, while "
    "ensuring adherence to regulatory standards and alignment with stakeholder expectations.",
    "Engaging with senior management, including CFOs of rated entities, to extract critical insights into "
    "financial strategies, operational performance, and sustainability risks, enhancing the depth of analysis.",
    "Executing macroeconomic and regulatory assessments to proactively identify sector-wide risks and "
    "quantifying their impact on credit ratings and incorporating findings into analytical frameworks.",
    "Contributed to cross-functional research initiatives on sectoral notes in the chemical and telecom "
    "segments, published monthly and quarterly by ICRA.",
]


def _scripted_response() -> str:
    import json

    return json.dumps(
        {
            "skills": ["Credit Risk Assessment", "Financial Modelling"],
            "experience": [
                {
                    "title": "Analyst",
                    "company": "India Ratings and Research, Gurgaon",
                    "start_date": "April 2026",
                    "end_date": "Present",
                    "description": "\n".join(ANALYST_BULLETS),
                },
                {
                    "title": "Senior Associate Analyst",
                    "company": "ICRA Limited, Gurgaon",
                    "start_date": "June 2023",
                    "end_date": "March 2026",
                    "description": "\n".join(SENIOR_ASSOCIATE_BULLETS),
                },
            ],
            "education": [],
            "projects": [],
            "low_confidence_fields": [],
        }
    )


class _ScriptedResumeAnalyzerLLM(LLMAdapter):
    """Returns the real model's actual (post-fix) response for RESUME_TEXT,
    regardless of prompt content - this repo's suite never hits the real
    Anthropic API (see test_skill_gap_cross_domain.py's docstring)."""

    def __init__(self):
        self.last_usage = None
        self.calls: list[str] = []

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        self.calls.append(prompt)
        return _scripted_response()


def test_prompt_requires_full_verbatim_bullet_capture_not_a_summary():
    # Direct guard on the actual root cause: the old prompt literally asked
    # for '"description": "<1-2 sentence summary>"', which is what caused
    # the LLM to paraphrase/condense every role instead of preserving its
    # bullets. A future revert back to summary-style wording must fail here.
    # (The fixed prompt does contain the word "summary" - in the phrase "not
    # a summary" - so check for the old instruction's exact phrasing rather
    # than the bare word.)
    assert "1-2 sentence summary" not in RESUME_ANALYSIS_PROMPT.lower()
    assert "every bullet" in RESUME_ANALYSIS_PROMPT.lower()
    assert "verbatim" in RESUME_ANALYSIS_PROMPT.lower()


def test_all_bullets_captured_in_full_for_every_role_not_just_the_first_two():
    llm = _ScriptedResumeAnalyzerLLM()

    result = analyze_resume(llm, RESUME_TEXT)

    experience = result["experience"]
    assert len(experience) == 2

    analyst = next(e for e in experience if e["title"] == "Analyst")
    senior_associate = next(e for e in experience if e["title"] == "Senior Associate Analyst")

    # Not just a count: each role's ORIGINAL bullet count from the source
    # resume (4 and 5) must all be present, including the 3rd/4th/5th
    # bullets the old prompt silently dropped.
    for bullet in ANALYST_BULLETS:
        assert bullet in analyst["description"]
    for bullet in SENIOR_ASSOCIATE_BULLETS:
        assert bullet in senior_associate["description"]


def test_bullets_are_not_cut_off_at_the_first_clause():
    # The reported symptom: each captured bullet was truncated to just its
    # first clause (cut off at the first semicolon/period). Assert the text
    # AFTER the first semicolon in a multi-clause bullet is still present.
    llm = _ScriptedResumeAnalyzerLLM()

    result = analyze_resume(llm, RESUME_TEXT)
    analyst = next(e for e in result["experience"] if e["title"] == "Analyst")

    first_bullet = ANALYST_BULLETS[0]
    before_semicolon, after_semicolon = first_bullet.split(";", 1)
    assert before_semicolon.strip() in analyst["description"]
    assert after_semicolon.strip() in analyst["description"]

    # The 4th bullet of this role has no semicolon at all - its mere
    # presence proves capture didn't stop after the first two bullets.
    assert ANALYST_BULLETS[3] in analyst["description"]


class _NullSectionsLLM(LLMAdapter):
    """Returns valid JSON but with `null` for every list-typed section -
    exercises how analyze_resume handles a genuinely-empty section, since
    the prompt's example shape can't force the model to always emit []
    rather than null (2026-09-13 empty-array display bug investigation)."""

    def __init__(self):
        self.last_usage = None

    def generate(self, prompt, *, agent_name, temperature=0.7, max_tokens=1024):
        import json

        return json.dumps(
            {
                "skills": None,
                "experience": None,
                "education": None,
                "projects": None,
                "low_confidence_fields": None,
            }
        )


def test_null_sections_are_normalized_to_empty_lists_not_left_as_none():
    # A resume with a genuinely empty section (e.g. no projects listed) must
    # never surface as None/null anywhere downstream - every consumer
    # (this system's own API responses, the frontend, skill_gap_service's
    # .get(key, []) calls) treats a present empty list as "no data" and a
    # null as an error condition.
    llm = _NullSectionsLLM()

    result = analyze_resume(llm, "irrelevant - the fake LLM ignores the prompt")

    assert result["skills"] == []
    assert result["experience"] == []
    assert result["education"] == []
    assert result["projects"] == []
    assert result["low_confidence_fields"] == []
