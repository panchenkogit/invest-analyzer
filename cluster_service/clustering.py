from sklearn.pipeline import Pipeline
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import numpy as np

class ClusterModel:
    def __init__(self, n_clusters: int = 5):
        self.pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('kmeans', KMeans(n_clusters=n_clusters, random_state=42))
        ])
    
    def fit(self, X: np.ndarray):
        """Обучение модели на данных"""
        self.pipeline.fit(X)
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Предсказание кластеров"""
        return self.pipeline.predict(X)
    
    def save(self, path: str):
        """Сохранение модели на диск"""
        joblib.dump(self.pipeline, path)
    
    @classmethod
    def load(cls, path: str):
        """Загрузка модели с диска"""
        model = cls()
        model.pipeline = joblib.load(path)
        return model
