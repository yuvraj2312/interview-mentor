**BUSINESS REQUIREMENTS DOCUMENT**

**Interview Mentor**

*An AI-Powered Adaptive Interview Coaching Platform*

Version 1.0 \| Draft

31 July 2026

Document Control

| **Field**         | **Detail**                                          |
|-------------------|-----------------------------------------------------|
| Document Title    | Business Requirements Document — Interview Mentor   |
| Version           | 1.0 (Draft)                                         |
| Prepared For      | Project Owner / Founding Team                       |
| Status            | Draft — pending stakeholder review                  |
| Last Updated      | 31 July 2026                                        |
| Related Documents | High-Level System Design & Development Roadmap (v1) |

Table of Contents

1\. Executive Summary

Interview Mentor is an AI-powered adaptive interview coaching platform
designed to replace static, generic mock-interview experiences with a
personalized, evolving interview "operating system." The platform
ingests a candidate's resume and a target job description, generates a
tailored interview plan, conducts an adaptive multi-turn interview that
adjusts difficulty in real time, evaluates the candidate across multiple
dimensions, and produces a long-term, trackable learning roadmap.

This Business Requirements Document (BRD) translates the previously
reviewed high-level architecture into a structured set of business
objectives, scope boundaries, functional and non-functional
requirements, data and AI-agent specifications, risks, and a phased
delivery plan. It is intended to be the single reference point
stakeholders and engineers align to before detailed design (ERDs, API
contracts, LangGraph workflows) begins.

The recommended approach is to validate the core adaptive-interview loop
with a minimal vertical slice before investing in the full multi-agent
architecture, and to treat advanced capabilities (voice mode, whiteboard
mode, hiring-probability scoring) as post-validation phases rather than
launch requirements.

2\. Business Objectives

The platform is being built to achieve the following measurable business
outcomes:

- Reduce candidate interview-preparation time by replacing generic
  question banks with a personalized, resume- and JD-aware interview
  plan.

- Improve candidate readiness by simulating realistic interview pressure
  with adaptive difficulty, rather than static question lists.

- Provide actionable, multi-dimensional feedback (technical,
  communication, reasoning, confidence) instead of generic pass/fail
  scoring.

- Enable long-term skill tracking across multiple sessions so candidates
  can see measurable improvement over time.

- Establish a defensible, differentiated product in the interview-prep
  space through multi-agent AI orchestration rather than a single-prompt
  chatbot.

2.1 Success Metrics (KPIs)

| **KPI**                                | **Target (Post-MVP, 90 days)**     | **Measurement Source**     |
|----------------------------------------|------------------------------------|----------------------------|
| Interview session completion rate      | ≥ 70%                              | Analytics — session funnel |
| Average sessions per active user       | ≥ 3 / month                        | Analytics — engagement     |
| Candidate-reported feedback usefulness | ≥ 4.0 / 5.0                        | In-app survey              |
| Evaluation-to-human-review agreement   | ≥ 80% agreement on a sampled audit | Manual QA sampling         |
| p95 question-to-question latency       | \< 4 seconds                       | APM / tracing              |
| Monthly active users (post-launch)     | Baseline + defined growth target   | Analytics                  |

3\. Problem Statement

Existing interview-preparation tools suffer from the following
well-understood gaps, which this platform is designed to close:

- Static interview question lists that do not adapt to the candidate's
  actual background or the specific role being targeted.

- Fixed-format mock interviews that do not adjust difficulty based on
  demonstrated performance.

- Generic, non-actionable feedback that does not identify specific
  knowledge gaps.

- No personalization to the candidate's resume or the job description
  they are preparing for.

- No mechanism for long-term progress tracking across multiple practice
  sessions.

- Poor simulation of real interview pressure and pacing.

4\. Scope

Scope is deliberately split between what is required to validate and
launch the product (MVP) and what is deferred to later phases. This
split follows directly from the architecture review: advanced modalities
and scoring mechanisms require usage data and calibration that will not
exist at launch.

4.1 In Scope — MVP (Phases 1–5)

- User authentication (email/password or OAuth) and session management.

- Resume upload and text-based parsing (PDF/DOCX to structured text).

- Job description input (pasted text) and analysis.

- AI-generated interview plan based on resume + JD.

- Text-based adaptive interview loop with difficulty adjustment based on
  answer quality.

- Multi-dimensional evaluation per answer (technical accuracy,
  communication, completeness).

- Session-level summary report with strengths, gaps, and a basic
  learning roadmap.

- Persistent storage of session history per user.

4.2 In Scope — Phase 2 Enhancements (Phases 6–7)

- Long-term memory across sessions (skill trend over time).

- Vector-based retrieval for question banks, ideal answers, and
  company-specific question patterns.

- Coding-round mode (code editor + execution/evaluation).

- Analytics dashboard for candidates (skill radar, progress charts).

4.3 Out of Scope — Deferred (Phase 8+, requires post-launch validation)

- Voice-based interview mode (speech-to-text/text-to-speech pipeline).

- Whiteboard / system-design collaborative canvas mode.

- Hallucination-score and hiring-probability scoring — requires labeled
  data and calibration against real hiring outcomes.

- Multi-language support.

- Enterprise/B2B features (recruiter dashboards, bulk candidate
  management, white-labeling).

- Mobile native applications (web-responsive only at launch).

5\. Stakeholders

| **Role**                | **Responsibility / Interest**                                             |
|-------------------------|---------------------------------------------------------------------------|
| Product Owner / Founder | Overall product vision, prioritization, and business decisions            |
| Engineering Lead        | Technical architecture, delivery quality, feasibility trade-offs          |
| AI/ML Engineer          | Agent design, prompt engineering, evaluation quality, model selection     |
| Frontend Engineer       | Candidate-facing UI/UX, session interface, analytics dashboard            |
| End User — Candidate    | Primary user; consumes interview sessions and feedback                    |
| QA / Reviewer           | Validates evaluation accuracy and system reliability                      |
| Data Privacy Reviewer   | Ensures resume/PII handling meets applicable data protection requirements |

6\. User Personas

6.1 Primary Persona — The Active Job Seeker

A candidate actively applying to roles (often technical or
knowledge-worker roles) who wants realistic, targeted practice rather
than generic question banks. Time-constrained, preparing for multiple
roles in parallel, and motivated by concrete, actionable feedback rather
than a raw score.

6.2 Secondary Persona — The Long-Term Skill Builder

A candidate preparing over weeks or months (e.g., for competitive roles)
who values trend tracking across sessions, identification of recurring
weaknesses, and a structured learning roadmap rather than one-off
practice.

7\. User Journey

The end-to-end candidate journey that all functional requirements below
must support:

1.  Login / account creation.

2.  Upload resume (file) and paste or upload target job description.

3.  System performs resume and JD analysis, extracting skills,
    experience level, and role requirements.

4.  System detects skill gaps between candidate profile and role
    requirements.

5.  System generates a tailored interview plan (topics, question mix,
    target difficulty range).

6.  Candidate proceeds through an adaptive interview session
    (multi-turn, difficulty adjusts per answer).

7.  System evaluates each answer and aggregates a session-level
    evaluation.

8.  System generates a personalized learning roadmap addressing
    identified gaps.

9.  Candidate reviews results and progress on an analytics dashboard.

10. Candidate returns for subsequent sessions; system uses long-term
    memory to adjust future plans.

8\. Functional Requirements

Requirements are grouped by module and tagged with priority: Must
(MVP-blocking), Should (targeted for Phase 2), Could (nice-to-have /
future).

8.1 Authentication

| **ID**     | **Requirement**                                                                   | **Priority** |
|------------|-----------------------------------------------------------------------------------|--------------|
| FR-AUTH-01 | System shall allow account creation via email/password or OAuth provider.         | Must         |
| FR-AUTH-02 | System shall issue JWT-based session tokens with defined expiry and refresh flow. | Must         |
| FR-AUTH-03 | System shall support password reset via verified email.                           | Should       |
| FR-AUTH-04 | System shall support role-based access (candidate vs. future admin roles).        | Could        |

8.2 Resume Processing

| **ID**    | **Requirement**                                                                                                | **Priority** |
|-----------|----------------------------------------------------------------------------------------------------------------|--------------|
| FR-RES-01 | System shall accept resume upload in PDF and DOCX formats.                                                     | Must         |
| FR-RES-02 | System shall extract structured data: skills, experience, education, projects.                                 | Must         |
| FR-RES-03 | System shall store the original file in object storage and extracted text/metadata in the relational database. | Must         |
| FR-RES-04 | System shall flag low-confidence extractions for candidate review/correction.                                  | Should       |

8.3 Job Description Processing

| **ID**   | **Requirement**                                                                       | **Priority** |
|----------|---------------------------------------------------------------------------------------|--------------|
| FR-JD-01 | System shall accept a pasted or uploaded job description.                             | Must         |
| FR-JD-02 | System shall extract required skills, seniority level, and role category from the JD. | Must         |
| FR-JD-03 | System shall compute a structured skill-gap comparison between resume and JD.         | Must         |

8.4 Interview Planning

| **ID**     | **Requirement**                                                                                                     | **Priority** |
|------------|---------------------------------------------------------------------------------------------------------------------|--------------|
| FR-PLAN-01 | System shall generate an interview plan (topic mix, question count, target difficulty) from the resume/JD analysis. | Must         |
| FR-PLAN-02 | System shall allow the candidate to select interview duration/format before starting.                               | Should       |
| FR-PLAN-03 | System shall incorporate prior session history into the plan when available.                                        | Should       |

8.5 Adaptive Interview Engine

| **ID**    | **Requirement**                                                                       | **Priority** |
|-----------|---------------------------------------------------------------------------------------|--------------|
| FR-INT-01 | System shall conduct a multi-turn, text-based interview session.                      | Must         |
| FR-INT-02 | System shall adjust question difficulty based on running evaluation of prior answers. | Must         |
| FR-INT-03 | System shall persist session state so an interrupted session can be resumed.          | Must         |
| FR-INT-04 | System shall support a coding-round sub-mode with code execution/evaluation.          | Should       |
| FR-INT-05 | System shall support a voice-based sub-mode (speech-to-text and text-to-speech).      | Could        |
| FR-INT-06 | System shall support a whiteboard/system-design collaborative sub-mode.               | Could        |

8.6 Evaluation

| **ID**     | **Requirement**                                                                                | **Priority** |
|------------|------------------------------------------------------------------------------------------------|--------------|
| FR-EVAL-01 | System shall score each answer on technical accuracy, communication, and completeness.         | Must         |
| FR-EVAL-02 | System shall generate a session-level aggregate evaluation with identified strengths and gaps. | Must         |
| FR-EVAL-03 | System shall score reasoning quality and response confidence.                                  | Should       |
| FR-EVAL-04 | System shall compute a hallucination/uncertainty indicator on evaluated answers.               | Could        |
| FR-EVAL-05 | System shall estimate a hiring-probability signal calibrated against outcome data.             | Could        |

8.7 Learning Roadmap

| **ID**     | **Requirement**                                                                                   | **Priority** |
|------------|---------------------------------------------------------------------------------------------------|--------------|
| FR-ROAD-01 | System shall generate a personalized learning roadmap from identified skill gaps.                 | Must         |
| FR-ROAD-02 | System shall recommend specific resources/topics per gap, sourced from the vector knowledge base. | Should       |
| FR-ROAD-03 | System shall update the roadmap after each subsequent session based on progress.                  | Should       |

8.8 Analytics & Long-Term Memory

| **ID**   | **Requirement**                                                                               | **Priority** |
|----------|-----------------------------------------------------------------------------------------------|--------------|
| FR-AN-01 | System shall present a per-session results summary to the candidate.                          | Must         |
| FR-AN-02 | System shall track and visualize skill trends across sessions (skill radar, progress charts). | Should       |
| FR-AN-03 | System shall retain long-term candidate profile data to personalize future sessions.          | Should       |
| FR-AN-04 | System shall allow the candidate to export or delete their historical data.                   | Must         |

9\. Non-Functional Requirements

| **Category**    | **Requirement**                                                                                                                                                  |
|-----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Performance     | p95 latency per interview turn (question generation + display) under 4 seconds; resume/JD analysis under 15 seconds via async processing with progress feedback. |
| Scalability     | Backend services shall scale horizontally; long-running AI tasks shall run on a background task queue, not inline with request/response.                         |
| Availability    | Target 99.5% uptime for core interview-session functionality post-launch.                                                                                        |
| Security        | All traffic over TLS; secrets managed via a secrets manager, not environment files in source control; JWT tokens short-lived with refresh rotation.              |
| Data Privacy    | Resumes and extracted PII classified as sensitive; encrypted at rest; access-logged; candidate-initiated deletion/export supported (see FR-AN-04).               |
| Reliability     | Interview session state must be persisted per turn so a dropped connection does not lose progress.                                                               |
| Observability   | All LLM/agent calls shall be traced (prompt, response, latency, token cost) for debugging and quality auditing.                                                  |
| Cost Control    | Token usage per session shall be tracked and capped/alerted to prevent runaway LLM spend.                                                                        |
| Maintainability | Provider-agnostic LLM adapter layer so the underlying model (GPT/Claude/etc.) can be swapped without touching agent logic.                                       |
| Portability     | Containerized services (Docker) deployable to either AWS or Azure without architectural rework.                                                                  |

10\. System Architecture Overview

Full architectural detail is maintained in the companion High-Level
System Design document; this section summarizes the layers this BRD's
requirements map onto.

- Client Layer: React/TypeScript frontend for authentication, upload,
  session UI, and analytics dashboard.

- API Layer: FastAPI backend exposing REST endpoints for one-shot
  operations (auth, upload, plan generation) and a WebSocket/SSE channel
  for the live, stateful interview session.

- Orchestration Layer: LangGraph-based orchestrator modeling the
  interview as a cyclic state machine (not a linear pipeline),
  coordinating the Resume, JD, Planner, Question Generator, Interviewer,
  Evaluator, and Mentor agents.

- Async Processing Layer: A background task queue (e.g., Celery/Arq)
  handling resume parsing, embedding generation, and other
  non-interactive-latency work.

- Data Layer: PostgreSQL for relational/session data, a vector database
  for retrieval-augmented question/answer knowledge, Redis for
  caching/session/rate-limiting, and object storage for original resume
  files.

- AI Provider Layer: A provider-agnostic adapter over the underlying
  LLM(s), enabling model swaps without touching agent logic.

11\. Data Requirements

11.1 Core Entities

- User — account, auth credentials/provider, profile.

- Resume — original file reference, extracted structured data, version
  history.

- JobDescription — raw text, extracted structured requirements.

- InterviewSession — plan, state, start/end, status
  (in-progress/complete/abandoned).

- Question — text, topic, difficulty, source (generated/retrieved).

- Answer — candidate response, timestamp, response time.

- Evaluation — per-answer and per-session scores across all dimensions.

- SkillProfile — long-term aggregated skill state per candidate.

- Roadmap — recommended topics/resources tied to identified gaps.

- AnalyticsEvent — usage/engagement events for reporting.

11.2 Data Classification & Storage

| **Data Type**                       | **Sensitivity** | **Store**                                 |
|-------------------------------------|-----------------|-------------------------------------------|
| Auth credentials / tokens           | High            | PostgreSQL (hashed) / secrets manager     |
| Resume file (original)              | High (PII)      | Object storage (S3/Azure Blob), encrypted |
| Extracted resume text/skills        | High (PII)      | PostgreSQL                                |
| Job descriptions                    | Low–Medium      | PostgreSQL                                |
| Interview Q&A transcripts           | Medium          | PostgreSQL                                |
| Evaluation scores                   | Medium          | PostgreSQL                                |
| Question/answer knowledge base      | Low             | Vector database                           |
| Session cache / rate-limit counters | Low             | Redis (ephemeral)                         |

12\. AI Agent Requirements

| **Agent**          | **Responsibility**                                                    | **Guardrails**                                                                         |
|--------------------|-----------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| Resume Analyzer    | Extract structured skills/experience from resume text.                | Flag low-confidence fields; never fabricate experience not present in source.          |
| JD Analyzer        | Extract role requirements and seniority signal from JD text.          | Distinguish required vs. preferred skills explicitly.                                  |
| Interview Planner  | Produce topic mix and difficulty range from gap analysis.             | Plan must stay within candidate's stated experience level.                             |
| Question Generator | Generate the next question given plan + running session state.        | No duplicate questions within a session; difficulty bounded by adaptive engine output. |
| Interviewer        | Deliver questions and manage conversational flow/turn-taking.         | Stay in-persona; no unsolicited hints unless candidate requests one.                   |
| Evaluator          | Score each answer across defined dimensions.                          | Scoring rubric must be consistent and auditable; log rationale per score.              |
| Mentor             | Synthesize session results into feedback and roadmap recommendations. | Feedback must be specific and evidence-based, not generic praise/criticism.            |

13\. Assumptions & Constraints

13.1 Assumptions

- Candidates will interact primarily via web browser at launch; no
  native mobile app required for MVP.

- English-language resumes and interviews only at launch.

- A single LLM provider (GPT or Claude family) will be used at launch,
  behind an adapter layer for future flexibility.

- Initial evaluation rubrics will be manually defined by the team and
  refined once usage data is available.

13.2 Constraints

- LLM API costs directly scale with session length and must be actively
  monitored (see Non-Functional Requirements — Cost Control).

- Advanced scoring features (hallucination score, hiring probability)
  are constrained by the absence of labeled/calibration data at launch.

- Real-time voice/whiteboard modes are constrained by additional
  infrastructure (speech pipeline, collaborative canvas) not required
  for MVP validation.

14\. Risks & Mitigations

| **Risk**                                                                  | **Impact** | **Mitigation**                                                                             |
|---------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------------|
| LLM evaluation inconsistency (same answer scored differently across runs) | High       | Fixed rubric prompts, low temperature for evaluation calls, periodic human-audit sampling. |
| Resume/JD parsing failures on non-standard formats                        | Medium     | Confidence flagging + candidate-editable extracted fields (FR-RES-04).                     |
| Runaway LLM cost from long/looping sessions                               | Medium     | Per-session token caps, timeout on interview loop, cost alerting.                          |
| Candidate PII exposure/breach                                             | High       | Encryption at rest/in transit, access logging, minimal retention, deletion on request.     |
| Synchronous request handling causing timeouts under agent chaining        | Medium     | Background task queue for non-interactive-latency work (see NFR — Scalability).            |
| Scope creep toward advanced features before core loop is validated        | Medium     | Phase-gated roadmap with an explicit MVP vertical-slice milestone before Phase 2.          |

15\. Dependencies

- LLM provider API availability and rate limits (GPT-5 / Claude family).

- Vector database service (FAISS self-hosted or managed Qdrant).

- Cloud infrastructure account (AWS or Azure) for compute, object
  storage, and CI/CD.

- Object storage bucket configuration for resume files.

- Background task queue infrastructure (Redis-backed Celery/Arq).

16\. Acceptance Criteria for MVP Launch

The MVP is considered launch-ready when all of the following are
demonstrably true:

11. A candidate can create an account, upload a resume, and paste a job
    description without errors on supported formats.

12. The system generates an interview plan and conducts a complete
    adaptive, text-based interview session end-to-end.

13. Difficulty visibly adjusts based on answer quality within a session
    (verified via test scenarios of strong vs. weak answers).

14. Every completed session produces a multi-dimensional evaluation and
    a learning roadmap.

15. Session state survives a dropped connection/page refresh
    mid-interview.

16. p95 turn latency is under the target defined in the Non-Functional
    Requirements.

17. Candidate data can be exported and deleted on request.

18. Core LLM calls are traced and auditable for cost and quality review.

17\. Development Roadmap & Phasing

This roadmap reflects a validate-first sequencing: the adaptive
interview loop is proven with a minimal vertical slice (Phase 0) before
the full multi-agent architecture, RAG layer, and advanced modalities
are built out.

| **Phase**                                  | **Goal**                                                                                  | **Exit Criteria**                                                      |
|--------------------------------------------|-------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| Phase 0 — Vertical Slice                   | Prove the core loop: resume+JD text in, adaptive Q&A, one evaluator call, stored session. | End-to-end demo works for one real resume/JD pair.                     |
| Phase 1 — Foundation                       | Auth, DB schema, base API structure, folder/project scaffolding.                          | A candidate can log in and reach an empty dashboard.                   |
| Phase 2 — Resume & JD Intelligence         | File upload, parsing, structured extraction, skill-gap comparison.                        | Extraction accuracy validated against a sample resume set.             |
| Phase 3 — Interview Planner                | Plan generation from gap analysis.                                                        | Plans are consistent and bounded by candidate experience level.        |
| Phase 4 — Adaptive Interview Engine        | Full LangGraph interview loop with real-time difficulty adjustment.                       | Loop passes scripted strong/weak-answer test scenarios.                |
| Phase 5 — Evaluation Pipeline              | Multi-dimensional scoring, rubric consistency checks.                                     | Evaluation-human agreement meets target KPI on sample audit.           |
| Phase 6 — Session Memory & Roadmap         | Cross-session skill tracking, roadmap generation/updates.                                 | Roadmap updates correctly after a second session.                      |
| Phase 7 — Analytics Dashboard              | Skill radar, progress charts, session history UI.                                         | Dashboard reflects accurate historical data.                           |
| Phase 8 — Voice, Coding & Whiteboard Modes | Additional interview modalities.                                                          | Each modality passes its own acceptance test independent of core loop. |
| Phase 9 — Production Hardening             | Load testing, cost controls, security review, observability.                              | NFR targets met under simulated production load.                       |

18\. Technology Stack

| **Layer**          | **Technologies**                                                                                                        |
|--------------------|-------------------------------------------------------------------------------------------------------------------------|
| Frontend           | React, TypeScript, Tailwind CSS, Shadcn UI, React Query, Zustand, Recharts                                              |
| Backend            | FastAPI, SQLAlchemy, Alembic, Pydantic                                                                                  |
| AI / Orchestration | GPT-5 / Claude (behind a provider adapter), LangGraph, LangChain where appropriate, Sentence Transformers, FAISS/Qdrant |
| Async Processing   | Celery or Arq with Redis as broker                                                                                      |
| Data               | PostgreSQL, Redis, Vector Database (FAISS/Qdrant), Object Storage (S3/Azure Blob)                                       |
| Infrastructure     | Docker, GitHub Actions (CI/CD), AWS or Azure                                                                            |
| Observability      | Structured logging + LLM call tracing (e.g., LangSmith or equivalent)                                                   |

19\. Glossary

| **Term**                  | **Definition**                                                                                                     |
|---------------------------|--------------------------------------------------------------------------------------------------------------------|
| Agent                     | A specialized AI component responsible for one part of the interview workflow (e.g., Evaluator, Mentor).           |
| Adaptive Interview Engine | The subsystem that adjusts question difficulty in real time based on candidate performance.                        |
| BRD                       | Business Requirements Document — this document.                                                                    |
| LangGraph                 | Framework used to orchestrate multi-agent, stateful AI workflows as a graph rather than a linear pipeline.         |
| RAG                       | Retrieval-Augmented Generation — retrieving relevant knowledge (from the vector database) to ground LLM responses. |
| Vertical Slice            | A minimal end-to-end implementation of the core user flow, used to validate the product before full build-out.     |
| Skill Radar               | A visual analytics representation of a candidate's strengths/weaknesses across evaluated dimensions.               |
