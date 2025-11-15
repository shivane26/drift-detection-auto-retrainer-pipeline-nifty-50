# 🚀 Render Deployment Guide for NIFTY50 MLOps Pipeline

## Overview

This guide walks you through deploying the MLOps pipeline to Render for production use with automated daily retraining and auto-deployment on model updates.

---

## 📋 Prerequisites

Before starting, make sure you have:

1. **GitHub Repository**: Your code is pushed to GitHub (✅ Already done)
2. **Render Account**: Free tier available at https://render.com
3. **GitHub Connection**: Ability to connect GitHub to Render
4. **SSH Keys**: Optional, but recommended for security

---

## 🔧 Step 1: Create Render Account & Connect GitHub

### 1.1 Sign Up for Render
- Go to https://render.com
- Click **Sign Up**
- Choose **GitHub** as authentication method
- Authorize Render to access your GitHub account
- Accept permissions (Render needs read access to your repos)

### 1.2 Grant Repository Access
- After authorization, you'll see your GitHub repos
- Find `drift-detection-auto-retrainer-pipeline-nifty-50`
- Click to allow Render access (optional but recommended for auto-deploy)

---

## 🌐 Step 2: Create Web Service on Render

### 2.1 Create New Web Service
- Go to https://dashboard.render.com
- Click **New +** → **Web Service**
- Select **GitHub** as the repository source
- Search for and select: `drift-detection-auto-retrainer-pipeline-nifty-50`

### 2.2 Configure Service Settings

Fill in the form with these values:

| Field | Value |
|-------|-------|
| **Name** | `nifty-mlops-api` |
| **Environment** | `Python 3` |
| **Region** | `Singapore (apac)` or `Frankfurt (eu-west)` (lowest latency) |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.app:app --host 0.0.0.0 --port 8080` |

### 2.3 Instance Settings

| Field | Value |
|-------|-------|
| **Instance Type** | `Free` (good for starting) |
| **Auto-deploy** | Toggle ON (redeploy on push) |

### 2.4 Environment Variables

Click **Add Environment Variable** and add these:

```
PYTHONUNBUFFERED = true
PORT = 8080
LOG_LEVEL = info
```

### 2.5 Health Check (Optional but Recommended)
- **Path**: `/api/meta`
- **Timeout**: 5s
- **Check Interval**: 5 minutes

---

## 💾 Step 3: Set Up Auto-Deployment on Model Updates

### 3.1 Add Deploy Hook to GitHub Actions

The workflow already writes to `app/models/` directory. Now we need to trigger Render redeployment when models update.

In your GitHub Actions workflow file (`.github/workflows/drift-detection-retrain.yml`), add a deploy trigger step:

```yaml
- name: 📢 Trigger Render Redeployment
  if: hashFiles('app/models/ensemble.pkl') != hashFiles('app/models/.previous_hash')
  run: |
    if [ -f "retrain_triggered.flag" ]; then
      curl -X POST https://api.render.com/deploy/srv-YOUR_SERVICE_ID?key=YOUR_DEPLOY_KEY
      echo "Render redeployment triggered!"
    fi
```

### 3.2 Get Your Render Deploy Key

1. Go to your service dashboard on Render
2. Click **Settings** → **API** (or look for deploy hooks)
3. Copy the **Deploy Hook URL**
4. It looks like: `https://api.render.com/deploy/srv-xxxxx?key=yyyy`

### 3.3 Add GitHub Action Secret

1. Go to GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add:
   - **Name**: `RENDER_DEPLOY_HOOK`
   - **Value**: Paste the complete URL from step 3.2

### 3.4 Update Workflow (Optional Advanced)

For now, Render's **Auto-deploy** feature will redeploy whenever you push to main branch. When the GitHub Actions workflow commits new models, it triggers auto-deploy automatically.

---

## 🔍 Step 4: Verify Deployment

### 4.1 Check Deployment Status
1. After creating the service, Render will start the initial deployment
2. Go to **Logs** tab to watch the build progress
3. Wait for: "App is live at https://YOUR_SUBDOMAIN.onrender.com"

### 4.2 Test the API Endpoints

Once deployment completes, your service will be live at a URL like:
`https://nifty-mlops-api-xxxxx.onrender.com`

Test these endpoints:

```bash
# Get model metadata
curl https://nifty-mlops-api-xxxxx.onrender.com/api/meta

# Get historical data
curl https://nifty-mlops-api-xxxxx.onrender.com/api/history

# Get next prediction
curl https://nifty-mlops-api-xxxxx.onrender.com/api/next_prediction

# View dashboard
open https://nifty-mlops-api-xxxxx.onrender.com/dashboard
```

### 4.3 Update Dashboard URL

If you have the dashboard running locally, update any hardcoded URLs to:
- Replace `http://127.0.0.1:8000` with `https://nifty-mlops-api-xxxxx.onrender.com`

---

## ⏰ Step 5: Automated Daily Retraining

Your GitHub Actions workflow is already configured to:

1. **Run daily at 4:30 PM IST** (11:00 AM UTC)
2. **Detect data drift** using Kolmogorov-Smirnov test
3. **Automatically retrain** if drift detected
4. **Commit new models** to `app/models/`
5. **Trigger Render redeployment** (via auto-deploy)
6. **New model serves predictions** within minutes

### 5.1 Monitor Retraining

Check workflow runs:
1. Go to GitHub repo → **Actions**
2. Click **drift-detection-retrain** workflow
3. Watch for daily executions
4. Green ✅ = Retraining successful
5. Red ❌ = Check logs for issues

### 5.2 Manual Retraining Trigger (Testing)

```bash
# To test the workflow immediately without waiting for schedule:
1. Go to GitHub repo → Actions
2. Click "drift-detection-retrain"
3. Click "Run workflow" → "Run workflow" button
4. Wait ~5 minutes for completion
5. Check Render logs for redeployment
```

---

## 🔐 Step 6: GitHub Actions Secrets Setup (For Render Deploy)

If you want automatic Render redeployment when models update:

### 6.1 Get Render API Credentials

1. Go to **https://dashboard.render.com/account**
2. Look for **API Key** section
3. Create or copy your API key
4. Note your Service ID (shown in service URL or settings)

### 6.2 Add to GitHub Secrets

1. Go to GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Add two secrets:

```
RENDER_API_KEY = your_api_key_here
RENDER_SERVICE_ID = srv_xxxxxxxxxxxxx
```

### 6.3 Update Workflow (If Using Secrets)

Optional: Add to `.github/workflows/drift-detection-retrain.yml`:

```yaml
- name: 🚀 Trigger Render Redeployment
  if: env.RETRAIN_TRIGGERED == 'true'
  run: |
    curl -X POST https://api.render.com/deploy/srv-${{ secrets.RENDER_SERVICE_ID }} \
      -H "Authorization: Bearer ${{ secrets.RENDER_API_KEY }}"
```

---

## 📊 Step 7: Production Monitoring

### 7.1 View Logs on Render
- Go to your service dashboard
- Click **Logs** tab
- Watch for:
  - API requests succeeding
  - Predictions being served
  - No error spikes

### 7.2 Set Up Alerts (Optional)
Render can send notifications:
1. Click **Alerts** in service settings
2. Add email for deployment failures
3. Get notified if service goes down

### 7.3 Monitor Model Performance

Your dashboard will auto-update with:
- Current AUC and Accuracy
- Last training timestamp
- Daily prediction metrics

---

## 🧪 Testing Checklist

Before going live, verify:

- [ ] Service deploys without errors
- [ ] `/api/meta` returns 200 OK with model metadata
- [ ] `/api/history` returns historical OHLCV data
- [ ] `/api/next_prediction` returns UP/DOWN prediction
- [ ] `/dashboard` loads with charts and data
- [ ] Manual prediction works with custom data
- [ ] No console errors in browser dev tools
- [ ] Logs show no Python exceptions
- [ ] Service stays alive for 5+ minutes

---

## 🐛 Troubleshooting

### Issue: "Build failed" in Render
**Solution**: Check logs for missing dependencies
```bash
# Make sure all imports in app/*.py are in requirements.txt
grep -r "^import\|^from" app/*.py | grep -v "^#"
```

### Issue: "Port 8080 already in use"
**Solution**: This shouldn't happen on Render. Check if service crashed in logs.

### Issue: "Module not found: utils"
**Solution**: Verify `app/__init__.py` exists and is empty (or has imports)

### Issue: "No data showing in dashboard"
**Solution**: 
- Check `/api/history` endpoint returns data
- Verify browser console for fetch errors
- Check Render logs for yfinance errors

### Issue: "Model retraining not triggering"
**Solution**:
1. Check GitHub Actions logs for workflow errors
2. Verify drift detection logic in `scripts/drift_detection_retrain.py`
3. Check if `retrain_triggered.flag` is being created

### Issue: "Render not redeploying after commit"
**Solution**: 
- Verify "Auto-deploy" is ON in service settings
- Check GitHub integration is authorized
- Manually trigger deployment from Render dashboard

---

## 📈 Performance Tips

### For Better Performance on Render Free Tier:

1. **Cold Start**: First request takes 10-30s (normal for free tier)
2. **Spin Down**: Service stops after 15 min inactivity (free tier only)
3. **Optimization**:
   - Upgrade to paid plan if you need <10s response times
   - Use Render's built-in caching
   - Pre-load model on startup (modify `app/app.py`)

### Pre-load Model at Startup (Optional)

Add to `app/app.py` after imports:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models at startup
    global models
    models = load_ensemble()
    yield
    # Cleanup on shutdown

app = FastAPI(lifespan=lifespan)
```

---

## 🎯 Next Steps After Deployment

1. **Monitor first 24 hours**: Check logs and API responses
2. **Wait for first daily retraining**: Watch the automated pipeline
3. **Verify model update**: Check if new metrics appear
4. **Set up monitoring**: Add alerts for errors
5. **Share dashboard**: Your public URL is ready to share!

---

## 📞 Support & Resources

- **Render Docs**: https://render.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/deployment/
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Your Service URL**: `https://nifty-mlops-api-xxxxx.onrender.com`

---

## ✅ Deployment Checklist

- [ ] Render account created and GitHub connected
- [ ] Web service created with correct settings
- [ ] Environment variables set
- [ ] Initial deployment successful
- [ ] All 4 API endpoints tested and returning 200 OK
- [ ] Dashboard displays data correctly
- [ ] GitHub Actions workflow visible on repo
- [ ] Daily retraining scheduled (4:30 PM IST)
- [ ] Render service set to auto-deploy
- [ ] Monitoring/alerts configured (optional)
- [ ] Production URL shared with stakeholders

---

**Congratulations! 🎉 Your MLOps pipeline is now live on Render!**
