import os
import time
import json
import pickle
import requests
from itertools import product

import numpy as np
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX

from .base_model import BaseTimeSeriesModel

class ARIMAModel(BaseTimeSeriesModel):
    def __init__(self):
        super().__init__("arima")
        self.model = None
        self.exog_data = None
        self.params = None
        
    def fetch_close(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        """Return a DataFrame with a single 'Close' column for *ticker*."""
        for wait in (1, 2, 3):  # three yfinance tries
            try:
                df = yf.download(
                    ticker,
                    start=start,
                    end=end,
                    auto_adjust=False,
                    progress=False,
                    threads=False,
                    repair=True
                )
                if not df.empty:
                    return df[['Close']]
            except (json.JSONDecodeError, requests.exceptions.RequestException):
                time.sleep(wait)

        # fallback to stooq
        try:
            alt = web.DataReader(ticker.lstrip('^'), 'stooq', start, end)
            return alt[::-1][['Close']]
        except Exception as e:
            raise RuntimeError(f"cannot retrieve data for {ticker}") from e
            
    def train(self, ticker: str, start: str, end: str, exog_tickers: list = None):
        """Train ARIMA model with optional exogenous variables"""
        if exog_tickers is None:
            exog_tickers = ['GLD', 'QQQ', '^TNX']
            
        # Download & merge data
        data = self.fetch_close(ticker, start, end).rename(columns={'Close': 'y'})
        exo_list = []
        for t in exog_tickers:
            df_exo = self.fetch_close(t, start, end).rename(columns={'Close': t})
            exo_list.append(df_exo)

        exog_data = pd.concat(exo_list, axis=1).ffill()
        df = pd.concat([data, exog_data], axis=1).dropna()
        df = df.asfreq('B').ffill()

        y = df['y']
        X = df[exog_tickers]

        # Train/test split
        split = int(len(y) * 0.9)
        train_y, test_y = y[:split], y[split:]
        train_X, test_X = X[:split], X[split:]

        # Grid search
        p_range = d_range = q_range = range(0, 2)
        P_range = D_range = Q_range = range(0, 1)
        m = 7  # weekly seasonality

        best_mse = np.inf
        best_params = None

        for p, d, q, P, D, Q in product(p_range, d_range, q_range,
                                      P_range, D_range, Q_range):
            try:
                mdl = SARIMAX(
                    train_y,
                    exog=train_X,
                    order=(p, d, q),
                    seasonal_order=(P, D, Q, m),
                    enforce_stationarity=False,
                    enforce_invertibility=False
                ).fit(disp=False, maxiter=200)

                pred = mdl.predict(
                    start=test_y.index[0],
                    end=test_y.index[-1],
                    exog=test_X
                )
                mse = mean_squared_error(test_y, pred)
                if mse < best_mse:
                    best_mse, best_params = mse, (p, d, q, P, D, Q)
            except Exception:
                continue

        if best_params is None:
            raise RuntimeError("all SARIMAX candidates failed")

        p, d, q, P, D, Q = best_params

        # Fit final model on full sample
        self.model = SARIMAX(
            y,
            exog=X,
            order=(p, d, q),
            seasonal_order=(P, D, Q, m),
            enforce_stationarity=False,
            enforce_invertibility=False
        ).fit(disp=False)

        self.exog_data = X
        self.params = {
            'ticker': ticker,
            'start': start,
            'end': end,
            'exog_tickers': exog_tickers,
            'best_params': {
                'order': best_params[:3],
                'seasonal_order': best_params[3:] + (m,),
                'mse': best_mse
            }
        }
        
        # Save the model
        self.save_model(ticker)
        return True
        
    def predict(self, ticker: str, days: int = 10):
        """Generate predictions using saved model"""
        self.load_model(ticker)
        if self.model is None:
            raise RuntimeError(f"No trained model found for {ticker}")
            
        # Build future exog by repeating last row
        last_row = self.exog_data.iloc[-1].values.reshape(1, -1)
        future_exog = pd.DataFrame(
            np.tile(last_row, (days, 1)),
            columns=self.params['exog_tickers'],
            index=pd.date_range(
                start=self.exog_data.index[-1] + pd.tseries.offsets.BDay(),
                periods=days,
                freq='B'
            )
        )

        # Generate forecast
        forecast = self.model.get_forecast(steps=days, exog=future_exog)
        mean = forecast.predicted_mean
        conf_int = forecast.conf_int()
        
        return {
            'dates': mean.index.strftime('%Y-%m-%d').tolist(),
            'forecast_mean': mean.values.tolist(),
            'forecast_ci': conf_int.values.tolist()
        }
        
    def save_model(self, ticker: str):
        """Save model artifacts"""
        if self.model is None:
            raise RuntimeError("No model to save")
            
        path = self.get_model_path(ticker)
        
        # Save model
        with open(os.path.join(path, "model.pkl"), "wb") as f:
            pickle.dump(self.model, f)
            
        # Save exogenous data
        self.exog_data.to_pickle(os.path.join(path, "exog_data.pkl"))
        
        # Save parameters and metadata
        self.save_metadata(ticker, self.params)
        
    def load_model(self, ticker: str):
        """Load model artifacts"""
        path = self.get_model_path(ticker)
        
        try:
            # Load model
            with open(os.path.join(path, "model.pkl"), "rb") as f:
                self.model = pickle.load(f)
                
            # Load exogenous data
            self.exog_data = pd.read_pickle(os.path.join(path, "exog_data.pkl"))
            
            # Load parameters
            self.params = self.load_metadata(ticker)
            
        except FileNotFoundError:
            raise RuntimeError(f"No saved model found for {ticker}") 