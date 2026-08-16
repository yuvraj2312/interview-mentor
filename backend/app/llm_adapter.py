"""Provider-agnostic LLM adapter.

Agent/service code (see interview.py) must call through LLMAdapter and
never import a provider SDK directly, so the underlying model can be
swapped without touching call sites (CLAUDE.md - Maintainability NFR).
"""

from abc import ABC, abstractmethod

import anthropic

from app.config import settings


class LLMAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, effort: str = "high", max_tokens: int = 1024) -> str:
        """Return the text completion for a single-turn prompt.

        `effort` (low/medium/high/xhigh/max) replaces temperature as the
        steering knob - claude-sonnet-5 rejects temperature/top_p/top_k
        entirely rather than just deprecating them.
        """


class AnthropicAdapter(LLMAdapter):
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    def generate(self, prompt: str, effort: str = "high", max_tokens: int = 1024) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            output_config={"effort": effort},
            messages=[{"role": "user", "content": prompt}],
        )
        # Thinking is on by default on claude-sonnet-5, so content[0] may be
        # a `thinking` block rather than `text` - find the text block explicitly.
        text_block = next(block for block in response.content if block.type == "text")
        return text_block.text


def get_llm_adapter() -> LLMAdapter:
    return AnthropicAdapter()
