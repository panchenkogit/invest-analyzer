import json
from redis.asyncio import Redis

async def cache_company_data(redis_client: Redis, ticker: str, data: dict, ttl: int):
    if redis_client:
        await redis_client.setex(f"ticker:{ticker}", ttl, json.dumps(data))

async def check_cache_company_data(redis_client: Redis, ticker: str):
    if redis_client:
        cache_data = await redis_client.get(f"ticker:{ticker}")
        if cache_data:
            return json.loads(cache_data)
    return None