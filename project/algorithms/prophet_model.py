import os
import pandas as pd
import yfinance as yf
from prophet import Prophet
import pickle

from .base_model import BaseTimeSeriesModel

class ProphetModel(BaseTimeSeriesModel):
    def __init__(self):
        super().__init__("prophet")
        self.model = None
        self.last_date = None
        
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for Prophet model"""
        # Prophet requires columns named 'ds' (date) and 'y' (target)
        prophet_df = pd.DataFrame()
        prophet_df['ds'] = df.index
        prophet_df['y'] = df['Close']
        return prophet_df
        
    def train(self, ticker: str, start: str, end: str, **kwargs):
        """Train Prophet model"""
        # Download data
        df = yf.download(ticker, start=start, end=end)
        df = self.prepare_data(df)
        self.last_date = df['ds'].max()
        
        # Initialize and train model
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=True,
            changepoint_prior_scale=0.05,
            **kwargs
        )
        
        self.model.fit(df)
        
        # Calculate metrics
        forecast = self.model.predict(df)
        mse = ((forecast['yhat'] - df['y']) ** 2).mean()
        
        # Save metadata
        metadata = {
            'ticker': ticker,
            'start': start,
            'end': end,
            'last_date': self.last_date.strftime('%Y-%m-%d'),
            'mse': float(mse),
            'parameters': kwargs
        }
        
        # Save model
        self.save_model(ticker)
        self.save_metadata(ticker, metadata)
        return True
        
    def predict(self, ticker: str, days: int = 20):
        """Generate predictions using saved model"""
        self.load_model(ticker)
        if self.model is None:
            raise RuntimeError(f"No trained model found for {ticker}")
            
        # Create future dates dataframe
        future = self.model.make_future_dataframe(
            periods=days,
            freq='B',  # Business days
            include_history=False
        )
        
        # Generate forecast
        forecast = self.model.predict(future)
        
        return {
            'dates': forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'forecast': forecast['yhat'].tolist(),
            'forecast_lower': forecast['yhat_lower'].tolist(),
            'forecast_upper': forecast['yhat_upper'].tolist()
        }
        
    def save_model(self, ticker: str):
        """Save model artifacts"""
        if self.model is None:
            raise RuntimeError("No model to save")
            
        path = self.get_model_path(ticker)
        
        # Save Prophet model
        with open(os.path.join(path, "model.pkl"), "wb") as f:
            pickle.dump(self.model, f)
            
    def load_model(self, ticker: str):
        """Load model artifacts"""
        path = self.get_model_path(ticker)
        
        try:
            # Load Prophet model
            with open(os.path.join(path, "model.pkl"), "rb") as f:
                self.model = pickle.load(f)
                
            # Load metadata to get last training date
            metadata = self.load_metadata(ticker)
            self.last_date = pd.Timestamp(metadata.get('last_date'))
            
        except FileNotFoundError:
            raise RuntimeError(f"No saved model found for {ticker}") 