# CYBER RAKSHA AI — KNOWN LIMITATIONS & OPERATIONAL BOUNDARIES
## Technical Transparency & Free-Tier Operational Constraints

**Date:** 2026-11-14  
**Classification:** Engineering Transparency Specification  

---

## 1. Cloud & Hosting Free-Tier Constraints

### 1.1 Render Free Web Service Spin-Down (Cold Starts)
- **Constraint:** Render spins down free web services after 15 minutes of inbound request inactivity.
- **Impact:** The first request after spin-down incurs a cold-start initialization delay of approximately 25–40 seconds while the container and ML model weights reload into RAM.
- **Mitigation & Handling:**
  - The Chromium browser extension enforces a strict 1,800 ms timeout ceiling (`AbortController`) on live queries. If the backend is cold or booting, the extension fails open (`allowNavigation`) and logs `OFFLINE_FALLBACK`, ensuring the user's web browsing is never hung or frozen.
  - Pre-installed DNR rules continue to protect against confirmed threats during cold starts.
  - The React frontend displays an active cold-start indicator and retry countdown for user transparency.

### 1.2 Neon Serverless PostgreSQL Compute Suspension
- **Constraint:** Neon scales compute to zero after 5 minutes of inactivity on free tier.
- **Impact:** Initial database wake-up takes ~1.5 seconds.
- **Mitigation:** The backend uses SQLAlchemy connection pre-pinging (`pool_pre_ping=True`) to automatically handle compute reconnection without raising 500 errors.

---

## 2. Browser Extension Constraints (Chromium Manifest V3)

### 2.1 Asynchronous Navigation Semantics
- **Constraint:** In Chrome Manifest V3, `chrome.webNavigation.onBeforeNavigate` is an asynchronous event notification, not a synchronous cancellation gate (unlike legacy blocking `webRequest` in MV2).
- **Impact:** For unknown destinations not present in pre-installed DNR rules, remote cloud classification runs asynchronously while the initial network connection begins.
- **Mitigation & Truthful Disclosure:**
  - Known threat feeds are pre-compiled into Chromium Declarative Net Request rules, which block network connections before connection.
  - Unknown URLs evaluated in-flight are quarantined by immediately redirecting the tab to `warning.html` and compiling dynamic network-quarantine rules for all subsequent origin subresources.

### 2.2 DNR Dynamic Rule Ceilings
- **Constraint:** Chromium caps dynamic rules at 5,000 rules and dynamic regex rules at 1,000 rules per extension.
- **Mitigation:** Cyber Raksha AI's `rules_manager.js` enforces a safe cap of 900 rules (`MAX_DYNAMIC_RULES`), with differential deduplication and least-recent indicator eviction.

---

## 3. Mobile Telephony & Android Platform Constraints

### 3.1 CallScreeningService System Role Requirements
- **Constraint:** On Android 10+ (API 29+), `CallScreeningService` operates only when the user explicitly grants the application the **Default Caller ID & Spam** system role in Android settings.
- **Mitigation:** The application provides an onboarding prompt requesting this role and gracefully indicates `STANDBY` if the user elects not to enable telecom call screening.

### 3.2 Telecom Framework Response Time Budget
- **Constraint:** Android Telecom subsystem requires `respondToCall()` within approximately 5 seconds, otherwise the call is automatically allowed by the OS.
- **Mitigation:** `CyberRakshaCallScreeningService` enforces a strict 3,000 ms coroutine timeout (`withTimeoutOrNull(3000L)`), invoking `allowCall()` immediately on timeout or network interruption.

---

## 4. AI & Machine Learning Detection Boundaries

### 4.1 Lexical & Structural Inference Limits
- **Constraint:** The URL phishing detector is a lightweight, local-CPU scikit-learn RandomForest model trained on lexical and structural features (URL length, domain entropy, brand keywords, token counts). It does not execute dynamic browser DOM headless rendering or live page scraping.
- **Impact:** Highly sophisticated zero-day phishing attacks that perfectly mimic benign lexical patterns on clean domains cannot be detected solely through lexical signals without threat intelligence corroboration.
- **Mitigation:** Cyber Raksha AI pairs lexical ML with verified authoritative threat intelligence feeds (URLhaus, CERT-In, TRAI).
