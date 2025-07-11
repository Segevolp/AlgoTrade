# prophet_model_service.py
import os
import yfinance as yf
import pandas as pd
from prophet import Prophet
import joblib
import json

MODELS_DIR = "models/prophet_models"
os.makedirs(MODELS_DIR, exist_ok=True)


def train_model(ticker='^GSPC', start='2020-01-01', end='2024-12-31', interval_width=0.95):
    """Train Prophet model"""
    stock_dir = os.path.join(MODELS_DIR, ticker.replace("^", "").replace("/", "_"))
    os.makedirs(stock_dir, exist_ok=True)

    # Download data
    data = yf.download(ticker, start=start, end=end)

    # Get close price - handle different data formats
    if 'Close' in data.columns:
        close_price = data['Close']
    else:
        # Handle MultiIndex or other formats
        close_price = data.iloc[:, -1]  # Last column is usually close price

    # Make sure it's a Series
    if hasattr(close_price, 'iloc'):
        close_price = close_price.squeeze()  # Convert to Series if DataFrame

    # Prepare for Prophet
    df = pd.DataFrame({
        'ds': close_price.index,
        'y': close_price.values
    }).dropna().reset_index(drop=True)

    # Remove timezone
    if df['ds'].dt.tz is not None:
        df['ds'] = df['ds'].dt.tz_localize(None)

    # Train model
    model = Prophet(interval_width=interval_width)
    model.fit(df)

    # Save
    joblib.dump(model, os.path.join(stock_dir, "model.pkl"))
    df.to_csv(os.path.join(stock_dir, "data.csv"), index=False)

    return True


def predict_next_days(ticker='^GSPC', days=20):
    """Predict next days"""
    stock_dir = os.path.join(MODELS_DIR, ticker.replace("^", "").replace("/", "_"))

    # Load model
    model = joblib.load(os.path.join(stock_dir, "model.pkl"))

    # Create future dates
    future = model.make_future_dataframe(periods=days)

    # Predict
    forecast = model.predict(future)

    # Get last 'days' predictions
    future_forecast = forecast.tail(days)

    return {
        "dates": future_forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
        "forecast": future_forecast['yhat'].tolist(),
        "forecast_upper": future_forecast['yhat_upper'].tolist(),
        "forecast_lower": future_forecast['yhat_lower'].tolist()
    }


def load_state(ticker):
    """Load model and data"""
    stock_dir = os.path.join(MODELS_DIR, ticker.replace("^", "").replace("/", "_"))
    model = joblib.load(os.path.join(stock_dir, "model.pkl"))
    df = pd.read_csv(os.path.join(stock_dir, "data.csv"), parse_dates=['ds'])
    return model, df


def list_trained_models():
    """List trained models"""
    return [name for name in os.listdir(MODELS_DIR)
            if os.path.isdir(os.path.join(MODELS_DIR, name))]