import asyncio
from fastapi import FastAPI, Query, HTTPException
import aiohttp
from redis.asyncio import Redis
from contextlib import asynccontextmanager
from settings import settings
from cache import cache_company_data, check_cache_company_data
from api_alpha import fetch_single_ticker
from database import save_to_mongo, init_mongo_collection

redis_client = None
mongo_collection = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, mongo_collection
    redis_client = Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
    mongo_collection = init_mongo_collection(settings.mongo_url)
    yield
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="MicroService for getting fundamental information",
    lifespan=lifespan
)

@app.get('/fetch', description="Tickers separated by commas (max 3). Example: AAPL,MSFT,GOOGL")
async def fetch(symbol: str = Query(...)):
    tickers = [t.strip().upper() for t in symbol.split(",")]
    if len(tickers) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 tickers allowed")
    
    cached_data = {}
    missing_tickers = []
    for ticker in tickers:
        cache_data = await check_cache_company_data(redis_client, ticker)
        if cache_data:
            cached_data[ticker] = cache_data
        else:
            missing_tickers.append(ticker)

    if missing_tickers:
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_single_ticker(session, ticker, settings.api_alpha) for ticker in missing_tickers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    raise result
                ticker, data = result
                await cache_company_data(redis_client, ticker, data, 86400)
                await save_to_mongo(mongo_collection, ticker, data)
                cached_data[ticker] = data
    
    return cached_data