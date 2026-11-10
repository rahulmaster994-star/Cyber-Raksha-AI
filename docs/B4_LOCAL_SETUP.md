# Cyber Raksha AI — Local Environment Setup & Execution Guide

This document provides instructions for running, testing, and developing Cyber Raksha AI locally on standard laptop hardware (16 GB RAM, CPU-only execution).

---

## 1. Prerequisites

- **Python**: 3.11 - 3.13 (Virtual environment in `backend/venv`)
- **Node.js**: v18+ & npm (for browser extension tests and Vite dashboard)
- **Java / JDK**: 17+ (for Android Gradle builds)
- **Git**: Standard installation

---

## 2. Backend Setup & Test Execution

### Activate Virtual Environment
```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
.\backend\venv\Scripts\Activate.ps1
```

### Configure Environment Variables
Create or verify `.env` file in root or `backend/`:
```env
CYBER_RAKSHA_SMS_PEPPER=cyber_raksha_local_pepper_minimum_32_chars_long_key_2026
ADMIN_SECRET_KEY=cyber_raksha_admin_secret_minimum_32_characters_key_2026
APP_ENV=development
DEBUG=True
DATABASE_URL=sqlite:///./cyber_raksha.db
```

### Run the Full Backend Regression Suite (360 Tests)
```powershell
$env:PYTHONPATH="c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha;c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\backend"
.\backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

### Run Only B4 Intelligent Detection Tests (19 Tests)
```powershell
$env:PYTHONPATH="c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha;c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\backend"
.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_stage22_b4_intelligent_detection.py -v
```

### Start the FastAPI Backend Server
```powershell
$env:PYTHONPATH="c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha;c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\backend"
.\backend\venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```
Swagger API Documentation will be accessible at: `http://127.0.0.1:8000/docs`

---

## 3. Browser Extension Tests & Loading

### Run Extension Test Suite (27 Tests)
```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\browser_extension
node tests/test_rules_manager.js
node tests/test_notifications.js
node tests/verify_a1_deep_audit.js
```

### Load in Google Chrome / Chromium
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** toggle in the top-right.
3. Click **Load unpacked** and select the folder:
   `c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\browser_extension`

---

## 4. Native Android App Testing & Compilation

### Run Android Unit Tests
```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\android
.\gradlew.bat testDebugUnitTest
```

### Assemble Debug APK
```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\android
.\gradlew.bat assembleDebug
```
Output APK is generated at:
`android/app/build/outputs/apk/debug/app-debug.apk`

---

## 5. React Dashboard (Frontend)

### Install Dependencies & Run Development Server
```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\frontend
npm install
npm run dev
```
Dashboard will be accessible at: `http://localhost:5173/`

### Build Production Bundle
```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\frontend
npm run build
```
Compiled production assets are output to `frontend/dist/`.

---

## 6. Model Retraining (Optional)

If updating benchmark datasets or retraining the local phishing classifier:
```powershell
$env:PYTHONPATH="c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha"
.\backend\venv\Scripts\python.exe ai_engine/training/train_phishing.py
```
This retrains `phishing_classifier.joblib` and updates `model_metadata.json` automatically.

