# CYBER RAKSHA AI — FINAL GAP ANALYSIS & REMEDIATION PLAN
## Master Architectural, Security, and Cross-Platform Gap Audit

**Date:** 2026-11-14  
**Audit Scope:** Entire Ecosystem (Backend, Frontend, Browser Extension, Android App, AI Engine, Database, CI/CD, Documentation)  
**Status:** ACTIVE REMEDIATION  

---

## 1. Executive Summary

This comprehensive gap analysis was conducted by auditing the complete Cyber Raksha AI codebase, live deployments (Render + Neon PostgreSQL, Vercel frontend), test suites, and hardware configurations against real-world digital fraud protection standards.

The project possesses strong foundational capabilities:
- Live FastAPI backend connected to Neon PostgreSQL with connection pooling.
- Live Vercel React/TypeScript dashboard with security headers and real-time state.
- scikit-learn machine learning classifiers for URL lexical analysis and SMS fraud detection.
- Android Jetpack Compose application with Room, DataStore, and Telecom CallScreeningService.
- Chromium Manifest V3 extension with Declarative Net Request dynamic rules.

However, several critical architectural, cross-platform, and security gaps were identified that must be remediated to achieve a production-grade, release-ready ecosystem.

---

## 2. Dependency Map & Component Architecture

```
[ Chromium Browser Extension ]           [ Android Native Mobile App ]
    |  - Declarative Net Request               |  - CallScreeningService
    |  - Threat Intel Feed Sync                |  - SMS Manual Inspection
    |  - Device Identity (UUIDv4)              |  - Encrypted Keystore Tokens
    +-----------------------+                  +-------------------+
                            |                                      |
                            | (HTTPS + Bearer Token)               | (HTTPS + X-Device-Token)
                            v                                      v
    +-------------------------------------------------------------------------------+
    |                        FASTAPI PRODUCTION CLOUD BACKEND                       |
    |                   (https://cyberraksha-backend.onrender.com)                  |
    |                                                                               |
    |  +--------------------+  +----------------------+  +-----------------------+  |
    |  | URL Phishing ML    |  | SMS Fraud Classifier |  | Threat Intel Engine   |  |
    |  | (RandomForest CPU) |  | (LinearSVC TF-IDF)   |  | (URLhaus IOC Cache)   |  |
    |  +--------------------+  +----------------------+  +-----------------------+  |
    |                                                                               |
    |  +-------------------------------------------------------------------------+  |
    |  |               CENTRAL SECURITY RISK & INCIDENT ENGINE                   |  |
    |  |  - Device-Isolated Security Event Ingestion                             |  |
    |  |  - Authoritative Source Validation (Google Safe Browsing, CERT-In)       |  |
    |  |  - Multi-Vector Incident Correlation (Browser + SMS + Call)             |  |
    |  |  - Deduplication within 30-Second Window                                |  |
    |  +-------------------------------------------------------------------------+  |
    +---------------------------------------+---------------------------------------+
                                            |
                                            v (SQLAlchemy Connection Pool)
    +-------------------------------------------------------------------------------+
    |                          NEON SERVERLESS POSTGRESQL                           |
    |                      (cyberraksha-db / US-East AWS)                           |
    |                                                                               |
    |  - Devices Table (UUIDv4, status, 256-bit token hashes)                       |
    |  - SecurityEvents Table (device-isolated audit records)                       |
    |  - SecurityIncidents Table (correlated incident lifecycle)                    |
    |  - Notifications Table (user alerts & unread counters)                        |
    |  - ThreatIndicators Table (verified indicators of compromise)                 |
    +-------------------------------------------------------------------------------+
                                            ^
                                            | (REST API + Real-Time Telemetry)
    +---------------------------------------+---------------------------------------+
    |                             VERCEL WEB DASHBOARD                              |
    |                    (https://frontend-lilac-nu-50.vercel.app)                  |
    |                                                                               |
    |  - Real-time Posture Monitor (Score: 0-100, High/Critical counts)             |
    |  - Security Incident Manager (New, Investigating, Resolved)                   |
    |  - Device Inventory & Revocation Controls                                     |
    |  - URL, SMS, and Digital Arrest Analysis Interactive Tools                    |
    +-------------------------------------------------------------------------------+
```

---

## 3. Comprehensive Gap Matrix

| Gap ID | Severity | Component | Summary of Issue | Root Cause | Required Correction | Verification Method | Status |
|---|---|---|---|---|---|---|---|
| **GAP-SEC-01** | **CRITICAL** | Browser Extension | Shared hosting suffix wildcard whitelist bypass | `isWhitelistedSafeDomain` matched `host.endsWith('.' + safe)` where `safe` included `vercel.app` & `onrender.com`. An attacker hosting a phishing site on `attacker.vercel.app` would be whitelisted. | Remove broad suffix matching for shared hosting; whitelist ONLY exact, verified infrastructure hostnames (`frontend-lilac-nu-50.vercel.app`, `cyberraksha-backend.onrender.com`). | Unit test with `evil-phishing.vercel.app` ensuring it is NOT whitelisted. | **IN PROGRESS** |
| **GAP-ARCH-02** | **HIGH** | Browser Extension | Asynchronous navigation interception misrepresentation in Chrome MV3 | `webNavigation.onBeforeNavigate` is asynchronous. In-flight cloud ML evaluation cannot guarantee blocking before initial network connection without pre-existing DNR rules. | Formally separate Known Threat Pre-Load DNR Blocking (guaranteed network block) from Unknown In-Flight ML Interception & Tab Quarantine. Update labels on warning page. | Test rule compilation timing and verify warning UI accurately reflects mode. | **IN PROGRESS** |
| **GAP-AND-03** | **MEDIUM** | Android Mobile | Hardcoded device ID in CallScreeningService & localhost default URL | `CyberRakshaCallScreeningService` used hardcoded `deviceId = "android-call-screener"`, and `AppPreferences` defaulted to `10.0.2.2:8000` (emulator-only). | Inject registered device ID from `AppPreferences` and default base URL to `https://cyberraksha-backend.onrender.com`. | Android unit tests & Gradle assemble. | **PENDING** |
| **GAP-SEC-04** | **HIGH** | Backend Risk Engine | Cross-platform multi-vector threat correlation | When a device encounters a phishing URL in the browser and subsequently receives an SMS with the same domain, correlation should unify them under one incident for that device. | Enhance correlation logic in `central_risk_engine.py` to match domains across `BROWSER_BLOCKED_URL` and `SMS_FRAUD_DETECTED` for the same device ID. | End-to-end multi-vector simulation script. | **PENDING** |
| **GAP-SEC-05** | **MEDIUM** | AI Engine | Unsafe URL shortener expansion & SSRF vulnerability | Expanding shortened URLs naively can expose the backend to Server-Side Request Forgery (SSRF) to internal cloud metadata (169.254.169.254) or private subnets. | Implement strict SSRF guards on any server-side URL resolution: validate IP resolution against private/link-local/loopback ranges. | Unit tests attempting to expand loopback and AWS/GCP metadata URLs. | **PENDING** |
| **GAP-FE-06** | **LOW** | Frontend | Hardcoded localhost fallbacks in legacy components | A few edge-case components contained fallback references to `localhost:8000`. | Ensure all API calls strictly resolve through `VITE_API_BASE_URL` with centralized error handling for Render cold starts. | Frontend production build and audit. | **PENDING** |
| **GAP-DOC-07** | **LOW** | Documentation | Inconsistent stage documentation and unsupported claims | Earlier stage documentation contained forward-looking statements that did not reflect actual final code state. | Author 10 complete, evidence-based final reports strictly reflecting tested reality. | Verification against test logs and Git history. | **PENDING** |

---

## 4. Remediation Action Plan

1. **Step 1:** Fix `rules_manager.js` to strictly eliminate shared-hosting wildcard bypasses (GAP-SEC-01).
2. **Step 2:** Refine Chrome extension warning experience and service worker to accurately distinguish between Pre-Load DNR Interception and In-Flight ML Quarantine (GAP-ARCH-02).
3. **Step 3:** Update Android `AppPreferences.kt` and `CyberRakshaCallScreeningService.kt` to bind to real device ID and live cloud URL (GAP-AND-03).
4. **Step 4:** Verify and enhance cross-platform incident correlation in `central_risk_engine.py` (GAP-SEC-04).
5. **Step 5:** Add SSRF protection guards in AI engine URL pre-processing (GAP-SEC-05).
6. **Step 6:** Run full test suites across Backend (371 tests), Extension (37 tests), and Android (Gradle build).
7. **Step 7:** Run End-to-End Cross-Platform Simulation (10 scenarios).
8. **Step 8:** Commit all verified deliverables and publish the complete final documentation suite.
