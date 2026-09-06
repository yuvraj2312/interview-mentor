import uuid

import pytest

from app.embedding_adapter import get_embedding_adapter
from app.services import vector_store_service

adapter = get_embedding_adapter()
_collection = "test_vector_store_service"


@pytest.fixture(autouse=True)
def _fresh_collection():
    client = vector_store_service.get_client()
    if client.collection_exists(_collection):
        client.delete_collection(_collection)
    yield


def test_ensure_collection_is_idempotent():
    vector_store_service.ensure_collection(_collection, vector_size=384)
    vector_store_service.ensure_collection(_collection, vector_size=384)


def test_upsert_and_search_returns_nearest_neighbor():
    vector_store_service.ensure_collection(_collection, vector_size=384)

    python_id, javascript_id, system_design_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    texts = {
        python_id: "Python list comprehensions and generators",
        javascript_id: "JavaScript closures and the event loop",
        system_design_id: "Designing a horizontally scalable system",
    }
    vectors = adapter.embed(list(texts.values()))

    vector_store_service.upsert_points(
        _collection,
        [{"id": point_id, "vector": vector, "payload": {"text": text}} for (point_id, text), vector in zip(texts.items(), vectors)],
    )

    query_vector = adapter.embed(["how do Python generators work"])[0]
    results = vector_store_service.search(_collection, query_vector, limit=1)

    assert results[0]["id"] == python_id
