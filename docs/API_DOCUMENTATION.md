# Cyber Raksha AI — Complete API Documentation

**Base URL (Local):** `http://127.0.0.1:8000`  
**Interactive Swagger UI:** `http://127.0.0.1:8000/docs`  
**OpenAPI JSON Specification:** `http://127.0.0.1:8000/openapi.json`  

---

## 1. Authentication Headers

| Header | Type | Description | Required On |
|---|---|---|---|
| `X-Device-Token` | `string` | Device authentication token issued during registration | Mobile & Extension device-scoped routes |
| `Authorization` | `Bearer <token>` | Admin secret or session authentication token | Admin & Incident management routes |
| `Content-Type` | `application/json` | Request payload format | All `POST`, `PUT`, `PATCH` requests |

---

## 2. API Endpoints

### 2.1 System Health
#### `GET /health`
Returns system status, active database connectivity, and uptime.
- **Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-11-10T23:30:00Z",
    "version": "1.0.0"
  }
  ```

---

### 2.2 Intelligent Threat Detection
#### `POST /api/v1/detection/url`
Analyzes a URL for phishing characteristics, brand impersonation, and structural deception.
- **Request Body:**
  ```json
  {
    "url": "http://sbi-netbanking-update.xyz/login",
    "device_id": "optional-device-uuid"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "url": "http://sbi-netbanking-update.xyz/login",
    "phishing_probability": 0.942,
    "risk_score": 92.5,
    "risk_level": "CRITICAL",
    "is_phishing": true,
    "brand_impersonation": {
      "impersonated": true,
      "brand_name": "State Bank of India",
      "matched_keyword": "sbi",
      "target_brand": "SBI"
    },
    "deceptive_indicators": [
      "SUSPICIOUS_TLD",
      "BRAND_KEYWORD_IN_UNOFFICIAL_HOST",
      "EXCESSIVE_HYPHENS"
    ]
  }
  ```

#### `GET /api/v1/detection/status`
Returns AI inference engine operational status and loaded model metadata.
- **Response (200 OK):**
  ```json
  {
    "status": "ready",
    "model_loaded": true,
    "model_type": "RandomForestClassifier",
    "features_count": 25,
    "engine_version": "1.0.0"
  }
  ```

---

### 2.3 SMS Fraud & Smishing Protection
#### `POST /api/v1/sms/analyze`
Scans SMS content for digital arrest threats, fake courier notices, banking fraud, and malicious links.
- **Request Body:**
  ```json
  {
    "message": "CBI Notice: You are under digital arrest. Pay verification fees immediately.",
    "sender": "+919876543210",
    "device_id": "b31-device-uuid"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "message_hash": "a4f89d31...",
    "risk_score": 95.0,
    "risk_level": "CRITICAL",
    "fraud_category": "DIGITAL_ARREST",
    "detected_categories": ["DIGITAL_ARREST", "URGENCY_COERCION"],
    "recommended_action": "Do not pay. Law enforcement never conducts digital arrest over calls.",
    "url_threats": []
  }
  ```

---

### 2.4 Device Registration & Management
#### `POST /api/v1/devices/register`
Registers a new client device and returns a single-use plaintext authentication token.
- **Request Body:**
  ```json
  {
    "device_name": "User Pixel 8",
    "platform": "ANDROID",
    "app_version": "1.0.0"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "device_id": "b3100000-0000-0000-0000-000000000001",
    "device_token": "secret-plaintext-token-save-now",
    "registered_at": "2026-11-10T23:30:00Z"
  }
  ```

#### `POST /api/v1/devices/heartbeat`
Pings device vitality and updates last-seen timestamps.
- **Headers:** `X-Device-Token: <token>`
- **Response (200 OK):** `{"status": "acknowledged"}`

---

### 2.5 Security Events & Incidents
#### `POST /api/v1/security/events`
Ingests telemetry events from Chrome DNR or Android security agents.
- **Request Body:**
  ```json
  {
    "event_type": "PHISHING_URL_BLOCKED",
    "severity": "HIGH",
    "source_component": "BROWSER_EXTENSION",
    "threat_indicator": "http://scam-site.com",
    "risk_score": 85.0,
    "description": "Navigation blocked by dynamic DNR rule."
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "event_id": "uuid-here",
    "incident_id": 142,
    "status": "recorded"
  }
  ```

#### `GET /api/v1/prevention/incidents`
Lists security incidents scoped to the requesting device.
- **Headers:** `X-Device-Token: <token>` or `Authorization: Bearer <admin_key>`
- **Response (200 OK):**
  ```json
  [
    {
      "id": 142,
      "incident_number": "CR-INC-2026-482103",
      "title": "HIGH Threat Intercepted: http://scam-site.com",
      "severity": "HIGH",
      "status": "ACTION_REQUIRED",
      "category": "MALICIOUS_WEBSITE",
      "created_at": "2026-11-10T23:30:00Z"
    }
  ]
  ```

---

### 2.6 Real-Time Notifications & SSE Streaming
#### `POST /api/v1/sse/ticket`
Generates a short-lived single-use ticket for connecting to the event stream.
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** `{"ticket": "single-use-ticket-string", "expires_in": 60}`

#### `GET /api/v1/sse/stream?ticket=<ticket>`
Server-Sent Events endpoint pushing real-time security alerts to the dashboard.

#### `GET /api/v1/notifications`
Retrieves persistent security notifications with multi-device scoping.
- **Query Params:** `device_id` (optional), `severity`, `is_read`, `limit`, `offset`
- **Response (200 OK):**
  ```json
  {
    "total": 12,
    "unread_count": 3,
    "items": [
      {
        "id": 1,
        "title": "Threat Blocked",
        "message": "Access to phishing domain prevented",
        "severity": "HIGH",
        "device_id": "b31-device-uuid",
        "is_read": false
      }
    ]
  }
  ```

