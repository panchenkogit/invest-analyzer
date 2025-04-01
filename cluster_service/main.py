from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from common.settings import settings
from common.database import MongoDBClient
from service import ClusterService

app = FastAPI(title="Clustering Microservice")

# Инициализация клиента БД и сервиса кластеризации
db_client = MongoDBClient(settings.mongo_url)
FEATURES = [
    'MarketCapitalization', 'RevenueTTM', 'EBITDA', 'Beta',
    'DividendYield', 'ReturnOnAssetsTTM', 'ReturnOnEquityTTM',
    'PERatio', 'PEGRatio', 'PriceToSalesRatioTTM',
    'PriceToBookRatio', 'EVToRevenue', 'EVToEBITDA'
]
cluster_service = ClusterService(db_client, FEATURES)

class Company(BaseModel):
    ticker: str
    data: Dict[str, Any]

@app.post("/update-company", description="Сохраняет компанию и обновляет ей кластер")
async def update_company(company: Company):
    try:
        doc = {
            "ticker": company.ticker,
            "data": company.data
        }
        db_client.collection.update_one(
            {"ticker": company.ticker},
            {"$set": doc},
            upsert=True
        )
        # Обновляем кластер для компании
        cluster = cluster_service.assign_cluster_for_company(company.dict())
        return {"ticker": company.ticker, "cluster": cluster}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
