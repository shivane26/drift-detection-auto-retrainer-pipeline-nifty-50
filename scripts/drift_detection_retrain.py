"""
Drift Detection & Automated Retraining Script
==============================================

This script runs daily to:
1. Fetch the latest NIFTY50 data
2. Compare current model performance against baseline
3. Detect data distribution drift using statistical tests
4. Automatically retrain the model if drift is detected
5. Create a flag file to trigger GitHub Actions deployment

Drift Detection Methods:
- Kolmogorov-Smirnov test on feature distributions
- Model performance degradation on recent data
- Data distribution shift analysis
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy import stats
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
import lightgbm as lgb

# Add app to path
sys.path.insert(0, 'app')
from utils import fetch_nifty, add_features, create_labels
from model_predict import load_ensemble, ensemble_predict

# Configuration
MODEL_DIR = "app/models"
META_PATH = os.path.join(MODEL_DIR, "meta.json")
ENSEMBLE_PATH = os.path.join(MODEL_DIR, "ensemble.pkl")
DRIFT_THRESHOLD_KS = 0.15  # KS statistic threshold for drift detection
DRIFT_THRESHOLD_PERFORMANCE = 0.05  # AUC drop tolerance (5%)
MIN_SAMPLES_FOR_DRIFT_CHECK = 50

print("=" * 70)
print("🔍 DRIFT DETECTION & AUTOMATED RETRAINING PIPELINE")
print("=" * 70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Step 1: Load existing model and metadata
print("📦 Loading existing model...")
try:
    models = load_ensemble()
    with open(META_PATH, 'r') as f:
        meta = json.load(f)
    baseline_auc = meta.get('auc', 0.5)
    baseline_accuracy = meta.get('accuracy', 0.5)
    print(f"   Baseline AUC: {baseline_auc:.4f}")
    print(f"   Baseline Accuracy: {baseline_accuracy:.4f}")
    print(f"   Last trained: {meta.get('trained_at', 'Unknown')}\n")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

# Step 2: Fetch fresh data
print("📊 Fetching latest NIFTY50 data...")
try:
    df_new = fetch_nifty(years=1)  # Get 1 year of data
    print(f"   Total records fetched: {len(df_new)}")
    print(f"   Date range: {df_new['Date'].min()} to {df_new['Date'].max()}\n")
except Exception as e:
    print(f"❌ Failed to fetch data: {e}")
    sys.exit(1)

# Step 3: Add features
print("✨ Engineering features...")
try:
    df_feat = add_features(df_new)
    print(f"   Feature set size: {df_feat.shape[1]} features")
    print(f"   Data points after feature engineering: {len(df_feat)}\n")
except Exception as e:
    print(f"❌ Failed to engineer features: {e}")
    sys.exit(1)

# Step 4: Drift Detection - Statistical Tests
print("🔬 Running drift detection analysis...")
drift_detected = False
drift_reasons = []

# Get feature columns from metadata
try:
    feature_list = meta.get("features", [])
    feature_cols = []
    for feat in feature_list:
        if isinstance(feat, list):
            feature_cols.append(feat[0])
        else:
            feature_cols.append(feat)
    feature_cols = [c for c in feature_cols if c in df_feat.columns]
    print(f"   Analyzing {len(feature_cols)} features for drift...")
except Exception as e:
    print(f"   ⚠️  Could not load feature list, using all numeric columns")
    feature_cols = [c for c in df_feat.columns if c not in ['Date','Close','return'] and df_feat[c].dtype in ['float64', 'float32', 'int64', 'int32']]

# Kolmogorov-Smirnov Test for distribution shift
ks_max = 0
for col in feature_cols[:10]:  # Test first 10 features for speed
    try:
        mid_point = len(df_feat) // 2
        old_data = df_feat[col].iloc[:mid_point].dropna()
        new_data = df_feat[col].iloc[mid_point:].dropna()
        
        if len(old_data) > 10 and len(new_data) > 10:
            ks_stat, p_value = stats.ks_2samp(old_data, new_data)
            ks_max = max(ks_max, ks_stat)
            if ks_stat > DRIFT_THRESHOLD_KS:
                drift_reasons.append(f"KS test on {col}: {ks_stat:.4f} > {DRIFT_THRESHOLD_KS}")
    except:
        pass

if ks_max > DRIFT_THRESHOLD_KS:
    drift_detected = True
    print(f"   ⚠️  DRIFT DETECTED: Max KS statistic = {ks_max:.4f}")

# Step 5: Model Performance on Recent Data
print("\n📈 Evaluating model performance on recent data...")
try:
    # Create labels and features for recent data (last 120 days)
    horizon = meta.get('horizon_days', 3)
    threshold = meta.get('threshold_return', 0.004)
    
    fut_ret = df_feat["Close"].shift(-horizon) / df_feat["Close"] - 1
    y_test = (fut_ret > threshold).astype(int)
    y_test = y_test[:-horizon]
    
    X_test = df_feat[feature_cols].iloc[:len(y_test)].copy()
    X_test.columns = [str(c).replace('[', '_').replace(']', '_').replace('{', '_').replace('}', '_').replace(':', '_').replace(',', '_').replace('"', '_').replace("'", '_') for c in X_test.columns]
    
    # Test on last 25% of data
    test_size = max(MIN_SAMPLES_FOR_DRIFT_CHECK, len(X_test) // 4)
    X_recent = X_test.iloc[-test_size:]
    y_recent = y_test.iloc[-test_size:]
    
    recent_preds = np.array([m.predict(X_recent) for m in models]).mean(axis=0)
    recent_auc = roc_auc_score(y_recent, recent_preds)
    recent_acc = accuracy_score(y_recent, (recent_preds > 0.5).astype(int))
    
    print(f"   Recent AUC: {recent_auc:.4f} (Baseline: {baseline_auc:.4f})")
    print(f"   Recent Accuracy: {recent_acc:.4f} (Baseline: {baseline_accuracy:.4f})")
    
    auc_drop = baseline_auc - recent_auc
    if auc_drop > DRIFT_THRESHOLD_PERFORMANCE:
        drift_detected = True
        drift_reasons.append(f"Performance drop: AUC decreased by {auc_drop:.4f}")
        print(f"   ⚠️  DRIFT DETECTED: AUC drop of {auc_drop:.4f} exceeds threshold {DRIFT_THRESHOLD_PERFORMANCE}")
        
except Exception as e:
    print(f"   ⚠️  Could not evaluate performance: {e}")

# Step 6: Decision - Retrain or Not
print("\n" + "=" * 70)
if drift_detected:
    print("🚨 DRIFT DETECTED - INITIATING RETRAINING")
    print("=" * 70)
    for reason in drift_reasons:
        print(f"   • {reason}")
    print()
    
    print("🔄 Starting model retraining...")
    try:
        # Prepare data
        X = df_feat[feature_cols].copy()
        X.columns = [str(c).replace('[', '_').replace(']', '_').replace('{', '_').replace('}', '_').replace(':', '_').replace(',', '_').replace('"', '_').replace("'", '_') for c in X.columns]
        y = create_labels(df_feat, horizon=horizon)
        X = X.iloc[:len(y)]
        
        # Retrain ensemble
        tscv = TimeSeriesSplit(n_splits=5)
        new_models = []
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
            new_models.append(model)
            fold_auc = roc_auc_score(yva, preds)
            print(f"   Fold {fold} AUC: {fold_auc:.4f}")
        
        # Evaluate
        new_auc = roc_auc_score(y, oof)
        new_acc = accuracy_score(y, (oof > 0.5).astype(int))
        
        print(f"\n   ✅ Retraining Complete!")
        print(f"   New CV AUC: {new_auc:.4f} (Previous: {baseline_auc:.4f})")
        print(f"   New CV Accuracy: {new_acc:.4f} (Previous: {baseline_accuracy:.4f})")
        
        # Save new models
        joblib.dump(new_models, ENSEMBLE_PATH)
        new_meta = {
            "auc": float(new_auc),
            "accuracy": float(new_acc),
            "horizon_days": horizon,
            "threshold_return": threshold,
            "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "features": [[c, ""] if isinstance(c, str) else c for c in feature_cols],
            "retrain_reason": "; ".join(drift_reasons),
            "previous_auc": float(baseline_auc),
            "previous_accuracy": float(baseline_accuracy)
        }
        
        with open(META_PATH, 'w') as f:
            json.dump(new_meta, f, indent=2)
        
        print(f"\n   💾 Model artifacts saved to {MODEL_DIR}/")
        
        # Create flag for GitHub Actions
        with open("retrain_triggered.flag", "w") as f:
            f.write(f"Retraining completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Drift reasons: {', '.join(drift_reasons)}\n")
            f.write(f"AUC improvement: {new_auc - baseline_auc:.4f}\n")
        
        print("\n🎯 Retraining SUCCESS - artifacts ready for deployment")
        
    except Exception as e:
        print(f"❌ Retraining FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

else:
    print("✅ NO DRIFT DETECTED")
    print("=" * 70)
    print("   Model is performing within acceptable parameters")
    print("   No retraining needed at this time")
    print("   Next check: Tomorrow at scheduled time")

print("\n" + "=" * 70)
print("Pipeline execution completed successfully")
print("=" * 70)
