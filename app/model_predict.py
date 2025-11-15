import joblib
import numpy as np
import pandas as pd
import os

MODEL_DIR = "app/models"

def load_ensemble():
    model_path = os.path.join(MODEL_DIR, "ensemble.pkl")
    models = joblib.load(model_path)
    return models

def ensemble_predict(models, X):
    preds = np.column_stack([m.predict(X) for m in models])
    avg = preds.mean(axis=1)
    return avg
