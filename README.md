# 🚀 Automated Drift Detection & Auto-Retraining Pipeline for NIFTY 50 (MLOps)

## 📊 Architecture

```
                    +--------------------+
                    |   yfinance (^NSEI) |
                    +---------+----------+
                              |
                              v
                       Daily data fetch
                              |
                              v
                    +---------------------+
                    | feature generation  |
                    +---------------------+
                              |
                              v
                    +---------------------+
                    | Drift detection     |
                    | (Kolmogorov-Smirnov)|
                    +----+----------------+
                         |      |
                    No   |      | Yes (drift detected)
                         v      v
                  Use current model    Retrain triggers
                  (FastAPI/Render)     retrain.py
                         |              |
                         |              v
                         |        Train 5-fold ensemble
                         |              |
                         |              v
                         |        Save new models.pkl
                         |              |
                         |              v
                         |        Commit to GitHub
                         |              |
                         |              v
                         +---> Auto-deploy on Render
                                       |
                                       v
                              New predictions live!
```

## 📋 Project Overview

- **Model**: LightGBM 5-fold ensemble for NIFTY50 return prediction
- **Target**: 3-day forward return (UP if >0.4%, DOWN otherwise)
- **Features**: 20 engineered features (RSI, Bollinger Bands, EMA, MACD, lags, etc.)
- **Drift Detection**: Kolmogorov-Smirnov statistical test + performance monitoring
- **Automation**: Daily scheduled GitHub Actions workflow
- **Deployment**: FastAPI on Render with auto-deploy on model updates
- **Dashboard**: Interactive neon-themed UI with real-time charts

## ⚡ Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/shivane26/drift-detection-auto-retrainer-pipeline-nifty-50
cd drift-detection-auto-retrainer-pipeline-nifty-50

# Run setup script
chmod +x run_local.sh
./run_local.sh
```

Server will start at `http://127.0.0.1:8000/dashboard`

### Production Deployment on Render

See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) for complete step-by-step instructions.

**Quick Summary**:
1. Create account on Render.com
2. Connect GitHub repository
3. Create Web Service with `render.yaml`
4. Auto-deploy enabled
5. Done! Daily retraining + deployment happens automatically

## 📁 Project Structure

```
drift-detection-auto-retrainer-pipeline-nifty-50/
├── app/
│   ├── __init__.py
│   ├── app.py                 # FastAPI routes
│   ├── train.py               # Model training pipeline
│   ├── utils.py               # Data fetching & features
│   ├── model_predict.py       # Inference functions
│   └── models/
│       ├── ensemble.pkl       # Trained LightGBM ensemble
│       └── meta.json          # Model metadata
├── templates/
│   ├── dashboard.html         # Main interactive dashboard
│   └── dashboard_debug.html   # Debug view
├── scripts/
│   └── drift_detection_retrain.py  # Automated retraining
├── .github/workflows/
│   └── drift-detection-retrain.yml # GitHub Actions schedule
├── render.yaml                # Render deployment config
├── requirements.txt           # Python dependencies
├── RENDER_DEPLOYMENT.md       # Deployment guide
└── README.md                  # This file
```

## 🔧 Configuration

### Model Hyperparameters (app/train.py)
- **Learning Rate**: 0.03
- **Num Leaves**: 41
- **Feature Fraction**: 0.85
- **Bagging Fraction**: 0.8
- **Early Stopping**: 80 rounds

### Feature Engineering (app/utils.py)
- **Lag features**: ret_lag_1, 2, 3, 5, 7 (returns)
- **Moving averages**: sma_5, sma_10, sma_20
- **Exponential MA**: ema_12, ema_26
- **MACD**: macd, signal_line
- **Volatility**: vol_10
- **RSI**: rsi_14 (custom)
- **Bollinger Bands**: bb_width

### Drift Detection (scripts/drift_detection_retrain.py)
- **KS Threshold**: 0.15 (distribution shift)
- **Performance Drop**: 5% AUC reduction
- **Retraining**: 5-fold cross-validation

### Scheduling (.github/workflows/drift-detection-retrain.yml)
- **Frequency**: Daily at 4:30 PM IST (11:00 AM UTC)
- **Trigger**: Cron schedule (can also manual trigger)
- **Action**: Drift check → Conditional retrain → Auto-commit → Deploy

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboard` | GET | Interactive dashboard UI |
| `/api/history` | GET | Last 120 days OHLCV + indicators |
| `/api/meta` | GET | Model metadata (AUC, accuracy, features) |
| `/api/next_prediction` | GET | UP/DOWN prediction for next 3 days |
| `/api/predict` | POST | Custom prediction with OHLCV data |
| `/docs` | GET | FastAPI Swagger documentation |

## 📈 Dashboard Features

- **Price Chart**: Close price + 20-day SMA
- **Volume Chart**: Trading volume bars
- **Prediction Gauge**: Confidence % (UP/DOWN)
- **Model Info**: AUC, Accuracy, Training timestamp
- **Manual Prediction**: Input custom OHLCV to get predictions

## 🤖 Automated Workflow

### Daily Execution (4:30 PM IST)

1. **Fetch Data**: Last 1 year of NIFTY50 data from Yahoo Finance
2. **Feature Engineering**: Generate 20 features from OHLCV
3. **Drift Detection**:
   - Kolmogorov-Smirnov test on distributions
   - Performance evaluation on recent data
4. **Decision**:
   - No drift → Use current model
   - Drift detected → Trigger retraining
5. **Retraining** (if needed):
   - Train 5-fold ensemble
   - Calculate new metrics
   - Save model artifacts
6. **Deployment**:
   - Commit new models to GitHub
   - Render auto-deploys new model
   - New predictions served within minutes

## 📊 Model Performance

- **CV AUC**: 0.533
- **CV Accuracy**: 0.535
- **Validation**: 5-fold TimeSeriesSplit (preserves temporal order)
- **Latest Training**: See `/api/meta` for timestamp

## 🔐 Production Checklist

- [x] Model training pipeline (LightGBM 5-fold ensemble)
- [x] FastAPI backend with 4 REST endpoints
- [x] Interactive dashboard UI
- [x] Drift detection algorithm (KS test + performance monitoring)
- [x] Automated retraining script
- [x] GitHub Actions daily schedule
- [x] Render deployment configuration
- [x] Auto-deploy on model updates
- [ ] **TODO**: Deploy to Render (follow [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md))

## 🚀 Deployment Status

**Local Development**: ✅ Complete
- All APIs tested and working
- Dashboard displays real data
- Model serving predictions

**GitHub Repository**: ✅ Complete
- All code committed and pushed
- Workflow configured for daily runs
- Ready for Render deployment

**Production (Render)**: ⏳ Pending
- Follow the [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) guide
- Expected deployment time: 5-10 minutes
- Auto-retraining starts next day

## 🔍 Monitoring

### View Logs Locally
```bash
# Watch API logs
tail -f /var/log/nifty-api.log

# Check model training logs
python app/train.py
```

### View Logs on Render
1. Go to service dashboard
2. Click **Logs** tab
3. Watch for deployment progress and errors

### GitHub Actions Monitoring
1. Go to repo → **Actions** tab
2. Click **drift-detection-retrain** workflow
3. View daily executions and logs

## 🛠️ Troubleshooting

### Issue: "No data showing in dashboard"
**Solution**: Check `/api/history` endpoint directly
```bash
curl http://localhost:8000/api/history | head -50
```

### Issue: "Model not training"
**Solution**: Check if data is being fetched
```bash
python3 -c "from app.utils import fetch_nifty; print(fetch_nifty().head())"
```

### Issue: "Render deployment failed"
**Solution**: Check Render logs for Python errors
- Missing dependencies? Update requirements.txt
- Wrong port? Check render.yaml uses 8080
- Memory issue? Upgrade to paid plan

### Issue: "Workflow not running"
**Solution**: 
- Verify GitHub Actions enabled in repo settings
- Check workflow YAML syntax
- Manually trigger from **Actions** tab

## 📚 Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **LightGBM Docs**: https://lightgbm.readthedocs.io/
- **Render Docs**: https://render.com/docs
- **GitHub Actions**: https://docs.github.com/en/actions
- **Chart.js**: https://www.chartjs.org/

## 📝 License

This project is open source and available for educational and commercial use.

---

**Last Updated**: November 15, 2025
**Status**: Ready for Render deployment 🚀
