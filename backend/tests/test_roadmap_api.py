import uuid
from datetime import datetime, timezone

from app.core.security import decode_access_token
from app.models import Roadmap, RoadmapItem
from tests.conftest import TestSessionLocal, signup_and_get_tokens
from tests.test_interview_sessions import _ready_plan
from tests.test_skill_profile_service import _seed_completed_session

_BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _seed_ready_roadmap(user_id, session_id):
    db = TestSessionLocal()
    try:
        roadmap = Roadmap(
            user_id=user_id,
            session_id=session_id,
            status="ready",
            summary="Solid session overall.",
            strengths=["Clear explanation of caching tradeoffs."],
            growth_areas=["Weak on distributed consensus."],
            completed_at=_BASE_TIME,
        )
        db.add(roadmap)
        db.flush()
        db.add(
            RoadmapItem(
                roadmap_id=roadmap.id,
                topic="Distributed Systems",
                gap_description="Could not explain quorum-based consensus.",
                priority="high",
                recommended_action="Study Raft consensus.",
                matched_resources=[
                    {
                        "resource_id": "distributed-systems-mit-6-824",
                        "title": "MIT 6.824",
                        "url": "https://pdos.csail.mit.edu/6.824/",
                        "resource_type": "course",
                        "score": 0.71,
                    }
                ],
            )
        )
        db.commit()
        return roadmap.id
    finally:
        db.close()


def test_get_roadmap_requires_auth(client):
    response = client.get("/roadmap")
    assert response.status_code == 401


def test_get_roadmap_returns_404_when_none_exists(client):
    tokens = signup_and_get_tokens(client)
    response = client.get("/roadmap", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 404


def test_get_roadmap_returns_latest_ready_roadmap(client):
    tokens = signup_and_get_tokens(client)
    access_token = tokens["access_token"]
    user_id = uuid.UUID(decode_access_token(access_token)["sub"])
    plan = _ready_plan(client, access_token)
    session_id = _seed_completed_session(
        user_id, plan["id"], [("Distributed Systems", 4.0, 6.0, 5.0)], completed_at=_BASE_TIME
    )
    _seed_ready_roadmap(user_id, session_id)

    response = client.get("/roadmap", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ready"
    assert body["summary"] == "Solid session overall."
    assert body["strengths"] == ["Clear explanation of caching tradeoffs."]
    assert len(body["items"]) == 1
    assert body["items"][0]["topic"] == "Distributed Systems"
    assert body["items"][0]["priority"] == "high"
    assert body["items"][0]["resources"][0]["resource_id"] == "distributed-systems-mit-6-824"


def test_user_cannot_see_another_users_roadmap(client):
    tokens_a = signup_and_get_tokens(client)
    user_id_a = uuid.UUID(decode_access_token(tokens_a["access_token"])["sub"])
    plan_a = _ready_plan(client, tokens_a["access_token"])
    session_a = _seed_completed_session(
        user_id_a, plan_a["id"], [("Caching", 7.0, 7.0, 7.0)], completed_at=_BASE_TIME
    )
    _seed_ready_roadmap(user_id_a, session_a)

    tokens_b = signup_and_get_tokens(client)
    response = client.get("/roadmap", headers={"Authorization": f"Bearer {tokens_b['access_token']}"})
    assert response.status_code == 404
