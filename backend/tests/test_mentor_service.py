"""Mentor agent / roadmap generation tests (Phase 6c).

Sessions are seeded directly at the data layer (reusing
test_skill_profile_service.py's _seed_completed_session and
test_interview_sessions.py's _ready_plan), not driven through a full
multi-turn interview + real Anthropic call - same direct-data-layer
pattern as 4b/6b. Only the Mentor LLM call is mocked (patched at its
mentor_service import site, matching how test_interview_sessions.py
patches app.workflows.interview_graph.generate_question rather than the
agent module itself); embedding + vector search run for real against a
throwaway Qdrant collection, mirroring test_vector_store_service.py.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from app.core.config import settings
from app.core.security import decode_access_token
from app.embedding_adapter import get_embedding_adapter
from app.models import Roadmap
from app.repositories import roadmap_repository
from app.services import mentor_service, skill_profile_service, vector_store_service
from tests.conftest import TestSessionLocal, signup_and_get_tokens
from tests.test_interview_sessions import _ready_plan
from tests.test_skill_profile_service import _seed_completed_session

_TEST_COLLECTION = "test_mentor_service_learning_resources"
_BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)

CANNED_RESULT = {
    "summary": "Solid on system design, weaker on Python generator internals this session.",
    "strengths": ["Clearly explained horizontal scaling tradeoffs in the System Design turn."],
    "growth_areas": ["Could not explain how Python generators maintain state between yields."],
    "roadmap_items": [
        {
            "topic": "Python generators",
            "gap_description": "The candidate could not explain how Python generators maintain state between yields.",
            "priority": "high",
            "recommended_action": "Review the generator/iterator protocol fundamentals.",
        }
    ],
}


def _setup_user_and_plan(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    user_id = uuid.UUID(decode_access_token(access_token)["sub"])
    plan = _ready_plan(client, access_token)
    return user_id, plan["id"]


def _recompute_skill_profile(user_id):
    db = TestSessionLocal()
    try:
        skill_profile_service.recompute_for_user(db, user_id)
        db.commit()
    finally:
        db.close()


def _generate(session_id):
    db = TestSessionLocal()
    try:
        mentor_service.generate_roadmap_for_session(db, session_id)
    finally:
        db.close()


@patch.object(settings, "qdrant_learning_resources_collection", _TEST_COLLECTION)
class TestGenerateRoadmapForSession:
    @staticmethod
    def _seed_test_resource():
        adapter = get_embedding_adapter()
        client = vector_store_service.get_client()
        if client.collection_exists(_TEST_COLLECTION):
            client.delete_collection(_TEST_COLLECTION)
        vector_store_service.ensure_collection(_TEST_COLLECTION, vector_size=settings.embedding_dimension)

        vector = adapter.embed(["Python list comprehensions and generators"])[0]
        vector_store_service.upsert_points(
            _TEST_COLLECTION,
            [
                {
                    "id": str(uuid.uuid4()),
                    "vector": vector,
                    "payload": {
                        "resource_id": "test-python-generators",
                        "title": "Python generators deep dive",
                        "url": "https://example.com/python-generators",
                        "resource_type": "article",
                    },
                }
            ],
        )

    def test_generate_roadmap_persists_ready_roadmap_with_matched_resources(self, client):
        self._seed_test_resource()
        user_id, plan_id = _setup_user_and_plan(client)
        session_id = _seed_completed_session(
            user_id,
            plan_id,
            [("System Design", 8.0, 8.0, 8.0), ("Python Fundamentals", 3.0, 5.0, 4.0)],
            completed_at=_BASE_TIME,
        )
        _recompute_skill_profile(user_id)

        with patch("app.services.mentor_service.generate_roadmap", return_value=CANNED_RESULT):
            _generate(session_id)

        db = TestSessionLocal()
        try:
            roadmap = roadmap_repository.get_latest_for_user(db, user_id)
            assert roadmap is not None
            assert roadmap.session_id == session_id
            assert roadmap.status == "ready"
            assert roadmap.summary == CANNED_RESULT["summary"]
            assert roadmap.strengths == CANNED_RESULT["strengths"]
            assert roadmap.growth_areas == CANNED_RESULT["growth_areas"]

            items = roadmap.items
            assert len(items) == 1
            assert items[0].topic == "Python generators"
            assert items[0].priority == "high"
            assert len(items[0].matched_resources) == 1
            assert items[0].matched_resources[0]["resource_id"] == "test-python-generators"
        finally:
            db.close()

    def test_second_session_creates_a_second_roadmap(self, client):
        self._seed_test_resource()
        user_id, plan_id = _setup_user_and_plan(client)
        session_1 = _seed_completed_session(
            user_id, plan_id, [("Python Fundamentals", 5.0, 5.0, 5.0)], completed_at=_BASE_TIME
        )
        _recompute_skill_profile(user_id)
        with patch("app.services.mentor_service.generate_roadmap", return_value=CANNED_RESULT):
            _generate(session_1)

        session_2 = _seed_completed_session(
            user_id, plan_id, [("Python Fundamentals", 8.0, 8.0, 8.0)], completed_at=_BASE_TIME
        )
        _recompute_skill_profile(user_id)
        with patch("app.services.mentor_service.generate_roadmap", return_value=CANNED_RESULT):
            _generate(session_2)

        db = TestSessionLocal()
        try:
            roadmaps = db.query(Roadmap).filter(Roadmap.user_id == user_id).all()
            assert len(roadmaps) == 2
            assert {r.session_id for r in roadmaps} == {session_1, session_2}

            latest = roadmap_repository.get_latest_for_user(db, user_id)
            assert latest.session_id == session_2
        finally:
            db.close()

    def test_llm_failure_marks_roadmap_failed(self, client):
        self._seed_test_resource()
        user_id, plan_id = _setup_user_and_plan(client)
        session_id = _seed_completed_session(
            user_id, plan_id, [("Python Fundamentals", 5.0, 5.0, 5.0)], completed_at=_BASE_TIME
        )
        _recompute_skill_profile(user_id)

        with patch("app.services.mentor_service.generate_roadmap", side_effect=ValueError("malformed LLM output")):
            _generate(session_id)

        db = TestSessionLocal()
        try:
            roadmap = roadmap_repository.get_latest_for_user(db, user_id)
            assert roadmap is not None
            assert roadmap.status == "failed"
            assert "malformed LLM output" in roadmap.error_message
        finally:
            db.close()
