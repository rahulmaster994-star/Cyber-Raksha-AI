# Cyber Raksha AI — Free Cloud Deployment Guide

**Version:** 1.0  
**Target:** 100% Zero-Cost Production Hosting  
**Architecture:** Decoupled Cloud API + Edge CDN Frontend  

---

## 1. Free Cloud Hosting Architecture

```
+--------------------------+          HTTPS           +--------------------------+
|  Frontend Dashboard      | -----------------------> |  Backend API & AI Engine |
|  Hosted on: Vercel /     |                          |  Hosted on: Render /     |
|  Netlify (Free Tier)     |                          |  HuggingFace Spaces      |
+--------------------------+                          +--------------------------+
                                                                   |
                                                                   | SQLAlchemy /
                                                                   | PostgreSQL
                                                                   v
                                                      +--------------------------+
                                                      |  Persistent Database     |
                                                      |  Hosted on: Neon.tech /  |
                                                      |  Supabase (Free 500MB)   |
                                                      +--------------------------+
```

---

## 2. Evaluation of Genuinely Free Hosting Providers

| Provider | Component | Free Tier Specifications | Credit Card Required? | Sleep / Idle Behavior | Verdict |
|---|---|---|:---:|---|:---:|
| **Vercel** | Frontend (Vite/React) | 100 GB bandwidth, unlimited deployments, custom domain | **NO** | Instant edge CDN response (no sleep) | **RECOMMENDED FOR FRONTEND** |
| **Render** | Backend (FastAPI) | 512 MB RAM, 0.1 CPU, free HTTPS, automatic Git deploy | **NO** | Spins down after 15m inactivity (cold start ~30s) | **RECOMMENDED FOR BACKEND** |
| **Hugging Face Spaces** | Backend (Docker) | 2 vCPU, 16 GB RAM, persistent container | **NO** | Remains active, exceptional memory for ML models | **ALTERNATIVE FOR BACKEND** |
| **Neon.tech** | PostgreSQL Database | 0.5 GB storage, serverless autoscaling, pooled connections | **NO** | Instant serverless resume (< 500ms) | **RECOMMENDED FOR DATABASE** |
| **Supabase** | PostgreSQL Database | 500 MB storage, free SSL, connection pooling | **NO** | Pauses after 1 week inactivity | Good alternative |
| **Railway** | Full Stack | $5 trial credits | No, but trial expires | Not permanent | Limited |
| **Fly.io** | Backend | Free allowance | **YES** (Requires CC) | Does not meet zero-card requirement | Disqualified |

---

## 3. Step-by-Step Deployment Instructions

### Step 1: Deploy Database (Neon.tech — Free Forever)
1. Sign up at [neon.tech](https://neon.tech) (Log in with GitHub, no credit card required).
2. Click **Create Project** $\rightarrow$ Name: `cyberraksha-db`.
3. Copy the provided connection string:
   ```text
   postgresql://user:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Update `DATABASE_URL` in your environment to point to this connection string.

### Step 2: Deploy Backend to Render.com (Free Web Service)
1. Fork or push the Cyber Raksha AI repository to your GitHub account.
2. Sign up at [render.com](https://render.com) using your GitHub account.
3. Click **New +** $\rightarrow$ **Web Service**.
4. Connect your `cyberRaksha` repository.
5. Configure the service settings:
   - **Name:** `cyberraksha-api`
   - **Region:** Nearest region (e.g. Frankfurt, Singapore, Oregon)
   - **Branch:** `main`
   - **Root Directory:** Leave empty (or use `.` to use root Dockerfile)
   - **Runtime:** `Docker` (or `Python 3`)
   - **Build Command:** `pip install -r backend/requirements.txt && python ai_engine/training/train_model.py`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port 10000`
   - **Instance Type:** `Free`
6. Add Environment Variables under **Advanced**:
   - `APP_ENV` = `production`
   - `DEBUG` = `False`
   - `ADMIN_SECRET_KEY` = `(generate 32+ random characters)`
   - `CYBER_RAKSHA_SMS_PEPPER` = `(generate 32+ random characters)`
   - `DATABASE_URL` = `(your Neon PostgreSQL connection string or leave blank for local SQLite)`
   - `ALLOWED_ORIGINS` = `https://your-frontend.vercel.app`
7. Click **Create Web Service**. Render will provision your service at `https://cyberraksha-api.onrender.com`.

### Step 3: Deploy Frontend to Vercel (Free Edge CDN)
1. Sign up at [vercel.com](https://vercel.com) using your GitHub account.
2. Click **Add New...** $\rightarrow$ **Project**.
3. Select your `cyberRaksha` repository.
4. Configure Project:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Add Environment Variable:
   - `VITE_API_BASE_URL` = `https://cyberraksha-api.onrender.com`
6. Click **Deploy**. Your dashboard will be live at `https://cyberraksha.vercel.app`.

### Step 4: Configure Chrome Extension for Production
1. Open `browser_extension/popup/popup.js` or extension settings.
2. Update the backend URL setting from `http://127.0.0.1:8000` to `https://cyberraksha-api.onrender.com`.
3. Reload the extension in Chrome.

### Step 5: Configure Android Application for Production
1. In `android/app/src/main/kotlin/com/cyberraksha/ai/data/remote/NetworkModule.kt`, change the base URL from local dev to:
   ```kotlin
   private const val BASE_URL = "https://cyberraksha-api.onrender.com/"
   ```
2. Build release APK:
   ```powershell
   cd android
   .\gradlew.bat assembleRelease
   ```

---

## 4. Live Verification Checklist

Once deployed, verify using the following endpoints:
1. `GET https://cyberraksha-api.onrender.com/health` $\rightarrow$ `{"status": "healthy"}`
2. `GET https://cyberraksha-api.onrender.com/api/v1/detection/status` $\rightarrow$ `{"model_loaded": true}`
3. Open `https://cyberraksha.vercel.app` in your browser to verify dashboard telemetry and live event stream.

