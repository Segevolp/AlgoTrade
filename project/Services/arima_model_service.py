# sarimax_service.py

import os
import json
import yfinance as yf
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResults

MODELS_DIR = "models"
MODEL_PATH = os.path.join(MODELS_DIR, "sarimax_model.pkl")
PARAMETERS_PATH = os.path.join(MODELS_DIR, "params.json")
DATA_PATH = os.path.join(MODELS_DIR, "data.csv")
FORECAST_PATH = os.path.join(MODELS_DIR, "forecast.json")

os.makedirs(MODELS_DIR, exist_ok=True)


def train_model(
    main_ticker: str = "^GSPC",
    exog_tickers: list = None,
    start: str = "2020-01-01",
    end: str = "2025-04-08",
    p_range: tuple = (0, 1),
    d_range: tuple = (0, 1),
    q_range: tuple = (0, 1),
    P_range: tuple = (0,),
    D_range: tuple = (0,),
    Q_range: tuple = (0,),
    m: int = 7,
) -> bool:
    """
    Downloads the main series (S&P 500 by default) and specified exogenous tickers,
    performs a grid search over SARIMAX hyperparameters, refits the best model on the
    full dataset, and saves both the fitted model and its parameters to disk.

    Returns True if training and saving succeed.
    """
    if exog_tickers is None:
        exog_tickers = ["GLD", "^TYX", "QQQ"]

    # 1. Download the main series (S&P 500)
    df_main = yf.download(main_ticker, start=start, end=end)[["Close"]].dropna()
    df_main.columns = ["y"]
    df_main.index.name = "ds"

    # 2. Download exogenous variables
    df_exog = yf.download(exog_tickers, start=start, end=end)[["Close"]].dropna()
    # Drop the top-level "Close" label from the MultiIndex
    df_exog.columns = df_exog.columns.droplevel(0)
    df_exog = df_exog.ffill()
    df_exog.index.name = "ds"

    # 3. Merge main series and exogenous data
    df = pd.concat([df_main, df_exog], axis=1).dropna()
    # Ensure business‐day frequency (matching the original script)
    df_reset_index = df.copy()
    df_reset_index.index = pd.date_range(
        start=df.index[0], periods=len(df), freq="B"
    )
    df_reset_index.index.name = "ds"

    y = df_reset_index["y"]
    X = df_reset_index[exog_tickers]

    # 4. Train/Test split (90% train, 10% test)
    train_size = int(len(y) * 0.9)
    train_y, test_y = y.iloc[:train_size], y.iloc[train_size:]
    train_X, test_X = X.iloc[:train_size], X.iloc[train_size:]

    # 5. Grid search over SARIMAX hyperparameters
    from itertools import product
    from sklearn.metrics import mean_squared_error

    results = []
    param_grid = list(product(p_range, d_range, q_range, P_range, D_range, Q_range))
    for p, d, q, P, D, Q in param_grid:
        try:
            model = SARIMAX(
                train_y,
                exog=train_X,
                order=(p, d, q),
                seasonal_order=(P, D, Q, m),
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False, maxiter=200)

            pred = model.predict(
                start=test_y.index[0], end=test_y.index[-1], exog=test_X
            )
            mse = mean_squared_error(test_y, pred)

            results.append(
                {
                    "params": (p, d, q, P, D, Q),
                    "mse": float(mse),
                }
            )
        except Exception:
            continue

    if not results:
        raise RuntimeError("No successful SARIMAX fits during grid search.")

    # 6. Select best hyperparameters
    best_result = min(results, key=lambda x: x["mse"])
    p, d, q, P, D, Q = best_result["params"]

    # 7. Refit on full data with the best hyperparameters
    final_model = SARIMAX(
        y,
        exog=X,
        order=(p, d, q),
        seasonal_order=(P, D, Q, m),
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False)

    # 8. Save merged data, fitted model, and parameters
    df_reset_index.to_csv(DATA_PATH)
    # Save parameters to JSON
    params_dict = {
        "order": [p, d, q],
        "seasonal_order": [P, D, Q, m],
        "exog_tickers": exog_tickers,
    }
    with open(PARAMETERS_PATH, "w") as f:
        json.dump(params_dict, f)

    # Save the SARIMAXResults instance
    final_model.save(MODEL_PATH)

    return True


def load_state():
    """
    Loads the trained SARIMAXResults object, the merged DataFrame, and the
    associated exogenous tickers. Returns (model, df, exog_tickers).
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(DATA_PATH) or not os.path.exists(
        PARAMETERS_PATH
    ):
        raise FileNotFoundError("Model, data, or parameters file missing. Please train first.")

    # Load the fitted model
    model = SARIMAXResults.load(MODEL_PATH)

    # Load the merged DataFrame
    df = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
    df.index.name = "ds"

    # Load exogenous tickers
    with open(PARAMETERS_PATH, "r") as f:
        params = json.load(f)
    exog_tickers = params.get("exog_tickers", [])

    return model, df, exog_tickers


def predict_next_days(days: int = 10) -> dict:
    """
    Loads the saved SARIMAX model and DataFrame, then forecasts 'days' business days
    into the future. Exogenous variables are assumed to remain constant at their last observed values.
    Saves the forecast (means and confidence intervals) to disk as JSON and also returns it.
    """
    model, df, exog_tickers = load_state()

    # Separate out y and X
    y = df["y"]
    X = df[exog_tickers]

    # Build future exogenous DataFrame by repeating the last observed exog row
    last_exog = X.iloc[[-1]].values  # shape (1, num_exogs)
    future_exog_array = np.tile(last_exog, (days, 1))
    future_index = pd.date_range(
        start=X.index[-1] + pd.Timedelta(days=1), periods=days, freq="B"
    )
    future_exog = pd.DataFrame(future_exog_array, index=future_index, columns=exog_tickers)

    # Perform forecast with confidence intervals
    forecast_result = model.get_forecast(steps=days, exog=future_exog)
    forecast_mean = forecast_result.predicted_mean
    forecast_ci = forecast_result.conf_int(alpha=0.05)

    # Prepare output dictionary
    output = {
        "dates": [dt.strftime("%Y-%m-%d") for dt in forecast_mean.index],
        "forecast": forecast_mean.tolist(),
        "lower_ci": forecast_ci.iloc[:, 0].tolist(),
        "upper_ci": forecast_ci.iloc[:, 1].tolist(),
    }

    # Save to JSON for caching
    with open(FORECAST_PATH, "w") as f:
        json.dump(output, f, indent=2)

    return output


def get_cached_forecast() -> dict:
    """
    If a JSON forecast already exists on disk, load and return it. Otherwise, return None.
    """
    if os.path.exists(FORECAST_PATH):
        with open(FORECAST_PATH, "r") as f:
            return json.load(f)
    return None
