from arq.connections import RedisSettings

from app.background.tasks import process_resume_upload
from app.core.config import settings


class WorkerSettings:
    functions = [process_resume_upload]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
