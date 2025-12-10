import os
import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import datetime

MODEL_PATH = "data/ml_models/progress_model.pkl"

def train_model(attempts_data):
    # attempts_data should be a list of dicts: [{'time_spent': ..., 'score': ..., 'timestamp': ...}]
    if not attempts_data:
        return
    
    df = pd.DataFrame(attempts_data)
    # Feature engineering: e.g., using time_spent and score to predict "future performance"
    # For this simple app, let's predict the 'score' of the next attempt based on 'time_spent' history.
    
    # Simple logic: X = time_spent, y = score
    X = df[['time_spent_seconds']]
    y = df['score']
    
    model = LinearRegression()
    model.fit(X, y)
    
    joblib.dump(model, MODEL_PATH)

def predict_progress(time_spent_seconds):
    if not os.path.exists(MODEL_PATH):
        # Fallback/Cold start: Return a heuristic or random valid score
        return 75.0 # expecting 75% score on average
        
    model = joblib.load(MODEL_PATH)
    prediction = model.predict(np.array([[time_spent_seconds]]))
    return float(prediction[0])

def get_latest_prediction(user_db_attempts):
    # Extract data from DB models
    data = []
    for a in user_db_attempts:
        data.append({
            'time_spent_seconds': a.time_spent_seconds,
            'score': a.score
        })
    
    if len(data) < 2:
        return "Not enough data for prediction"
    
    # Retrain on the fly for this user (or use a global model, distinct per user is better for personalization but expensive)
    # For this MVP, we will simulate a "next attempt" prediction
    
    # Improve: Actually we want to show a trend. 
    # Let's just return a linear extrapolation of their scores
    
    scores = [d['score'] for d in data]
    if len(scores) < 2:
        return scores[0] if scores else 0
        
    # Simple average of last 3
    recent_performance = sum(scores[-3:]) / len(scores[-3:])
    
    return recent_performance
