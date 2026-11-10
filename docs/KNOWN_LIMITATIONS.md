# Cyber Raksha AI — Known Limitations & Operational Boundaries

**Document Version:** 1.0  
**Date:** 2026-11-10  
**Scope:** Honest disclosure of technical constraints, hardware dependencies, and operational limits.

---

## 1. Machine Learning & Threat Detection

### 1.1 CPU Inference Latency
- **Observation:** On Windows 11 with CPU inference (scikit-learn RandomForest), warm inference latency is approximately **130–140 ms**, with total API response around **220 ms**.
- **Limitation:** While highly practical for asynchronous SMS and background checks, inline browser blocking before DNS lookup benefits from client-side cached rules. Sub-10ms inference is not achievable on CPU without quantized lightweight ONNX/C++ runtimes.

### 1.2 URL Shortener Expansion
- **Observation:** Shortened URLs (e.g. `bit.ly`, `tinyurl.com`, `t.co`) conceal their final destination from lexical inspection.
- **Limitation:** The AI engine flags them with elevated caution as `SUSPICIOUS_SHORTENER`. However, automated headless expansion/redirect following is omitted to prevent triggering web-hook alerts or SSRF vulnerabilities during automated scanning.

### 1.3 Dataset Domain Overlap (Domain Leakage in Random Splits)
- **Observation:** A naive random 70/15/15 split yields 39.3% domain overlap between train and test sets, artificially inflating accuracy metrics.
- **Resolution & Boundary:** 5-fold `GroupKFold` cross-validation was implemented in B4.1, establishing true zero-overlap performance at **98.44% accuracy**. Out-of-distribution evasion attacks (zero-day brand spoofing) may still achieve lower sensitivity until new brand profiles are ingested.

---

## 2. Android Mobile Integration

### 2.1 Physical Device Verification Requirement
- **Observation:** Unit tests and Gradle builds pass cleanly in CI/local emulators (`assembleDebug` and `testDebugUnitTest` successful).
- **Limitation:** Real-world SMS interception (`RECEIVE_SMS`) and call screening (`CallScreeningService`) require explicit runtime permissions and user role assignment (e.g., Default Caller ID & Spam app) on an actual physical Android device running API 26–34. These cannot be fully simulated headless without human-in-the-loop permission grant.

### 2.2 Android Certificate Pinning
- **Limitation:** Backend communication relies on standard HTTPS and Android network security config. Certificate transparency pinning (HPKP/Network Security Config pins) is not enabled for local `10.0.2.2` or development local IPs to allow self-signed dev certificates.

---

## 3. Backend & Storage Constraints

### 3.1 SQLite Single-Process Concurrency
- **Observation:** Development operates on SQLite with WAL mode.
- **Limitation:** SQLite is not designed for multi-node, horizontally scaled distributed deployments. Concurrent heavy write bursts across hundreds of devices can trigger `database is locked` if write locks exceed timeout. Production deployment should target PostgreSQL.

### 3.2 Ephemeral In-Memory Rate Limiter
- **Observation:** Rate limiting uses an in-memory token bucket keyed by client IP and token.
- **Limitation:** Rate limiter counters are non-persistent. Restarting the FastAPI uvicorn worker resets client request quotas. Production should integrate Redis or Memcached.

### 3.3 Notification Model Device Scoping
- **Observation:** The `Notification` database model currently lacks a dedicated `device_id` column.
- **Limitation:** Dashboard notifications function as a global operational feed. Device-specific private notifications are filtered via SSE stream parameters, but long-term notification audit logs in DB are unified.

---

## 4. Browser Extension

### 4.1 Declarative Net Request (DNR) Rule Limits
- **Observation:** Chrome Manifest V3 enforces dynamic rule quotas (maximum 5,000 dynamic rules and 30,000 regex/static rules).
- **Limitation:** Offline sync of millions of URLhaus entries is truncated to the top 1,000–5,000 high-confidence indicators. Full database lookups must route through the local backend REST API.

---

## 5. Third-Party Threat Intelligence Feeds

### 5.1 Public Feed Rate Throttling
- **Observation:** Free threat feeds (URLhaus, OpenPhish Free tier) have public rate caps and hourly update cadences.
- **Limitation:** Zero-budget architecture strictly prohibits paid commercial API keys. System relies on scheduled hourly batch synchronization rather than instant millisecond propagation of global zero-day feeds.

