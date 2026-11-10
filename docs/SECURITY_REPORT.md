# Cyber Raksha AI — Security Report & Threat Model

**Document Version:** 1.0 (Release Standard)  
**Security Status:** **NO CRITICAL VULNERABILITIES IDENTIFIED**  
**Review Standard:** OWASP Top 10, CWE / SANS Top 25, Mobile ASVS  

---

## 1. System Threat Model

```
+-----------------------------------------------------------------------------+
|                               ATTACK VECTORS                                |
|  [Phishing URLs]   [Brand Spoofing]   [Smishing/OTP]   [Malicious Calls]    |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                          CYBER RAKSHA DEFENSE TIERS                         |
|                                                                             |
|  Tier 1: Client Edge (Chrome DNR / Android Local KeyStore AES-256-GCM)       |
|  Tier 2: API Gateway (Token-Bucket Rate Limiter, Pydantic Schema Validation) |
|  Tier 3: Auth Layer (SHA-256 Device Hashes, Single-Use 60s SSE Tickets)     |
|  Tier 4: Business Logic (Central Risk Engine, Zero-Trust Score Recomputation)|
|  Tier 5: Data Privacy (Row-Level 403 Scoping, HMAC Pepper Rotation)         |
+-----------------------------------------------------------------------------+
```

---

## 2. Core Security Controls Implemented

### 2.1 Device Authentication & Token Protection
- **Entropy:** Tokens generated via `secrets.token_urlsafe(32)` providing 256 bits of cryptographic entropy.
- **Storage:** Only SHA-256 digests (`device_token_hash`) are stored in the database. Plaintext tokens cannot be extracted even in the event of database exposure.
- **Constant-Time Verification:** Token comparison employs `secrets.compare_digest` to prevent side-channel timing attacks.
- **Revocation Enforcement:** Each request checks `is_revoked`. Revoked devices are terminated with immediate HTTP 401.

### 2.2 Row-Level Multi-Device Isolation
- **Incident Scoping:** Endpoints `/api/v1/prevention/incidents` and `/api/v1/security/events` enforce that requests only return records matching the caller's verified `device_id`. Cross-device attempts yield **HTTP 403 Forbidden**.
- **Notification Privacy (Hardened):** The `Notification` model includes an indexed `device_id` column. Scoped queries return private device alerts and global system advisories only, strictly withholding private notifications from foreign devices.

### 2.3 SMS Privacy & HMAC Deduplication
- **Zero Raw Content Storage:** Message texts and phone numbers are never persisted in plaintext.
- **Keyed Hashing:** Deduplication uses HMAC-SHA256 with a secret pepper (`CYBER_RAKSHA_SMS_PEPPER`, minimum 32 characters enforced).
- **Pepper Rotation:** The system supports rotating peppers through `get_all_peppers()`, allowing smooth cryptographic key transitions without invalidating legacy deduplication caches.

### 2.4 Real-Time Streaming (SSE) Security
- **Single-Use Tickets:** SSE connections require a ticket issued via `POST /api/v1/sse/ticket` with an authorized bearer token.
- **Ephemeral TTL:** Tickets expire after 60 seconds and are invalidated immediately upon first consumption (`ticket_service.consume_ticket()`). Replay attempts are rejected.

### 2.5 Android Mobile Cryptography
- **Hardware-Backed KeyStore:** Tokens on Android are secured using `AndroidKeyStore` with `AES-256-GCM` and zero padding. Keys never leave the hardware security module (TEE/StrongBox).
- **Network Security:** Cleartext HTTP traffic is disabled in `network_security_config.xml`.

### 2.6 Rate Limiting & DoS Defense
- **Sliding Token Bucket:** Global rate limiter restricts standard requests to 120 req/min and intensive AI inference to 30 req/min.
- **Production Guard:** Rate limit bypass headers (`x-test-bypass-rate-limit`) are strictly ignored when `APP_ENV=production`.

---

## 3. Secret Scanning & Privacy Check

A comprehensive scan of the repository confirms:
- Zero committed private keys, keystores, or `.pem` files.
- Zero committed production passwords or hardcoded API tokens.
- Secret pepper and admin keys configured via environment variables with length validation ($\ge 32$ chars).
- Clean `.env.example` with generic placeholders.

