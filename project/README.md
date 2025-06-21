# AlgoTrade Time Series Prediction Service

This service provides time series prediction capabilities using multiple algorithms:

- ARIMA (with exogenous variables support)
- LSTM (with technical indicators)
- Prophet (with seasonality components)

## Project Structure

```
project/
├── algorithms/           # Algorithm implementations
│   ├── __init__.py
│   ├── base_model.py    # Base class for all models
│   ├── arima_model.py   # ARIMA implementation
│   ├── lstm_model.py    # LSTM implementation
│   └── prophet_model.py # Prophet implementation
├── saved_models/        # Trained models are saved here
│   ├── arima/          # ARIMA models by ticker
│   ├── lstm/           # LSTM models by ticker
│   └── prophet/        # Prophet models by ticker
├── ServiceServer.py     # Flask server implementation
└── requirements.txt     # Python dependencies
```

## API Endpoints

### ARIMA

- POST `/arima/train`
  - Parameters: ticker, start, end, exog_tickers (optional)
- POST `/arima/predict`
  - Parameters: ticker, days

### LSTM

- POST `/lstm/train`
  - Parameters: ticker, start, end, sequence_length
- POST `/lstm/predict`
  - Parameters: ticker, days

### Prophet

- POST `/lstm/train`
  - Parameters: ticker, start, end
- POST `/lstm/predict`
  - Parameters: ticker, days

### Model Management

- GET `/models/list`
  - Lists all trained models by algorithm

## Model Storage

Each trained model is saved in its own directory under `saved_models/<algorithm>/<ticker>/`:

- Model artifacts (model.pkl, model.h5, etc.)
- Metadata (metadata.json)
- Additional data needed for predictions

## Setup and Running

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the server:

```bash
python ServiceServer.py
```

The server will run on http://localhost:5000
