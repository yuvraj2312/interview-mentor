from arq.connections import RedisSettings

from app.background.tasks import generate_roadmap, process_resume_upload
from app.core.config import settings


class WorkerSettings:
    functions = [process_resume_upload, generate_roadmap]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
