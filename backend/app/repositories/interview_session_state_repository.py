"""Redis-backed store for live, in-progress interview session state.

Postgres (interview_session_repository) remains the source of truth for
completed turns and final results. This module holds the fast, resumable
in-progress snapshot: current question, topic queue, asked questions,
difficulty, turn index, and fine-grained status. Keyed by session id, one
JSON blob per session, TTL refreshed on every write (cache hygiene, not the
abandonment mechanism - see workflows.session_state.is_inactive for that).
"""

import json
import uuid

from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.workflows.session_state import LiveSessionState


def _key(session_id: uuid.UUID) -> str:
    return f"{settings.redis_key_prefix}:interview-session-state:{session_id}"


def save(state: LiveSessionState) -> None:
    client = get_redis_client()
    client.set(
        _key(uuid.UUID(state["session_id"])),
        json.dumps(state),
        ex=settings.interview_session_state_ttl_seconds,
    )


def load(session_id: uuid.UUID) -> LiveSessionState | None:
    raw = get_redis_client().get(_key(session_id))
    return json.loads(raw) if raw is not None else None


def delete(session_id: uuid.UUID) -> None:
    get_redis_client().delete(_key(session_id))
