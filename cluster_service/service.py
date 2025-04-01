import pandas as pd
import numpy as np
from typing import List, Dict, Any
from clustering import ClusterModel
from common.database import MongoDBClient

class CompanyClassifier:
    def __init__(self, df: pd.DataFrame):
        """Инициализация классификатора с полным набором данных"""
        self.df = df
        self.thresholds = self.calculate_thresholds()

    def calculate_thresholds(self) -> Dict[str, float]:
        """Вычисление медианных значений для разделения компаний на категории"""
        return {
            'market_cap': self.df['MarketCapitalization'].median(),
            'beta': self.df['Beta'].median(),
            'dividend_yield': self.df['DividendYield'].median(),
            'pe_ratio': self.df['PERatio'].median(),
            'pb_ratio': self.df['PriceToBookRatio'].median(),
            'return_on_assets': self.df['ReturnOnAssetsTTM'].median(),
            'revenue_growth': (self.df['RevenueTTM'] / self.df['RevenueTTM'].shift(1)).median()
        }

    def classify_company(self, company: dict) -> str:
        """Определяет категорию компании по её финансовым показателям"""
        market_cap = company.get('MarketCapitalization', 0)
        beta = company.get('Beta', 1)
        dividend_yield = company.get('DividendYield', 0)
        pe_ratio = company.get('PERatio', 0)
        pb_ratio = company.get('PriceToBookRatio', 0)
        return_on_assets = company.get('ReturnOnAssetsTTM', 0)
        
        # 1. Голубые фишки – высокая капитализация, низкая волатильность
        if market_cap > self.thresholds['market_cap'] and beta < self.thresholds['beta']:
            return "Blue Chip"
        # 2. Волатильные – высокая бета (рынок реагирует резкими скачками)
        if beta > self.thresholds['beta'] * 1.5:
            return "High Volatility"
        # 3. Дивидендные – высокая доходность по дивидендам
        if dividend_yield > self.thresholds['dividend_yield']:
            return "Dividend Stock"
        # 4. Растущие – высокая цена к прибыли и рост выручки
        if pe_ratio > self.thresholds['pe_ratio'] and pb_ratio > self.thresholds['pb_ratio']:
            return "Growth Stock"
        # 5. Недооцененные – низкие P/E, P/B, но высокая доходность активов
        if pe_ratio < self.thresholds['pe_ratio'] * 0.7 and return_on_assets > self.thresholds['return_on_assets']:
            return "Undervalued"
        
        return "Other"


class ClusterService:
    def __init__(self, db_client: MongoDBClient, features: List[str]):
        self.db = db_client
        self.features = features

    def _extract_numeric_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Извлекает и преобразует числовые признаки из словаря data."""
        result = {}
        for feature in self.features:
            value = data.get(feature)
            try:
                result[feature] = float(value) if value is not None else 0.0
            except (ValueError, TypeError):
                result[feature] = 0.0
        return result

    def prepare_data(self) -> pd.DataFrame:
        """Подготовка данных для кластеризации по всем компаниям"""
        companies = self.db.get_all_companies()
        rows = []
        for company in companies:
            data = company.get('data', {})
            features_numeric = self._extract_numeric_features(data)
            if any(features_numeric.values()):
                features_numeric['ticker'] = company.get('ticker')
                rows.append(features_numeric)
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.fillna(0)
        return df

    def update_all_clusters(self):
        """Обновление категорий для всех компаний"""
        try:
            df = self.prepare_data()
            if df.empty:
                raise ValueError("Нет данных для классификации")
            classifier = CompanyClassifier(df)
            for _, row in df.iterrows():
                category = classifier.classify_company(row.to_dict())
                self.db.update_cluster(row['ticker'], {"category": category})
            print(f"Успешно обработано {len(df)} компаний")
        except Exception as e:
            print(f"Ошибка классификации: {str(e)}")
            raise

    def assign_cluster_for_company(self, company: Dict[str, Any], model_path: str = "cluster_model.pkl") -> str:
        """
        Обрабатывает новую компанию и присваивает текстовую категорию.
        """
        try:
            data = company.get('data', {})
            features_numeric = self._extract_numeric_features(data)
            df_new = pd.DataFrame([features_numeric]).fillna(0)
            numeric_cols = df_new.select_dtypes(include=[np.number]).columns
            if numeric_cols.empty:
                raise ValueError("Нет числовых признаков для новой компании")

            # Загрузить модель кластеризации (если это необходимо)
            model = ClusterModel.load(model_path)
            cluster = int(model.predict(df_new[numeric_cols].values)[0])
            
            # Классификация на основе выбранных признаков
            classifier = CompanyClassifier(pd.DataFrame([features_numeric]))  # Используем classifier для новой компании
            category = classifier.classify_company(features_numeric)  # Получаем категорию компании

            ticker = company.get('ticker')
            if ticker is None:
                raise KeyError("Отсутствует ключ 'ticker' в данных компании")

            # Сохраняем категорию в базе данных
            self.db.update_cluster(ticker, {"category": category})
            return category
        except Exception as e:
            print(f"Ошибка обработки новой компании: {str(e)}")
            raise
