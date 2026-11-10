# Cyber Raksha AI — Final Installation Guide

**Version:** B4.1 Final  
**Platform:** Windows 11 (primary), Windows 10 compatible  
**Hardware requirement:** 8 GB RAM minimum, 16 GB recommended  

---

## Prerequisites

| Component | Minimum Version | Download |
|-----------|----------------|---------|
| Python | 3.11 | https://python.org/downloads |
| Node.js | 18.0 | https://nodejs.org |
| JDK | 17 | https://adoptium.net |
| Android SDK | API 26+ | Via Android Studio |
| Chrome | 109+ | https://www.google.com/chrome |
| Git | Any recent | https://git-scm.com |

---

## 1. Clone / Extract Project

```powershell
# If cloning from repository
git clone <repository-url> cyberRaksha
cd cyberRaksha

# Or navigate to existing directory
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
```

---

## 2. Backend Setup

### 2.1 Create Virtual Environment

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

### 2.2 Environment Configuration

Create `backend/.env` with the following variables:

```env
# Application
APP_ENV=development
DEBUG=True

# Security — CHANGE THESE IN PRODUCTION
ADMIN_SECRET_KEY=your-admin-secret-key-minimum-32-characters-long
CYBER_RAKSHA_SMS_PEPPER=your-sms-pepper-minimum-32-characters-here

# Database
DATABASE_URL=sqlite:///./cyberraksha.db

# AI Engine
AI_ENGINE_PATH=../ai_engine

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

> **Important:** `ADMIN_SECRET_KEY` and `CYBER_RAKSHA_SMS_PEPPER` must each be at least 32 characters. The backend will refuse to start if they are shorter.

### 2.3 Initialize Database

```powershell
Set-Location c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
$env:PYTHONPATH = "c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha;c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\backend"
.\backend\venv\Scripts\python.exe -c "from backend.app.core.database import init_db; init_db()"
```

### 2.4 Train AI Model (First Time Only)

```powershell
Set-Location c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
$env:PYTHONPATH = "c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha"
.\backend\venv\Scripts\python.exe ai_engine/training/train_model.py
```

Expected output: `Model saved to ai_engine/models/phishing/phishing_classifier.joblib`

### 2.5 Start Backend Server

```powershell
Set-Location c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
$env:PYTHONPATH = "c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha;c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\backend"
.\backend\venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Verify:** Open http://127.0.0.1:8000/health — should return `{"status": "healthy"}`  
**API Docs:** http://127.0.0.1:8000/docs

---

## 3. Frontend Dashboard Setup

```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\frontend
npm install
npm run dev
```

**Dashboard URL:** http://localhost:5173

For production build:

```powershell
npm run build
# Output in frontend/dist/
```

---

## 4. Browser Extension Setup

1. Open Chrome → address bar → `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Navigate to: `c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\browser_extension`
5. Click **Select Folder**

The Cyber Raksha extension icon should appear in the toolbar.

**Configure backend URL:**
- Click the extension icon → Settings
- Backend URL: `http://127.0.0.1:8000`
- Save and reload the extension

---

## 5. Android Application Setup

### 5.1 Prerequisites

- Android Studio installed with Android SDK (API 26+)
- USB debugging enabled on device (or use emulator)
- JDK 17 configured

### 5.2 Build Debug APK

```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\android
.\gradlew.bat assembleDebug
```

APK location: `android/app/build/outputs/apk/debug/app-debug.apk`

### 5.3 Install on Device

```powershell
# With ADB
adb install android/app/build/outputs/apk/debug/app-debug.apk
```

Or open the APK file on the Android device directly.

### 5.4 Configure Backend URL in App

In the app settings, set the backend URL to your machine's local network IP (not `127.0.0.1` — that is the phone's own loopback):

```
http://192.168.x.x:8000
```

Replace `192.168.x.x` with your Windows machine's IP address (run `ipconfig` to find it).

---

## 6. Quick Start Script

Use the provided PowerShell startup script:

```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
.\start_cyberraksha.ps1
```

This script starts the backend server and prints connection URLs.

---

## 7. Run Tests

### Backend Tests (370 tests)

```powershell
Set-Location c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
$env:PYTHONPATH = "c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha;c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\backend"
.\backend\venv\Scripts\python.exe -m pytest backend/tests -q --tb=short
```

Expected: **370 passed**

### Browser Extension Tests (27 tests)

```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\browser_extension
node tests/test_rules_manager.js
node tests/test_notifications.js
node tests/verify_a1_deep_audit.js
```

Expected: **27 passed total**

### Android Unit Tests

```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\android
.\gradlew.bat testDebugUnitTest
```

Expected: **BUILD SUCCESSFUL**

### Frontend Build Verification

```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\frontend
npm run build
```

Expected: **Build completed successfully**

---

## 8. Health Check

```powershell
# Backend health
Invoke-WebRequest -Uri http://127.0.0.1:8000/health | Select-Object -ExpandProperty Content

# AI model status
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/v1/detection/status | Select-Object -ExpandProperty Content

# Or use the health check script
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
.\scripts\health_check.ps1
```

---

## 9. Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ADMIN_SECRET_KEY` | Yes | Admin API authentication | `change-this-in-production-32chars` |
| `CYBER_RAKSHA_SMS_PEPPER` | Yes | HMAC pepper for SMS hashing | `another-long-pepper-string-here32` |
| `APP_ENV` | No | `development` or `production` | `development` |
| `DEBUG` | No | Enable debug logging | `True` |
| `DATABASE_URL` | No | SQLAlchemy database URL | `sqlite:///./cyberraksha.db` |
| `ALLOWED_ORIGINS` | No | CORS allowed origins | `http://localhost:5173` |

---

## 10. Troubleshooting

| Problem | Solution |
|---------|----------|
| `ADMIN_SECRET_KEY must be at least 32 characters` | Update `.env` with a longer key |
| `ModuleNotFoundError: No module named 'app'` | Set `PYTHONPATH` to include both project root and `backend/` |
| Backend port 8000 already in use | `netstat -ano \| findstr :8000` then `taskkill /PID <pid> /F` |
| Extension not connecting to backend | Verify backend is running; check extension settings for correct URL |
| AI model not found | Run `.\backend\venv\Scripts\python.exe ai_engine/training/train_model.py` |
| Android build fails | Verify JDK 17 is set in `JAVA_HOME`; run `.\gradlew.bat --version` |
| `torch` not installed warning | Install with `pip install torch --index-url https://download.pytorch.org/whl/cpu` (optional) |

