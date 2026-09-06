from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.deps import get_current_user
from app.db import get_db
from app.models import SkillProfile, User
from app.repositories import skill_profile_repository
from app.schemas.skill_profile import SkillProfileOut, SkillProfileTopicStatOut

router = APIRouter()


def _to_out(profile: SkillProfile) -> SkillProfileOut:
    return SkillProfileOut(
        sessions_completed=profile.sessions_completed,
        overall_avg_technical_score=profile.overall_avg_technical_score,
        overall_avg_communication_score=profile.overall_avg_communication_score,
        overall_avg_completeness_score=profile.overall_avg_completeness_score,
        updated_at=profile.updated_at,
        topics=[
            SkillProfileTopicStatOut(
                topic=stat.topic_label,
                sessions_count=stat.sessions_count,
                avg_technical_score=stat.avg_technical_score,
                avg_communication_score=stat.avg_communication_score,
                avg_completeness_score=stat.avg_completeness_score,
                trend=stat.trend,
            )
            for stat in profile.topic_stats
        ],
    )


@router.get("", response_model=SkillProfileOut)
def get_skill_profile(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillProfileOut:
    profile = skill_profile_repository.get_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="No skill profile yet - complete an interview session first")
    return _to_out(profile)
