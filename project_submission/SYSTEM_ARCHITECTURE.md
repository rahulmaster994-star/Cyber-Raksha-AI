# CYBER RAKSHA AI — SYSTEM ARCHITECTURE
**Comprehensive End-to-End Component & Data Flow Specification**

---

## 1. High-Level System Architecture Diagram

```
+-----------------------------------------------------------------------------------------+
|                                    CLIENT ACCESS LAYER                                  |
|                                                                                         |
|   +---------------------+   +---------------------+   +-----------------------------+   |
|   |  React 18 Desktop   |   |   Chromium Browser  |   |    Android / Mobile PWA     |   |
|   |  Web Dashboard      |   |   Extension (MV3)   |   |   (Web Share Target API)    |   |
|   +----------+----------+   +----------+----------+   +--------------+--------------+   |
+--------------|-------------------------|-----------------------------|------------------+
               |                         |                             |
               +--------------------+    |    +------------------------+
                                    |    |    |
                                    v    v    v
+-----------------------------------------------------------------------------------------+
|                               FASTAPI APPLICATION GATEWAY                               |
|                                                                                         |
|   - Defensive Security Headers (CSP, HSTS, X-Frame-Options)                             |
|   - In-Memory Sliding-Window Rate Limiter (120 req/min general, 30 req/min heavy)       |
|   - Request Observability Middleware (p50/p95/p99 latency tracker & X-Response-Time)    |
|   - Dynamic Feature Flags & Maintenance Mode Guard                                      |
+-------------------------------------------+---------------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+-----------------------+        +-----------------------+         +-----------------------+
|  DETECTION ROUTERS    |        |  THREAT INTEL ROUTERS |         |  GOVERNANCE ROUTERS   |
|  - /detection/url     |        |  - /intel/search      |         |  - /feedback/submit   |
|  - /comm/analyze      |        |  - /intel/unified     |         |  - /admin/overview    |
|  - /audio/analyze     |        |  - /intel/feed/update |         |  - /admin/feature-flag|
+-----------+-----------+        +-----------+-----------+         +-----------+-----------+
            |                                |                                 |
            +--------------------+           |           +---------------------+
                                 |           |           |
                                 v           v           v
+-----------------------------------------------------------------------------------------+
|                                  AI & RISK INFERENCE LAYER                              |
|                                                                                         |
|   +---------------------+   +---------------------+   +-----------------------------+   |
|   | Phishing Detector   |   | Communication NLP   |   | VoiceShield Audio Detector  |   |
|   | (RandomForest - 25) |   | (LinearSVC + TFIDF) |   | (RandomForest - 24 Spectral)|   |
|   +----------+----------+   +----------+----------+   +--------------+--------------+   |
|              |                         |                             |                  |
|              +-------------------+     |     +-----------------------+                  |
|                                  |     |     |                                          |
|                                  v     v     v                                          |
|                     +-----------------------------------+                               |
|                     |     UNIFIED RISK ASSESSMENT       |                               |
|                     | - Corroborating Evidence Fusion   |                               |
|                     | - Contradiction & Penalty Logic   |                               |
|                     | - Feed Freshness Discounting      |                               |
|                     +-----------------+-----------------+                               |
+---------------------------------------|-------------------------------------------------+
                                        |
         +------------------------------+------------------------------+
         |                                                             |
         v                                                             v
+-----------------------------------+         +-------------------------------------------+
|    PROACTIVE PROTECTION LAYER     |         |             PERSISTENCE LAYER             |
|                                   |         |                                           |
| - Safety Playbook Generator       |         | SQLite Relational Engine                  |
| - Incident Classifier & Escalation|         | (SQLAlchemy ORM - 12 Tables)              |
| - Action Confirmations            |         | - analysis_history  - analysis_feedback   |
| - Indian Cyber Helpline (1930)    |         | - security_incidents- threat_indicators   |
+-----------------------------------+         +-------------------------------------------+
```

---

## 2. Component Descriptions

### A. Client Access Layer
1. **React 18 Single-Page Application (SPA):** Built with TypeScript and Vite. Features a dark cybersecurity aesthetic (`#050811`), live health indicators, and reactive views for all 12 modules.
2. **Chromium Web Shield (Manifest V3):** Connects to `http://127.0.0.1:8000/api/v1/detection/url` using `chrome.tabs.query` to scan the active web page and context menus.
3. **Android / Mobile PWA:** Registers a service worker with cache-first routing for static assets and a Web Share Target manifest allowing users to share suspicious SMS/links from native mobile apps.

### B. Gateway & Middleware Layer
1. **SecurityHeadersMiddleware:** Enforces `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and `Referrer-Policy`.
2. **RateLimiterMiddleware:** In-memory sliding window keyed by client IP. Bypassed safely in test suites via `x-test-bypass-rate-limit` header.
3. **RequestObservabilityMiddleware:** Attaches high-precision duration timers to each request, logging operational statistics and adding `X-Response-Time-Ms` response header.
4. **Maintenance Mode Guard:** Halts public analysis endpoints with HTTP 503 during scheduled maintenance while leaving `/api/health` and `/admin/*` accessible.

### C. AI Detection & Inference Layer
1. **Phishing URL Classifier (`ai_engine/inference/phishing_detector.py`):**
   - Extracts 25 structural and lexical features (Shannon entropy, dot count, subdomain depth, suspicious keywords, URL length).
   - Scored by a trained Scikit-Learn `RandomForestClassifier`.
2. **Communication Fraud Detector (`ai_engine/inference/communication_detector.py`):**
   - Applies regex-based PII masking, urgency token weighting, and TF-IDF feature extraction.
   - Evaluated by a calibrated `LinearSVC` classifier for SMS spam, fake bank notices, and digital arrest extortion.
3. **Voice Deepfake Impersonation Detector (`ai_engine/inference/audio_detector.py`):**
   - Validates audio container headers (RIFF/WAV), extracts 24 acoustic spectral features (spectral centroid, bandwidth, rolloff, zero-crossing rate).
   - Classifies synthetic vocoder and TTS artifacts using an acoustic Random Forest model.

### D. Unified Risk Engine (`ai_engine/threat_intelligence/intelligence_engine.py`)
- Fuses detections from URLs, messages, and voice notes with verified threat intelligence IoCs.
- **Corroboration Logic:** Elevates risk when indicators align across multiple modalities.
- **Deduplication:** Prevents double-counting overlapping lexical markers.
- **Freshness Discounting:** Discounts stale feed indicators (> 24h old) to prevent outdated reputation skew.

### E. Persistence Layer
- SQLite relational database (`cyber_raksha.db`) managed via SQLAlchemy ORM.
- Contains 12 normalized tables: `users`, `system_configs`, `security_events`, `analysis_history`, `notifications`, `threat_indicators`, `threat_feed_logs`, `unified_risk_records`, `security_incidents`, `incident_actions`, `user_protection_settings`, and `analysis_feedback`.

