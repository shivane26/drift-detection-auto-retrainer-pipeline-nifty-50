import os, json, joblib, time
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
import lightgbm as lgb
from utils import fetch_nifty, add_features, create_labels

MODEL_DIR = "app/models"
os.makedirs(MODEL_DIR, exist_ok=True)

def train_model():
    print("Fetching NIFTY50 data...")
    df = fetch_nifty(years=6)
    df_feat = add_features(df)

    # ------ NEW LABEL ------
    # 3-day forward return with +0.4% threshold
    horizon = 3
    threshold = 0.004  # 0.4%
    fut_ret = df_feat["Close"].shift(-horizon) / df_feat["Close"] - 1
    y = (fut_ret > threshold).astype(int)
    y = y[:-horizon]  # drop tail without label

    # Features
    feature_cols = [c for c in df_feat.columns if c not in ['Date','Close','return'] and df_feat[c].dtype in ['float64', 'float32', 'int64', 'int32']]
    X = df_feat[feature_cols].copy().iloc[:len(y)]
    
    # Sanitize column names for LightGBM (no special JSON characters)
    X.columns = [str(c).replace('[', '_').replace(']', '_').replace('{', '_').replace('}', '_').replace(':', '_').replace(',', '_').replace('"', '_').replace("'", '_') for c in X.columns]

    print("Training LightGBM ensemble (3-day + threshold)...")
    tscv = TimeSeriesSplit(n_splits=5)
    models = []
    oof = np.zeros(len(y))

    for fold, (tr, va) in enumerate(tscv.split(X)):
        Xtr, Xva = X.iloc[tr], X.iloc[va]
        ytr, yva = y.iloc[tr], y.iloc[va]

        train_data = lgb.Dataset(Xtr, label=ytr)
        val_data = lgb.Dataset(Xva, label=yva)

        params = {
            "objective": "binary",
            "metric": "auc",
            "learning_rate": 0.03,
            "num_leaves": 41,
            "feature_fraction": 0.85,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "seed": 42,
            "verbosity": -1
        }

        model = lgb.train(
            params,
            train_data,
            valid_sets=[val_data],
            num_boost_round=1200,
            callbacks=[
                lgb.early_stopping(stopping_rounds=80),
                lgb.log_evaluation(period=0)
            ]
        )

        preds = model.predict(Xva, num_iteration=model.best_iteration)
        oof[va] = preds
        models.append(model)

        print(f"Fold {fold} AUC:", roc_auc_score(yva, preds))

    auc = roc_auc_score(y, oof)
    acc = accuracy_score(y, (oof > 0.5).astype(int))

    print("====== FINAL METRICS ======")
    print("Final CV AUC:", auc)
    print("Final CV ACC:", acc)

    joblib.dump(models, f"{MODEL_DIR}/ensemble.pkl")
    meta = {
        "auc": float(auc),
        "accuracy": float(acc),
        "horizon_days": horizon,
        "threshold_return": threshold,
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "features": feature_cols
    }

    with open(f"{MODEL_DIR}/meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print("Saved ensemble.pkl + meta.json")
    return auc, acc

if __name__ == "__main__":
    train_model()
