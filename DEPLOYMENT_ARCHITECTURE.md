# 🏗️ DEPLOYMENT ARCHITECTURE

## Complete System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                        YOUR USERS                                   │
│                                                                     │
│  Browser → https://nifty-mlops-api-xxxxx.onrender.com/dashboard   │
│                                                                     │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             │ HTTPS
                             │
        ┌────────────────────▼──────────────────────┐
        │      🌐 RENDER (PRODUCTION)               │
        │                                           │
        │  ┌──────────────────────────────────────┐ │
        │  │  Web Service: nifty-mlops-api        │ │
        │  │  Runtime: Python 3.11                │ │
        │  │  Port: 8080                          │ │
        │  │  Region: Singapore/Frankfurt         │ │
        │  │                                      │ │
        │  │  ┌─────────────────────────────────┐ │ │
        │  │  │ FastAPI Server                  │ │ │
        │  │  │                                 │ │ │
        │  │  │  GET  /dashboard ─────────────┐ │ │
        │  │  │  GET  /api/history ──────────┐ │ │
        │  │  │  GET  /api/meta ─────────────┐ │ │
        │  │  │  GET  /api/next_prediction ──┐ │ │
        │  │  │  POST /api/predict ──────────┐ │ │
        │  │  │                             ▼ │ │
        │  │  │  ┌──────────────────────────┐ │ │
        │  │  │  │ Load Models (ensemble)   │ │ │
        │  │  │  │ Get NIFTY50 Data         │ │ │
        │  │  │  │ Generate Features        │ │ │
        │  │  │  │ Make Predictions         │ │ │
        │  │  │  └──────────────────────────┘ │ │
        │  │  └─────────────────────────────────┘ │
        │  │                                      │
        │  │  Models: app/models/ensemble.pkl    │
        │  │  Metadata: app/models/meta.json     │
        │  │                                      │
        │  └──────────────────────────────────────┘ │
        │                                           │
        └────────────┬──────────────────────────────┘
                     │
        ┌────────────▼──────────────────────────────────────┐
        │     🔄 AUTO-DEPLOYMENT (GitHub Integration)      │
        │                                                  │
        │  When models update:                            │
        │  1. Render detects commit to main branch        │
        │  2. Auto-deploy enabled                         │
        │  3. Service redeploys in 2-3 minutes            │
        │  4. New model serving predictions!              │
        │                                                  │
        └────────────┬──────────────────────────────────────┘
                     │
        ┌────────────▼──────────────────────────────────────┐
        │          📅 GITHUB ACTIONS (Daily)               │
        │                                                  │
        │  Cron: 4:30 PM IST (11:00 AM UTC)                │
        │  Workflow: drift-detection-retrain.yml           │
        │                                                  │
        │  ┌────────────────────────────────────────────┐  │
        │  │ 1. Fetch Latest NIFTY50 Data              │  │
        │  │    From: Yahoo Finance                    │  │
        │  │    Ticker: ^NSEI                          │  │
        │  │    Period: 1 year                         │  │
        │  └────────────────────────────────────────────┘  │
        │                    │                             │
        │                    ▼                             │
        │  ┌────────────────────────────────────────────┐  │
        │  │ 2. Feature Engineering                    │  │
        │  │    Generate 20 features                   │  │
        │  │    RSI, BB, EMA, MACD, Lags, etc          │  │
        │  └────────────────────────────────────────────┘  │
        │                    │                             │
        │                    ▼                             │
        │  ┌────────────────────────────────────────────┐  │
        │  │ 3. Drift Detection                        │  │
        │  │    • Kolmogorov-Smirnov Test (KS > 0.15)  │  │
        │  │    • Performance Check (AUC drop > 5%)    │  │
        │  │    • Distribution Analysis                │  │
        │  └────────────────────────────────────────────┘  │
        │                    │                             │
        │        ┌───────────┴───────────┐                │
        │        │                       │                │
        │     No Drift              Drift Detected         │
        │        │                       │                │
        │        │                       ▼                │
        │        │          ┌──────────────────────────┐  │
        │        │          │ 4. Retrain Ensemble     │  │
        │        │          │    • 5-fold CV          │  │
        │        │          │    • LightGBM models    │  │
        │        │          │    • TimeSeriesSplit    │  │
        │        │          │    • Calculate metrics  │  │
        │        │          └──────────────────────────┘  │
        │        │                       │                │
        │        │                       ▼                │
        │        │          ┌──────────────────────────┐  │
        │        │          │ 5. Save & Commit        │  │
        │        │          │    • ensemble.pkl       │  │
        │        │          │    • meta.json          │  │
        │        │          │    • Git commit         │  │
        │        │          └──────────────────────────┘  │
        │        │                       │                │
        │        └───────────┬───────────┘                │
        │                    │                             │
        │                    ▼                             │
        │       ┌──────────────────────┐                  │
        │       │ 6. Push to GitHub    │                  │
        │       │ • Triggers Render    │                  │
        │       │   auto-deploy        │                  │
        │       └──────────────────────┘                  │
        │                                                  │
        └──────────────────────────────────────────────────┘
                             │
                             │ Auto-deploy trigger
                             │
        ┌────────────────────▼──────────────────────┐
        │      🌐 RENDER (Service Redeploy)         │
        │                                           │
        │  New model now serving live predictions! │
        │  All users get updated model             │
        │  Cycle repeats tomorrow at 4:30 PM IST   │
        │                                           │
        └───────────────────────────────────────────┘
```

---

## 📊 Data Flow

### REQUEST FLOW (User → Predictions)

```
User opens dashboard
        │
        ▼
GET /dashboard
        │
        ▼
Loads HTML + JavaScript
        │
        ├─→ GET /api/history
        │       │
        │       ▼
        │   Python: fetch_nifty(years=1)
        │   Returns: [Date, Open, High, Low, Close, Volume, ...indicators]
        │       │
        │       ▼
        │   Chart.js renders price + volume charts
        │
        ├─→ GET /api/meta
        │       │
        │       ▼
        │   JSON: {auc, accuracy, features, trained_at}
        │       │
        │       ▼
        │   Display model metrics
        │
        └─→ GET /api/next_prediction
                │
                ▼
            Python: add_features(latest_data)
                │
                ▼
            LightGBM ensemble.predict()
                │
                ▼
            JSON: {label: "UP/DOWN", probability: 0-100}
                │
                ▼
            Gauge chart + arrow indicator updated
```

### RETRAINING FLOW (Daily Automation)

```
4:30 PM IST
    │
    ▼
GitHub Actions triggered
    │
    ├─→ Fetch historical NIFTY50
    │       │
    │       ▼
    │   Add features (20 engineered)
    │       │
    │       ▼
    │   KS Test (old vs new distribution)
    │   IF ks_stat > 0.15 OR auc_drop > 5%
    │       │
    │       ▼
    │   RETRAIN:
    │   • Load training data
    │   • 5-fold TimeSeriesSplit
    │   • Train LightGBM on each fold
    │   • Calculate CV metrics
    │   • Save ensemble.pkl
    │   • Save meta.json
    │   • Create retrain_triggered.flag
    │       │
    │       ▼
    │   Git commit & push
    │       │
    │       ▼
    │   Render webhook triggered
    │   Auto-deploy new model
    │       │
    │       ▼
    └─→ ✅ Done! New model live

ELSE (No drift)
    └─→ Skip retraining, try again tomorrow
```

---

## 🔄 Component Interactions

### LOCAL DEVELOPMENT
```
Your Machine (macOS)
├─ app/train.py          ← Train model locally
├─ app/app.py            ← Run FastAPI server
├─ http://127.0.0.1:8000 ← Test dashboard
└─ app/models/           ← Store models
```

### GITHUB REPOSITORY
```
GitHub (shivane26/...)
├─ app/                  ← Source code
├─ templates/            ← HTML templates
├─ scripts/              ← Automation scripts
├─ .github/workflows/    ← GitHub Actions
├─ render.yaml           ← Render config
└─ requirements.txt      ← Dependencies
```

### RENDER PRODUCTION
```
Render Service
├─ Pull from GitHub (auto on push)
├─ pip install -r requirements.txt
├─ uvicorn app.app:app --host 0.0.0.0 --port 8080
├─ Load models/ensemble.pkl
└─ Serve on https://nifty-mlops-api-xxxxx.onrender.com
```

### GITHUB ACTIONS SCHEDULER
```
Daily Cron Job (11:00 AM UTC)
├─ Setup Python 3.11
├─ pip install -r requirements.txt
├─ python scripts/drift_detection_retrain.py
│  ├─ Fetch data from Yahoo Finance
│  ├─ Calculate drift metrics
│  └─ IF drift detected → retrain → commit
├─ Git push to main branch
└─ Webhook → Render (auto-deploy)
```

---

## 🚀 DEPLOYMENT TIMELINE

### Week 1: Initial Deployment
```
Day 1:
├─ 9:00 AM - Create Render account
├─ 9:10 AM - Connect GitHub
├─ 9:20 AM - Create web service
├─ 9:30 AM - Deploy (3-5 min)
└─ 9:35 AM ✅ LIVE!

Day 2-7: Monitor & Validate
├─ Check logs for errors
├─ Test all API endpoints
├─ Verify dashboard loads
└─ Confirm auto-deploy working
```

### Week 2+: Automated Operation
```
Daily (4:30 PM IST):
├─ GitHub Actions runs
├─ Drift detection executes
├─ IF drift: retrain & commit
├─ Render auto-deploys
└─ Dashboard updates with new model

You focus on: Monitoring logs & metrics
System handles: Everything else!
```

---

## 📈 COST ESTIMATE (Render)

| Service | Free Tier | Pro Tier |
|---------|-----------|----------|
| Web Service | ✅ Included | $7/month |
| Monthly uptime | 750 hrs (~50%) | 100% |
| Cold starts | Yes (30s) | No |
| Sleep period | After 15 min idle | Never |
| Data transfer | 100 GB | Paid |
| **For this project** | ✅ Sufficient | Better performance |

**Recommendation**: Start free, upgrade to Pro after 1 month if needed.

---

## ✅ SUCCESS CRITERIA

After deployment, you should see:

- [x] Dashboard loads at service URL
- [x] API endpoints return 200 OK
- [x] Price charts display real NIFTY50 data
- [x] Next prediction shows UP/DOWN label
- [x] Model metrics display AUC and Accuracy
- [x] Logs show no Python errors
- [x] GitHub Actions runs daily (visible in Actions tab)
- [x] Retraining commits appear when drift detected
- [x] Render auto-redeploys on commits
- [x] New predictions reflect retrained model

**When all checks pass → Production ready! 🎉**

---

## 🔗 IMPORTANT URLS

After deployment, bookmark these:

```
Dashboard:     https://nifty-mlops-api-xxxxx.onrender.com/dashboard
API Docs:      https://nifty-mlops-api-xxxxx.onrender.com/docs
Service Logs:  https://dashboard.render.com (click service)
GitHub Actions: https://github.com/shivane26/.../actions
Render Dash:   https://dashboard.render.com
```

---

**Status**: Ready to deploy 🚀
**Estimated Time**: 5-10 minutes
**Support**: See RENDER_DEPLOYMENT.md for troubleshooting
