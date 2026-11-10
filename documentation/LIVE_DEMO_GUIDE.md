# Cyber Raksha AI — Faculty Live Demonstration Guide

This guide provides a structured, step-by-step walkthrough for presenting **Cyber Raksha AI** during technical evaluations and faculty demonstrations.

---

## 1. Quick Startup Instructions

### Prerequisites
- Python 3.13+ installed in `backend/venv`
- Node.js 18+ installed

### Step A: Launch Backend API
Open a PowerShell terminal:
```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
$env:PYTHONPATH="c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha;c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\backend"
.\backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **Health Endpoint:** `http://127.0.0.1:8000/api/v1/health`

### Step B: Launch Frontend Dashboard
Open a second PowerShell terminal:
```powershell
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\frontend
npm run dev
```
- **Web Interface:** `http://localhost:5173`

---

## 2. Seven-Stage Demonstration Sequence

```
[1. Dashboard Overview] ──> [2. Phishing URL Shield] ──> [3. Comm & Digital Arrest]
            │                                                      │
            ▼                                                      ▼
[4. Voice Shield (Deepfake)] ──> [5. Unified Threat Engine] ──> [6. Incident Response]
            │
            ▼
[7. Browser Extension & Mobile]
```

---

### SCENARIO 1: Phishing URL Detection
- **Page to Open:** `http://localhost:5173/phishing` (Phishing Detection)
- **What to Demonstrate:**
  1. **Malicious Link Test:**
     - Paste: `http://sbi-online.netbanking.update-kyc.phishtest.invalid/secure`
     - Click **Analyze URL**.
     - **Expected Output:** Classification `PHISHING`, Risk Score `99.53/100`, Level `CRITICAL`.
     - Highlight: Subdomain depth, brand impersonation flags, lexical entropy metrics.
  2. **Legitimate Control Test:**
     - Paste: `https://www.google.com/`
     - Click **Analyze URL**.
     - **Expected Output:** Classification `LEGITIMATE`, Risk Score `0.03/100`, Level `LOW`.
  3. **SSRF Guard Demonstration:**
     - Paste: `http://127.0.0.1:8000/api/health`
     - Click **Analyze URL**.
     - **Expected Output:** Instant security rejection (`400 Bad Request: Blocked internal network address`).

---

### SCENARIO 2: Communication Fraud Detection
- **Page to Open:** `http://localhost:5173/communication` (Communication Threat Analyzer)
- **What to Demonstrate:**
  1. **Bank Credential Harvester:**
     - Input:
       > "Dear Customer, Your SBI YONO account has been blocked due to incomplete PAN KYC. Click immediately to update documents within 24 hours to prevent permanent deactivation: http://sbi-kyc-verify.net"
     - Click **Analyze Communication**.
     - **Expected Output:** Classification `IMPERSONATION`, Risk Score `74.54/100`, Level `HIGH`.
     - Highlight: Urgency framing, KYC deception indicator, credential request detection.
  2. **Contextual Negation & Educational Text (Stage 11 Remediation):**
     - Input:
       > "Cyber Safety Tip: Beware of scammers pretending to be police officers claiming digital arrest over video calls. Law enforcement never conducts arrests on Skype."
     - Click **Analyze Communication**.
     - **Expected Output:** Classification `SAFE`, Risk Score `18.5/100`, Level `LOW`.
     - Explain to Faculty: Dual-layer regex recognizes educational framing and negation keywords, preventing false alarms on advisory bulletins.

---

### SCENARIO 3: Digital-Arrest Scam Detection
- **Page to Open:** `http://localhost:5173/digital-arrest` (Digital Arrest Shield)
- **What to Demonstrate:**
  - Input:
    > "This is Officer Sharma from CBI Mumbai Headquarters. An arrest warrant has been issued in your name under PMLA Act regarding money laundering. You are under digital arrest immediately. Join this Skype call and do not disconnect or local police will arrive in 15 minutes."
  - Click **Inspect Extortion Message**.
  - **Expected Output:**
    - Classification: `DIGITAL_ARREST_SCAM`
    - Risk Score: `88.0/100` (CRITICAL)
    - Key Indicators: Government Impersonation, Non-Standard Video Platform, Confinement Coercion.
  - Show Safety Guidance: Emphasize that Indian law enforcement conducts physical arrests with documented summons, never digital arrests over Skype or WhatsApp.

---

### SCENARIO 4: Voice Shield / AI Deepfake Audio Detection
- **Page to Open:** `http://localhost:5173/voice-shield` (Voice Shield)
- **What to Demonstrate:**
  1. Point out the prominent banner:
     > *"Forensic Scope: This engine evaluates acoustic and vocoder signal anomalies to detect generative AI voice synthesis. It DOES NOT authenticate speaker biometric identity."*
  2. Upload a sample `.wav` recording.
  3. **Expected Output:**
     - Acoustic spectral metrics (Zero-Crossing Rate, Spectral Flatness, Spectral Centroid, Bandwidth).
     - Classification: `SYNTHETIC_SPEECH` or `NATURAL_SPEECH` / `INCONCLUSIVE`.
     - Recommendations and explanation chain.

---

### SCENARIO 5: Unified Fraud Risk Engine
- **Page to Open:** `http://localhost:5173/unified` (Unified Threat Analyzer)
- **What to Demonstrate:**
  - Enter combined attack scenario:
    - URL: `http://sbi-online.netbanking.update-kyc.phishtest.invalid/secure`
    - Message: `CBI: You are under digital arrest. Transfer Rs 2 lakh to safe account immediately.`
  - Click **Execute Cross-Vector Analysis**.
  - **Expected Output:**
    - Unified Risk Level: `CRITICAL`
    - Unified Score: `100.0/100`
    - Corroborated: `True` (Both web and message vectors corroborated)
    - Full multi-step evidence timeline.

---

### SCENARIO 6: Prevention & Incident Management
- **Page to Open:** `http://localhost:5173/incidents` or `http://localhost:5173/dashboard`
- **What to Demonstrate:**
  - Demonstrate incident history logged in SQLite database.
  - Review automated mitigation workflows:
    - Step 1: Disconnect communication and refuse money transfer.
    - Step 2: Contact bank helpline to freeze compromised cards/accounts.
    - Step 3: Dial **1930** (Indian National Cyber Crime Helpline) or lodge report at `cybercrime.gov.in`.

---

### SCENARIO 7: Browser Extension
- **What to Demonstrate:**
  1. Open Chrome / Edge `chrome://extensions/`.
  2. Enable "Developer mode".
  3. Click "Load unpacked" and select the `browser_extension/` directory.
  4. Open the extension popup: Displays real-time status connected to `http://127.0.0.1:8000`.
  5. Test visiting a mock malicious URL: Trigger warning interception overlay.

---

## 3. Explaining the AI Architecture to Faculty

1. **URL Classifier:**
   - Model: Scikit-learn Random Forest (100 estimators).
   - Features: 25 structural and lexical indicators (length, Shannon entropy, Punycode markers, token ratios, TLD heuristics).
2. **Communication Classifier:**
   - Model: TF-IDF vectorizer + Linear Support Vector Classifier (LinearSVC).
   - Augmented by: Rule-based indicator extraction for digital-arrest terms, bank KYC phrases, and negation detection.
3. **Voice Deepfake Classifier:**
   - Model: Random Forest trained on vocoder acoustic features (spectral centroid, spectral rolloff, zero-crossing rate, band energy variance).
4. **Threat Intelligence IoC Cache:**
   - In-memory and SQLite-backed hash maps for zero-latency offline indicator lookups.

---

## 4. Transparent Limitations to Acknowledge

1. **Acoustic vs. Biometric:** The system detects synthetic speech vocoder artifacts, not speaker voiceprints.
2. **Offline-Safe by Design:** The core engine does not make live outbound WHOIS or external cloud calls during analysis to protect user privacy and avoid third-party API dependencies.
3. **Subtle Scams:** Low-urgency scams (lottery, task fraud) register as `MEDIUM/SUSPICIOUS`, prompting user caution rather than automatic blocking.

