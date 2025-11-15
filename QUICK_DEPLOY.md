## 🚀 RENDER DEPLOYMENT - QUICK START (5 STEPS)

### ⏱️ Estimated Time: 5-10 minutes

---

## STEP 1️⃣: CREATE RENDER ACCOUNT

1. Go to **https://render.com**
2. Click **Sign Up**
3. Choose **GitHub** authentication
4. Authorize Render to access your GitHub
5. Done! ✅

---

## STEP 2️⃣: CREATE WEB SERVICE

1. Go to **https://dashboard.render.com**
2. Click **New +** → **Web Service**
3. Select **GitHub** as repository source
4. Search and select: `drift-detection-auto-retrainer-pipeline-nifty-50`

---

## STEP 3️⃣: CONFIGURE SERVICE

Fill in these fields:

| Field | Value |
|-------|-------|
| **Name** | `nifty-mlops-api` |
| **Environment** | `Python 3` |
| **Region** | `Singapore` or `Frankfurt` |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.app:app --host 0.0.0.0 --port 8080` |

---

## STEP 4️⃣: ADD ENVIRONMENT VARIABLES

Click **Add Environment Variable** three times:

```
PYTHONUNBUFFERED = true
PORT = 8080
LOG_LEVEL = info
```

---

## STEP 5️⃣: ENABLE AUTO-DEPLOY & LAUNCH

1. Toggle **Auto-deploy** = ON
2. Scroll down and click **Create Web Service**
3. Wait 3-5 minutes for deployment
4. You'll see: "App is live at https://nifty-mlops-api-xxxxx.onrender.com" ✅

---

## ✅ VERIFY DEPLOYMENT

Once live, test these URLs:

### Dashboard (See predictions!)
```
https://nifty-mlops-api-xxxxx.onrender.com/dashboard
```

### API Health Check
```
https://nifty-mlops-api-xxxxx.onrender.com/api/meta
```

### Next Prediction
```
https://nifty-mlops-api-xxxxx.onrender.com/api/next_prediction
```

### Price History
```
https://nifty-mlops-api-xxxxx.onrender.com/api/history
```

---

## 🤖 AUTOMATIC DAILY RETRAINING

Your GitHub Actions workflow will:
- ✅ Run every day at 4:30 PM IST
- ✅ Check for data drift
- ✅ Retrain model if drift detected
- ✅ Automatically commit new model
- ✅ Render auto-deploys new model!

**No manual intervention needed!** 🎉

---

## 📊 MONITORING

### Check Deployment Logs
1. Go to your service on Render
2. Click **Logs** tab
3. Watch for successful startup

### Check Daily Retraining
1. Go to GitHub repo → **Actions** tab
2. Click **drift-detection-retrain** workflow
3. See daily execution history

---

## 🎯 YOU'RE DONE! 

Your MLOps pipeline is now live and will:

1. **Serve predictions** 24/7 on Render
2. **Retrain daily** via GitHub Actions
3. **Auto-deploy** when models update
4. **Monitor drift** with Kolmogorov-Smirnov test
5. **Display analytics** on interactive dashboard

---

## 📞 NEED HELP?

- **Render won't deploy?** → Check logs tab, verify render.yaml syntax
- **API returning errors?** → Check if app/models/ensemble.pkl exists
- **Dashboard not loading?** → Check browser console (F12)
- **Workflow not running?** → Verify GitHub Actions enabled in Settings

---

**Full detailed guide available in:** `RENDER_DEPLOYMENT.md`

**Render Dashboard:** https://dashboard.render.com

**Your Service URL:** `https://nifty-mlops-api-xxxxx.onrender.com`

🚀 **Happy Deploying!**
