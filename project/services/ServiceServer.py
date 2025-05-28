from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from lstm_model_service import train_model, predict_next_days, get_cached_forecast

app = Flask(__name__)



@app.get("/")
def home():
    return {"message": "Hello from FastAPI"}

@app.post("/train")
def train():
    success = train_model()
    if success:
        return {"message": "Model trained and saved successfully."}
    return {"error": "Training failed."}

@app.get("/predict")
def predict(days: int = Query(20, gt=0, le=60)):
    return predict_next_days(days)

@app.get("/cached-forecast")
def cached():
    data = get_cached_forecast()
    if data:
        return data
    return {"error": "No cached forecast available."}
