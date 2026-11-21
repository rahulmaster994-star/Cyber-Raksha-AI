# Cyber Raksha AI - Deployment Guide

This guide details the deployment procedures for both the FastAPI backend (Render / Linux VPS) and the Android client application (`com.cyberraksha.ai`).

---

## 1. Backend Deployment (FastAPI on Render / Cloud VPS)

### Architecture Overview
- **Framework:** FastAPI (Python 3.11 / 3.13)
- **Database:** PostgreSQL (with SQLAlchemy 2.0 ORM)
- **Authentication:** OAuth2 JWT bearer tokens
- **Target URL:** `https://cyberraksha-backend.onrender.com`

### Deployment Steps on Render
1. **Repository Link:** Connect the GitHub repository `cyberRaksha` to Render.
2. **Build Command:**
   ```bash
   pip install --upgrade pip && pip install -r backend/requirements.txt
   ```
3. **Start Command:**
   ```bash
   cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. **Environment Variables Configuration:**
   - `DATABASE_URL`: `postgresql://user:password@hostname:5432/cyberraksha`
   - `SECRET_KEY`: `<generated-secure-256-bit-key>`
   - `ALGORITHM`: `HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: `1440`
   - `ENVIRONMENT`: `production`

### Database Migrations
On startup or deployment hook:
```bash
cd backend
alembic upgrade head
```
The SQLAlchemy models automatically ensure the following tables are created if not present:
- `keypad_family_members`
- `keypad_scam_reports`
- `keypad_scam_intelligence`
- `keypad_alerts`

---

## 2. Android APK Release Build & Signing

### Build Debug APK (For Testing / Sideloading)
```powershell
cd android
.\gradlew.bat assembleDebug
```
Output: `android/app/build/outputs/apk/debug/app-debug.apk` (Size: ~20.88 MB)

### Build Signed Release APK (For Play Store / Production Sideloading)
1. **Generate Keystore (if not already existing):**
   ```powershell
   keytool -genkey -v -keystore cyberraksha-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias cyberraksha
   ```
2. **Configure `android/key.properties`:**
   ```properties
   storePassword=yourStorePassword
   keyPassword=yourKeyPassword
   keyAlias=cyberraksha
   storeFile=../cyberraksha-release-key.jks
   ```
3. **Assemble Release APK:**
   ```powershell
   cd android
   .\gradlew.bat assembleRelease
   ```
4. **Output Location:**
   `android/app/build/outputs/apk/release/app-release.apk`

---

## 3. Web Dashboard Build & Deployment

### Vercel / Netlify Deployment
1. **Root Directory:** `frontend/`
2. **Build Command:** `npm run build`
3. **Output Directory:** `dist/`
4. **Environment Variables:**
   - `VITE_API_BASE_URL`: `https://cyberraksha-backend.onrender.com`

---

## 4. Verification & Health Check

After deployment, test the backend health and keypad endpoints:
```bash
# Check service health
curl -s https://cyberraksha-backend.onrender.com/health

# Check Keypad Helpdesk (Public Route)
curl -s https://cyberraksha-backend.onrender.com/api/v1/keypad/helpdesks

# Check Keypad Education (Public Route)
curl -s "https://cyberraksha-backend.onrender.com/api/v1/keypad/education?lang=en"
```
All should return HTTP 200 with structured JSON responses.
