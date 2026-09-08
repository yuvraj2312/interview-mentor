"""Populate the learning_resources Qdrant collection from the hand-written
seed list in app/data/learning_resources_seed.py.

Run manually (`python -m app.scripts.seed_learning_resources`), not at app
startup - main.py's lifespan already creates the empty collection; there's
no reason to re-embed the seed set on every restart.

Idempotent: each entry's Qdrant point id is uuid5-derived from its stable
seed slug, so re-running after editing/adding entries upserts in place
rather than duplicating. Qdrant requires point ids to be a UUID or an
unsigned int - the human-readable slug itself is kept in the payload as
"resource_id" for display/reference (see mentor_service.py).
"""

import uuid

from app.core.config import settings
from app.data.learning_resources_seed import LEARNING_RESOURCES
from app.embedding_adapter import get_embedding_adapter
from app.services import vector_store_service

_NAMESPACE = uuid.UUID("d6f2b6d0-6f1a-4b7a-9c9f-2f6c9b8a2b31")


def _point_id(slug: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, slug))


def seed() -> None:
    vector_store_service.ensure_collection(
        settings.qdrant_learning_resources_collection, vector_size=settings.embedding_dimension
    )

    embedding_adapter = get_embedding_adapter()
    vectors = embedding_adapter.embed([entry["description"] for entry in LEARNING_RESOURCES])

    points = [
        {
            "id": _point_id(entry["id"]),
            "vector": vector,
            "payload": {
                "resource_id": entry["id"],
                "topic_key": entry["topic_key"],
                "title": entry["title"],
                "url": entry["url"],
                "resource_type": entry["resource_type"],
                "description": entry["description"],
            },
        }
        for entry, vector in zip(LEARNING_RESOURCES, vectors)
    ]
    vector_store_service.upsert_points(settings.qdrant_learning_resources_collection, points)
    print(f"Seeded {len(points)} learning_resources entries.")


if __name__ == "__main__":
    seed()
