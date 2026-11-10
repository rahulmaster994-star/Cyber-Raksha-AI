# CYBER RAKSHA AI — LIVE PILOT TEST PLAN
**Stage 9: Validation, Quality Assurance & Security Acceptance Matrix**

---

## 1. Executive Summary & Objective

This Pilot Test Plan defines the formal validation protocol for transitioning the Cyber Raksha AI platform from an integrated development artifact to a field-tested, production-grade cybersecurity tool. The testing scope spans functional accuracy, operational reliability, resilience under load, privacy safeguards, and administrative security controls.

All validation procedures are designed to run under a zero-budget deployment constraint without dependencies on paid cloud services.

---

## 2. Test Environment Specifications

| Component | Specification |
|:---|:---|
| **Host Node** | Local Workstation / Continuous Integration Runner (`DESKTOP-5SJO5Q8`) |
| **Operating System** | Windows 11 64-bit |
| **Python Runtime** | Python 3.13.14 (Virtual Environment: `backend/venv`) |
| **Backend Framework** | FastAPI 0.115+ on Uvicorn ASGI Server |
| **Database** | SQLite Relational Engine (`cyber_raksha.db`, SQLAlchemy ORM) |
| **AI Inference** | Scikit-Learn 1.6+ (Joblib Serialized Models) |
| **Frontend Runtime** | Node.js 20+ with Vite 8.3 & React 18 |
| **Test Client** | Pytest 9.2.0 with AnyIO 4.15 & HTTPX 0.28+ |

---

## 3. Test Matrix & Validation Scenarios

### A. Functional Detection & Inference Scenarios

| Scenario ID | Test Name | Target Subsystem | Input Vector | Expected Verdict | Verified Result |
|:---|:---|:---|:---|:---|:---|
| **TC-F01** | Benign Top-100 URL | Phishing Detector | `https://www.google.com` | `LEGITIMATE`, Score < 30 | PASS |
| **TC-F02** | Credential Harvesting URL | Phishing Detector | `https://paypa1-security-verification.xyz/login.php` | `PHISHING`, Score > 70 | PASS |
| **TC-F03** | Indian Banking OTP Scam | Communication NLP | SMS demanding KYC update with urgent link | `PHISHING` / `OTP_THEFT`, High Risk | PASS |
| **TC-F04** | Digital Arrest Extortion | Communication NLP | Threat of CBI arrest warrant & Skype call | `DIGITAL_ARREST_SCAM`, Critical Risk | PASS |
| **TC-F05** | Harmless Everyday Message | Communication NLP | Dinner invitation / delivery notification | `SAFE` / `INCONCLUSIVE`, Low Risk | PASS |
| **TC-F06** | Synthesized Audio Deepfake | VoiceShield RF | Acoustic spectral features from TTS/vocoder | `SYNTHETIC_MANIPULATED`, High Risk | PASS |
| **TC-F07** | Cross-Vector Corroboration | Unified Risk Engine | Extortion message + malicious link simultaneously | Corroborated High Risk, Multi-Factor | PASS |

### B. Reliability, Observability & Resilience Scenarios

| Scenario ID | Test Name | Target Subsystem | Condition | Success Criteria | Verified Result |
|:---|:---|:---|:---|:---|:---|
| **TC-R01** | Subsystem Health Check | Observability Service | `GET /api/v1/monitoring/health/detailed` | Returns status for API, DB, AI, Feeds, Workers | PASS |
| **TC-R02** | Real-Time Latency Tracking | Observability Middleware | 10+ sequential API calls | `X-Response-Time-Ms` header present; p95 calculated | PASS |
| **TC-R03** | Database Outage Degraded Mode | Session Manager | Simulated DB disconnect | Platform reports `DEGRADED`, returns cached responses | PASS |
| **TC-R04** | AI Model Drift Telemetry | Model Monitor | Input length and entropy tracking | Baseline vs observed comparison logged without auto-retrain | PASS |
| **TC-R05** | Threat Feed Freshness Rating | Threat Intel Ops | URLhaus & PhishTank feed checks | Telemetry records freshness tier (`FRESH` / `STALE`) | PASS |
| **TC-R06** | Async Job Queueing & SSE | Job Manager | `POST /api/v1/jobs/submit` | Returns 202 Accepted, tracks progress to COMPLETED | PASS |

### C. Security, Governance & Human-in-the-Loop Scenarios

| Scenario ID | Test Name | Target Subsystem | Security Constraint | Verified Result |
|:---|:---|:---|:---|:---|
| **TC-S01** | Admin Authentication Gate | Admin Routes | Requests without `X-Admin-Key` return 401 Unauthorized | PASS |
| **TC-S02** | Feature Flag Safety Toggle | Feature Flags | Disabling flag blocks subsystem instantly | PASS |
| **TC-S03** | Maintenance Mode Guard | Global Middleware | 503 Service Unavailable returned on public endpoints | PASS |
| **TC-S04** | Privacy PII Sanitization | Text Preprocessor | Credit cards, Aadhaar (12-digit), OTPs masked | PASS |
| **TC-S05** | Zero Auto-Retrain Enforcement | Feedback & Admin | User feedback queued as PENDING; no weights altered | PASS |
| **TC-S06** | Rate Limiting Enforcement | Security Middleware | Exceeding 120 req/min yields 429 Too Many Requests | PASS |

---

## 4. Test Execution Summary

The complete automated pilot test suite is executed using pytest:
```bash
python -m pytest backend -v --tb=short
```

**Results:**
- **Total Tests Executed:** 99
- **Passed:** 99
- **Failed:** 0
- **Execution Duration:** 38.75 seconds
- **Pass Rate:** 100.0%

