from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Dict, Any

class MongoDBClient:
    def __init__(self, mongo_url: str):
        self.client = MongoClient(mongo_url)
        self.db = self.client["invest_analyzer"]
        self.collection = self.db["companies"]
        # Создаём индекс для поля expires_at
        self.collection.create_index("expires_at", expireAfterSeconds=0)

    def update_cluster(self, ticker: str, cluster_data: Dict[str, Any]):
        """Обновляет кластер компании"""
        try:
            result = self.collection.update_one(
                {"ticker": ticker},
                {"$set": {"cluster": cluster_data}}
            )
            if result.modified_count > 0:
                print(f"Кластер для компании {ticker} успешно обновлён.")
            else:
                print(f"Кластер для компании {ticker} не был обновлён, возможно, изменений не было.")
        except Exception as e:
            print(f"Ошибка при обновлении кластера для компании {ticker}: {str(e)}")

    def get_all_companies(self):
        """Возвращает список всех компаний"""
        try:
            return list(self.collection.find({}, {"_id": 0}))
        except Exception as e:
            print(f"Ошибка при получении всех компаний: {str(e)}")
            return []

    def save_to_mongo(self, ticker: str, data: dict):
        """Сохраняет или обновляет компанию в MongoDB"""
        doc = {
            "ticker": ticker,
            "data": data,
            "last_updated": data.get("LatestQuarter"),
            "expires_at": datetime.now() + timedelta(days=90)
        }
        try:
            result = self.collection.update_one(
                {"ticker": ticker},
                {"$set": doc},
                upsert=True
            )
            if result.upserted_id:
                print(f"Компания {ticker} успешно добавлена в базу данных.")
            elif result.modified_count > 0:
                print(f"Компания {ticker} успешно обновлена в базе данных.")
            else:
                print(f"Компания {ticker} не была обновлена, возможно, данных не было изменено.")
        except Exception as e:
            print(f"Ошибка при сохранении данных компании {ticker}: {str(e)}")
