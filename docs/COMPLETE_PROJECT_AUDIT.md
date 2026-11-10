# Cyber Raksha AI — Complete Project Audit

**Audit Date**: November 2026  
**Auditor**: Principal Cybersecurity Architect & Senior Engineering Team  
**Scope**: Full Repository Audit (Backend, AI Engine, Android Native App, Browser Extension, Frontend Dashboard, Database, Threat Feeds)

---

## 1. Executive Summary

A comprehensive architectural and code-level audit was conducted across all existing components of the Cyber Raksha AI repository. Cyber Raksha AI is an integrated proactive digital fraud protection ecosystem designed to protect users across Web Browsing, Phishing URLs, Smishing Messages, Fraudulent Phone Calls, Brand Impersonation, and Digital Arrest scams.

The codebase currently spans:
- **Backend**: FastAPI + SQLite/SQLAlchemy with 360 automated tests (100% passing).
- **AI Engine**: Local scikit-learn Random Forest classifier (`v1.0.0-rf-lexical`) with 25 structural/lexical features, Brand Impersonation Detector (16 high-value target profiles), and Threat Intelligence Correlation.
- **Browser Protection**: Chrome Manifest V3 extension with Declarative Net Request (DNR) dynamic blocking and context-menu scanning (27 automated tests passing).
- **Android Protection**: Kotlin + Jetpack Compose application with Room persistence, EncryptedSharedPreferences / Android KeyStore token management, and CallScreeningService integration (Gradle build and unit tests passing).
- **Frontend Dashboard**: React 18 + Vite + Tailwind CSS with live SSE connection, incident lifecycle actions, and cross-vector telemetry (Production build successful).

---

## 2. Existing Architecture & Subsystem Audit

```mermaid
graph TD
    subgraph BrowserClient["Browser Protection (Chrome MV3)"]
        DNR["Declarative Net Request Engine"]
        BG["Service Worker (background.js)"]
        POP["Popup & Warnings"]
    end

    subgraph MobileClient["Native Android Client (Kotlin Compose)"]
        SMS["SMS Receiver & Analysis"]
        CALL["CallScreeningService (Fail-Open)"]
        ENC["SecureTokenManager (KeyStore AES-256-GCM)"]
        ROOM["Room Local Cache"]
    end

    subgraph CentralBackend["FastAPI Central Backend"]
        AUTH["Device Token & Single-Use Ticket Auth"]
        RISK["Central Security Risk Engine"]
        TI_SYNC["Threat Intel Scheduler (URLhaus)"]
        SSE_PUB["Cryptographic SSE Stream Ticket Service"]
        DB[(SQLite / SQLAlchemy)]
    end

    subgraph IntelligenceEngine["Autonomous AI Engine"]
        FEAT["25+ Dimension Lexical Feature Extractor"]
        BRAND["Brand Impersonation Engine (16 Brands)"]
        ML_MOD["Random Forest Model (v1.0.0-rf-lexical)"]
    end

    subgraph OperationsDashboard["React Dashboard (Vite)"]
        OVW["Security Overview & Incident Drawer"]
        ACT["Live Security Event Activity"]
        NOTIF_UI["Notification Center & Preferences"]
    end

    DNR --> BG
    BG -->|REST API / Security Events| AUTH
    SMS --> ENC
    CALL --> ENC
    ENC -->|REST API / SMS Analysis| AUTH
    AUTH --> RISK
    RISK --> DB
    RISK --> SSE_PUB
    RISK --> FEAT
    FEAT --> BRAND
    FEAT --> ML_MOD
    TI_SYNC --> DB
    SSE_PUB -->|SSE Stream (?ticket=)| NOTIF_UI
    DB --> OVW
    DB --> ACT
```

---

## 3. Verified Working Features by Phase

### Phase A1 — Browser Protection
- **Declarative Net Request (DNR) Dynamic Blocking**: Converts threat feed indicators into Chrome MV3 regex blocking rules (`browser_extension/rules_manager.js`).
- **Context-Menu On-Demand Scanning**: Scans links via `POST /api/v1/detection/url` without forcing pre-navigation blocks on unverified targets.
- **Fail-Safe Offline Mode**: Previous rule sets persist if backend becomes temporarily unreachable.
- **Shared Hosting Domain Protection**: Whitelists platforms like `github.com`, `drive.google.com`, `vercel.app` from whole-domain DNS blocking.

### Phase A2 — Automated Threat Intelligence
- **URLhaus Synchronization Scheduler**: Asynchronous background cron synchronizing active malware and phishing URLs with TTL-based expiration and deduplication.
- **Indicator Database**: SQLite `threat_indicators` table with normalized domains, URLs, hashes, and source attribution (`URLHAUS`, `PHISHTANK`, `CERT_IN`).
- **Indicator Normalization**: IDN/punycode handling, signature query param preservation (`Signature`, `X-Amz-Signature`), and multi-param sorting.

### Phase A3 — Security Alert Notifications
- **Persistent Notifications**: SQLite `notifications` table storing category, severity, device_id, and read state.
- **Browser Desktop Notifications**: Chrome extension notifications with 30s domain deduplication.
- **Notification Preferences**: Configurable minimum severity thresholds, desktop alert toggles, and email alert switches.

### Phase B1 — Native Android Foundation
- **Architecture**: Modern Android architecture with Kotlin, Jetpack Compose, MVVM, Room, WorkManager, and Retrofit.
- **Device Registration & Heartbeat**: Registers UUID, device model, and app version, acquiring a device-bound Bearer token.
- **Offline Persistence**: Room SQLite database caching incident history and offline scan records.

### Phase B2 & B2.1 — Mobile Fraud Protection & Security Hardening
- **Context-Aware SMS Smishing Detection**: Scans incoming text for urgency, credential demands, UPI fraud pretexts, and Digital Arrest scams.
- **OTP False-Positive Guard**: Legitimate outbound bank transaction receipts are recognized and prevented from triggering OTP theft alerts.
- **Zero-Retention HMAC Hashing**: Plaintext SMS is never stored; messages are normalized and hashed via HMAC-SHA256 with server-side pepper keys and key-rotation support.
- **Fail-Open Call Screening**: `CallScreeningService` screens caller numbers against reputation feeds, failing open to prevent missed legitimate calls during backend offline periods.
- **KeyStore MasterKey Hardening**: AES-256-GCM authenticated encryption for auth token persistence in Android KeyStore.

### Phase B3 & B3.1 — Unified Integration & Security Closure
- **Central Security Risk Engine**: Correlates web, mobile, and threat intelligence events into unified `SecurityIncident` records.
- **Client Confidence Untrusted (Zero-Trust)**: Numerical confidence from clients is untrusted. Authority is conferred strictly by verified threat intelligence sources (`AUTHORITATIVE_SOURCES`).
- **Cryptographic SSE Tickets**: Single-use tickets (`secrets.token_urlsafe(32)`) with 60s TTL; long-lived tokens in query strings are rejected with HTTP 400.
- **Device & Data Isolation**: Device-bound queries enforce row-level access control; cross-device access returns HTTP 403.

### Phase B4 — Intelligent Threat Detection
- **Local Machine Learning Classifier**: 100-tree Random Forest (`v1.0.0-rf-lexical`) evaluating 25 lexical/structural dimensions in < 2.5ms without external APIs.
- **Brand Impersonation Engine**: Identifies typosquatting and unauthorized lookalike domains across 16 target brands (HDFC, SBI, ICICI, Paytm, PhonePe, IndiaPost, Amazon, UIDAI, IncomeTax).
- **Explainable Decisions**: Unified API responses deliver structured evidence items, classification reasons, intelligence status, and recommended actions.

---

## 4. Incomplete Features, Technical Debt & Integration Gaps

1. **Domain Leakage in Random Test Splitting**:
   - The initial training pipeline used a random 70/15/15 split on 1,600 URLs where 90 legitimate domains had multiple sub-paths.
   - Result: 39.3% of test domains overlapped with training domains. Under true GroupKFold domain-separated evaluation, accuracy is 98.44% +/- 1.54%.
2. **Overfitting to Domain Hyphens**:
   - The lexical classifier had learned to associate multiple hyphens with phishing because top-50 Alexa domains rarely had hyphens. Legitimate multi-hyphen business domains (`acme-cyber-solutions-2026.org`) were receiving inflated phishing probabilities.
3. **Over-reliance on Static Whitelists**:
   - Hardcoded `.endswith((".gov.in", ...))` checks bypass legitimate defense-in-depth principles (attackers can abuse compromised government subdomains or open redirects).
4. **Duplicate Threat Analyzer Interfaces**:
   - Two frontend analyzer pages exist (`PhishingDetectionPage.tsx` and `UnifiedThreatAnalyzerPage.tsx`). They should share a unified risk engine client.
5. **Rate Limiting Middleware In-Memory Saturation**:
   - Rapid test execution of 360+ tests against localhost within 30 seconds can trigger `429 Too Many Requests` unless test bypass headers are passed.
6. **Physical Android Device Verification**:
   - Automated unit tests run on host JVM with KeyStore fallback mocks; actual runtime SMS interception requires physical device permission granting (`RECEIVE_SMS` / Default SMS app role).

---

## 5. Security & Privacy Posture Audit

- **Zero Paid Dependencies**: Confirmed 0 external cloud inference or commercial API dependencies.
- **Secrets Management**: Zero hardcoded secrets in source code; production checks fail startup if secrets are under 32 characters or default.
- **Data Retention**: SMS text zero-retention enforced via HMAC-SHA256 with key rotation.
- **CORS & Headers**: Strict CORS origin whitelisting, Content-Security-Policy, X-Frame-Options, HSTS headers applied via middleware.

