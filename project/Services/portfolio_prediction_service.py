import os
from typing import Dict, List, Tuple, Optional
import statistics

from Services.lstm_model_service import predict_next_days as lstm_predict, list_trained_models as lstm_models
from Services.arima_model_service import predict_next_days as arima_predict, list_trained_models as arima_models  
from Services.prophet_model_service import predict_next_days as prophet_predict, list_trained_models as prophet_models

def normalize_ticker(ticker: str) -> str:
    """Normalize ticker name to match model directory naming"""
    return ticker.replace("^", "").replace("/", "_")

def check_model_exists(ticker: str, algorithm: str) -> bool:
    """Check if a trained model exists for a specific ticker and algorithm"""
    normalized_ticker = normalize_ticker(ticker)
    
    if algorithm == 'lstm':
        return normalized_ticker in lstm_models()
    elif algorithm == 'arima':
        return normalized_ticker in arima_models()
    elif algorithm == 'prophet':
        return normalized_ticker in prophet_models()
    else:
        return False

def get_missing_models(tickers: List[str], algorithms: List[str]) -> Dict[str, List[str]]:
    """
    Check which models are missing for the given tickers and algorithms.
    Returns dict with ticker as key and list of missing algorithms as value.
    """
    missing = {}
    
    for ticker in tickers:
        missing_algos = []
        for algo in algorithms:
            if not check_model_exists(ticker, algo):
                missing_algos.append(algo)
        
        if missing_algos:
            missing[ticker] = missing_algos
    
    return missing

def predict_stock_price(ticker: str, algorithm: str, days: int = 30) -> Optional[float]:
    """
    Get price prediction for a specific stock using the specified algorithm.
    Returns the predicted price after 'days' or None if model doesn't exist.
    """
    if not check_model_exists(ticker, algorithm):
        return None
    
    try:
        if algorithm == 'lstm':
            result = lstm_predict(ticker=ticker, days=days)
            # Return the last predicted price
            return result['forecast'][-1] if result['forecast'] else None
            
        elif algorithm == 'arima':
            result = arima_predict(ticker=ticker, days=days)
            # Return the last predicted price
            return result['forecast_mean'][-1] if result['forecast_mean'] else None
            
        elif algorithm == 'prophet':
            result = prophet_predict(ticker=ticker, days=days)
            # Return the last predicted price
            return result['forecast'][-1] if result['forecast'] else None
            
    except Exception as e:
        print(f"Error predicting {ticker} with {algorithm}: {e}")
        return None
    
    return None

def predict_portfolio_earnings(portfolio_items: List[Dict], method: str, days: int = 30) -> Dict:
    """
    Predict portfolio earnings based on trained models.
    
    Args:
        portfolio_items: List of portfolio items with ticker, quantity, purchase_price
        method: 'lstm', 'arima', 'prophet', or 'average'
        days: Number of days to predict
    
    Returns:
        Dict with success status, predictions, and missing models if any
    """
    # Extract unique tickers
    tickers = list(set(item['ticker'] for item in portfolio_items))
    
    # Determine which algorithms to check
    if method == 'average':
        algorithms = ['lstm', 'arima', 'prophet']
    else:
        algorithms = [method]
    
    # Check for missing models
    missing_models = get_missing_models(tickers, algorithms)
    
    if missing_models:
        return {
            'success': False,
            'error': 'Missing trained models',
            'missing_models': missing_models,
            'required_algorithms': algorithms
        }
    
    # Calculate predictions for each stock
    predictions = {}
    portfolio_predictions = []
    
    for item in portfolio_items:
        ticker = item['ticker']
        quantity = item['quantity']
        purchase_price = item['purchase_price']
        
        if method == 'average':
            # Get predictions from all algorithms and average them
            predicted_prices = []
            
            for algo in algorithms:
                price = predict_stock_price(ticker, algo, days)
                if price is not None:
                    predicted_prices.append(price)
            
            if predicted_prices:
                predicted_price = statistics.mean(predicted_prices)
            else:
                continue  # Skip this stock if no predictions available
                
        else:
            # Use specific algorithm
            predicted_price = predict_stock_price(ticker, method, days)
            if predicted_price is None:
                continue  # Skip this stock if prediction failed
        
        # Calculate earnings for this position
        current_value = quantity * purchase_price
        predicted_value = quantity * predicted_price
        profit_loss = predicted_value - current_value
        profit_loss_percent = (profit_loss / current_value) * 100
        
        stock_prediction = {
            'ticker': ticker,
            'quantity': quantity,
            'purchase_price': purchase_price,
            'predicted_price': predicted_price,
            'current_value': current_value,
            'predicted_value': predicted_value,
            'profit_loss': profit_loss,
            'profit_loss_percent': profit_loss_percent
        }
        
        predictions[ticker] = stock_prediction
        portfolio_predictions.append(stock_prediction)
    
    # Calculate total portfolio metrics
    total_current_value = sum(pred['current_value'] for pred in portfolio_predictions)
    total_predicted_value = sum(pred['predicted_value'] for pred in portfolio_predictions)
    total_profit_loss = total_predicted_value - total_current_value
    total_profit_loss_percent = (total_profit_loss / total_current_value) * 100 if total_current_value > 0 else 0
    
    return {
        'success': True,
        'method': method,
        'days': days,
        'stock_predictions': portfolio_predictions,
        'total_metrics': {
            'current_value': total_current_value,
            'predicted_value': total_predicted_value,
            'profit_loss': total_profit_loss,
            'profit_loss_percent': total_profit_loss_percent
        }
    } 