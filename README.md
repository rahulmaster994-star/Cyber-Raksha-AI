# 🛡️ CYBER RAKSHA AI (साइबर रक्षा)
> **AI-Powered Proactive Digital Fraud Detection & Prevention Ecosystem**  
> *Native Android Protection • Chrome MV3 Shield • Intelligent Risk Evaluation • Real-Time Alert Engine*

[![GitHub Repo](https://img.shields.io/badge/GitHub-Cyber--Raksha--AI-181717?logo=github)](https://github.com/rahulmaster994-star/Cyber-Raksha-AI)
[![Backend Tests](https://img.shields.io/badge/pytest-371%20passed%20(100%25)-brightgreen)](backend/tests/)
[![E2E Scenarios](https://img.shields.io/badge/E2E%20Scenarios-16%2F16%20verified-success)](docs/TESTING_REPORT.md)
[![Browser Tests](https://img.shields.io/badge/Chrome%20Extension-27%20passed-blue)](browser_extension/tests/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688)](https://fastapi.tiangolo.com)
[![Android](https://img.shields.io/badge/Android-Kotlin%20%2B%20Compose-3DDC84)](android/)
[![Chrome MV3](https://img.shields.io/badge/Chrome-Manifest%20V3%20DNR-4285F4)](browser_extension/)
[![ML Model](https://img.shields.io/badge/ML%20Accuracy-98.44%25%20(GroupKFold)-orange)](docs/B4_1_DETECTION_INTELLIGENCE_AUDIT.md)
[![Zero Budget](https://img.shields.io/badge/Cloud%20APIs-Zero%20Paid%20Dependencies-purple)](#)

---

## 1. Project Overview

**Cyber Raksha AI** is a multi-platform cybersecurity ecosystem built to protect citizens and organizations from modern social engineering and digital fraud attacks across browsers, mobile devices, and telecommunications.

### Protection Capabilities:
1. **Phishing & Deceptive URLs:** Supervised Random Forest lexical and structural analyzer with 25+ extracted features (133ms CPU inference).
2. **Brand Impersonation Detection:** Levenshtein edit-distance matching protecting major Indian banks (SBI, HDFC, ICICI, PNB) and public utilities.
3. **SMS Smishing Protection:** Multi-pattern category detection identifying coercive urgent demands, lottery lures, and fake KYC notices.
4. **Digital Arrest Scam Shield:** Detection of forged law enforcement notices (CBI, ED, Cyber Police) demanding video interrogation or funds transfers.
5. **Fake Courier / Delivery Scams:** Detection of spoofed courier tracking alerts (India Post, BlueDart, DTDC).
6. **Legitimate OTP & Transaction Guards:** False-positive suppression for genuine debit notifications and two-factor authentication codes.
7. **Threat Intelligence Synchronization:** Automated ingestion of high-confidence indicators from open-source feeds (URLhaus).
8. **Browser Extension Shield:** Chrome MV3 Declarative Net Request (DNR) dynamic rule generation blocking malicious navigation.
9. **Android Security Suite:** Native Kotlin + Jetpack Compose application with AndroidKeyStore AES-256-GCM encrypted token storage.
10. **Unified Incident Management:** Cross-vector corroboration, incident state tracking, and live Server-Sent Events (SSE) streaming.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph Client["Client Tier"]
        EXT["Chrome MV3 Extension\n(DNR Dynamic Blocking)"]
        AND["Android App\n(Kotlin + Compose)"]
        DASH["Dashboard UI\n(React 18 + Vite)"]
    end

    subgraph Backend["Core Backend (FastAPI)"]
        API["REST API Gateway\n:8000"]
        RATE["Token-Bucket Rate Limiter\n(120/min & 30/min)"]
        AUTH["Device Token Auth\n(SHA-256 Hashes)"]
        RISK["Central Risk Engine\n(Calibrated Scoring)"]
        NOTIF["Notification Engine\n(Device Isolation)"]
        SSE["SSE Event Stream\n(Single-Use Tickets)"]
    end

    subgraph AI["AI Inference Engine"]
        RF["RandomForest Phishing Model\n(98.44% Accuracy)"]
        FEAT["25+ URL Feature Extractor"]
        BRAND["Brand Impersonation Matcher"]
        DIGIT["Digital Arrest Scam Analyzer"]
    end

    subgraph Storage["Persistence Layer"]
        DB["SQLite / PostgreSQL\n(SQLAlchemy ORM)"]
        FEED["URLhaus Threat Intel\n(Hourly Sync)"]
    end

    EXT -->|"URL Scan / Telemetry"| API
    AND -->|"SMS Text / Heartbeat"| API
    DASH -->|"Dashboard Telemetry"| API
    API --> RATE --> AUTH --> RISK
    RISK --> AI
    AI --> RF
    AI --> FEAT
    AI --> BRAND
    AI --> DIGIT
    RISK --> NOTIF --> SSE --> DASH
    API --> DB
    API --> FEED
```

---

## 3. Technology Stack

| Component | Technologies |
|---|---|
| **Backend API** | Python 3.11–3.13, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy |
| **AI / Machine Learning** | Scikit-learn (RandomForestClassifier), NumPy, Joblib |
| **Android Application** | Kotlin, Jetpack Compose, Retrofit, Room DB, WorkManager, AndroidKeyStore |
| **Browser Extension** | Chrome Manifest V3, Declarative Net Request (DNR), Service Workers |
| **Frontend Dashboard** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons |
| **Security & Cryptography** | HMAC-SHA256 (Pepper rotation), AES-256-GCM, SHA-256 Token Hashing |
| **Database** | SQLite (Development) / PostgreSQL (Production) |

---

## 4. Quick Start (Local Setup)

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- JDK 17+ (for Android builds)
- Google Chrome (for extension)

### 1. Launch Backend API
```powershell
# In PowerShell:
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
.\start_cyberraksha.ps1
```
*API will run on `http://127.0.0.1:8000` (Docs at `http://127.0.0.1:8000/docs`).*

### 2. Launch Dashboard UI
```powershell
cd frontend
npm install
npm run dev
```
*Dashboard will open on `http://localhost:5173`.*

### 3. Load Chrome Browser Extension
1. Open Chrome and navigate to `chrome://extensions/`.
2. Toggle on **Developer mode** in the top right corner.
3. Click **Load unpacked** and select the folder:
   `c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\browser_extension`

### 4. Build Android APK
```powershell
cd android
.\gradlew.bat assembleDebug
```
*APK generated at `android/app/build/outputs/apk/debug/app-debug.apk`.*

---

## 5. Verification & Testing

Execute the test suites across all platforms:

```powershell
# 1. Backend Tests (371 tests, 100% pass)
python -m pytest backend/tests -q --tb=short

# 2. Browser Extension Tests (27 tests, 100% pass)
cd browser_extension
node tests/test_rules_manager.js
node tests/test_notifications.js
node tests/verify_a1_deep_audit.js

# 3. Android Unit Tests
cd ../android
.\gradlew.bat testDebugUnitTest

# 4. Frontend Production Build
cd ../frontend
npm run build
```

---

## 6. Project Documentation Index

Comprehensive engineering documents are located in [`docs/`](docs/):
- [docs/FINAL_RELEASE_AUDIT.md](docs/FINAL_RELEASE_AUDIT.md) — Complete release audit and verification matrix.
- [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) — Mermaid architecture diagrams and database ER models.
- [docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md) — Detailed deployment and installation instructions.
- [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) — Zero-cost cloud deployment guide (Render, Vercel, Neon).
- [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) — REST API endpoint specification.
- [docs/TESTING_REPORT.md](docs/TESTING_REPORT.md) — 16 end-to-end scenario verification results.
- [docs/SECURITY_REPORT.md](docs/SECURITY_REPORT.md) — Threat model, cryptography, and vulnerability audit.
- [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) — Operational boundaries and hardware requirements.
- [docs/CHANGELOG.md](docs/CHANGELOG.md) — Version release history.

---

## 7. Known Limitations & Operational Boundaries

1. **Android SMS Mode:** Operates in user-submitted/manual mode (`SmsAccessMode.MANUAL_ONLY`). Automatic background SMS interception is not implemented in this release.
2. **Inference Latency:** Warm CPU inference is ~133 ms on Windows 11 hardware.
3. **URL Shorteners:** URLs using `bit.ly` or `tinyurl.com` are flagged as `SUSPICIOUS_SHORTENER`; automatic HTTP redirect following is omitted to prevent SSRF vulnerabilities.
4. **Multi-Process Concurrency:** SQLite is configured for single-instance development; production should use PostgreSQL via `DATABASE_URL`.

---

## 8. License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.
