import json
from typing import Optional
import redis.asyncio as aioredis
from app.core.config import get_settings

settings = get_settings()
_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def cache_get(key: str) -> Optional[dict]:
    r = await get_redis()
    val = await r.get(key)
    return json.loads(val) if val else None


async def cache_set(key: str, data: dict, ttl: Optional[int] = None) -> None:
    r = await get_redis()
    ttl = ttl or settings.cache_ttl_seconds
    await r.setex(key, ttl, json.dumps(data))



async def cache_delete(key: str) -> None:
    r = await get_redis()
    await r.delete(key)


async def cache_keys(pattern: str) -> list[str]:
    r = await get_redis()
    return await r.keys(pattern)
