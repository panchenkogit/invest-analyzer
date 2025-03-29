from pymongo import MongoClient
from pymongo.collection import Collection
from datetime import datetime, timedelta

def init_mongo_collection(mongo_url: str):
    client = MongoClient(mongo_url)
    db = client["invest_analyzer"]
    collection = db["companies"]
    collection.create_index("expires_at", expireAfterSeconds=0)
    return collection

async def save_to_mongo(collection: Collection, ticker: str, data: dict):
    if collection is not None:
        doc = {
            "ticker": ticker,
            "data": data,
            "last_updated": data.get("LatestQuarter"),
            "expires_at": datetime.now() + timedelta(days=90)
        }
        collection.update_one(
            {"ticker": ticker},
            {"$set": doc},
            upsert=True
        )