from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Flask!"

@app.route('/prophet/returns')
def prophet_get_returns():
    # taking arguments
    data = request.json
    # fetch specific argument from json: data["arg name"]

    # returns = call backend logic
    returns = ""

    # Convert to JSON serializable format
    returns_json = returns.reset_index().rename(columns={"Date": "ds", "Adj Close": "y"}).to_dict(orient="records")
    return jsonify(returns_json)


if __name__ == '__main__':
    app.run(debug=True)