"""Shared slowapi Limiter for auth-endpoint rate limiting.

Backed by Redis (settings.redis_url) rather than in-memory storage so limits
hold correctly if the app ever runs as multiple worker processes in
production - an in-memory limiter would give each worker its own counter,
silently multiplying the effective limit.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)
