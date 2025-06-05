from project.models.prophet_model import forecast_ta35, train_prophet_model, generate_forecast
import yfinance as yf


def get_prophet_forecast(csv_path, ticker="TA35.TA", start_date="2024-01-01", end_date="2025-04-07", days=25):
    """
    Fetches Prophet forecast for the given ticker and date range.

    :param csv_path: Path to the holidays CSV file.
    :param ticker: Stock ticker to fetch from Yahoo Finance (default: "TA35.TA").
    :param start_date: Start date for historical data.
    :param end_date: End date for historical data.
    :param days: Number of future days to forecast.
    :return: DataFrame with forecast (ds, yhat, yhat_lower, yhat_upper)
    """
    # Note: ticker is currently hardcoded in model; can be generalized later.
    forecast = forecast_ta35(csv_path, start_date=start_date, end_date=end_date, days=days)
    return forecast
def get_returns(ticker, start_date="2023-01-01"):
    df = yf.download(ticker, start=start_date).reset_index()
    return df

def get_forecast(ticker, days):
    df = get_returns(ticker)
    model = train_prophet_model(df)
    forecast = generate_forecast(model, days)
    return forecast