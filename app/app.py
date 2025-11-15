# app/app.py
import os
import json
import joblib
import pandas as pd
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.utils import fetch_nifty, add_features   # adjust import if utils location differs
from app.model_predict import load_ensemble, ensemble_predict

# App and templates
app = FastAPI(title="NIFTY50 Neon Dashboard API")
templates = Jinja2Templates(directory="templates")

# models folder
MODEL_DIR = "app/models"
ENSEMBLE_PATH = os.path.join(MODEL_DIR, "ensemble.pkl")
META_PATH = os.path.join(MODEL_DIR, "meta.json")

# Load ensemble into memory (if available)
def safe_load_models():
    if not os.path.exists(ENSEMBLE_PATH):
        return None
    try:
        return load_ensemble()
    except Exception as e:
        print("Failed to load ensemble:", e)
        return None

models = safe_load_models()

# ---- API: serve meta reliably ----
@app.get("/api/meta")
def api_meta():
    if not os.path.exists(META_PATH):
        raise HTTPException(status_code=404, detail="meta.json not found. Run training.")
    with open(META_PATH) as f:
        meta = json.load(f)
    return JSONResponse(meta)

# ---- API: History data (for charts) ----
@app.get("/api/history")
def api_history(days: int = 120):
    df = fetch_nifty(5)
    df = df.tail(days).reset_index(drop=True)
    # ensure Date column exists as datetime
    if 'Date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Convert to lists safely
    dates = df["Date"].dt.strftime("%Y-%m-%d").values.tolist() if pd.api.types.is_datetime64_any_dtype(df['Date']) else df["Date"].astype(str).values.tolist()
    opens = df["Open"].values.tolist()
    highs = df["High"].values.tolist()
    lows = df["Low"].values.tolist()
    closes = df["Close"].values.tolist()
    volumes = df["Volume"].astype(int).values.tolist()
    
    return {
        "dates": dates,
        "open": [round(float(x), 2) for x in opens],
        "high": [round(float(x), 2) for x in highs],
        "low": [round(float(x), 2) for x in lows],
        "close": [round(float(x), 2) for x in closes],
        "volume": volumes
    }

# ---- API: Next prediction (uses ensemble average) ----
@app.get("/api/next_prediction")
def api_next_prediction():
    global models
    if models is None:
        models = safe_load_models()
    if models is None:
        raise HTTPException(status_code=500, detail="Model not available. Train first.")
    df = fetch_nifty(1)
    df_feat = add_features(df)
    last_row = df_feat.tail(1).copy()
    
    # read features from meta (fallback to all columns)
    try:
        with open(META_PATH) as f:
            meta = json.load(f)
        # Convert feature list from JSON (which serializes tuples as arrays) back to strings
        feature_list = meta.get("features", [])
        feature_cols = []
        for feat in feature_list:
            if isinstance(feat, list):
                feature_cols.append(feat[0])  # Extract just the first part of the tuple
            else:
                feature_cols.append(feat)
    except Exception:
        feature_cols = [c for c in last_row.columns if c not in ['Date','Close','return'] and last_row[c].dtype in ['float64', 'float32', 'int64', 'int32']]
    
    # Flatten feature cols if they're still tuples
    feature_cols = [c[0] if isinstance(c, tuple) else c for c in feature_cols]
    
    # Get the columns from the dataframe, handling both tuple and string column names
    actual_cols = []
    for target_col in feature_cols:
        # Try to find the column
        for col in last_row.columns:
            if isinstance(col, tuple):
                if col[0] == target_col:
                    actual_cols.append(col)
                    break
            elif col == target_col:
                actual_cols.append(col)
                break
    
    X = last_row[actual_cols].copy() if actual_cols else last_row[feature_cols].copy()
    
    # Flatten column names to strings
    X.columns = [c[0] if isinstance(c, tuple) else c for c in X.columns]
    # Sanitize column names to match training
    X.columns = [str(c).replace('[', '_').replace(']', '_').replace('{', '_').replace('}', '_').replace(':', '_').replace(',', '_').replace('"', '_').replace("'", '_') for c in X.columns]
    
    prob = float(ensemble_predict(models, X)[0])
    label = "UP" if prob >= 0.5 else "DOWN"
    return {"label": label, "probability": round(prob * 100, 2)}

# ---- API: Manual predict (POST) ----
@app.post("/api/predict")
async def api_predict(request: Request):
    global models
    if models is None:
        models = safe_load_models()
    if models is None:
        raise HTTPException(status_code=500, detail="Model not available. Train first.")
    payload = await request.json()
    # payload expected: Open, High, Low, Close, Volume
    # Ensure numeric types (accept decimals) - coerce to float where possible
    for k, v in list(payload.items()):
        try:
            # preserve missing/empty as NaN
            if v is None or (isinstance(v, str) and v.strip() == ""):
                payload[k] = float('nan')
            else:
                payload[k] = float(v)
        except Exception:
            # leave as-is (pandas will coerce later and raise if unusable)
            pass
    data = pd.DataFrame([payload])
    # need some recent history to compute indicators; fetch last 60 days
    hist = fetch_nifty(2).tail(60)
    combined = pd.concat([hist, data], ignore_index=True)
    combined = add_features(combined)
    last = combined.tail(1).copy()
    
    # features
    with open(META_PATH) as f:
        meta = json.load(f)
    # meta may contain feature names serialized as lists/tuples; normalize to strings
    feature_list = meta.get("features", [])
    feature_cols = []
    try:
        for feat in feature_list:
            if isinstance(feat, list) and len(feat) > 0:
                feature_cols.append(feat[0])
            else:
                feature_cols.append(feat)
    except Exception:
        # fallback: pick numeric columns from last
        feature_cols = [c for c in last.columns if c not in ['Date','Close','return'] and last[c].dtype in ['float64', 'float32', 'int64', 'int32']]

    # Ensure feature names are strings (handle tuple columns coming from yfinance multi-index)
    feature_cols = [c[0] if isinstance(c, tuple) else c for c in feature_cols]

    # Map desired feature names to actual dataframe columns (which may be tuples or strings)
    actual_cols = []
    for target_col in feature_cols:
        for col in last.columns:
            if isinstance(col, tuple):
                if col[0] == target_col:
                    actual_cols.append(col)
                    break
            elif col == target_col:
                actual_cols.append(col)
                break

    X = last[actual_cols].copy() if actual_cols else last[feature_cols].copy()
    # Flatten column names to strings
    X.columns = [c[0] if isinstance(c, tuple) else c for c in X.columns]
    # Sanitize column names to match training
    X.columns = [str(c).replace('[', '_').replace(']', '_').replace('{', '_').replace('}', '_').replace(':', '_').replace(',', '_').replace('"', '_').replace("'", '_') for c in X.columns]
    
    prob = float(ensemble_predict(models, X)[0])
    label = "UP" if prob >= 0.5 else "DOWN"
    return JSONResponse({"label": label, "probability": round(prob * 100, 2)})

# ---- Dashboard UI route (Jinja2 template) ----
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    # Try to pass meta to template to render initial values without extra fetch
    meta_obj = {}
    if os.path.exists(META_PATH):
        with open(META_PATH) as f:
            meta_obj = json.load(f)
    return templates.TemplateResponse("dashboard.html", {"request": request, "meta": meta_obj})

# ---- Debug Dashboard UI route ----
@app.get("/debug", response_class=HTMLResponse)
def debug_dashboard(request: Request):
    return templates.TemplateResponse("dashboard_debug.html", {"request": request})

# default
from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")

