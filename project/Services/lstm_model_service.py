# model_service.py
import os
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense
import joblib

MODELS_DIR = "models"
MODEL_PATH = os.path.join(MODELS_DIR, "model.h5")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")
DATA_PATH = os.path.join(MODELS_DIR, "data.csv")
FORECAST_PATH = os.path.join(MODELS_DIR, "forecast.json")

os.makedirs(MODELS_DIR, exist_ok=True)

def train_model(ticker='^GSPC', start='2010-01-01', end='2025-05-22', sequence_length=60):
    df = yf.download(ticker, start=start, end=end)[['Close']].dropna()
    df['change'] = df['Close'].pct_change()

    for window in [5, 10, 20, 30, 60]:
        df['ma_change'] = df['change'].rolling(window).mean()
        df['std_change'] = df['change'].rolling(window).std()
        df['zscore_change'] = (df['change'] - df['ma_change']) / df['std_change']
        df[f'ma_{window}'] = df['Close'].rolling(window).mean()
        df[f'std_{window}'] = df['Close'].rolling(window).std()
        df[f'Sharp_{window}'] = df[f'ma_{window}'] / df[f'std_{window}']

    df = df.ffill().bfill().dropna()
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df)

    # Save data
    pd.DataFrame(scaled, index=df.index).to_csv(DATA_PATH)
    joblib.dump(scaler, SCALER_PATH)

    # Build sequences
    X, y = [], []
    for i in range(sequence_length, len(scaled)):
        X.append(scaled[i-sequence_length:i])
        y.append(scaled[i, 0])

    X, y = np.array(X), np.array(y)
    split = int(0.9 * len(X))
    X_train, y_train = X[:split], y[:split]

    model = Sequential([
        LSTM(98, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
        LSTM(48, return_sequences=True),
        LSTM(22),
        Dense(1)
    ])

    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, y_train, epochs=20, batch_size=32, verbose=1)

    model.save(MODEL_PATH)
    return True

def load_state():
    model = load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    df = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
    return model, scaler, df

def predict_next_days(days=20, sequence_length=60):
    model, scaler, df = load_state()
    scaled = scaler.transform(df)

    forecast_input = scaled[-sequence_length:].copy()
    forecast = []

    for _ in range(days):
        input_reshaped = forecast_input.reshape(1, sequence_length, scaled.shape[1])
        pred = model.predict(input_reshaped, verbose=0)[0][0]
        forecast.append(pred)
        new_row = np.concatenate([[pred], forecast_input[-1, 1:]])
        forecast_input = np.vstack([forecast_input[1:], new_row])

    forecast_prices = scaler.inverse_transform(
        np.concatenate([np.array(forecast).reshape(-1, 1), np.zeros((days, scaled.shape[1] - 1))], axis=1)
    )[:, 0]

    last_date = df.index[-1]
    forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days, freq='B')

    # Optional: save forecast to disk to reuse
    pd.DataFrame({"date": forecast_dates, "price": forecast_prices}).to_json(FORECAST_PATH, orient="records", date_format="iso")

    return {
        "dates": forecast_dates.strftime('%Y-%m-%d').tolist(),
        "forecast": forecast_prices.tolist()
    }

def get_cached_forecast():
    if os.path.exists(FORECAST_PATH):
        return pd.read_json(FORECAST_PATH).to_dict(orient="list")
    return None
