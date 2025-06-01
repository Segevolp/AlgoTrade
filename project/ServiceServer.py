from flask import Flask, request, jsonify
from flask_cors import CORS

from Services.lstm_model_service import train_model, predict_next_days
from Services.arima_model_service import train_model as train_arima, predict_next_days as predict_arima

app = Flask(__name__)
CORS(app)


@app.route('/hello')
def hello():
    return jsonify({'success': True, 'message': 'Hello World!'})


@app.route('/lstm/train', methods=['POST'])
def train_lstm():
    try:
        data = request.get_json()
        ticker = data.get('ticker', '^GSPC')
        start = data.get('start', '2010-01-01')
        end = data.get('end', '2025-05-22')
        sequence_length = data.get('sequence_length', 60)

        success = train_model(ticker=ticker, start=start, end=end, sequence_length=sequence_length)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/lstm/predict', methods=['GET'])
def predict_lstm():
    try:
        days = int(request.args.get('days', 20))
        sequence_length = int(request.args.get('sequence_length', 60))

        forecast = predict_next_days(days=days, sequence_length=sequence_length)
        return jsonify({'success': True, 'data': forecast})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/arima/train', methods=['POST'])
def train_arima_endpoint():
    """
    Expects a JSON POST body like:
    {
      "main_ticker": "^GSPC",
      "exog_tickers": ["GLD","^TYX","QQQ"],
      "start": "2020-01-01",
      "end": "2025-04-08"
    }
    All keys are optional (defaults are set inside train_arima).
    """
    try:
        data = request.get_json() or {}
        main_ticker = data.get('main_ticker', '^GSPC')
        exog_tickers = data.get('exog_tickers', ["GLD", "^TYX", "QQQ"])
        start = data.get('start', '2020-01-01')
        end = data.get('end', '2025-04-08')

        # We’re using the default grid-search ranges inside train_arima unless you decide to pass them explicitly.
        success = train_arima(
            main_ticker=main_ticker,
            exog_tickers=exog_tickers,
            start=start,
            end=end,
            # You could also pass custom p_range, d_range, etc. as additional kwargs here if you want.
        )
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/arima/predict', methods=['GET'])
def predict_arima_endpoint():
    """
    Expects query string ?days=<int> 
    (e.g. /arima/predict?days=10)
    """
    try:
        days = int(request.args.get('days', 10))
        forecast = predict_arima(days=days)
        return jsonify({'success': True, 'data': forecast})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5555)