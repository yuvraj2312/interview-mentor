"""Provider-agnostic LLM adapter.

Agent/service code (see interview.py) must call through LLMAdapter and
never import a provider SDK directly, so the underlying model can be
swapped without touching call sites (CLAUDE.md - Maintainability NFR).

This is also the single instrumentation point for LLM observability
(CLAUDE.md - "All LLM/agent calls must be traced [...] from Phase 4
onward"): every generate() call is timed, its token usage/cost computed,
persisted to the llm_calls table, and logged - once, here, rather than
bolted onto each agent separately.
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

import anthropic
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.llm_pricing import estimate_cost_usd
from app.repositories import llm_call_repository

logger = logging.getLogger("app.llm_adapter")


@dataclass
class LLMCallUsage:
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int


class LLMAdapter(ABC):
    # Usage/cost for the most recent generate() call on this instance, or
    # None if no call has completed successfully yet. This is how callers
    # that can't change generate()'s str return type (the interview graph
    # nodes, for the cost cap) read per-call cost.
    last_usage: LLMCallUsage | None = None

    @abstractmethod
    def generate(
        self, prompt: str, *, agent_name: str, temperature: float = 0.7, max_tokens: int = 1024
    ) -> str:
        """Return the text completion for a single-turn prompt.

        agent_name identifies the caller for tracing (e.g. "resume_analyzer",
        "question_generator") - required so every persisted/logged call is
        attributable, without agents needing to do their own tracing.
        """


class AnthropicAdapter(LLMAdapter):
    def __init__(self, db: DBSession, *, session_id: UUID | None = None) -> None:
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model
        self._db = db
        self._session_id = session_id
        self.last_usage = None
        # Guards self._db (a SQLAlchemy Session, not safe for concurrent
        # use) and self.last_usage for callers that run generate() from
        # multiple threads against one adapter instance (e.g. the
        # skill-gap LLM fallback pass). The network call itself is
        # intentionally made outside this lock so concurrent callers still
        # overlap on the slow part.
        self._lock = threading.Lock()

    def generate(
        self, prompt: str, *, agent_name: str, temperature: float = 0.7, max_tokens: int = 1024
    ) -> str:
        started = time.monotonic()
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            latency_ms = int((time.monotonic() - started) * 1000)
            with self._lock:
                self.last_usage = None
                llm_call_repository.create(
                    self._db,
                    agent_name=agent_name,
                    session_id=self._session_id,
                    model=self._model,
                    prompt=prompt,
                    response=None,
                    input_tokens=None,
                    output_tokens=None,
                    latency_ms=latency_ms,
                    cost_usd=None,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    status="error",
                    error_message=str(exc),
                )
            logger.error(
                "llm_call agent=%s model=%s status=error latency_ms=%d error=%s",
                agent_name,
                self._model,
                latency_ms,
                exc,
            )
            raise

        latency_ms = int((time.monotonic() - started) * 1000)
        text_block = next(block for block in response.content if block.type == "text")
        text = text_block.text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost_usd = estimate_cost_usd(self._model, input_tokens, output_tokens)

        with self._lock:
            self.last_usage = LLMCallUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
            )

            llm_call_repository.create(
                self._db,
                agent_name=agent_name,
                session_id=self._session_id,
                model=self._model,
                prompt=prompt,
                response=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                temperature=temperature,
                max_tokens=max_tokens,
                status="success",
                error_message=None,
            )
        logger.info(
            "llm_call agent=%s model=%s status=success latency_ms=%d input_tokens=%d output_tokens=%d cost_usd=%.6f",
            agent_name,
            self._model,
            latency_ms,
            input_tokens,
            output_tokens,
            cost_usd,
        )
        return text


def get_llm_adapter(db: DBSession, *, session_id: UUID | None = None) -> LLMAdapter:
    return AnthropicAdapter(db, session_id=session_id)
