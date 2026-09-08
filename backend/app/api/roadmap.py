from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.deps import get_current_user
from app.db import get_db
from app.models import Roadmap, User
from app.repositories import roadmap_repository
from app.schemas.roadmap import RoadmapItemOut, RoadmapItemResourceOut, RoadmapOut

router = APIRouter()


def _to_out(roadmap: Roadmap) -> RoadmapOut:
    return RoadmapOut(
        status=roadmap.status,
        summary=roadmap.summary,
        strengths=roadmap.strengths,
        growth_areas=roadmap.growth_areas,
        items=[
            RoadmapItemOut(
                topic=item.topic,
                gap_description=item.gap_description,
                priority=item.priority,
                recommended_action=item.recommended_action,
                resources=[RoadmapItemResourceOut(**resource) for resource in item.matched_resources],
            )
            for item in roadmap.items
        ],
        error_message=roadmap.error_message,
        created_at=roadmap.created_at,
        completed_at=roadmap.completed_at,
    )


@router.get("", response_model=RoadmapOut)
def get_roadmap(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoadmapOut:
    roadmap = roadmap_repository.get_latest_for_user(db, current_user.id)
    if roadmap is None:
        raise HTTPException(status_code=404, detail="No roadmap yet - complete an interview session first")
    return _to_out(roadmap)
