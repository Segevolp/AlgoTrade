# Services/arima_model_service.py

import os
import time
import json
import requests
import pickle
from itertools import product

import numpy as np
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web  # fallback source
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
from project.algorithms.base_model import BaseTimeSeriesModel

# ------------------------------------------------------------------
# 1. Safe download helper (yfinance → stooq fallback)
# ------------------------------------------------------------------
def fetch_close(ticker: str, start: str, end: str) -> pd.DataFrame:
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

    # fallback to stooq (works for most major symbols)
    try:
        alt = web.DataReader(ticker.lstrip('^'), 'stooq', start, end)
        return alt[::-1][['Close']]
    except Exception as e:
        raise RuntimeError(f"cannot retrieve data for {ticker}") from e


# ------------------------------------------------------------------
# 2. Paths for storing trained model and exogenous data
# ------------------------------------------------------------------
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH    = os.path.join(BASE_DIR, 'arima_model.pkl')
EXOG_PATH     = os.path.join(BASE_DIR, 'arima_exog.pkl')
PARAMS_PATH   = os.path.join(BASE_DIR, 'arima_params.json')

# ------------------------------------------------------------------
# 3. Train function
# ------------------------------------------------------------------
def train_model(ticker: str = '^GSPC',
                start: str = '2020-01-01',
                end: str = '2025-04-08',
                exog_tickers: list = None) -> bool:
    """
    Downloads data for *ticker* and *exog_tickers*, performs grid search over SARIMAX
    orders, fits the best model on the full sample, and saves both the model and
    latest exogenous DataFrame to disk.
    Returns True on success, raises on failure.
    """

    if exog_tickers is None:
        exog_tickers = ['GLD', 'QQQ', '^TNX']

    # 1. Download & merge
    data = fetch_close(ticker, start, end).rename(columns={'Close': 'y'})
    exo_list = []
    for t in exog_tickers:
        df_exo = fetch_close(t, start, end).rename(columns={'Close': t})
        exo_list.append(df_exo)

    exog_data = pd.concat(exo_list, axis=1).ffill()
    df = pd.concat([data, exog_data], axis=1).dropna()
    df = df.asfreq('B').ffill()

    y = df['y']
    X = df[exog_tickers]

    # 2. Train / test split
    split = int(len(y) * 0.9)
    train_y, test_y = y[:split], y[split:]
    train_X, test_X = X[:split], X[split:]

    # 3. Grid search over orders
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

    # 4. Save best_params to JSON
    with open(PARAMS_PATH, 'w') as f:
        json.dump({
            'ticker': ticker,
            'start': start,
            'end': end,
            'exog_tickers': exog_tickers,
            'best_params': {
                'order': best_params[:3],
                'seasonal_order': best_params[3:] + (m,)
            }
        }, f)

    p, d, q, P, D, Q = best_params

    # 5. Refit best model on full sample
    final_model = SARIMAX(
        y,
        exog=X,
        order=(p, d, q),
        seasonal_order=(P, D, Q, m),
        enforce_stationarity=False,
        enforce_invertibility=False
    ).fit(disp=False)

    # 6. Persist the fitted model and exogenous DataFrame
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(final_model, f)

    # Save the last-known exogenous DataFrame to disk (to construct future exog)
    X.to_pickle(EXOG_PATH)

    return True


# ------------------------------------------------------------------
# 4. Predict function
# ------------------------------------------------------------------
def predict_next_days(days: int = 10) -> dict:
    """
    Loads the previously trained SARIMAX model and the saved exogenous DataFrame,
    constructs a future exogenous DataFrame by repeating the last row, and returns
    a dictionary with:
      - 'forecast_mean': list of predicted values
      - 'forecast_ci': list of [lower, upper] intervals for each day
    Raises if the model or exog data does not exist.
    """

    # 1. Ensure model and exog-data exist
    if not os.path.exists(MODEL_PATH) or not os.path.exists(EXOG_PATH) or not os.path.exists(PARAMS_PATH):
        raise RuntimeError("Model or exogenous data not found. Please call /arima/train first.")

    # 2. Load JSON to get exogenous variable names (and their order)
    with open(PARAMS_PATH, 'r') as f:
        params = json.load(f)

    exog_tickers = params['exog_tickers']

    # 3. Load the pickled model and exogenous DataFrame
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)

    X = pd.read_pickle(EXOG_PATH)

    # 4. Build future_exog by repeating the last row
    last_row = X.iloc[-1].values.reshape(1, -1)
    future_exog = pd.DataFrame(
        np.tile(last_row, (days, 1)),
        columns=exog_tickers,
        index=pd.date_range(
            start=X.index[-1] + pd.tseries.offsets.BDay(),
            periods=days, freq='B'
        )
    )

    # 5. Generate forecast
    forecast = model.get_forecast(steps=days, exog=future_exog)
    forecast_mean = forecast.predicted_mean
    forecast_ci = forecast.conf_int(alpha=0.05)

    # 6. Return as serializable structures
    return {
        'dates': [d.strftime('%Y-%m-%d') for d in forecast_mean.index],
        'forecast_mean': forecast_mean.tolist(),
        'forecast_ci_lower': forecast_ci.iloc[:, 0].tolist(),
        'forecast_ci_upper': forecast_ci.iloc[:, 1].tolist()
    }

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
        self.save_metadata(ticker, self.params)
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
            'forecast': mean.values.tolist(),
            'forecast_ci_lower': conf_int.iloc[:, 0].tolist(),
            'forecast_ci_upper': conf_int.iloc[:, 1].tolist()
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

