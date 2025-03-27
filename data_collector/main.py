import json
from fastapi import FastAPI, Query, HTTPException
import aiohttp
from pymongo import MongoClient
from datetime import datetime, timedelta
from redis.asyncio import Redis
from contextlib import asynccontextmanager

from config import API_ALPHA, MONGO_URL, REDIS_HOST, REDIS_PORT

redis_client = None
mongo_collection = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, mongo_collection

    redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    client = MongoClient(MONGO_URL)
    db = client["invest_analyzer"]
    mongo_collection = db["companies"]
    mongo_collection.create_index("expires_at", expireAfterSeconds=0)

    yield

    if redis_client:
        await redis_client.close()

app = FastAPI(title="MicroService for getting fundamental information", lifespan=lifespan)

# Сохраняет данные в кэш
async def cache_company_data(ticker: str, data: dict, ttl: int):
    if redis_client:
        await redis_client.setex(f"ticker:{ticker}", ttl, json.dumps(data))

# Проверяет наличие данных в кэше
async def check_cache_company_data(ticker: str):
    if redis_client:
        cache_data = await redis_client.get(f"ticker:{ticker}")
        if cache_data:
            return json.loads(cache_data)
    return None

@app.get('/fetch')
async def fetch(symbol: str = Query(...)):
    symbol = symbol.upper()
    cache_data = await check_cache_company_data(symbol)
    if cache_data:
        return cache_data
    
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_ALPHA}'
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        if response.status != 200:
            raise HTTPException(status_code=response.status, detail=await response.text())
        data = await response.json()
        if not data:
            raise HTTPException(status_code=404, detail="Данных нет")
        
        await cache_company_data(symbol, data, 86400)

        if mongo_collection is not None:
            doc = {
                "ticker": symbol,
                "data": data,
                "last_updated": data.get("LatestQuarter"),
                "expires_at": datetime.now() + timedelta(days=90)
            }
            mongo_collection.update_one(
                {"ticker": symbol},
                {"$set": doc},
                upsert=True
            )
        
        return data