# Cyber Raksha AI — Stage 11 Red-Team Test Plan

**Version:** 1.0.0-rc.1  
**Scope:** Internal Application Red-Team & Adversarial Security Audit  
**Classification:** Independent Evaluation / Pre-Production Validation  
**Date:** November 2026  

---

## 1. Audit Authorization & Safety Statement

### 1.1 Authorization Boundary
This assessment was performed under strict non-destructive, internal testing guidelines:
- **Authorized Target:** The local Cyber Raksha AI backend (`http://127.0.0.1:8000`), frontend client (`http://127.0.0.1:5173`), in-memory SQLite database, and local AI Engine detection pipelines.
- **Safety Envelope:** All adversarial vectors were evaluated against local test harness instances using synthetic fixtures, documented RFC test domains (`.invalid`, `.test`), documentation IP subnets (RFC 5737 `198.51.100.0/24`, `203.0.113.0/24`), and in-memory generated PCM WAV buffers.
- **Prohibitions Honored:**
  - No active outbound HTTP network connections to public infrastructure, threat feeds, or malicious staging servers.
  - No phishing simulations or coercive text delivered to real human subjects.
  - Zero use of live victim credentials, real credit card numbers, or real government identity numbers.

---

## 2. Test Plan Objectives & Coverage Matrix

| Area | Audit Scope | Objective | Methodology |
|---|---|---|---|
| **API & Transport Security** | Security headers, CORS, rate limits, DoS resistance | Identify bypasses, injection points, and state exhaustion | Dynamic fuzzing, header tampering, unit tests |
| **Authentication & AuthZ** | Admin routes (`/api/v1/admin/*`), secrets management | Verify access boundaries and default credential safety | Secret key manipulation, missing header tests |
| **SSRF & Input Injection** | `/api/v1/detection/url`, `/api/v1/intel/unified/*` | Ensure loopback, cloud metadata, and internal subnets are blocked | Boundary analysis with reserved CIDR blocks |
| **Phishing URL Detection** | Stage 2 Random Forest ML Classifier | Measure adversarial resilience, evasion, homographs, and IP URLs | 24-case controlled benchmark + metric collection |
| **Communication NLP** | Stage 3 TF-IDF LinearSVC Classifier | Measure false-alarm rates on educational/legitimate text & scam capture | 16-case synthetic red-team benchmark |
| **Audio Impersonation** | Stage 4 Random Forest Acoustic Classifier | Validate acoustic feature bounds without claiming biometric identity | In-memory WAV generation, corrupted headers, boundary tests |
| **Unified Risk Engine** | Stage 5 Cross-vector corroboration & conflict resolution | Verify dilution prevention, corroboration boost, and conflict explanations | Multi-modal conflicting payload tests |
| **Data Privacy & PII** | Analysis persistence, feedback queue, logs | Confirm PII scrubbing (phone, Aadhaar, account numbers, OTPs) | Database inspection & storage validation |

---

## 3. Test Suites & Execution Tooling

All red-team test suites are automated as reproducible Pytest integration modules located in `backend/tests/`:

1. `test_stage11_security_fixes.py` — Verifies remediation of findings SEC-001 through SEC-007.
2. `test_stage11_url_redteam.py` — Adversarial URL evasion, homographs, IP URLs, and metric calculation.
3. `test_stage11_comm_redteam.py` — Digital arrest, impersonation, utility fraud, educational false-alarm testing.
4. `test_stage11_audio_redteam.py` — Corrupted files, non-audio uploads, acoustic limits, and biometric disclaimer checks.
5. `test_stage11_risk_engine.py` — Dilution prevention, corroboration boosting, and multi-vector conflicts.

---

## 4. Evaluation Criteria & Decision Thresholds

- **Security Findings:** All CRITICAL and HIGH severity findings must be patched and retested with passing automated tests.
- **URL Classifier:** F1-score >= 0.85, False Positive Rate <= 0.05 on benchmark suite.
- **Communication Classifier:** Precision >= 0.70, Recall >= 0.60 on adversarial text fixtures.
- **Audio Classifier:** Zero crash on malformed payloads, 100% rejection of non-audio files, strict disclaimers regarding non-biometric status.
- **Overall Verdict:** AUDIT PASSED WITH LIMITATIONS (limitations clearly documented in audit findings).

