import os
import json
from datetime import datetime
from abc import ABC, abstractmethod

class BaseTimeSeriesModel(ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "saved_models")
        os.makedirs(self.base_path, exist_ok=True)
        
    def get_model_path(self, ticker: str) -> str:
        """Get the path for saving model artifacts for a specific ticker"""
        ticker_path = os.path.join(self.base_path, self.model_name, ticker.replace("^", "").replace("/", "_"))
        os.makedirs(ticker_path, exist_ok=True)
        return ticker_path
        
    def save_metadata(self, ticker: str, metadata: dict):
        """Save model metadata including training parameters and performance metrics"""
        path = self.get_model_path(ticker)
        metadata["last_updated"] = datetime.now().isoformat()
        with open(os.path.join(path, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
            
    def load_metadata(self, ticker: str) -> dict:
        """Load model metadata"""
        path = self.get_model_path(ticker)
        try:
            with open(os.path.join(path, "metadata.json"), "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    @abstractmethod
    def train(self, ticker: str, start: str, end: str, **kwargs):
        """Train the model for a specific ticker"""
        pass
        
    @abstractmethod
    def predict(self, ticker: str, days: int, **kwargs):
        """Generate predictions for a specific ticker"""
        pass
        
    @abstractmethod
    def save_model(self, ticker: str):
        """Save model artifacts"""
        pass
        
    @abstractmethod
    def load_model(self, ticker: str):
        """Load model artifacts"""
        pass 