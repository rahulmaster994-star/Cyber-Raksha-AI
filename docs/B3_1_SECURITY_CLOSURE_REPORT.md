# Cyber Raksha AI — B3.1 Security Closure Report
## Stage 1 Verification & Security Acceptance Gate

**Date:** 2026-11-10  
**Phase:** B3.1 Security Closure  
**Status:** COMPLETE — STAGE 1 ACCEPTANCE GATE PASSED  
**Total Backend Tests:** 341 Passed, 0 Failed  
**New Security Closure Tests:** 19 Passed, 0 Failed  
**Android KeyStore Tests:** Passed (BUILD SUCCESSFUL)

---

## 1. Objective 1 — Server-Side Confidence Validation

### Problem Addressed
Previously, client-supplied confidence scores or `is_authority=true` flags could potentially influence risk severity escalation. Clients could attempt to claim `CRITICAL` severity directly or claim authoritative threat feed origins.

### Architectural Corrections
- **Untrusted Client Inputs**: In `backend/app/services/central_risk_engine.py`, all client-supplied confidence scores and authority assertions are marked UNTRUSTED.
- **Strict Authority Decoupling**: Numerical confidence score ($\ge 0.90$) alone NO LONGER confers authoritative status. Authoritative status strictly requires that the indicator originates from verified database records belonging to `AUTHORITATIVE_SOURCES` (`URLHAUS`, `PHISHTANK`, `GOOGLE_SAFE_BROWSING`, `CERT_IN`, `TRAI_REGISTRY`, `CYBER_CRIME_PORTAL`, `GOV_DATABASE`, `ADMIN_VERIFIED`).
- **CRITICAL Classification Cap**: If an uncorroborated client reports `CRITICAL`, the severity is automatically capped at `HIGH` and marked with `verification_status="UNVERIFIED"`.
- **Explainability**: Corroboration notes detail why the severity was capped or which verified feed confirmed the escalation.

---

## 2. Objective 2 — Secure SSE Connection Ticket Mechanism

### Problem Addressed
Previously, browser `EventSource` connections could accept device tokens in URL query strings (`?token=`), risking credential leakage in server logs, reverse proxy access logs, browser history, and referer headers.

### Architectural Corrections
- **Single-Use Ticket Service**: Implemented `backend/app/services/ticket_service.py` generating cryptographically random, 32-byte tokens (`secrets.token_urlsafe(32)`) with a short 60-second expiration.
- **Ticket Issuance Endpoint**: `POST /api/v1/security/stream-ticket` requires standard header authentication (`X-Device-Token` or `X-Admin-Key`) and returns a one-time ticket bound to the caller's identity and scope.
- **Ticket Consumption**: `GET /api/v1/security/stream?ticket=<ticket>` consumes the ticket atomically. Replay or reuse attempts fail immediately with `401 Unauthorized`.
- **Prohibition of Long-Lived Tokens in URLs**: Attempting to pass `?token=<long_lived_token>` is strictly rejected with `400 Bad Request`.
- **Zero Ticket Logging**: Connection tickets are never written to disk or logs.

---

## 3. Objective 3 — Safe URL Normalization

### Problem Addressed
Previous URL normalization was overly aggressive in reordering query parameters, which could break cryptographically signed URLs (AWS S3, Azure SAS, HMAC links) and did not handle Internationalized Domain Names (IDN/Punycode).

### Architectural Corrections
- **IDN / Punycode Support**: In `backend/app/utils/helpers.py`, hostnames are encoded using RFC 3492 ASCII punycode via `idna.encode()`.
- **Signed URL Preservation**: Added `is_signed_url()` detector targeting `Signature`, `X-Amz-Signature`, `sig`, `hmac`, `sp`, `sv`, `se`. For signed URLs, exact query parameter order is preserved intact.
- **Repeated Parameters**: Query parameter parsing preserves multi-value parameters (`key=val1&key=val2`).
- **Default Port Cleanup**: Only default ports (`:80` for HTTP, `:443` for HTTPS) are removed; non-default ports (`:8080`, `:8443`) are strictly preserved.
- **Fragment Handling**: Client-side fragments (`#...`) are stripped from network destination analysis.
- **Defensive Error Handling**: Malformed or unparseable URLs return safe fallback representations without unhandled exceptions.

---

## 4. Objective 4 — HMAC Pepper Validation & Rotation

### Problem Addressed
Ensuring that production deployments cannot accidentally boot with default development secrets and providing a seamless rotation strategy for historical HMAC SMS hashes.

### Architectural Corrections
- **Production Startup Validation**: In `backend/app/main.py` `lifespan()`, the application aborts with `RuntimeError` if `CYBER_RAKSHA_SMS_PEPPER` or `ADMIN_SECRET_KEY` is missing, default, or less than 32 characters in production mode.
- **Historical Pepper Rotation**: `backend/app/services/sms_analysis_service.py` supports `CYBER_RAKSHA_SMS_PREVIOUS_PEPPERS`. The `verify_message_hash()` method checks active and historical peppers to prevent breaking historical audit deduplication.
- **Information Leakage Prevention**: Verified via tests that neither the pepper nor its internal configuration is ever exposed in API responses or logs.

---

## 5. Objective 5 — Android KeyStore Verification

### Problem Addressed
Ensuring that Android production builds cannot fall back to plaintext tokens or weak keys when storing device credentials.

### Architectural Corrections & Testing
- **Runtime Detection**: `SecureTokenManager.kt` verifies `isAndroidRuntime()`. Production builds running on Android OS strictly invoke the hardware KeyStore. The software fallback key is restricted to JVM host unit tests where `SDK_INT == 0`.
- **Safe Failure Semantics**: Encryption and decryption failures return empty strings `""` to enforce re-authentication rather than persisting plaintext tokens.
- **Unit Test Suite**: Created `SecureTokenManagerTest.kt` verifying encryption roundtrip, tampered ciphertext rejection, truncated IV rejection, blank input handling, and credential wiping.

---

## 6. Stage 1 Acceptance Gate Results

| Acceptance Criteria | Verification Method | Status |
|---|---|---|
| Client confidence cannot bypass authoritative feed validation | `test_client_cannot_force_critical_with_high_confidence` | ✅ PASSED |
| Client-forged authority claims rejected | `test_client_claiming_authoritative_source_name_is_not_trusted` | ✅ PASSED |
| SSE prohibits long-lived tokens in query parameters | `test_sse_long_lived_token_in_query_param_rejected` | ✅ PASSED |
| Single-use connection tickets work and reject replays | `test_sse_stream_ticket_single_use_consumption` | ✅ PASSED |
| Expired connection tickets rejected | `test_sse_stream_ticket_expired_rejected` | ✅ PASSED |
| Revoked device tickets rejected | `test_sse_stream_ticket_revoked_device_rejected` | ✅ PASSED |
| URL normalization handles IDN, signed URLs, default ports | `test_url_normalization_*` (7 tests) | ✅ PASSED |
| HMAC pepper rotation and non-exposure verified | `test_sms_pepper_*` (3 tests) | ✅ PASSED |
| Android KeyStore tests pass in testDebugUnitTest | Gradle `:app:testDebugUnitTest` (28 tasks) | ✅ PASSED |
| Full backend regression suite passes | Pytest 341 tests | ✅ 341/341 PASSED |

**Gate Outcome:** ACCEPTED. Proceeding to Stage 2: B4 Intelligent Threat Detection.

