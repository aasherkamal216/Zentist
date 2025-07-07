import redis.asyncio as redis
from core.config import get_settings

settings = get_settings()

# create an async Redis client pool
redis_pool = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

async def get_redis_client():
    """
    FastAPI dependency to get a Redis client from the connection pool.
    """
    return redis_pool