# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current State

This repository currently contains **only planning documentation** (`docs/BRD.md` and `docs/architecture.md`) — no application code, no `backend/`, `frontend/`, or build tooling exist yet. There are no build/lint/test commands to run because nothing has been scaffolded.

When the user asks you to start implementing, follow the folder structure and phasing below rather than inventing a different structure. When code does exist in this repo in a future session, re-derive actual commands (package.json scripts, Makefile targets, etc.) from what's on disk rather than trusting this file blindly — update this section once real tooling exists.

## Project

**Interview Mentor** — an AI-powered adaptive interview coaching platform. It ingests a candidate's resume and a target job description, generates a tailored interview plan, runs a multi-turn adaptive interview (difficulty adjusts in real time based on answer quality), evaluates answers across multiple dimensions, and produces a long-term learning roadmap.

Full requirements: `docs/BRD.md`. Full architecture (v2, supersedes v1): `docs/architecture.md`.

## Architecture

The interview loop is a **cyclic state machine**, not a linear pipeline — this is the central architectural decision and should shape how the orchestration layer is built.

### Layers
- **Client** — React + TypeScript (Tailwind CSS, Shadcn UI, React Query, Zustand, Recharts).
- **API (REST)** — FastAPI, for one-shot ops: auth, resume/JD upload, plan generation, roadmap retrieval.
- **API (WebSocket/SSE)** — a dedicated real-time channel for the live interview session only, separate from REST because this traffic is stateful and long-lived.
- **Orchestration** — LangGraph-based. Resume Agent and JD Agent run once, in parallel, at session start → Interview Planner produces the plan → then **Question Generator → Interviewer → Evaluator cycles repeatedly**, each evaluation updating the candidate's running profile and determining the next question's difficulty, until the plan's exit condition (question count/time budget) is met → Mentor runs once at the end to produce the roadmap.
- **Async Processing** — Celery or Arq (Redis-backed) for resume parsing, embedding generation, and any other non-interactive-latency work. Must not run inline with request/response.
- **Session State Store** — Redis, persists current question/running score/difficulty per turn, so a dropped connection can resume without losing progress.
- **LLM Adapter Layer** — a thin provider-agnostic interface between agents and the model provider (GPT-5/Claude/etc.), so the model can be swapped without touching agent logic. Agents must never call a provider SDK directly.
- **Data Layer** — PostgreSQL (relational: users, resumes metadata, JDs, sessions, questions, answers, evaluations, skills, roadmaps, analytics), a vector DB (FAISS/Qdrant, for question banks/ideal answers/company patterns), Redis (cache/session/rate-limiting), object storage (S3/Azure Blob, original resume files only — never store original files in Postgres).

### Adaptive Interview Engine — state machine
`PLANNED → IN_PROGRESS → EVALUATING → ADVANCING → IN_PROGRESS (next turn, loops) → COMPLETE`, with `ABANDONED` if a dropped connection exceeds a timeout without resuming.

### AI agents and their guardrails
| Agent | Responsibility | Guardrail |
|---|---|---|
| Resume Analyzer | Extract structured skills/experience from resume text | Flag low-confidence fields; never fabricate experience not present in source |
| JD Analyzer | Extract role requirements/seniority from JD text | Distinguish required vs. preferred skills explicitly |
| Interview Planner | Produce topic mix and difficulty range from gap analysis | Plan must stay within candidate's stated experience level |
| Question Generator | Generate the next question given plan + running session state | No duplicate questions within a session; difficulty bounded by adaptive engine output |
| Interviewer | Deliver questions, manage conversational turn-taking | Stay in-persona; no unsolicited hints unless requested |
| Evaluator | Score each answer across defined dimensions | Rubric must be consistent and auditable; log rationale per score |
| Mentor | Synthesize session results into feedback + roadmap | Feedback must be specific and evidence-based, not generic |

### Planned backend folder structure
```
interview-mentor/
├── backend/
│   ├── app/
│   │   ├── api/            # REST route handlers
│   │   ├── websockets/     # live interview session channel
│   │   ├── core/           # config, security, dependency injection
│   │   ├── services/
│   │   ├── agents/
│   │   ├── workflows/      # LangGraph graph definitions
│   │   ├── background/     # Celery/Arq task definitions
│   │   ├── repositories/
│   │   ├── prompts/
│   │   ├── schemas/
│   │   ├── models/
│   │   └── utils/
│   ├── alembic/            # migrations, sibling of app/
│   ├── tests/
│   └── docker/
├── frontend/                # sibling of backend/, not nested inside it
└── docs/
```
`frontend/` must be a sibling of `backend/`, not nested inside it — this was an explicit correction from the v1 architecture.

## Key non-obvious constraints

- **Provider-agnostic LLM adapter is mandatory** — a single provider is used at launch, but agent code must go through the adapter layer, never a provider SDK directly (NFR — Maintainability).
- **Long-running AI work is never inline** — resume parsing, embeddings, etc. go through the async task queue so the request/response API layer stays responsive.
- **Session state must persist every turn** (Redis) — a dropped connection/page refresh mid-interview must be resumable without lost progress.
- **Evaluation calls should use low temperature / fixed rubric prompts** — scoring consistency across repeated runs is a named risk (BRD §14); log rationale per score for auditability.
- **Token usage must be tracked and capped per session** — runaway LLM cost from long/looping sessions is a named risk; the interview loop needs a timeout/exit condition, not just a natural completion path.
- **All LLM/agent calls must be traced** (prompt, response, latency, token cost) from Phase 4 onward — required for both cost control and quality auditing, not optional instrumentation.
- **Resume files never go in PostgreSQL** — original files go to object storage; only extracted text/metadata is relational. This was an explicit fix from v1.
- **Hallucination scoring and hiring-probability scoring are deferred (Could-have)** — they require labeled/calibration data that won't exist at launch. Don't build these speculatively.
- Voice mode, whiteboard/system-design canvas mode, multi-language support, and enterprise/B2B features are explicitly **out of scope** until Phase 8+.

## Delivery sequencing

The project follows a validate-first roadmap: **Phase 0 (vertical slice — hardcoded loop, no auth, no vector DB) proves the core adaptive Q&A experience before any multi-agent build-out begins.** Do not jump ahead to full LangGraph orchestration, RAG, or the corrected folder structure before Phase 0 is validated, unless the user explicitly directs otherwise. Full phase list is in `docs/BRD.md` §17 and `docs/architecture.md` §11.
