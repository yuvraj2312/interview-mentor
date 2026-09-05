import uuid

from sqlalchemy.orm import Session as DBSession

from app.models import LLMCall


def create(
    db: DBSession,
    *,
    agent_name: str,
    session_id: uuid.UUID | None,
    model: str,
    prompt: str,
    response: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
    latency_ms: int,
    cost_usd: float | None,
    temperature: float,
    max_tokens: int,
    status: str,
    error_message: str | None,
) -> LLMCall:
    call = LLMCall(
        agent_name=agent_name,
        session_id=session_id,
        model=model,
        prompt=prompt,
        response=response,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        temperature=temperature,
        max_tokens=max_tokens,
        status=status,
        error_message=error_message,
    )
    db.add(call)
    db.flush()
    return call
