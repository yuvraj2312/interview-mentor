import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from app.models import SkillProfile, SkillProfileTopicStat


def get_by_user_id(db: DBSession, user_id: uuid.UUID) -> SkillProfile | None:
    return db.query(SkillProfile).filter(SkillProfile.user_id == user_id).first()


def get_or_create(db: DBSession, user_id: uuid.UUID) -> SkillProfile:
    profile = get_by_user_id(db, user_id)
    if profile is None:
        profile = SkillProfile(user_id=user_id, sessions_completed=0)
        db.add(profile)
        db.flush()
    return profile


def update_aggregate(
    db: DBSession,
    profile: SkillProfile,
    *,
    sessions_completed: int,
    overall_avg_technical_score: float | None,
    overall_avg_communication_score: float | None,
    overall_avg_completeness_score: float | None,
) -> SkillProfile:
    profile.sessions_completed = sessions_completed
    profile.overall_avg_technical_score = overall_avg_technical_score
    profile.overall_avg_communication_score = overall_avg_communication_score
    profile.overall_avg_completeness_score = overall_avg_completeness_score
    profile.updated_at = datetime.now(timezone.utc)
    db.add(profile)
    db.flush()
    return profile


def replace_topic_stats(db: DBSession, profile: SkillProfile, topic_stats: list[SkillProfileTopicStat]) -> None:
    db.query(SkillProfileTopicStat).filter(SkillProfileTopicStat.skill_profile_id == profile.id).delete(
        synchronize_session=False
    )
    for stat in topic_stats:
        stat.skill_profile_id = profile.id
        db.add(stat)
    db.flush()
