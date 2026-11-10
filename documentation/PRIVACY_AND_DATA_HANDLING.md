# 🛡️ CYBER RAKSHA AI — PRIVACY & DATA GOVERNANCE POLICY
**Stage 8: Data Privacy, User Retention Control & Redaction Standards**

---

## 1. Privacy Principles

1. **Local-First Processing:** By default, all machine-learning model inference and database persistence runs locally on the user's host machine. No user telemetry is sent to cloud providers.
2. **Zero Commercial Data Sharing:** User submissions, scanned URLs, text messages, and audio samples are never sold, monetized, or shared with advertisers.
3. **Automatic In-Memory Redaction:** Highly sensitive personal data (OTPs, Aadhaar/national IDs, payment card numbers) is redacted prior to database write operations.
4. **User-Controlled Retention:** Users have sovereign control over how long records are preserved, ranging from 1 to 365 days, with on-demand purge APIs.

---

## 2. What Data Is Collected and Processed?

| Input Vector | Purpose of Processing | Stored in Database? | Redaction Policy |
|---|---|---|---|
| **Submitted URLs** | Extract 25 lexical/structural features for phishing classification. | Yes (`analysis_history`). Basic auth passwords and tracking query parameters stripped. | Sanitized URL logged; passwords stripped. |
| **Submitted Messages** | Detect impersonation, financial fraud, and digital arrest coercion signatures. | Yes (`analysis_history`). | **Mandatory Redaction:** OTPs -> `[REDACTED_OTP]`, Aadhaar -> `[REDACTED_AADHAAR]`, Cards -> `[REDACTED_CARD]`. Message truncated to 500 characters. |
| **Audio Recordings** | Detect neural vocoder and spectral boundary artifacts. | **NO raw audio is stored on disk.** | Only filename, duration, sample rate, and computed risk score are logged in `analysis_history`. |
| **Security Incidents** | Track containment steps and recovery progress. | Yes (`security_incidents`, `incident_actions`). | Contains user-provided title, severity, category, and action completion timestamps. |

---

## 3. External Network Communication

- **Inbound Threat Feeds:** The platform periodically fetches public malware/phishing domain lists from URLhaus (abuse.ch) to update local threat intelligence caches.
- **Outbound User Data:** User-submitted content is **NOT** forwarded to external cloud analysis APIs by default.

---

## 4. User Deletion & Retention Controls

Users can control their data via dedicated REST API endpoints:
- **`GET /api/v1/privacy/policy`**: Retrieve current transparency and data policy details.
- **`GET /api/v1/privacy/settings`**: View data retention days limit and strict privacy mode.
- **`PATCH /api/v1/privacy/settings`**: Update retention window (e.g. set to 30 days).
- **`DELETE /api/v1/privacy/history`**: Purge all stored historical analyses on-demand.
- **`DELETE /api/v1/privacy/history/{id}`**: Delete a single specific analysis record.
- **`POST /api/v1/privacy/cleanup-expired`**: Automatically remove records older than the configured retention window.

