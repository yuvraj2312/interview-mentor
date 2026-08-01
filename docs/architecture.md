**UPDATED HIGH-LEVEL ARCHITECTURE**

**Interview Mentor**

*Revision incorporating the architecture review findings*

Version 2.0 \| Draft

1 August 2026

*Supersedes: High-Level System Design & Development Roadmap v1*

Document Control

| **Field**         | **Detail**                                         |
|-------------------|----------------------------------------------------|
| Document Title    | Interview Mentor — Updated High-Level Architecture |
| Version           | 2.0 (Draft) — supersedes v1                        |
| Status            | Draft — reflects architecture review changes       |
| Related Documents | Business Requirements Document v1.0                |
| Last Updated      | 1 August 2026                                      |

Table of Contents

1\. Purpose of This Revision

This document supersedes the original High-Level System Design &
Development Roadmap. It carries forward the product vision, agents, and
data layers already agreed, and incorporates the structural changes
identified during architecture review: an explicit cyclic orchestration
model for the interview loop, an async processing layer, a stateful
session channel, object storage for resume files, a provider-agnostic
LLM adapter, and a corrected backend folder structure. Section 2
summarizes every change; later sections present the full updated
architecture.

2\. Summary of Changes

| **Area**              | **v1 (Original)**                                                        | **v2 (Updated)**                                                                                      |
|-----------------------|--------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| Interview loop        | Drawn as one step in a linear pipeline                                   | Modeled explicitly as a cyclic LangGraph state machine (Question → Answer → Evaluate → Update → Next) |
| Request handling      | Implicit synchronous FastAPI calls only                                  | REST for one-shot ops; dedicated WebSocket/SSE channel for the live interview session                 |
| Long-running work     | Not addressed — implied inline processing                                | Background task queue (Celery/Arq + Redis) for resume parsing, embeddings, and other slow jobs        |
| Session continuity    | Not addressed                                                            | Session state persisted turn-by-turn in Redis; a dropped connection can resume                        |
| Resume files          | Implied stored in PostgreSQL                                             | Original files in object storage (S3/Azure Blob); only metadata/extracted text in PostgreSQL          |
| LLM provider coupling | Agents implied to call GPT-5/Claude directly                             | Provider-agnostic LLM adapter layer sits between agents and the model provider                        |
| Folder structure      | frontend/ nested inside backend/; no core/ or background/                | frontend/ is a sibling of backend/; added core/, background/, websockets/                             |
| Evaluation scope      | Hallucination Score and Hiring Probability listed alongside core metrics | Marked as deferred (Could-have) until calibration data exists post-launch                             |
| Roadmap               | Phase 1 (Foundation) was the first build phase                           | Phase 0 (Vertical Slice) added ahead of Phase 1 to validate the core loop first                       |
| Observability         | Not addressed                                                            | LLM call tracing (prompt/response/latency/cost) required from Phase 4 onward                          |

3\. Updated High-Level Architecture

The diagram below reflects the corrected architecture: the interview
loop is a cycle rather than a pipeline step, and three
previously-missing layers — async processing, session state, and the LLM
adapter — are now explicit.

<img src="media/c1acfba7607bff4b5a5b3ae0eae8fd5762246246.png"
style="width:4.79167in;height:6.55208in" />

3.1 Layer-by-Layer Description

**Client Layer —** React + TypeScript frontend. Handles auth UI, upload
flows, the live interview UI, and the analytics dashboard.

**Auth Layer —** OAuth/JWT. Issues short-lived access tokens with
refresh rotation; authenticates both the REST API and the WebSocket
channel.

**API Layer (REST) —** FastAPI endpoints for one-shot operations:
account management, resume/JD upload, plan generation, roadmap
retrieval.

**API Layer (WebSocket/SSE) —** A dedicated real-time channel for the
live interview session — turn-by-turn question delivery and answer
submission, distinct from REST because this traffic is stateful and
long-lived.

**Orchestration Layer —** LangGraph-based orchestrator. Resume Agent, JD
Agent, Interview Planner, and Mentor run as discrete steps; the Question
Generator, Interviewer, and Evaluator form an explicit cycle that
repeats until the session's exit condition is met.

**Async Processing Layer —** A background task queue (Celery or Arq,
Redis-backed) handles resume parsing, embedding generation, and any
other work that would otherwise block a request.

**Session State Store —** Redis-backed store persisting current
question, running score, and difficulty level per session, so a dropped
connection can resume without losing progress.

**LLM Adapter Layer —** A thin, provider-agnostic interface between
agents and the underlying model provider(s), so GPT-5/Claude (or others)
can be swapped without touching agent logic.

**Data Layer —** PostgreSQL for relational data, a vector database for
retrieval-augmented knowledge, Redis for caching/session/rate-limiting,
and object storage for original resume files.

4\. Major Services

Services are now split by latency/statefulness profile rather than
listed flat, reflecting the distinction between one-shot analysis work
and the long-lived interview session.

4.1 One-Shot / Request-Response Services

- Authentication

- Resume Processing

- Job Description Processing

- Interview Planning

- Learning Roadmap

- Analytics

4.2 Stateful / Long-Lived Services

- Interview Session Runtime (WebSocket-backed, holds live session state)

- Long-term Memory (cross-session skill tracking)

4.3 Background Services

- Async Task Workers (resume parsing, embedding generation)

- LLM Call Tracing / Observability

5\. Corrected Backend Folder Structure

frontend/ moves to be a sibling of backend/, not nested inside it.
core/, background/, and websockets/ are added; alembic/ moves to the
backend root next to app/.

interview-mentor/

├── backend/

│ ├── app/

│ │ ├── api/ \# REST route handlers

│ │ ├── websockets/ \# live interview session channel

│ │ ├── core/ \# config, security, dependency injection

│ │ ├── services/

│ │ ├── agents/

│ │ ├── workflows/ \# LangGraph graph definitions

│ │ ├── background/ \# Celery/Arq task definitions

│ │ ├── repositories/

│ │ ├── prompts/

│ │ ├── schemas/

│ │ ├── models/

│ │ └── utils/

│ ├── alembic/ \# migrations (sibling of app/, not inside models/)

│ ├── tests/

│ └── docker/

├── frontend/ \# sibling of backend/, not nested inside it

└── docs/

6\. AI Agent Orchestration (Cyclic Workflow)

The workflow is a graph with a cycle, not the straight pipeline shown in
v1:

1.  Resume Analyzer and JD Analyzer run once per session, in parallel,
    at session start.

2.  Interview Planner consumes both outputs and produces the plan (topic
    mix, difficulty range).

3.  The Question Generator → Interviewer → Evaluator cycle then repeats:
    each evaluation updates the candidate's running profile, which
    determines the next question's difficulty, until the plan's exit
    condition (question count or time budget) is reached.

4.  Mentor runs once at session end, consuming the full evaluation
    history to produce the roadmap.

7\. Updated Data Layer

| **Store**            | **Contents**                                                                                                                                | **Change from v1**                                   |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| PostgreSQL           | Users, Resumes (metadata), JDs, Sessions, Questions, Answers, Evaluations, Skills, Roadmaps, Analytics                                      | Unchanged — now explicitly metadata-only for resumes |
| Vector Database      | Interview questions, ideal answers, company experiences, behavioral examples, system design knowledge, coding questions, learning resources | Unchanged                                            |
| Redis                | Caching, rate limiting, session management, live interview turn-state                                                                       | Session state responsibility made explicit           |
| Object Storage (new) | Original resume files (PDF/DOCX)                                                                                                            | New — was implicitly missing in v1                   |

8\. Adaptive Interview Engine — State Machine

Formalized as an explicit state machine so the loop shown in Section 6
has concrete states and transitions:

- PLANNED → session created, plan attached, no questions asked yet.

- IN_PROGRESS → current question delivered, awaiting candidate answer.

- EVALUATING → answer received, Evaluator scoring in progress.

- ADVANCING → candidate profile updated; Difficulty Estimator selects
  the next question's difficulty.

- IN_PROGRESS (next turn) → repeats until exit condition met.

- COMPLETE → Mentor generates session summary and roadmap.

- ABANDONED → connection dropped past a timeout threshold without
  resume; session flagged for later cleanup.

9\. Non-Functional Additions

| **Category**    | **Addition**                                                                                                                       |
|-----------------|------------------------------------------------------------------------------------------------------------------------------------|
| Scalability     | Long-running AI tasks run on the async task queue, not inline with request/response, so the API layer stays responsive under load. |
| Reliability     | Interview session state persists per turn in Redis, so a dropped connection does not lose progress (see Section 8).                |
| Maintainability | The LLM adapter layer isolates agent logic from any single model provider's SDK.                                                   |
| Observability   | All LLM/agent calls are traced (prompt, response, latency, token cost) from Phase 4 onward for debugging and quality auditing.     |
| Data Handling   | Resume files live in object storage, not the relational database, keeping PostgreSQL lean and access-controlled separately.        |

10\. Updated Technology Stack

| **Layer**          | **Technologies**                                                                                                            |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------|
| Frontend           | React, TypeScript, Tailwind CSS, Shadcn UI, React Query, Zustand, Recharts                                                  |
| Backend            | FastAPI, SQLAlchemy, Alembic, Pydantic                                                                                      |
| Real-time          | WebSockets / Server-Sent Events for the live interview channel (new)                                                        |
| Async Processing   | Celery or Arq with Redis as broker (new)                                                                                    |
| AI / Orchestration | GPT-5 / Claude behind a provider adapter (new), LangGraph, LangChain where appropriate, Sentence Transformers, FAISS/Qdrant |
| Data               | PostgreSQL, Redis, Vector Database (FAISS/Qdrant), Object Storage — S3/Azure Blob (new)                                     |
| Infrastructure     | Docker, GitHub Actions, AWS or Azure                                                                                        |
| Observability      | Structured logging + LLM call tracing, e.g. LangSmith or equivalent (new)                                                   |

11\. Updated Development Roadmap

| **Phase**                                  | **Goal**                                                                                                           | **Change from v1**                                                                              |
|--------------------------------------------|--------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| Phase 0 — Vertical Slice (new)             | Prove the core adaptive loop end-to-end with a minimal, hardcoded implementation before any multi-agent build-out. | Added ahead of Phase 1                                                                          |
| Phase 1 — Foundation                       | Auth, DB schema, base API structure, corrected folder scaffolding.                                                 | Folder structure corrected (Section 5)                                                          |
| Phase 2 — Resume & JD Intelligence         | File upload, parsing, structured extraction, skill-gap comparison.                                                 | Object storage now specified for files                                                          |
| Phase 3 — Interview Planner                | Plan generation from gap analysis.                                                                                 | Unchanged                                                                                       |
| Phase 4 — Adaptive Interview Engine        | Full LangGraph interview loop as a cyclic state machine over WebSocket, with async workers live.                   | Cyclic model, WebSocket channel, async queue, LLM adapter, and observability all specified here |
| Phase 5 — Evaluation Pipeline              | Multi-dimensional scoring, rubric consistency checks.                                                              | Unchanged                                                                                       |
| Phase 6 — Session Memory & Roadmap         | Cross-session skill tracking, roadmap generation/updates.                                                          | Unchanged                                                                                       |
| Phase 7 — Analytics Dashboard              | Skill radar, progress charts, session history UI.                                                                  | Unchanged                                                                                       |
| Phase 8 — Voice, Coding & Whiteboard Modes | Additional interview modalities.                                                                                   | Explicitly deferred until after core loop validation                                            |
| Phase 9 — Production Hardening             | Load testing, cost controls, security review, observability.                                                       | Unchanged                                                                                       |

12\. Recommended Starting Point

Unchanged in principle from the original recommendation, now sequenced
explicitly behind the Phase 0 vertical slice:

5.  Build the Phase 0 vertical slice first (hardcoded loop, no auth, no
    vector DB) to validate the core product experience.

6.  Design the database schema (ERD), including the corrected
    object-storage reference for resumes.

7.  Design REST and WebSocket API contracts separately, given their
    different statefulness.

8.  Design the LangGraph workflow as a graph with the Question
    Generator/Interviewer/Evaluator cycle made explicit.

9.  Define agent input/output contracts, including the LLM adapter
    interface.

10. Design the RAG indexing strategy for the vector database.

11. Finalize the corrected folder structure (Section 5).

12. Separate relational data from vector knowledge and object storage
    explicitly.

13. Design the adaptive interview session state machine (Section 8)
    before implementing Phase 4.
