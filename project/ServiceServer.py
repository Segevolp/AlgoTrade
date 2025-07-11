from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
import os

# Import models and database
from models import db, bcrypt, User, Portfolio, PortfolioItem

# Import existing services
from Services.lstm_model_service import train_model, predict_next_days
from Services.arima_model_service import train_model as train_arima, predict_next_days as predict_arima
from Services.prophet_model_service import train_model as train_prophet, predict_next_days as predict_prophet
from Services.portfolio_prediction_service import predict_portfolio_earnings

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///algotrade.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)

# JWT Error Handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print("JWT Error: Token has expired")
    return jsonify({'success': False, 'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"JWT Error: Invalid token - {error}")
    return jsonify({'success': False, 'error': 'Invalid token'}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"JWT Error: Missing token - {error}")
    return jsonify({'success': False, 'error': 'Authorization token is required'}), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    print("JWT Error: Token has been revoked")
    return jsonify({'success': False, 'error': 'Token has been revoked'}), 401

# Create tables
with app.app_context():
    db.create_all()

# ==================== AUTHENTICATION ====================

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'success': False, 'error': 'Username, email, and password are required'})
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'error': 'Username already exists'})
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'error': 'Email already registered'})
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create default portfolio
        default_portfolio = Portfolio(
            user_id=user.id,
            name='My Portfolio'
        )
        db.session.add(default_portfolio)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User registered successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'success': False, 'error': 'Username and password are required'})
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and user.check_password(data['password']):
            # Convert user.id to string for JWT
            access_token = create_access_token(identity=str(user.id))
            return jsonify({
                'success': True,
                'access_token': access_token,
                'user': user.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        # Convert JWT identity back to int
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        return jsonify({'success': True, 'user': user.to_dict()})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== PORTFOLIO MANAGEMENT ====================

@app.route('/portfolios', methods=['GET'])
@jwt_required()
def get_portfolios():
    try:
        user_id = int(get_jwt_identity())
        portfolios = Portfolio.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'success': True,
            'portfolios': [portfolio.to_dict() for portfolio in portfolios]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/portfolios', methods=['POST'])
@jwt_required()
def create_portfolio():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'success': False, 'error': 'Portfolio name is required'})
        
        portfolio = Portfolio(
            user_id=user_id,
            name=data['name']
        )
        
        db.session.add(portfolio)
        db.session.commit()
        
        return jsonify({'success': True, 'portfolio': portfolio.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/portfolios/<int:portfolio_id>', methods=['DELETE'])
@jwt_required()
def delete_portfolio(portfolio_id):
    try:
        user_id = int(get_jwt_identity())
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).first()
        
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'})
        
        db.session.delete(portfolio)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Portfolio deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/portfolios/<int:portfolio_id>/items', methods=['POST'])
@jwt_required()
def add_portfolio_item(portfolio_id):
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Verify portfolio belongs to user
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'})
        
        if not data or not all(key in data for key in ['ticker', 'quantity', 'purchase_price']):
            return jsonify({'success': False, 'error': 'Ticker, quantity, and purchase price are required'})
        
        item = PortfolioItem(
            portfolio_id=portfolio_id,
            ticker=data['ticker'].upper(),
            quantity=float(data['quantity']),
            purchase_price=float(data['purchase_price']),
            notes=data.get('notes', '')
        )
        
        db.session.add(item)
        db.session.commit()
        
        return jsonify({'success': True, 'item': item.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/portfolios/<int:portfolio_id>/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_portfolio_item(portfolio_id, item_id):
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Verify portfolio belongs to user
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'})
        
        item = PortfolioItem.query.filter_by(id=item_id, portfolio_id=portfolio_id).first()
        if not item:
            return jsonify({'success': False, 'error': 'Portfolio item not found'})
        
        # Update item fields
        if 'ticker' in data:
            item.ticker = data['ticker'].upper()
        if 'quantity' in data:
            item.quantity = float(data['quantity'])
        if 'purchase_price' in data:
            item.purchase_price = float(data['purchase_price'])
        if 'notes' in data:
            item.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({'success': True, 'item': item.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/portfolios/<int:portfolio_id>/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_portfolio_item(portfolio_id, item_id):
    try:
        user_id = int(get_jwt_identity())
        
        # Verify portfolio belongs to user
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'})
        
        item = PortfolioItem.query.filter_by(id=item_id, portfolio_id=portfolio_id).first()
        if not item:
            return jsonify({'success': False, 'error': 'Portfolio item not found'})
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Portfolio item deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# ==================== PORTFOLIO EARNINGS PREDICTION ====================

@app.route('/portfolios/<int:portfolio_id>/predict', methods=['POST'])
@jwt_required()
def predict_portfolio_earnings_route(portfolio_id):
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Verify portfolio belongs to user
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user_id).first()
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'})
        
        # Get prediction parameters
        method = data.get('method', 'average')  # 'lstm', 'arima', 'prophet', or 'average'
        days = int(data.get('days', 30))  # Number of days to predict
        
        # Validate method
        if method not in ['lstm', 'arima', 'prophet', 'average']:
            return jsonify({'success': False, 'error': 'Invalid prediction method. Use: lstm, arima, prophet, or average'})
        
        # Get portfolio items
        if not portfolio.items:
            return jsonify({'success': False, 'error': 'Portfolio is empty. Add some stocks first.'})
        
        # Convert portfolio items to the format expected by the prediction service
        portfolio_items = [item.to_dict() for item in portfolio.items]
        
        # Get predictions
        result = predict_portfolio_earnings(portfolio_items, method, days)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Portfolio prediction error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test-auth', methods=['GET'])
@jwt_required()
def test_auth():
    try:
        user_id = int(get_jwt_identity())
        print(f"Test Auth - User ID from JWT: {user_id}")
        return jsonify({'success': True, 'message': 'Authentication working!', 'user_id': user_id})
    except Exception as e:
        print(f"Test Auth Error: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ==================== EXISTING API ENDPOINTS (Updated with Authentication) ====================

@app.route('/hello')
def hello():
    return jsonify({'success': True, 'message': 'Hello World!'})

# -------------------- LSTM --------------------
@app.route('/lstm/train', methods=['POST'])
@jwt_required()
def train_lstm():
    try:
        user_id = int(get_jwt_identity())  # Convert to int
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
@jwt_required()
def predict_lstm():
    try:
        user_id = int(get_jwt_identity())  # Convert to int
        ticker = request.args.get('ticker', '^GSPC')
        days = int(request.args.get('days', 20))
        sequence_length = int(request.args.get('sequence_length', 60))

        forecast = predict_next_days(ticker=ticker, days=days, sequence_length=sequence_length)
        return jsonify({'success': True, 'data': forecast})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/lstm/models', methods=['GET'])
@jwt_required()
def list_lstm_models():
    from Services.lstm_model_service import list_trained_models
    try:
        user_id = int(get_jwt_identity())
        print(f"LSTM Models - User ID from JWT: {user_id}")
        return jsonify({'success': True, 'tickers': list_trained_models()})
    except Exception as e:
        print(f"LSTM Models Error: {e}")
        return jsonify({'success': False, 'error': str(e)})

# -------------------- ARIMA -------------------
@app.route('/arima/train', methods=['POST'])
@jwt_required()
def train_arima_route():
    try:
        user_id = int(get_jwt_identity())  # Convert to int
        data = request.get_json() or {}
        ticker = data.get('ticker', '^GSPC')
        start = data.get('start', '2020-01-01')
        end = data.get('end', '2025-04-08')
        exog_tickers = data.get('exog_tickers', ['GLD', 'QQQ', '^TNX'])

        success = train_arima(ticker=ticker, start=start, end=end, exog_tickers=exog_tickers)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/arima/models', methods=['GET'])
@jwt_required()
def list_arima_models_route():
    from Services.arima_model_service import list_trained_models
    try:
        user_id = int(get_jwt_identity())  # Convert to int
        return jsonify({'success': True, 'tickers': list_trained_models()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/arima/predict', methods=['GET'])
@jwt_required()
def predict_arima_route():
    try:
        user_id = int(get_jwt_identity())  # Convert to int
        ticker = request.args.get('ticker', '^GSPC')
        days = int(request.args.get('days', 10))
        forecast = predict_arima(ticker=ticker, days=days)
        return jsonify({'success': True, 'data': forecast})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# -------------------- Prophet --------------------
@app.route('/prophet/train', methods=['POST'])
@jwt_required()
def train_prophet_route():
    try:
        user_id = int(get_jwt_identity())  # Convert to int
        data = request.get_json() or {}
        ticker = data.get('ticker', '^GSPC')
        start = data.get('start', '2015-01-01')
        end = data.get('end', '2025-05-22')

        success = train_prophet(ticker=ticker, start=start, end=end)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/prophet/predict', methods=['GET'])
@jwt_required()
def predict_prophet_route():
    try:
        user_id = int(get_jwt_identity())  # Convert to int
        ticker = request.args.get('ticker', '^GSPC')
        days = int(request.args.get('days', 10))
        forecast = predict_prophet(ticker=ticker, days=days)
        return jsonify({'success': True, 'data': forecast})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/prophet/models', methods=['GET'])
@jwt_required()
def list_prophet_models_route():
    from Services.prophet_model_service import list_trained_models
    try:
        user_id = int(get_jwt_identity())  # Convert to int
        return jsonify({'success': True, 'tickers': list_trained_models()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5555)