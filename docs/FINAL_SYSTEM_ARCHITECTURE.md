# CYBER RAKSHA AI — FINAL SYSTEM ARCHITECTURE
## End-to-End Real-World Digital Fraud Protection Ecosystem

**Document Version:** 1.0.0-RELEASE  
**Date:** 2026-11-14  
**Classification:** Technical Architecture Specification  

---

## 1. Architectural Blueprint

Cyber Raksha AI operates as a unified, multi-vector cybersecurity platform safeguarding citizens against financial fraud, brand impersonation, deceptive telecommunications, and coercive scams (such as "Digital Arrest").

```
+----------------------------------------------------------------------------------------------------+
|                                         EDGE CLIENT TIERS                                          |
|                                                                                                    |
|    +------------------------------------------+    +------------------------------------------+    |
|    |     CHROMIUM BROWSER SHIELD (MV3)        |    |       ANDROID NATIVE APPLICATION         |    |
|    |                                          |    |                                          |    |
|    |  - Declarative Net Request (DNR) Rules   |    |  - Jetpack Compose Reactive UI           |    |
|    |  - Real-Time Navigation Interception     |    |  - Telecom CallScreeningService          |    |
|    |  - Local Heuristics & Suffix Hardening   |    |  - Privacy-Preserving Manual SMS Scanner |    |
|    |  - Automated Threat Intel Synchronization|    |  - Encrypted Keystore DataStore Tokens   |    |
|    |  - Interstitial Quarantine Warning       |    |  - Room Local Persistence                |    |
|    +--------------------+---------------------+    +--------------------+---------------------+    |
+-------------------------|-----------------------------------------------|--------------------------+
                          |                                               |
                          | HTTPS (REST API + JSON)                       | HTTPS (REST API + JSON)
                          | Bearer Device Token (UUIDv4)                  | X-Device-Token Header
                          v                                               v
+----------------------------------------------------------------------------------------------------+
|                                 PRODUCTION APPLICATION CLOUD TIER                                  |
|                             FastAPI / Python 3.11 on Render Container                              |
|                            (https://cyberraksha-backend.onrender.com)                              |
|                                                                                                    |
|  +----------------------------------------------------------------------------------------------+  |
|  |                                  SECURITY CONTEXT & GATEWAY                                  |  |
|  |  - Cryptographic Device Authentication (HMAC-SHA256 Token Verification)                      |  |
|  |  - Strict Multi-Device Data Isolation (Per-Device Security Scoping)                          |  |
|  |  - In-Memory Per-Device Token Rate Limiting (60 req/min)                                     |  |
|  |  - Strict Production CORS Whitelist & Security Headers (CSP, HSTS, X-Frame-Options)          |  |
|  +----------------------------------------------------------------------------------------------+  |
|                                                                                                    |
|  +-------------------------------------+  +-----------------------------------------------------+  |
|  |      AI / ML DETECTION SUBSYSTEM    |  |          THREAT INTELLIGENCE & REPUTATION           |  |
|  |                                     |  |                                                     |  |
|  |  - URL Phishing (RandomForest CPU)   |  |  - URLhaus Verified Threat Intel Feeds              |  |
|  |  - Brand Impersonation Classifier   |  |  - Telecom Phone Number Reputation Service          |  |
|  |  - Communication Fraud (LinearSVC)  |  |  - Authoritative Source Registry (CERT-In / TRAI)   |  |
|  |  - Coercive Digital Arrest Detector |  |  - Differential Sync & Stale IOC Retirement        |  |
|  +-------------------------------------+  +-----------------------------------------------------+  |
|                                                                                                    |
|  +----------------------------------------------------------------------------------------------+  |
|  |                        CENTRAL SECURITY RISK & INCIDENT ENGINE                               |  |
|  |  - Cross-Platform Multi-Vector Correlation (Browser + SMS + Call matching by domain/target)  |  |
|  |  - 30-Second Event Hash Deduplication Window                                                 |  |
|  |  - Authoritative Threat Escalation Guard (Cap unverified CRITICAL at HIGH)                   |  |
|  |  - Automated Incident Lifecycle (NEW -> INVESTIGATING -> RESOLVED)                           |  |
|  |  - Notification Dispatch & Real-Time Queue Management                                        |  |
|  +----------------------------------------------------------------------------------------------+  |
+---------------------------------------------------+------------------------------------------------+
                                                    |
                                                    v (SQLAlchemy Connection Pool: size=10, max=20)
+----------------------------------------------------------------------------------------------------+
|                               PERSISTENCE & MANAGED DATABASE TIER                                  |
|                                    Neon Serverless PostgreSQL                                      |
|                                                                                                    |
|  - devices: Registered UUIDv4 hardware profiles, status, 256-bit token hashes                      |
|  - security_events: Immutable audit log of threat detections with device foreign keys              |
|  - security_incidents: Correlated multi-vector incidents, evidence references, status lifecycle    |
|  - notifications: User-targeted security alerts, severity ratings, read/unread status              |
|  - threat_indicators: Active indicators of compromise (IOCs), threat types, confidence scores      |
|  - phone_reputation: Telecom caller reputation, report counters, dispute history                  |
+----------------------------------------------------------------------------------------------------+
                                                    ^
                                                    | HTTPS REST API (JSON)
+---------------------------------------------------+------------------------------------------------+
|                                    PRESENTATION & DASHBOARD TIER                                   |
|                                  React 18 / TypeScript / Vite on Vercel                            |
|                                 (https://frontend-lilac-nu-50.vercel.app)                          |
|                                                                                                    |
|  - Unified Cyber Posture Score Indicator (0-100 gauge with dynamic health bands)                   |
|  - Incident Command Center (Actionable containment, acknowledgement, resolution)                 |
|  - Interactive Analysis Consoles: URL Scanner, SMS Analyzer, Digital Arrest Evaluator              |
|  - Fleet Device Inventory: Active vs Revoked devices, telemetry status                            |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Core Subsystems

### 2.1 Browser Protection (Chromium Extension)
- **Manifest Version:** 3 (MV3)
- **Network Enforcement:** Declarative Net Request (DNR) dynamic and session rules.
- **Pre-Load vs In-Flight Model:**
  - Known IOCs are pre-compiled into Chromium DNR redirect rules that execute synchronously in the browser network stack before connection.
  - Unknown URLs undergo lexical pre-screening and asynchronous cloud ML evaluation; detected threats trigger tab quarantine and dynamic DNR rule compilation.
- **Privacy Architecture:** URLs are sanitized locally before egress, stripping sensitive credentials and session tokens (`password`, `token`, `otp`, `auth`).

### 2.2 Mobile Protection (Native Android)
- **Language / Runtime:** Kotlin 2.0 / Android SDK 26–36 / Jetpack Compose.
- **Call Screening:** Extends `android.telecom.CallScreeningService`. Normalizes incoming numbers, queries backend caller reputation within 3 seconds, and executes fail-open call response (`allowCall`) on benign or unverified callers.
- **SMS Analysis:** User-directed manual inspection preserving user privacy without background message harvesting.
- **Token Security:** Device tokens are encrypted at rest using AES-GCM via Android Keystore.

### 2.3 Central Security Risk & Incident Engine
- Deduplicates identical event hashes within a 30-second sliding window.
- Correlates cross-platform signals: when a device blocks a phishing URL in Chrome and subsequently receives an SMS with the same domain, both events unify under the same Incident.
- Strictly guards CRITICAL classification: unverified client claims are capped at HIGH unless corroborated by authoritative feeds (URLhaus, CERT-In, TRAI).

### 2.4 Cloud Backend & Database
- Hosted on Render Free Web Service with Python 3.11.9 and Docker runtime.
- Powered by Neon Serverless PostgreSQL with SSL connection pooling (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`).
- Resilient fallback to SQLite for local isolated development.
