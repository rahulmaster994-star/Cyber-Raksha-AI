# 📖 CYBER RAKSHA AI — COMPLETE API SPECIFICATION
**Version:** 1.0.0 (Stage 8)  
**Base URL:** `http://127.0.0.1:8000` (Versioned: `/api/v1`)  
**Interactive Docs:** `http://127.0.0.1:8000/docs` (Swagger UI) / `/redoc`

---

## 1. System & Health

### `GET /api/health`
Checks backend responsiveness and active database query latency (`SELECT 1`).
- **Response 200 OK:**
  ```json
  {
    "status": "healthy",
    "application": "Cyber Raksha AI",
    "version": "1.0.0",
    "stage": "Stage 1-8: Final System Integration, Security Hardening & Deployment",
    "database_connected": true,
    "database_latency_ms": 1.42,
    "database_message": "Query execution succeeded (SELECT 1)",
    "uptime_seconds": 128.4,
    "timestamp": "2026-11-08T00:00:00Z"
  }
  ```

### `GET /api/system/info`
Returns architectural telemetry, engine status, implemented and planned components.

### `GET /api/v1/system/dashboard-stats`
Aggregated live counts across all 11 database tables for the operations dashboard.
- **Response 200 OK:**
  ```json
  {
    "total_analyses": 24,
    "url_threats": { "total": 12, "threats_detected": 8 },
    "comm_threats": { "total": 8, "threats_detected": 6 },
    "audio_threats": { "total": 4, "threats_detected": 2 },
    "incidents": { "active": 3, "total": 5 },
    "threat_intelligence": { "active_indicators": 140, "status": "OPERATIONAL" },
    "recent_alerts_count": 8,
    "risk_distribution": { "LOW": 8, "MEDIUM": 4, "HIGH": 7, "CRITICAL": 5 },
    "recent_analyses": [...],
    "recent_incidents": [...]
  }
  ```

---

## 2. Threat Detection

### `POST /api/v1/detection/url`
Submits target URL for machine-learning feature extraction and risk classification.
- **Request Body:**
  ```json
  { "url": "http://secure-login-hdfcbank.serveo.net/verify" }
  ```
- **Response 200 OK:**
  ```json
  {
    "success": true,
    "classification": "PHISHING",
    "risk_level": "CRITICAL",
    "risk_score": 82.8,
    "model_version": "v1.2.0",
    "confidence": 0.969,
    "analysis": {
      "features": { "url_length": 47, "dot_count": 3, "is_https": 0 },
      "risk_indicators": ["HTTP plain-text transmission", "Suspicious serveo.net tunnel"],
      "latency_ms": 78.4
    },
    "recommendation": "DO NOT visit this link or enter credentials."
  }
  ```

### `GET /api/v1/detection/status`
Returns URL detector readiness, loaded model algorithm, and metrics summary.

### `GET /api/v1/detection/history`
Returns historical URL scan records from the database (query param: `limit`).

---

## 3. Communication Fraud & Digital Arrest

### `POST /api/v1/communication/analyze`
Analyzes message text for social engineering, financial urgency, and credential theft.
- **Request Body:**
  ```json
  { "message": "URGENT: Your SBI netbanking account is blocked. Call 9876543210 immediately." }
  ```
- **Response 200 OK:**
  ```json
  {
    "success": true,
    "classification": "FINANCIAL_SCAM",
    "risk_level": "HIGH",
    "risk_score": 75.0,
    "detected_indicators": ["Financial urgency coercion", "Account block pressure"],
    "explanation": "High probability social engineering attack.",
    "recommendations": ["Do not call the provided number", "Verify with bank independently"]
  }
  ```

### `POST /api/v1/communication/digital-arrest/analyze`
Specialized evaluation of fake police/CBI warrants, Aadhaar coercion, and video arrest demands.

### `GET /api/v1/communication/history`
Returns privacy-sanitized communication analysis history.

---

## 4. Voice Deepfake Detection

### `POST /api/v1/audio/analyze` (Multipart Form-Data)
Uploads WAV recording for acoustic spectrogram and vocoder artifact analysis.
- **Form Param:** `file`: `UploadFile` (WAV format, max 25 MB).
- **Response 200 OK:**
  ```json
  {
    "classification": "LIKELY_SYNTHETIC",
    "risk_level": "HIGH",
    "risk_score": 74.2,
    "audio_metadata": { "duration_seconds": 3.4, "sample_rate": 16000, "channels": 1 },
    "detected_indicators": [
      { "code": "HIGH_FREQ_ABSENCE", "name": "Synthetic High-Frequency Cutoff" }
    ],
    "explanation": "Acoustic features demonstrate unnatural phase continuity."
  }
  ```

---

## 5. Threat Intelligence & Unified Risk

### `POST /api/v1/intel/search`
Searches query against verified IoC database cache.
- **Request Body:** `{ "query": "serveo.net" }`

### `POST /api/v1/intel/unified/analyze`
Multi-vector unified analysis combining URL, message, and digital arrest signals.
- **Request Body:**
  ```json
  {
    "url": "http://suspicious-link.com",
    "message": "Urgent update required",
    "is_digital_arrest": false
  }
  ```
- **Response 200 OK:** Returns `overall_risk_level`, `overall_risk_score`, `factual_evidence`, `model_predictions`, `limitations`, `conflict_notes`, and `recommended_actions`.

### `POST /api/v1/intel/feed/update`
Triggers inbound feed refresh from URLhaus.

### `GET /api/v1/intel/events/live`
Streams recent security events logged across the unified platform.

---

## 6. Proactive Prevention & Incidents

### `POST /api/v1/incidents`
Creates a security incident and automatically populates guided action playbooks.
- **Request Body:**
  ```json
  {
    "title": "Compromised OTP on Phishing Site",
    "category": "ACCOUNT_COMPROMISE",
    "severity": "HIGH",
    "summary": "User entered SMS OTP on deceptive portal"
  }
  ```

### `GET /api/v1/incidents`
Lists all tracked incidents with optional `status` filter (`NEW`, `ACTION_REQUIRED`, `RESOLVED`, etc.).

### `PATCH /api/v1/incidents/{incident_id}`
Updates incident status and appends resolution notes.

### `POST /api/v1/prevention/actions/{action_id}/complete`
Marks a specific user containment step (e.g. "Called bank to freeze cards") as completed.

### `POST /api/v1/assistant/security-guidance`
Interactive security Q&A assistant providing verified Indian reporting doctrine (1930 / cybercrime.gov.in).

---

## 7. Data Privacy & Governance

### `GET /api/v1/privacy/policy`
Returns full transparency policy on data collection, local SQLite storage, and redaction rules.

### `GET /api/v1/privacy/settings` & `PATCH /api/v1/privacy/settings`
Retrieves or updates data retention window (`data_retention_days`: 1 to 365) and strict privacy mode.

### `DELETE /api/v1/privacy/history`
Purges user analysis history (supports optional `module_code` filter).

### `POST /api/v1/privacy/cleanup-expired`
Automated maintenance: deletes records older than configured retention window.
