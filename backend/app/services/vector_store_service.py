"""Generic Qdrant-backed vector store.

Thin wrapper so callers never talk to qdrant-client directly - same
provider-isolation rationale as llm_adapter.py/embedding_adapter.py.
Currently used to stand up the (empty) learning-resources collection that
Phase 6c's roadmap-matching will populate and query; skill-gap matching
does not use this (see skill_gap_service.py - it compares two small lists
in-process instead of round-tripping through a persistent collection).
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import settings

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.qdrant_url)
    return _client


def ensure_collection(collection_name: str, vector_size: int) -> None:
    client = get_client()
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )


def upsert_points(collection_name: str, points: list[dict]) -> None:
    client = get_client()
    client.upsert(
        collection_name=collection_name,
        points=[
            qmodels.PointStruct(id=p["id"], vector=p["vector"], payload=p.get("payload", {})) for p in points
        ],
    )


def search(
    collection_name: str, query_vector: list[float], limit: int = 5, score_threshold: float | None = None
) -> list[dict]:
    client = get_client()
    response = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=limit,
        score_threshold=score_threshold,
    )
    return [{"id": point.id, "score": point.score, "payload": point.payload} for point in response.points]
