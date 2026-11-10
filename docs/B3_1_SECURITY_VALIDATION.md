# Cyber Raksha AI — B3.1 Security Validation
## Integration Security, Privacy Isolation & Real-World Validation

**Phase:** B3.1  
**Status:** IMPLEMENTATION PARTIALLY COMPLETE — SOME CRITERIA REMAIN  
**Date:** 2026-11-10  
**Backend Tests:** 322 passed, 0 failed  
**Browser Extension Tests:** 27 passed, 0 failed  
**Android Unit Tests:** BUILD SUCCESSFUL (28 tasks)  
**Frontend Build:** SUCCESS (3.22s)

---

## 1. Architecture Changes in B3.1

### 1.1 Security Context Model

A unified `SecurityContext` class was introduced in `backend/app/core/security.py` to carry
authentication information through every request. It replaces ad-hoc header parsing scattered
across route handlers.

```
SecurityContext
├── auth_type: str           ("ADMIN" | "DEVICE" | "ANONYMOUS")
├── is_authenticated: bool
├── is_admin: bool
├── device_id: Optional[str]  (normalized device ID, None for admin/anon)
├── device: Optional[Device]  (ORM row, None for admin/anon)
├── can_access_device(target_device_id) → bool
└── can_access_incident(incident) → bool
```

The `get_security_context(request)` FastAPI dependency:
1. Checks for `X-Admin-Key` header → `auth_type=ADMIN` if secret matches.
2. Checks for `X-Device-Token` / `Authorization: Bearer <token>` / `?token=` → hashes token with
   SHA-256, looks up device row, sets `auth_type=DEVICE`.
3. Falls through to `auth_type=ANONYMOUS` with `is_authenticated=False`.

### 1.2 Multi-Device Event Deduplication Fix

Previously, `_compute_event_hash()` in `central_risk_engine.py` did **not** include `device_id`.
Two different devices reporting the same URL+event_type produced identical hashes and were
collapsed into the same incident. This was a critical correctness bug.

**Fix:** Hash now includes `device_id`:
```python
raw = f"{device_id}:{source_component}:{event_type}:{normalized_indicator.lower()}"
```

Deduplication query also filters by `SecurityEvent.device_id == device_id` to prevent
cross-device event suppression.

### 1.3 Incident Device Isolation

`incident_service.correlate_or_create_incident_from_event()` now enforces strict device scope:
- Events from Device A create/correlate incidents within Device A's scope only.
- Global incidents (device_id=None) are created for browser extension events with no device.
- Cross-device incident merge is prevented at the query level.

### 1.4 SSE Stream Device Scoping

`notification_service._subscribers` was changed from `Set[asyncio.Queue]` to
`Set[tuple[asyncio.Queue, Optional[str], bool]]` — carrying `(queue, client_device_id, is_admin)`.

`broadcast_event()` skips queues where `event.device_id != client_device_id` unless:
- The subscriber is an admin, or
- The event has no device_id (global event), or
- The subscriber has no device_id (admin listener).

Bounded queue size (maxsize=100) prevents memory exhaustion from slow clients.

---

## 2. Data Ownership Model

### 2.1 Global Threat Intelligence (Shared)

| Entity | Scope | Who Can Modify |
|---|---|---|
| `ThreatIndicator` | Global — all devices | Admin only (via `mark_false_positive` with `is_admin=True`) |
| URLhaus feed entries | Global | Automated sync only |
| `AUTHORITATIVE_SOURCES` set | Global constant | Code change only |

### 2.2 Private Incident Data (Per-Device)

| Entity | Scope | Who Can Access |
|---|---|---|
| `SecurityIncident` | Per device_id | Only the device that owns it, or admin |
| `SecurityEvent` | Per device_id | Only the device that generated it, or admin |
| SMS analysis results | Per device | Never persisted in raw form; only hash stored |

### 2.3 Key Rule

> A device can only read, acknowledge, resolve, dispute, or mark-false-positive incidents
> belonging to itself. Attempting to access another device's incident returns HTTP 403.

---

## 3. Authentication and Authorization Rules

### 3.1 Header Priority

```
X-Admin-Key: <ADMIN_SECRET_KEY>          → Full admin access (all devices)
X-Device-Token: <raw_token>              → Device-scoped access
Authorization: Bearer <raw_token>        → Same as X-Device-Token
?token=<raw_token>                       → Same (for SSE EventSource compatibility)
(none)                                   → Anonymous — read-only public endpoints only
```

### 3.2 Endpoint Access Matrix

| Endpoint | ADMIN | DEVICE (own) | DEVICE (other) | ANON |
|---|---|---|---|---|
| `GET /incidents` | All | Own only | 403 | 401 |
| `GET /incidents/{id}` | ✅ | Own only | 403 | 401 |
| `POST /incidents/{id}/acknowledge` | ✅ | Own only | 403 | 401 |
| `POST /incidents/{id}/resolve` | ✅ | Own only | 403 | 401 |
| `POST /incidents/{id}/dispute` | ✅ | Own only | 403 | 401 |
| `POST /incidents/{id}/false_positive` | ✅ (deactivates IOC) | Own (closes incident only) | 403 | 401 |
| `GET /devices/{id}/status` | ✅ | Own only | 403 | 401 |
| `GET /devices/{id}/activity` | ✅ | Own only | 403 | 401 |
| `GET /security/events` | All | Own + global | 403 for other device | 401 |
| `GET /security/stream` | All | Own + global | 403 for other device | 401 |

---

## 4. False-Positive and Dispute Lifecycle

```
Incident created
      │
      ▼
User disputes (POST /incidents/{id}/dispute)
      │
      ├─ Records dispute in evidence_references JSON
      ├─ Sets incident status = DISPUTED
      └─ Does NOT touch global ThreatIndicator.is_active
             │
             ▼
      Admin reviews
             │
      ┌──────┴──────────────────────────┐
      │                                 │
      ▼                                 ▼
Admin resolves (normal)        Admin marks false positive
(status=RESOLVED)              POST /incidents/{id}/false_positive
                               ├─ Sets incident status = FALSE_POSITIVE
                               └─ Sets ThreatIndicator.is_active = False
                                  (removes from future threat matching)
```

**Key invariant:** Only admin can deactivate a global `ThreatIndicator`. A device user's
false-positive call closes the incident but preserves the authoritative threat record.

---

## 5. Event Normalization Rules

### 5.1 URL Normalization (`normalize_url_indicator()`)

Applied before hashing, storage, and deduplication:

1. Parse with `urllib.parse.urlparse`.
2. Lowercase scheme and host.
3. Remove default ports: `:80` from HTTP, `:443` from HTTPS.
4. Sort query parameters deterministically (`urllib.parse.urlencode(sorted(...))`).
5. Remove fragment (`#...`).
6. Strip trailing slash from path (but preserve root `/`).

Examples:
```
http://EVIL.COM:80/path?b=2&a=1#frag  →  http://evil.com/path?a=1&b=2
HTTPS://EVIL.COM:443/path/            →  https://evil.com/path
```

### 5.2 Phone Normalization (`normalize_phone_indicator()`)

1. Strip all non-digit characters.
2. If result is 10 digits → prefix `+91` (Indian standard).
3. If result starts with `91` and is 12 digits → normalize to `+91XXXXXXXXXX`.
4. Otherwise → `+<digits>`.

Examples:
```
+91 98765 43210  →  +919876543210
9876543210       →  +919876543210
+1-555-123-4567  →  +15551234567
```

---

## 6. SSE Stream Security

### 6.1 Authentication

- `GET /security/stream` requires valid `X-Device-Token`, `Authorization: Bearer`, or `?token=`
  query parameter (since `EventSource` JS API cannot set custom headers).
- Revoked device tokens are rejected with HTTP 403.
- Invalid tokens (no matching device) are rejected with HTTP 401.
- Cross-device SSE subscription (requesting another device's stream) is rejected with HTTP 403.

### 6.2 Bounded Queues

- Each SSE subscriber gets a dedicated `asyncio.Queue(maxsize=100)`.
- If a slow client's queue is full, the oldest event is discarded (non-blocking `put_nowait`).
- This prevents unbounded memory growth from slow or stalled SSE clients.

### 6.3 Connection Event

On connect, the server sends a `connection` event with the subscriber's scope:
```json
{"scope": "device", "device_id": "DEVICE_UUID_HERE"}
```
or for admin:
```json
{"scope": "admin"}
```

---

## 7. Android Token Storage Implementation

### 7.1 Storage Backend

`SecureTokenManager.kt` uses Android KeyStore with AES-256-GCM:

```
AndroidKeyStore
└── Key alias: "CyberRakshaDeviceToken"
    ├── Algorithm: AES/GCM/NoPadding
    ├── Key size: 256 bits
    ├── User auth required: false (background operation)
    └── Purpose: ENCRYPT | DECRYPT
```

Encrypted value layout: `[12-byte IV] + [AES-GCM ciphertext + 16-byte auth tag]`
Stored as Base64 in `DataStore<Preferences>` (encrypted value, not plaintext).

### 7.2 Runtime Detection

`isAndroidRuntime()` checks `Build.VERSION.SDK_INT > 0` to distinguish Android from JVM.
- **Android runtime**: always uses AndroidKeyStore; no JVM fallback.
- **JVM (unit tests)**: uses a deterministic AES key derived from a fixed seed for testability.

This prevents the security anti-pattern of a try/catch that silently falls back to plaintext
or a weaker key in production.

### 7.3 Failure Semantics

| Operation | Failure Result | Consequence |
|---|---|---|
| `encrypt()` | Returns `""` | Token not stored; device must re-register |
| `decrypt()` | Returns `""` | App detects missing token; triggers re-registration |
| `wipeCredentials()` | Deletes KeyStore alias | Called on logout or token revocation |

> **Note:** If the legitimate token value is an empty string, `encrypt("")` returns `""` —
> indistinguishable from failure. This edge case is documented as a known limitation.
> Device tokens in Cyber Raksha AI are always non-empty UUID-derived strings, so this
> does not occur in practice.

### 7.4 Hardware Backing

Android KeyStore keys may be hardware-backed (StrongBox TEE) or software-backed depending on
device capability. The `KeyGenParameterSpec` does not explicitly require `.setIsStrongBoxBacked(true)`
to maintain compatibility with devices without StrongBox. Hardware backing cannot be verified
without a physical device running `KeyInfo.isInsideSecureHardware()`.

---

## 8. HMAC Pepper Configuration

### 8.1 Configuration

| Setting | Default (dev) | Production requirement |
|---|---|---|
| `CYBER_RAKSHA_SMS_PEPPER` env var | `CYBER_RAKSHA_MOBILE_SMS_PEPPER_V2_1` | Must be overridden with ≥32 random bytes |
| `ADMIN_SECRET_KEY` env var | `cyber-raksha-admin-secret-key-2026` | Must be overridden with ≥32 random bytes |

### 8.2 Startup Validation

`backend/app/main.py` `lifespan()` function raises `RuntimeError` at startup if:
- `DEBUG=False` OR `APP_ENV=="production"`, AND
- Either `SMS_PEPPER_KEY` or `ADMIN_SECRET_KEY` still holds the default value.

This prevents accidentally deploying to production with weak, public default secrets.

### 8.3 Generating Secure Values

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Run twice — once for `CYBER_RAKSHA_SMS_PEPPER`, once for `ADMIN_SECRET_KEY`.

---

## 9. Authoritative Source Verification

### 9.1 AUTHORITATIVE_SOURCES Set

```python
AUTHORITATIVE_SOURCES = {"URLHAUS", "CERT_IN", "PHISHTANK", "GOOGLE_SAFE_BROWSING"}
```

### 9.2 Client CRITICAL Cap

If a client-submitted event (Android or browser extension) claims `severity=CRITICAL`:
- The engine checks whether a matching `ThreatIndicator` row exists in `AUTHORITATIVE_SOURCES`
  OR has `confidence_score >= 0.90`.
- If not corroborated: severity is capped at `HIGH`, `verification_status = "UNVERIFIED"`.
- If corroborated: `severity = CRITICAL`, `verification_status = "CORROBORATED"`.

This prevents a compromised client from injecting false CRITICAL alerts.

### 9.3 Verification Status Values

| Status | Meaning |
|---|---|
| `CORROBORATED` | Authoritative feed confirms the indicator |
| `VERIFIED` | High confidence score (≥0.90) from known source |
| `UNVERIFIED` | Client-claimed; not in authoritative feed |

---

## 10. Rate Limiting

### 10.1 Limits

| Endpoint class | Limit |
|---|---|
| General API | 120 requests / minute |
| Heavy endpoints (SMS analysis, URL check) | 30 requests / minute |

### 10.2 Implementation

- In-memory sliding window counter (single-process).
- Keyed by `request.client.host` (IP address).
- Returns HTTP 429 with `Retry-After` header on limit exceeded.

### 10.3 Debug Bypass Guard

Rate limiting can be bypassed in development via `X-Debug-Bypass: true` header.  
In production this bypass is **explicitly blocked**:

```python
if settings.APP_ENV == "production" or not settings.DEBUG:
    # bypass header is ignored; rate limit is always enforced
```

Previously, only `settings.DEBUG` was checked — meaning `DEBUG=False` in a non-production
env still allowed the bypass. The additional `APP_ENV != "production"` guard closes this gap.

### 10.4 Known Limitation

Rate limiting is single-process and in-memory. It does not synchronize across multiple
worker processes (e.g., Uvicorn with `--workers 4`) or across separate server instances.
For distributed deployments, Redis-backed rate limiting (e.g., `slowapi` with Redis) is required.

---

## 11. Test Results

### 11.1 Backend (All Stages)

```
322 passed, 0 failed, 2 warnings
Run time: 38.66s
```

#### B3.1 Security Tests (13/13)

| Test | Status |
|---|---|
| `test_b31_multidevice_incident_creation_and_isolation` | ✅ PASSED |
| `test_b31_multidevice_incident_access_and_modification_denial` | ✅ PASSED |
| `test_b31_multidevice_device_status_and_activity_isolation` | ✅ PASSED |
| `test_b31_user_dispute_preserves_authoritative_threat_intelligence` | ✅ PASSED |
| `test_b31_admin_adjudication_can_deactivate_ioc` | ✅ PASSED |
| `test_b31_deterministic_url_normalization` | ✅ PASSED |
| `test_b31_deterministic_phone_normalization` | ✅ PASSED |
| `test_b31_distinct_source_evidence_preservation` | ✅ PASSED |
| `test_b31_revoked_device_sse_stream_rejected` | ✅ PASSED |
| `test_b31_invalid_device_token_sse_rejected` | ✅ PASSED |
| `test_b31_unauthorized_cross_device_sse_stream_rejected` | ✅ PASSED |
| `test_b31_client_cannot_forge_critical_without_authoritative_feed` | ✅ PASSED |
| `test_b31_rate_limit_bypass_forbidden_in_production` | ✅ PASSED |

### 11.2 Browser Extension

```
test_rules_manager.js:    11/11 PASSED
test_notifications.js:     6/6 PASSED
verify_a1_deep_audit.js:  10/10 PASSED
Total: 27/27 PASSED
```

### 11.3 Android Unit Tests

```
BUILD SUCCESSFUL (28 tasks)
testDebugUnitTest: PASSED
```

### 11.4 Frontend Build

```
vite v8.3.5 — 2064 modules transformed
✓ built in 3.22s
```

---

## 12. Known Limitations

### 12.1 No Distributed Rate Limiting
Single-process, in-memory rate limiter. Does not work across multiple Uvicorn workers or
server instances. Mitigation: documented; use Redis-backed rate limiter for production scale.

### 12.2 Android KeyStore Hardware Backing Not Physically Verified
Unit tests confirm software-backed AES-256-GCM KeyStore behavior via JVM fallback path.
Hardware backing (StrongBox TEE) cannot be confirmed without a physical device.
`KeyInfo.isInsideSecureHardware()` must be called at runtime on the device.

### 12.3 Physical SMS Interception Not Implemented
By design (B2.1 scope), incoming SMS interception is manual only (user pastes or uses Android
Share Target). Automatic `BroadcastReceiver`-based SMS interception would require the app to
become the default SMS handler, which is a significant UX and permission change deferred to a
future phase.

### 12.4 Physical Call Screening Not Tested
`CallScreeningService` is registered in the manifest and logic is implemented, but physical
testing requires a carrier SIM on a real Android device. Unit tests cover the logic only.

### 12.5 `encrypt("")` Edge Case
If the device token is legitimately an empty string (not expected in practice — tokens are
non-empty UUID-derived strings), `encrypt("")` returns `""` — indistinguishable from an
encryption failure. This is documented and acceptable given the token generation constraints.

### 12.6 SQLite for Production
The backend uses SQLite. For multi-user, multi-device production deployments, PostgreSQL is
recommended for concurrent write performance and proper row-level locking.

---

## 13. Physical Device Verification Remaining Items

| Item | Status | Action Required |
|---|---|---|
| Android KeyStore hardware backing | ❌ Not verified | Run `KeyInfo.isInsideSecureHardware()` on physical device |
| Incoming SMS auto-interception | ❌ Not implemented (by design) | Future phase |
| Call screening with real carrier | ❌ Not tested | Physical device + SIM required |
| Background service keepalive | ❌ Not tested | Physical device required |
| APK installation on real device | ❌ Not tested | Requires signed APK + physical device |

---

## 14. Local Development Setup

### 14.1 Environment Variables (`.env` in `backend/`)

```bash
# Generate secure values:
# python -c "import secrets; print(secrets.token_hex(32))"

CYBER_RAKSHA_SMS_PEPPER=<32-byte-random-hex>
ADMIN_SECRET_KEY=<32-byte-random-hex>
APP_ENV=development
DEBUG=True
DATABASE_URL=sqlite:///./cyber_raksha.db
```

### 14.2 Running the Backend

```bash
cd backend
source venv/bin/activate   # Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

### 14.3 Running Tests

```bash
cd cyberRaksha
$env:PYTHONPATH="$PWD;$PWD\backend"
.\backend\venv\Scripts\python.exe -m pytest backend/tests -q
```

### 14.4 Running Android Tests

```bash
cd android
.\gradlew.bat testDebugUnitTest
.\gradlew.bat assembleDebug
```

