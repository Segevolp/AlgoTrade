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
MODELS_DIR    = "models"
FORECAST_PATH = os.path.join(MODELS_DIR, 'forecast.json')

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

    stock_dir = os.path.join(MODELS_DIR, ticker.replace('^','').replace('/','_'))
    os.makedirs(stock_dir, exist_ok=True)

    MODEL_PATH  = os.path.join(stock_dir, 'arima_model.pkl')
    EXOG_PATH   = os.path.join(stock_dir, 'arima_exog.pkl')
    PARAMS_PATH = os.path.join(stock_dir, 'arima_params.json')
    DATA_PATH   = os.path.join(stock_dir, 'data.csv')

    if exog_tickers is None:
        exog_tickers = ['GLD', 'QQQ', '^TNX']

    # 1. Download & merge
    data = fetch_close(ticker, start, end).rename(columns={'Close': 'y'})
    exo_list = []
    for t in exog_tickers:
        df_exo = fetch_close(t, start, end).rename(columns={'Close': t})
        exo_list.append(df_exo)
        df_exo.index.name = 'ds'

    exog_data = pd.concat(exo_list, axis=1).ffill()
    df = pd.concat([data, exog_data], axis=1).dropna()
    df = df.asfreq('B').ffill()
    df.index.name = 'ds'
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
    X.to_pickle(EXOG_PATH)
    df.to_csv(DATA_PATH, index=True)

    
    return True


# ------------------------------------------------------------------
# 4. Predict function
# ------------------------------------------------------------------
def predict_next_days(ticker: str = '^GSPC', days: int = 10) -> dict:
    """
    Forecast the next *days* business days using the trained SARIMAX and exogenous series.
    Returns a dict with 'dates', 'forecast_mean', 'forecast_ci_lower', and 'forecast_ci_upper'.
    """
    # Load all saved state from ticker directory
    model, exog, params, df = load_state(ticker)

    # Build future exogenous by repeating the last row
    last_row = exog.iloc[-1].values.reshape(1, -1)
    future_exog = pd.DataFrame(
        np.tile(last_row, (days, 1)),
        columns=params['exog_tickers'],
        index=pd.date_range(
            start=exog.index[-1] + pd.tseries.offsets.BDay(),
            periods=days,
            freq='B'
        )
    )

    # Generate forecast
    forecast = model.get_forecast(steps=days, exog=future_exog)
    mean = forecast.predicted_mean
    ci   = forecast.conf_int(alpha=0.05)

    return {
        'dates':             mean.index.strftime('%Y-%m-%d').tolist(),
        'forecast_mean':     mean.tolist(),
        'forecast_ci_lower': ci.iloc[:, 0].tolist(),
        'forecast_ci_upper': ci.iloc[:, 1].tolist()
    }

def load_state(ticker: str):
    """
    Load model, exogenous DataFrame, params JSON & full history for *ticker*.
    """
    stock_dir   = os.path.join(MODELS_DIR, ticker.replace('^','').replace('/','_'))
    MODEL_PATH  = os.path.join(stock_dir, 'arima_model.pkl')
    EXOG_PATH   = os.path.join(stock_dir, 'arima_exog.pkl')
    PARAMS_PATH = os.path.join(stock_dir, 'arima_params.json')
    DATA_PATH   = os.path.join(stock_dir, 'data.csv')

    model  = pickle.load(open(MODEL_PATH, 'rb'))
    exog   = pd.read_pickle(EXOG_PATH)
    params = json.load(open(PARAMS_PATH))
    df     = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
    return model, exog, params, df

def get_cached_forecast() -> dict | None:
    """If you ever write out a forecast.json, load & return it here."""
    if os.path.exists(FORECAST_PATH):
        return pd.read_json(FORECAST_PATH).to_dict(orient='list')
    return None

def list_trained_models() -> list[str]:
    """Returns all tickers for which a model folder exists."""
    return [
        name for name in os.listdir(MODELS_DIR)
        if os.path.isdir(os.path.join(MODELS_DIR, name))
    ]