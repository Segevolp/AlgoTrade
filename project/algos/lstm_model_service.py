# model_service.py
import os
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense
import joblib
from project.algorithms.base_model import BaseTimeSeriesModel

MODELS_DIR = "models"
MODEL_PATH = os.path.join(MODELS_DIR, "model.h5")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")
DATA_PATH = os.path.join(MODELS_DIR, "data.csv")
FORECAST_PATH = os.path.join(MODELS_DIR, "forecast.json")

os.makedirs(MODELS_DIR, exist_ok=True)

class LSTMModel(BaseTimeSeriesModel):
    def __init__(self):
        super().__init__("lstm")
        self.model = None
        self.scaler = None
        self.sequence_length = 60

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for LSTM model"""
        df = df[['Close']].copy()
        df['change'] = df['Close'].pct_change()

        for window in [5, 10, 20, 30, 60]:
            df['ma_change'] = df['change'].rolling(window).mean()
            df['std_change'] = df['change'].rolling(window).std()
            df['zscore_change'] = (df['change'] - df['ma_change']) / df['std_change']
            df[f'ma_{window}'] = df['Close'].rolling(window).mean()
            df[f'std_{window}'] = df['Close'].rolling(window).std()
            df[f'Sharp_{window}'] = df[f'ma_{window}'] / df[f'std_{window}']

        return df.ffill().bfill()

    def build_sequences(self, data: np.ndarray) -> tuple:
        """Build input sequences for LSTM"""
        X, y = [], []
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i, 0])  # predict Close price
        return np.array(X), np.array(y)

    def train(self, ticker: str, start: str, end: str, sequence_length: int = 60):
      """Train LSTM model using only Close prices"""
      self.sequence_length = sequence_length

      # Download and prepare data
      df = yf.download(ticker, start=start, end=end)[['Close']]
      df = df.dropna()

      # Scale only Close
      self.scaler = MinMaxScaler()
      scaled_data = self.scaler.fit_transform(df[['Close']])

      # Build sequences
      X, y = self.build_sequences(scaled_data)

      # Train/test split
      split = int(0.9 * len(X))
      X_train, y_train = X[:split], y[:split]

      # Build and train model
      self.model = Sequential([
          LSTM(98, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
          LSTM(48, return_sequences=True),
          LSTM(22),
          Dense(1)
      ])

      self.model.compile(optimizer='adam', loss='mean_squared_error')
      history = self.model.fit(
          X_train, y_train,
          epochs=20,
          batch_size=32,
          verbose=1
      )

      # Save metadata
      metadata = {
          'ticker': ticker,
          'start': start,
          'end': end,
          'sequence_length': sequence_length,
          'training_loss': float(history.history['loss'][-1]),
          'input_shape': list(X.shape[1:]),
          'feature_names': ['Close']
      }

      # Save model and metadata
      self.save_model(ticker)
      self.save_metadata(ticker, metadata)
      return True


    def predict(self, ticker: str, days: int = 20):
      """Generate predictions using only Close prices"""
      self.load_model(ticker)
      if self.model is None:
          raise RuntimeError(f"No trained model found for {ticker}")

      # Get latest Close prices
      latest_data = yf.download(
          ticker,
          start=pd.Timestamp.now() - pd.Timedelta(days=120),
          end=pd.Timestamp.now()
      )[['Close']].dropna()

      # Scale
      scaled_data = self.scaler.transform(latest_data[['Close']])
      input_seq = scaled_data[-self.sequence_length:]

      # Predict
      predictions = []
      current_sequence = input_seq.copy()

      for _ in range(days):
          current_input = current_sequence.reshape(1, self.sequence_length, 1)
          next_pred = self.model.predict(current_input, verbose=0)[0][0]
          predictions.append(next_pred)
          current_sequence = np.vstack([current_sequence[1:], [[next_pred]]])

      # Inverse scale
      pred_array = np.array(predictions).reshape(-1, 1)
      original_scale_preds = self.scaler.inverse_transform(pred_array).flatten()

      # Prediction dates
      last_date = latest_data.index[-1]
      pred_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days, freq='B')

      return {
          'dates': pred_dates.strftime('%Y-%m-%d').tolist(),
          'forecast': original_scale_preds.tolist()
      }


    def save_model(self, ticker: str):
        """Save model artifacts"""
        if self.model is None or self.scaler is None:
            raise RuntimeError("No model to save")

        path = self.get_model_path(ticker)

        # Save Keras model
        self.model.save(os.path.join(path, "model.h5"))

        # Save scaler
        joblib.dump(self.scaler, os.path.join(path, "scaler.pkl"))

    def load_model(self, ticker: str):
        """Load model artifacts"""
        path = self.get_model_path(ticker)

        try:
            # Load Keras model
            self.model = load_model(os.path.join(path, "model.h5"))

            # Load scaler
            self.scaler = joblib.load(os.path.join(path, "scaler.pkl"))

            # Load metadata to get sequence length
            metadata = self.load_metadata(ticker)
            self.sequence_length = metadata.get('sequence_length', 60)

        except FileNotFoundError:
            raise RuntimeError(f"No saved model found for {ticker}")

def get_cached_forecast():
    if os.path.exists(FORECAST_PATH):
        return pd.read_json(FORECAST_PATH).to_dict(orient="list")
    return None

def list_trained_models():
    return [name for name in os.listdir(MODELS_DIR)
            if os.path.isdir(os.path.join(MODELS_DIR, name))]