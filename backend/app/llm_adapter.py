"""Provider-agnostic LLM adapter.

Agent/service code (see interview.py) must call through LLMAdapter and
never import a provider SDK directly, so the underlying model can be
swapped without touching call sites (CLAUDE.md - Maintainability NFR).
"""

from abc import ABC, abstractmethod

import anthropic

from app.core.config import settings


class LLMAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Return the text completion for a single-turn prompt."""


class AnthropicAdapter(LLMAdapter):
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        text_block = next(block for block in response.content if block.type == "text")
        return text_block.text


def get_llm_adapter() -> LLMAdapter:
    return AnthropicAdapter()
