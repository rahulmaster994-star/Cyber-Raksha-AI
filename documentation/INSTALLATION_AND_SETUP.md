# Cyber Raksha AI — Installation & Setup Guide

This guide describes how to set up, configure, and verify **Cyber Raksha AI** on a local development workstation.

---

## 1. System Requirements

- **Operating System:** Windows 10/11, Ubuntu 22.04+, or macOS
- **Python:** Version 3.13 (Python 3.10+ supported)
- **Node.js:** Version 18.0+ with `npm`
- **RAM:** Minimum 4 GB (8 GB recommended)
- **Disk Space:** Approximately 1.5 GB for dependencies and pre-trained model weights

---

## 2. Step-by-Step Installation

### Step 1: Clone or Navigate to Repository
```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
```

### Step 2: Set Up Python Backend Environment
Ensure the virtual environment is present and configured:
```powershell
# Create venv if not already created
python -m venv backend\venv

# Activate venv
.\backend\venv\Scripts\Activate.ps1

# Install core dependencies
pip install -r backend\requirements.txt
```

Verified dependencies in `backend/requirements.txt`:
```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.9.0
pydantic-settings>=2.5.0
sqlalchemy>=2.0.35
pytest>=8.3.0
httpx>=0.27.0
python-dotenv>=1.0.1
scikit-learn>=1.5.0
pandas>=2.2.0
numpy>=1.26.0
joblib>=1.4.0
scipy>=1.13.0
```

### Step 3: Set Up Frontend Environment
```powershell
cd frontend
npm install
cd ..
```

---

## 3. Configuration & Environment Variables

Copy the example configuration to `.env` if not present:
```powershell
Copy-Item backend\.env.example backend\.env
```

Key environment settings in `backend/.env`:
```ini
APP_NAME="Cyber Raksha AI"
APP_ENV=development
DEBUG=True
HOST=127.0.0.1
PORT=8000
DATABASE_URL=sqlite:///./cyber_raksha.db
RATE_LIMIT_PER_MINUTE=120
ADMIN_SECRET_KEY=cyber-raksha-admin-secret-key-2026
```

---

## 4. Verification & Testing

### Run Complete Automated Test Suite
From the project root:
```powershell
$env:PYTHONPATH="c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha;c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\backend"
.\backend\venv\Scripts\python.exe -m pytest backend -q --tb=short
```
*Expected Result:* `216 passed, 2 warnings in ~38s`

### Build Frontend
```powershell
npm --prefix frontend run build
```
*Expected Result:* `0 TypeScript errors, built in ~2.7s`

---

## 5. Starting the Application

### 1. Start Backend Service
```powershell
$env:PYTHONPATH="c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha;c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\backend"
.\backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Check health: `http://127.0.0.1:8000/api/v1/health`

### 2. Start Frontend Service
In a separate terminal:
```powershell
cd frontend
npm run dev
```
Open browser: `http://localhost:5173`

### 3. Load Browser Extension (Optional)
1. Open Chrome/Edge and navigate to `chrome://extensions/`.
2. Enable **Developer mode** (top right).
3. Click **Load unpacked**.
4. Select the folder: `c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\browser_extension`.

