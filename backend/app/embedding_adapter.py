"""Provider-agnostic embedding adapter.

Mirrors llm_adapter.py's pattern: service code must call through
EmbeddingAdapter and never import fastembed directly, so the embedding
model/provider can be swapped without touching call sites. Anthropic has
no embeddings API, so this wraps a local model instead of the Anthropic
adapter.
"""

from abc import ABC, abstractmethod

from app.core.config import settings

_model_cache: dict[str, object] = {}


class EmbeddingAdapter(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text, in the same order."""


def _get_model(model_name: str):
    if model_name not in _model_cache:
        from fastembed import TextEmbedding

        _model_cache[model_name] = TextEmbedding(model_name=model_name)
    return _model_cache[model_name]


class FastEmbedAdapter(EmbeddingAdapter):
    def __init__(self) -> None:
        self._model = _get_model(settings.embedding_model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return [vector.tolist() for vector in self._model.embed(texts)]


def get_embedding_adapter() -> EmbeddingAdapter:
    return FastEmbedAdapter()


def warm_embedding_model() -> None:
    """Load the embedding model once at startup instead of on first request."""
    _get_model(settings.embedding_model_name)
