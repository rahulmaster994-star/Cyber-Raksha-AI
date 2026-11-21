# Keypad User Protection — API Reference

Base Path: `/api/v1/keypad`  
Authentication: `Authorization: Bearer <JWT>` required on all protected endpoints.

---

### 1. Family Management

#### `POST /api/v1/keypad/family`
Registers an elderly family member under the guardian.
* **Headers:** `Authorization: Bearer <token>`
* **Request Body:**
  ```json
  {
    "full_name": "Ramesh Sharma",
    "mobile_number": "9845012345",
    "relationship": "Father",
    "device_type": "Nokia 105",
    "preferred_language": "hi",
    "consent_given": true,
    "consent_notes": "Verbal caregiver consent"
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "id": 1,
    "guardian_user_id": 10,
    "full_name": "Ramesh Sharma",
    "mobile_number": "+919845012345",
    "masked_mobile_number": "+91******2345",
    "relationship": "Father",
    "device_type": "Nokia 105",
    "preferred_language": "hi",
    "consent_given": true,
    "is_active": true,
    "created_at": "2026-11-20T17:40:00Z"
  }
  ```

#### `GET /api/v1/keypad/family`
Lists active dependents for the authenticated guardian.
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):** Array of `KeypadElderlyUserResponse`.

#### `DELETE /api/v1/keypad/family/{elderly_id}`
Deactivates a dependent record. Only succeeds if owned by the caller.
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):** `{"status": "success", "message": "Elderly dependent successfully removed."}`

---

### 2. Threat Analysis

#### `POST /api/v1/keypad/check-sms`
Analyzes SMS text for scams, phishing, and fake threats.
* **Headers:** `Authorization: Bearer <token>`
* **Request Body:**
  ```json
  {
    "message": "CBI Police Notice: Arrest warrant issued. Pay Rs 50,000 immediately.",
    "sender": "+919988776655",
    "preferred_language": "en"
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "risk_score": 85.0,
    "risk_level": "HIGH",
    "category": "DIGITAL_ARREST",
    "matched_signatures": ["GOV_IMPERSONATION_OR_ARREST_THREAT"],
    "explanation": "HIGH RISK FRAUD DETECTED!...",
    "recommended_action": "NEVER share your OTP, UPI PIN...",
    "golden_rule": "NEVER share your OTP, UPI PIN...",
    "helpline": "Call 1930 immediately...",
    "is_automatic_detection": false,
    "disclaimer": "Cyber Raksha AI analyzes SMS entered or submitted by the guardian..."
  }
  ```

#### `POST /api/v1/keypad/check-call`
Checks reputation of an incoming caller number.
* **Headers:** `Authorization: Bearer <token>`
* **Request Body:** `{"phone_number": "9876500001", "preferred_language": "en"}`
* **Response (200 OK):**
  ```json
  {
    "phone_number": "9876500001",
    "normalized_number": "+919876500001",
    "risk_level": "MEDIUM",
    "risk_score": 35.0,
    "report_count": 1,
    "verification_status": "COMMUNITY_UNVERIFIED",
    "is_automatic_blocking": false,
    "disclaimer": "Cyber Raksha AI provides reputation intelligence based on verified reports..."
  }
  ```

---

### 3. Scam Intelligence & Alerts

#### `POST /api/v1/keypad/report-scam`
Submits predatory number with Anti-Sybil de-duplication.
* **Headers:** `Authorization: Bearer <token>`
* **Request Body:** `{"phone_number": "9876500001", "fraud_category": "DIGITAL_ARREST"}`
* **Response (201 Created):** `{"id": 1, "normalized_number": "+919876500001", "status": "REPORTED", "verification_status": "COMMUNITY_UNVERIFIED"}`

#### `GET /api/v1/keypad/alerts`
Returns guardian incident summary and incident history.
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):** `KeypadAlertSummaryResponse`.

#### `POST /api/v1/keypad/alerts/{incident_id}/acknowledge`
Marks an incident as reviewed. Validates guardian ownership.

---

### 4. Education & Official Help

#### `GET /api/v1/keypad/education?lang=en|hi|kn`
Public endpoint returning localized fraud guides.

#### `GET /api/v1/keypad/helpdesks`
Public endpoint returning official reporting portals (Chakshu, 1930, 1909).

