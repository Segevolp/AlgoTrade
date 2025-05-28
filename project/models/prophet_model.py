import pandas as pd
from prophet import Prophet
import yfinance as yf

def fetch_ta35_data(start_date="2024-01-01", end_date="2025-04-07"):
    data = yf.download("TA35.TA", start=start_date, end=end_date, auto_adjust=False)["Adj Close"]
    return data.reset_index()

def load_holidays(csv_path):
    holidays = pd.read_csv(csv_path)
    holidays["ds"] = pd.to_datetime(holidays["date"], format="%m/%d/%Y")
    holidays = holidays.rename(columns={"eng_name": "holiday"})[["ds", "holiday"]]
    return holidays

def prepare_dataframe(data):
    return data.rename(columns={"Date": "ds", "Adj Close": "y"})

def train_prophet_model(df, holidays_df=None, interval_width=0.99):
    model = Prophet(holidays=holidays_df, interval_width=interval_width) if holidays_df is not None else Prophet()
    model.fit(df)
    return model

def generate_forecast(model, days=25):
    future = model.make_future_dataframe(periods=days, freq="D")
    forecast = model.predict(future)
    return forecast

def forecast_ta35(csv_path, start_date="2024-01-01", end_date="2025-04-07", days=25):
    data = fetch_ta35_data(start_date, end_date)
    holidays = load_holidays(csv_path)
    df = prepare_dataframe(data)
    model = train_prophet_model(df, holidays)
    forecast = generate_forecast(model, days)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]