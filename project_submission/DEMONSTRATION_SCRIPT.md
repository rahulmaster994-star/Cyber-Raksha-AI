# CYBER RAKSHA AI — FACULTY & EVALUATOR DEMONSTRATION SCRIPT
**Practical 8–10 Minute Live Evaluation Sequence**

---

## 1. Demonstration Preparation Checklist (0:00 - 1:00)

1. **Start the Backend:**
   ```bash
   cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
   backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Start the Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:5173` in a Chromium browser (Google Chrome or Microsoft Edge).
4. Verify the top right telemetry pills display:
   - **`API: ONLINE`** (green pulsing indicator)
   - **`DB: ACTIVE`** (cyan indicator with database latency in ms)

---

## 2. Step 1: Security Operations Dashboard & Live Telemetry (1:00 - 2:30)

- **What to open:** Click on **Control Center** / **Dashboard**.
- **What to show:**
  - The banner reads: **CYBER RAKSHA AI — Intelligent Digital Fraud Protection**.
  - Show the 6 Top Operational Metric Cards (Total Scans, URL Threats, Message Scams, Voice Clones, Active Incidents, Active IoCs).
  - Point out the **Database Verified** note: all numbers reflect genuine SQLite records. There are no fabricated attack counters or fake percentages.
  - Highlight the **12-Module Protection Matrix** providing one-click access across all capabilities.
- **Concept to explain:** "Cyber Raksha AI operates as a unified platform rather than disconnected prototypes. Every analysis performed in any module writes directly to the local relational database and updates these metrics live."

---

## 3. Step 2: AI Phishing URL Detection (2:30 - 4:00)

- **What to open:** Click on **Phishing Detection** tab.
- **What to enter:**
  - *Test Case 1 (Phishing):* `http://account-verification-support.paypal.com.crypto-wallet-verify.net/security/login.php?session=id`
  - Click **Analyze Target URL**.
- **What should happen:**
  - Returns **PHISHING** (High/Critical Risk, Score > 75).
  - Displays the 25-feature breakdown: excessive subdomains, brand keywords in subdomains, Shannon entropy score.
  - Raw ML probability is shown (e.g., > 90%).
  - Shows clear recommendation: *"Do not enter credentials. Domain exhibits deceptive subdomains mimicking financial entities."*
- **What to enter:**
  - *Test Case 2 (Legitimate):* `https://www.google.com`
  - Click **Analyze Target URL**.
  - Returns **LEGITIMATE** (Low Risk, Score < 20).
- **Show Human Governance Feedback:**
  - Click the **Report / Submit Feedback** button on the result card.
  - Explain: "Users can report false positives or novel scams. The feedback is queued for human review in the Admin Center and does NOT automatically alter active model weights, preventing adversarial data poisoning."

---

## 4. Step 3: Message Threats & Digital Arrest Scam Analysis (4:00 - 5:30)

- **What to open:** Click on **Message Threats** or **Digital Arrest** tab.
- **What to enter:**
  ```
  URGENT NOTICE: CBI Officer Rajesh Sharma. Arrest warrant issued under PMLA Act for money laundering. Join Skype video interrogation immediately within 15 minutes or police will be dispatched to your address. Do not inform anyone.
  ```
- **What to click:** Click **Analyze Suspicious Message**.
- **What should happen:**
  - Classification: **DIGITAL_ARREST_SCAM** (Critical Risk).
  - High urgency token score, coercive legal authority impersonation flagged, non-standard video call channel detected.
  - PII Sanitizer demonstrates that any Aadhaar or phone numbers submitted are masked.
  - Action guidance: *"Indian law enforcement agencies (CBI, ED, Police) NEVER conduct digital arrests or demand money via video calls. Disconnect immediately and dial 1930."*

---

## 5. Step 4: VoiceShield Deepfake Detection (5:30 - 6:30)

- **What to open:** Click on **Voice Shield** tab.
- **What to show:**
  - Supported audio container verification (WAV, PCM).
  - Upload a test WAV sample (or explain the 24 acoustic spectral features extracted: spectral centroid, rolloff, vocoder synthesis artifacts).
  - Explain: "The model identifies acoustic vocoder artifacts indicative of Text-to-Speech (TTS) synthesis. We explicitly maintain that this model does not perform biometric speaker identity verification, which is an important safety boundary."

---

## 6. Step 5: Threat Intelligence & Unified Cross-Vector Risk (6:30 - 7:45)

- **What to open:** Click on **Unified Risk** tab.
- **What to demonstrate:**
  - Enter both the digital arrest extortion message AND a suspicious verification link simultaneously.
  - Click **Run Unified Analysis**.
  - Show how the **Unified Risk Engine** correlates the two signals: instead of treating them as isolated events, it fuses the evidence into a corroborated multi-vector profile, checks threat feeds, applies freshness discounting, and produces an actionable safety playbook.

---

## 7. Step 6: Operations Center & Administration (7:45 - 9:00)

- **What to open:** Click on **Admin** (top right in navbar).
- **Authenticate:** Enter the secret key: `cyber-raksha-admin-secret-key-2026`.
- **What to show:**
  - **Subsystem Health Status:** Live discrete status of API, DB, AI Models, Threat Feeds, and Worker Pool.
  - **Performance Telemetry:** Actual p50, p95, and p99 response times measured by the `RequestObservabilityMiddleware`.
  - **Feature Flags:** Demonstrate toggling a feature flag (e.g., `enable_audio_analysis` or `maintenance_mode`) to show real-time administrative control without restarting the server.
  - **Human Review Queue:** View the feedback submission entered in Step 2. Demonstrate an analyst approving or rejecting it with notes.

---

## 8. Fallback Procedures for External Outages (9:00 - 10:00)

- **If internet is disconnected during demo:**
  - Threat feed queries gracefully return cached IoCs from the local SQLite database.
  - The AI models run 100% locally on the host machine using Scikit-Learn without cloud calls.
  - Point to the `THREAT_INTELLIGENCE_OPERATIONS.md` runbook explaining the offline graceful degradation policy.

