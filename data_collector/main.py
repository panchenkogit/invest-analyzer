import asyncio
import aiohttp
from fastapi import FastAPI, Query, HTTPException
from redis.asyncio import Redis
from contextlib import asynccontextmanager
from common.settings import settings
from cache import cache_company_data, check_cache_company_data
from api_alpha import fetch_single_ticker
from common.database import MongoDBClient

redis_client = None
mongo_collection = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, mongo_collection
    redis_client = Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
    mongo_collection = MongoDBClient(settings.mongo_url)
    yield
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="MicroService for getting fundamental information",
    lifespan=lifespan
)


SECOND_MICROSERVICE_URL = "http://claster_servis:8001/update-company"  # URL второго микросервиса

async def send_to_clustering_service(company_data: dict):
    """Отправляет данные компании во второй микросервис"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(SECOND_MICROSERVICE_URL, json=company_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    print(f"Ошибка при отправке в кластеризацию: {error_text}")
                    return {"error": error_text}
        except Exception as e:
            print(f"Ошибка сети при отправке в кластеризацию: {str(e)}")
            return {"error": str(e)}

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
<<<<<<< HEAD
            for result in results:
                if isinstance(result, Exception):
                    cached_data[ticker] = {"error": str(result)}
                else:
                    ticker, data = result
=======
            
            for i, result in enumerate(results):
                ticker = missing_tickers[i]
                if isinstance(result, Exception):
                    cached_data[ticker] = {"error": str(result)}
                    continue
                
                ticker, data = result
                
                # Сначала сохраняем в кэш и базу
>>>>>>> claster
                await cache_company_data(redis_client, ticker, data, 86400)
                mongo_collection.save_to_mongo(ticker, data)
                
                # Затем отправляем в кластеризацию
                company_data = {"ticker": ticker, "data": data}
                clustering_response = await send_to_clustering_service(company_data)
                
                cached_data[ticker] = {"data": data, "clustering_response": clustering_response}
    
    return cached_data
