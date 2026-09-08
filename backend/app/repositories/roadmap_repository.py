import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from app.models import Roadmap, RoadmapItem


def create(db: DBSession, *, user_id: uuid.UUID, session_id: uuid.UUID) -> Roadmap:
    roadmap = Roadmap(user_id=user_id, session_id=session_id, status="generating")
    db.add(roadmap)
    db.flush()
    return roadmap


def get_by_id(db: DBSession, roadmap_id: uuid.UUID) -> Roadmap | None:
    return db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()


def get_latest_for_user(db: DBSession, user_id: uuid.UUID) -> Roadmap | None:
    return db.query(Roadmap).filter(Roadmap.user_id == user_id).order_by(Roadmap.created_at.desc()).first()


def mark_ready(
    db: DBSession, roadmap: Roadmap, *, summary: str, strengths: list, growth_areas: list, items: list[RoadmapItem]
) -> Roadmap:
    roadmap.status = "ready"
    roadmap.summary = summary
    roadmap.strengths = strengths
    roadmap.growth_areas = growth_areas
    roadmap.error_message = None
    roadmap.completed_at = datetime.now(timezone.utc)
    db.add(roadmap)
    for item in items:
        item.roadmap_id = roadmap.id
        db.add(item)
    db.flush()
    return roadmap


def mark_failed(db: DBSession, roadmap: Roadmap, *, error_message: str) -> Roadmap:
    roadmap.status = "failed"
    roadmap.error_message = error_message
    db.add(roadmap)
    db.flush()
    return roadmap
