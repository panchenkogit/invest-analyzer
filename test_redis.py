from redis.asyncio import Redis
import asyncio

# 1. redis_client is created but not awaited - it's a coroutine
async def create_redis_client():
    return Redis(host="localhost", port=6380, decode_responses=True)

async def test_cache():
    try:
        # 2. Get the client instance within the async function
        redis_client = await create_redis_client()
        
        # 3. ping() is async and needs to be awaited
        print("Ping:", await redis_client.ping())
        
        # setex and get are already awaited correctly
        await redis_client.setex("test_key", 3600, "test_value")
        print("Get:", await redis_client.get("test_key"))
        
        # 4. Good practice to close the connection
        await redis_client.close()
    except Exception as e:
        print(f"Error: {e}")

# 5. Properly run the async function
if __name__ == "__main__":
    asyncio.run(test_cache())