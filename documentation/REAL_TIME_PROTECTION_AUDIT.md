# Cyber Raksha AI — Real-Time Protection Capability Audit

**Auditor:** Senior Cybersecurity Architect, Browser Security Engineer, Android Security Engineer & QA Auditor  
**Audit Target:** Cyber Raksha AI Platform (Core Backend, AI Engine, Frontend PWA, Browser Extension)  
**Evaluation Date:** November 2026  
**Audited Version:** v1.0.0-rc.1  
**Audit Objective:** Determine whether Cyber Raksha AI provides genuine real-time ACTIVE PROTECTION or primarily DETECTION AND USER-ASSISTED PROTECTION.

---

## 1. Executive Summary & Final Verdict

### Final Verdict:
# **DETECTION AND USER-ASSISTED PROTECTION ONLY**

### Forensic Finding Summary:
Cyber Raksha AI is a robust, functional, and highly accurate **Detection, Risk Assessment, and Incident Playbook Advisory Platform**. However, it **does NOT provide autonomous, device-wide, or background real-time active blocking**. 

- **Autonomous Active Blocking:** **NOT IMPLEMENTED** across general web browsing, operating system processes, SMS, telephony, or financial transactions.
- **User-Assisted Protection:** **VERIFIED IMPLEMENTED** via the Manifest V3 browser extension's context-menu pre-navigation verification, interstitial warning screen (`warning.html`), user confirmation override modal, and incident recovery playbooks.
- **Detection & Advisory:** **VERIFIED IMPLEMENTED** across structural URL analysis, NLP communication analysis, digital-arrest threat extraction, acoustic deepfake detection, unified risk correlation, and offline threat intelligence matching.

---

## 2. Protection Capability Inventory (14 Core Capabilities)

| # | Capability | Classification | Source Files & Implementation | API Endpoints | Required Permissions / External Dependencies | Verification Evidence & Current Limitations |
|---|---|---|---|---|---|---|
| 1 | **Phishing URL Protection** | **USER-ASSISTED PROTECTION** (Extension) / **DETECTION ONLY** (Web UI) | `browser_extension/background.js`, `frontend/src/pages/PhishingDetectionPage.tsx`, `ai_engine/core/engine.py` | `POST /api/v1/detection/url` | Permissions: `activeTab`, `contextMenus`, `storage`. External deps: None (Local ML). | **Verified:** Right-click context check warns and prevents navigation to malicious links. **Limitation:** Does not scan left-clicks or omnibox entry automatically. |
| 2 | **Malicious Website Blocking** | **USER-ASSISTED PROTECTION** | `browser_extension/warning.html`, `warning.js`, `background.js` | `POST /api/v1/detection/url` | Permissions: Chromium extension tabs creation. | **Verified:** Redirects to `warning.html` and halts navigation for HIGH/CRITICAL links when triggered via context menu. Overridable with modal confirmation. **Limitation:** No system-wide DNS/hosts blocking. |
| 3 | **Browser Navigation Interception** | **USER-ASSISTED PROTECTION** | `browser_extension/background.js` (lines 13-75) | `POST /api/v1/detection/url` | Permissions: `contextMenus`. Missing: `declarativeNetRequest`, `webNavigation`. | **Verified:** Intercepts link only when user right-clicks and chooses "Check with Cyber Raksha AI". **Limitation:** Standard left-clicks and address bar entries are NOT intercepted. |
| 4 | **Fraudulent SMS Protection** | **DETECTION ONLY** | `frontend/src/pages/CommunicationThreatPage.tsx`, `ai_engine/communication/` | `POST /api/v1/communication/analyze` | Permissions: None (User copy-paste into PWA). | **Verified:** Correctly scores KYC bank fraud (74.54/100). **Limitation:** Cannot read incoming SMS from Android device due to web sandbox. |
| 5 | **WhatsApp Message Protection** | **DETECTION ONLY** | `frontend/src/pages/CommunicationThreatPage.tsx`, `frontend/src/App.tsx` | `POST /api/v1/communication/analyze` | Permissions: Web Share Target API (`title`, `text`, `url`). | **Verified:** User can share copied WhatsApp text into PWA. **Limitation:** Cannot intercept encrypted WhatsApp chats in background. |
| 6 | **Email Phishing Protection** | **DETECTION ONLY** | `ai_engine/communication/`, `backend/app/api/routes/communication.py` | `POST /api/v1/communication/analyze` | Permissions: None. | **Verified:** Analyzes email bodies for urgency, fake bank alerts, and credential demands. **Limitation:** No IMAP/OAuth mail server hook. |
| 7 | **Digital-Arrest Scam Protection** | **DETECTION ONLY & ADVISORY** | `frontend/src/pages/DigitalArrestPage.tsx`, `ai_engine/communication/digital_arrest_detector.py` | `POST /api/v1/communication/digital-arrest/analyze` | Permissions: None. | **Verified:** High detection on fake police/CBI warrants and Skype extortion (88.0/100, CRITICAL). Generates guidance playbooks. **Limitation:** Cannot disconnect VoIP/Skype calls. |
| 8 | **Voice-Cloning / Deepfake Protection** | **DETECTION ONLY** | `frontend/src/pages/VoiceShieldPage.tsx`, `ai_engine/audio/` | `POST /api/v1/audio/analyze` | Permissions: File upload (`.wav`). | **Verified:** Inspects acoustic vocoder anomalies. **Limitation:** No live call audio tapping; explicit disclaimer: does NOT verify biometric speaker identity. |
| 9 | **Android Device Protection** | **NOT IMPLEMENTED** | `frontend/public/manifest.json` (PWA Shell only) | N/A | Missing: Native Android APK, `RECEIVE_SMS`, `CallScreeningService`, `QUERY_ALL_PACKAGES`. | **Verified:** Operates strictly as a browser PWA. **Limitation:** No background Android OS services, call monitoring, or app scanning. |
| 10 | **Threat Intelligence Updates** | **USER-ASSISTED / ON-DEMAND** | `backend/app/services/threat_intel_service.py`, `ai_engine/threat_intelligence/feed_updater.py` | `POST /api/v1/intel/feed/update` | Permissions: Outbound HTTPS to URLhaus. | **Verified:** Manual/API trigger fetches URLhaus feed and logs to DB. **Limitation:** No autonomous background cron/timer running periodically on startup. |
| 11 | **Unified Risk Assessment** | **DETECTION ONLY** | `backend/app/services/threat_intel_service.py`, `ai_engine/threat_intelligence/intelligence_engine.py` | `POST /api/v1/intel/unified/analyze` | Permissions: None. | **Verified:** Correlates multi-vector threats (URL + message + audio) and escalates risk to 100.0/100 (CRITICAL). |
| 12 | **Automatic Incident Alerts** | **DETECTION ONLY & IN-APP LOGGING** | `backend/app/models/security_event.py`, `backend/app/models/notification.py` | `GET /api/v1/incidents`, `GET /api/v1/intel/events/live` | Permissions: SQLite database. | **Verified:** Logs `SecurityEvent` and in-app `Notification`. **Limitation:** No external push notifications, SMS alerts, or webhooks. |
| 13 | **Prevention Recommendations** | **USER-ASSISTED PROTECTION** | `ai_engine/prevention/prevention_engine.py`, `ai_engine/prevention/protection_rules.py` | `POST /api/v1/prevention/recommendations` | Permissions: None. | **Verified:** Returns contextual mitigation checklists and Indian Cyber Crime reporting instructions (1930 / cybercrime.gov.in). |
| 14 | **Incident Response** | **USER-ASSISTED PROTECTION** | `backend/app/services/incident_service.py`, `backend/app/api/routes/prevention.py` | `POST /api/v1/incidents`, `PUT /api/v1/incidents/{id}/actions/{action_id}/complete` | Permissions: SQLite database. | **Verified:** Incident lifecycle tracking with manual action completion checkboxes. **Limitation:** Does not autonomously contact authorities or banks. |

---

## 3. What Works Automatically vs. What Requires User Interaction

### A. What Works Automatically (Zero User Interaction Required)
1. **SSRF Perimeter Defense:** Internal addresses (`127.0.0.1`, `169.254.169.254`, `192.168.0.0/16`) and dangerous schemes (`javascript:`, `file:`) are automatically rejected with HTTP 400 before model execution.
2. **Defensive Security Headers:** FastAPI automatically attaches strict CSP (`script-src 'self'`), HSTS, X-Content-Type-Options, and X-Frame-Options to all outgoing HTTP responses.
3. **Sliding-Window Rate Limiting:** Throttles incoming client requests (120 general, 30 heavy req/min) and automatically prunes state dictionaries when entries exceed 5,000.
4. **Offline Machine Learning Inference:** AI models extract features and compute risk scores locally in-process with zero network dependency.
5. **Cross-Vector Risk Escalation:** Unified risk engine automatically boosts scores when independent indicators confirm simultaneous extortion.

### B. What Requires User Interaction (User-Assisted Protection)
1. **Link Verification via Browser Extension:** Requires the user to right-click a hyperlink and select "Check with Cyber Raksha AI" from the context menu (or click "Scan Current Page URL" in the popup).
2. **Warning Interstitial & Override:** If a link is flagged, the user must review `warning.html` and explicitly click "Override & Proceed" (with a modal confirmation) to bypass the block.
3. **PWA Mobile Share Target:** Requires the user to tap "Share" in Android (e.g. from WhatsApp or SMS) and select "CyberRaksha" to transfer the text/URL into the PWA input field.
4. **Threat Feed Refresh:** Requires an administrator or API client to invoke `POST /api/v1/intel/feed/update`.
5. **Incident Action Resolution:** Containment actions (calling bank, changing password, filing 1930 complaint) require physical execution by the user and manual completion check-off.

### C. What Provides Recommendations Only
1. **Digital Arrest Guidance:** Recommends refusing Skype video calls and noting officer badge numbers.
2. **Financial Scam Guidance:** Recommends calling official bank customer care numbers and freezing debit cards.
3. **Incident Recovery Playbooks:** Pre-packaged step-by-step guidance for password resets, session revocation, and evidence preservation.

### D. What Cannot Currently Be Done (Platform Boundaries)
1. **No Autonomous Web Traffic Interception:** Does not block arbitrary URL navigations typed directly in the browser address bar.
2. **No Background Mobile Telephony or SMS Monitoring:** Cannot scan incoming SMS messages or phone calls due to browser sandbox boundaries.
3. **No Financial Transaction Interception:** Cannot halt UPI, IMPS, NEFT, or credit card transfers.
4. **No Automated Official Reporting:** Does not automatically file cybercrime complaints with government agencies or law enforcement portals.
5. **No Biometric Speaker Authentication:** Cannot confirm legal identity or identify who is speaking from voice recordings.

---

## 4. Prioritized Engineering Roadmap to Active Protection

To transition from "Detection & User-Assisted Protection" to "Autonomous Active Protection", the following phased implementations are required:

### Phase 1: Browser-Wide Active Interception (No Paid Services Required)
- **Mechanism:** Implement `chrome.declarativeNetRequest` (or `chrome.webNavigation.onBeforeNavigate`) in `browser_extension/manifest.json`.
- **Permissions Required:** `declarativeNetRequest`, `webNavigation`, host permissions `<all_urls>`.
- **Outcome:** Every top-level page navigation across all tabs is intercepted before HTTP request transmission, checked against an in-memory Bloom filter of known IoCs, and queried against the local backend, automatically halting confirmed phishing pages.

### Phase 2: Autonomous Threat Intelligence Refresh (No Paid Services Required)
- **Mechanism:** Add an `apscheduler` or `asyncio` background task in `backend/app/main.py` lifespan hook that invokes `feed_updater.update_urlhaus_feed()` on an hourly timer.
- **Outcome:** Threat intelligence feeds automatically stay up to date without manual API calls.

### Phase 3: Native Android Security Companion (Requires Android Platform Permissions)
- **Mechanism:** Package an Android application using Kotlin/Java (or Capacitor with custom native plugins).
- **Permissions Required:** `RECEIVE_SMS`, `READ_SMS`, `READ_PHONE_STATE`, `CallScreeningService`.
- **Platform Policy:** Requires compliance with Google Play Store SMS/Call Log permission declaration policies or distribution as an enterprise/sideloaded APK.
- **Outcome:** Real-time incoming SMS screening and caller-ID spam interrogation.

