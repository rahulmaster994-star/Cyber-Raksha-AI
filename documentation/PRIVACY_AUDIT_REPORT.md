# Cyber Raksha AI — Privacy & Data Protection Audit Report

**Assessment Target:** Data Ingestion, Storage Sanitization & PII Handling  
**Standard Evaluated:** India Digital Personal Data Protection (DPDP) Act & Privacy-by-Design  
**Evaluation Date:** November 2026  
**Auditor:** Independent Cybersecurity Evaluator  
**Status:** PRIVACY COMPLIANT WITH VERIFIED SANITIZATION  

---

## 1. Executive Summary

A comprehensive data privacy and telemetry audit was conducted across the Cyber Raksha AI codebase, including database models, API services, preprocessors, browser extension, and frontend client.

The objective was to verify that no high-risk Personally Identifiable Information (PII) — specifically One-Time Passwords (OTPs), bank account numbers, UPI IDs, Aadhaar numbers, or raw biometric voiceprints — are permanently stored in database tables or leaked into operational log files.

---

## 2. PII Sanitization Inspection

### A. Message Analysis Persistence (`backend/app/services/communication_service.py`)
- **Control:** `sanitize_message_for_storage(raw_msg, max_length=120)` in `ai_engine/communication/text_preprocessor.py`.
- **Finding:** Before an analysis record is inserted into `analysis_history`, all 4-6 digit numeric sequences (OTPs), 12-digit numbers (Aadhaar), 10-digit mobile numbers, and bank account sequences are replaced with masked tokens (e.g. `[REDACTED_NUM]`).
- **Target Identifier Truncation:** Raw text snippets stored in the database are truncated to a maximum of 120 characters to prevent excessive data retention.

### B. URL Sanitization (`backend/app/services/detection_service.py`)
- **Control:** `sanitize_url_for_logging(raw_url)` in `ai_engine/utils/logging.py`.
- **Finding:** Target URLs stripped of sensitive query parameters (e.g., `?token=...`, `?auth=...`, `?password=...`) before database persistence and logging.

### C. Audio Upload Handling (`backend/app/services/audio_service.py`)
- **Control:** In-memory stream processing using `io.BytesIO`.
- **Finding:** Uploaded WAV files are processed entirely in memory buffers for acoustic feature extraction. Uploaded raw audio bytes are NOT written to permanent disk storage or retained after feature extraction completes.

---

## 3. Browser Extension & Frontend Client Audit

### A. Browser Extension (`browser_extension/`)
- **Manifest V3 Compliance:** Evaluated `manifest.json`. Permissions are restricted to `activeTab`, `storage`, and `contextMenus`.
- **Zero Passive Interception:** `background.js` only sends requests to the local backend when the user explicitly right-clicks a hyperlink and selects *"Check with Cyber Raksha AI"*. No background browsing history is transmitted or tracked.
- **Local Storage:** `chrome.storage.sync` only stores the user's configured backend API base URL (`apiUrl`). No authentication tokens, browsed URLs, or passwords are stored in extension storage.

### B. Frontend Client Secrets (`frontend/`)
- Static scan of `frontend/src/services/api.ts` confirmed zero embedded secrets, zero hardcoded JWTs, and zero cloud API keys. The frontend communicates with the backend exclusively via standard CORS-gated REST endpoints.

---

## 4. Privacy Management Endpoints

The backend provides dedicated privacy management routes under `/api/v1/privacy/`:
1. `GET /api/v1/privacy/policy` — Returns dynamic data governance notice.
2. `GET /api/v1/privacy/settings` — Returns user consent state (`telemetry_enabled`, `store_analysis_history`).
3. `PATCH /api/v1/privacy/settings` — Allows user to toggle off history retention.
4. `DELETE /api/v1/privacy/history` — Allows complete on-demand purging of stored analysis history from SQLite.

---

## 5. Privacy Audit Conclusion
The privacy architecture demonstrates compliance with privacy-by-design principles. User data minimization, in-memory audio processing, and automated PII masking ensure that sensitive financial and personal credentials are protected throughout the detection lifecycle.

