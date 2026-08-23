import redis

from app.core.config import settings

_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    # Lazy singleton, same spirit as deps.get_arq_pool(). Unlike the arq
    # pool, a sync redis.Redis client isn't bound to an asyncio event loop,
    # so tests don't need to reset this between runs.
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client
