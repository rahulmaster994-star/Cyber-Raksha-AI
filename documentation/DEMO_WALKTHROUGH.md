# 🎬 CYBER RAKSHA AI — DEMONSTRATION WALKTHROUGH SCRIPT
**Stage 8: Live Demonstration Guide for Reviewers & Stakeholders**

This script outlines the exact sequence to demonstrate all implemented features of the integrated platform.

---

## Step 1: Start Services

```bash
# Terminal 1: Backend
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```
Open your browser to: **http://localhost:5173**

---

## Step 2: Central Operations Dashboard

1. Navigate to **Control Center** in the top navigation bar.
2. Point out:
   - Live telemetry status pills in the header (**API: ONLINE**, **DB: ACTIVE** with live ping latency).
   - Real multi-entity database counts (Total Scans, Phishing Threats, Message Threats, Voice Clones, Active Incidents).
   - Risk distribution breakdown (LOW, MEDIUM, HIGH, CRITICAL).
   - Status of all 6 core security modules (all showing operational).

---

## Step 3: Phishing URL Detection (Stage 2)

1. Click **Phishing Detection** in the navigation bar.
2. Click the sample button **"Phishing: Deceptive PayPal"** or enter:
   `http://account-verification-support.paypal.com.crypto-wallet-verify.net/security/login.php?session=id`
3. Click **Scan Target URL**.
4. Show:
   - Classification: `PHISHING` (Risk Score: 85-90/100, CRITICAL Risk).
   - Detected indicators: HTTP plain-text transmission, abnormal dot counts, high entropy.
   - Genuine latency in milliseconds and model probabilities.

---

## Step 4: Digital Arrest Scam Detection (Stage 3)

1. Click **Digital Arrest** in the navigation bar.
2. Paste the following test message:
   > "CBI POLICE WARRANT: An illegal parcel containing contraband has been seized at customs under your Aadhaar. You are under digital arrest. Join Skype immediately for video interrogation and transfer security deposit to RBI safe account."
3. Click **Analyze Message**.
4. Show:
   - Classification: `DIGITAL_ARREST_SCAM` (Risk Score: 92/100, CRITICAL).
   - Detected markers: Fake CBI police notice, illegal parcel threat, Skype interrogation coercion, safe account transfer demand.
   - Prominently displayed advisory: *"There is NO legal concept of 'Digital Arrest' under Indian Law. Police never conduct court hearings over Skype."*
   - Emergency contact buttons for **1930** and **cybercrime.gov.in**.

---

## Step 5: Voice Cloning Detection (Stage 4)

1. Click **Voice Shield** in the navigation bar.
2. Upload a WAV audio recording (e.g. sample voice call).
3. Click **Analyze Voice Recording**.
4. Show:
   - Acoustic spectral feature breakdown (MFCCs, spectral roll-off, vocoder artifacts).
   - Disclosed limitation note: System detects synthetic acoustic artifacts; does not claim speaker identity.

---

## Step 6: Unified Risk Analyzer (Stage 5)

1. Click **Unified Risk** in the navigation bar.
2. Enter a message containing an embedded link:
   > "Dear SBI customer, your netbanking is blocked. Update immediately at http://secure-login-hdfcbank.serveo.net/verify to restore access."
3. Click **Execute Unified Analysis**.
4. Show:
   - Cross-vector corroboration: Phishing link confirmed inside an actively coercive message (+15 pts boost).
   - Factual evidence vs Model prediction segregation.
   - Defensible evidence chain and tailored recommendations.

---

## Step 7: Incident Response & Protection Center (Stage 6)

1. Click **Protection Center**.
2. Create an incident:
   - Title: "Compromised OTP on Phishing Site"
   - Category: "Account Compromise"
   - Severity: "High"
3. Show:
   - Auto-populated containment playbook actions (Call bank, block cards, change credentials, enable TOTP).
   - Click **Complete Action** on a step and watch the posture progress update in real-time.
4. Try the **Security Guidance Assistant**:
   - Query: *"I shared my OTP on a website, what should I do?"*
   - Show: Instant, authoritative guidance referencing the Golden Hour and 1930 reporting.

---

## Step 8: Browser Extension & Mobile Experience (Stage 7)

1. Open Chrome with the loaded unpacked extension from `browser_extension/`.
2. Click the 🛡️ toolbar icon to scan the active page.
3. Show:
   - Real-time connection status to local backend (`http://127.0.0.1:8000`).
   - Risk badge display.
   - Options page for configuring custom backend URLs.
4. On mobile viewport (or phone):
   - Show responsive layout and fixed 5-button bottom navigation bar.
   - PWA installation option in Chrome menu.

