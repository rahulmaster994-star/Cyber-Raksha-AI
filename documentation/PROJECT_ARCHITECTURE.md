# Cyber Raksha AI — System Architecture & Design Specification

**System Version:** v1.0.0-rc.1  
**Architecture Pattern:** Modular Monolith with Decoupled AI/ML Engine  
**Deployment Model:** Local Offline-First Hybrid (FastAPI + React SPA + Chrome Extension)  

---

## 1. High-Level Architecture Overview

Cyber Raksha AI is structured into four primary layers:
1. **Client Tier:** React 18 Single-Page Application (Vite + Tailwind CSS), Manifest V3 Browser Extension, and Responsive PWA Shell.
2. **API & Service Tier:** FastAPI asynchronous REST server providing validation, rate limiting, and incident management.
3. **Intelligence & ML Tier:** Pure Python machine learning inference engine (`ai_engine`) operating on offline, pre-trained scikit-learn models.
4. **Data Persistence Tier:** SQLite relational storage (`cyber_raksha.db`) with SQLAlchemy ORM for analysis records, IoC feeds, and incident lifecycles.

```
┌─────────────────────────────────────────────────────────────┐
│                       Client Tier                           │
│  React SPA (Vite)  │  Browser Extension  │  PWA Shell View  │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / JSON
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Gateway Layer                    │
│   • SecurityHeadersMiddleware (CSP, HSTS, X-Frame)          │
│   • RateLimiterMiddleware (In-Memory Sliding Window)        │
│   • RequestObservabilityMiddleware (Audit Logging)          │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                      AI Detection Engine                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────┐  │
│  │  URL Phishing    │  │  Communication   │  │  Voice    │  │
│  │  RandomForest    │  │  TF-IDF+LinearSVC│  │  Deepfake │  │
│  └─────────┬────────┘  └─────────┬────────┘  └─────┬─────┘  │
│            └──────────────┬──────┴─────────────────┘        │
│                           ▼                                 │
│             Unified Risk & Correlation Engine               │
│             Cross-Signal Weighted Aggregation               │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                     Persistence Tier                        │
│   SQLite Database (cyber_raksha.db)                         │
│   • Threat Intelligence IoC Table (URLhaus, PhishTank)      │
│   • Incident Records & Recovery Actions Table               │
│   • Audit & Feedback Logging                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Machine Learning Engine Specifications

### A. Stage 2: URL & Phishing Detection Engine
- **Model:** `RandomForestClassifier` (100 estimators, max depth 20).
- **Artifact Path:** `ai_engine/models/phishing/phishing_classifier.joblib`.
- **Feature Pipeline (25 Lexical/Structural Features):**
  - URL length, hostname length, path depth.
  - Subdomain count, numeric character ratio.
  - Shannon entropy of hostname characters.
  - Brand token presence (e.g. `sbi`, `hdfc`, `paypal`, `aadhaar`).
  - Punycode homograph prefix detection (`xn--`).
  - Non-standard port markers and IPv4 host parsing.

### B. Stage 3: Communication & Digital-Arrest Detection Engine
- **Model:** `LinearSVC` with TF-IDF Vectorizer (ngram range 1-2, sublinear TF scaling).
- **Artifact Path:** `ai_engine/models/communication/communication_fraud_classifier.joblib`.
- **Hybrid Rule Engine:**
  - `DIRECT_COERCION_PATTERNS`: Identifies immediate personal threats ("I am a police officer", "you will be arrested").
  - `EDUCATIONAL_ADVISORY_PATTERNS`: Recognizes awareness articles and news alerts.
  - `NEGATION_PATTERNS`: Identifies cautionary negations ("never transfer", "courts never").
  - Gated evaluation prevents scammers from exploiting educational phrasing.

### C. Stage 4: Voice Shield / Acoustic Deepfake Detection
- **Model:** `RandomForestClassifier` trained on synthetic speech vocoder artifacts.
- **Artifact Path:** `ai_engine/models/voice/voice_deepfake_detector.joblib`.
- **Feature Extraction:**
  - Zero-Crossing Rate (ZCR).
  - Spectral Centroid, Rolloff, and Flatness.
  - Short-Time Fourier Transform (STFT) spectral variance.
- **Scope Restriction:** Evaluates vocoder and acoustic anomalies only; does not authenticate biometric speaker identity.

---

## 3. Threat Intelligence & Unified Risk Engine

- **Threat Database:** Local offline cache populated with verified indicators from URLhaus, PhishTank, and CERT-In advisories.
- **Corroboration Matrix:**
  $$\text{Risk}_{\text{unified}} = \min(100, \, w_{\text{url}} \cdot S_{\text{url}} + w_{\text{comm}} \cdot S_{\text{comm}} + w_{\text{audio}} \cdot S_{\text{audio}} + B_{\text{corroboration}})$$
  - Where $B_{\text{corroboration}} = +20$ if independent vectors confirm simultaneous extortion (e.g. URL + Digital Arrest demand).

---

## 4. Security Architecture & Controls

1. **SSRF Guard:**
   - Enforces IP validation via standard library `ipaddress`.
   - Rejects loopback (`127.0.0.0/8`, `::1`), RFC 1918 private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and AWS/cloud link-local metadata (`169.254.169.254`).
2. **Content Security Policy:**
   - App and API endpoints serve `script-src 'self'`.
   - Swagger documentation endpoints (`/docs`, `/redoc`) conditionally grant `cdn.jsdelivr.net`.
3. **Memory DoS Protection:**
   - In-memory rate limiting client records self-prune when dictionary size exceeds 5,000 entries.
4. **Admin Protection:**
   - Protected routes enforce `secrets.compare_digest` constant-time token comparison against `ADMIN_SECRET_KEY`.

