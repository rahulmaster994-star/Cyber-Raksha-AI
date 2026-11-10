# Cyber Raksha AI — Changelog

All notable changes to the Cyber Raksha AI project are documented in this file.

---

## [1.0.0] — 2026-11-10 (Production Release)

### Added
- **Notification Device Isolation:**
  - Added `device_id` column to `Notification` SQLAlchemy database model with index.
  - Added `device_id` field to `NotificationCreate` and `NotificationResponse` Pydantic schemas.
  - Added multi-device scoping to `list_notifications` and `get_unread_count` in `notification_service.py` and API routes.
  - Added automated security test `test_b31_notification_device_isolation` in `backend/tests/test_stage20_b3_1_security.py` (total backend tests now 371).
  - Added non-destructive database migration for `notifications.device_id` in `backend/app/database/session.py` and `backend/tests/conftest.py`.

- **Incident Uniqueness Hardening:**
  - Added collision-resistant retry loop for `incident_number` (`CR-INC-YYYY-XXXXXX`) in `backend/app/services/incident_service.py`.

- **Stage 23 End-to-End Scenarios:**
  - Implemented and verified 10 real-world fraud scenarios in `backend/tests/test_stage23_final_e2e_scenarios.py`.

- **Deployment & Production Assets:**
  - Added `Dockerfile` for backend containerization.
  - Added `docker-compose.yml` for unified local stack deployment.
  - Added `.env.example` with sanitized placeholders.
  - Added `.gitignore` tailored for Python, Node, Vite, Android, and SQLite.
  - Added `start_cyberraksha.ps1` and `scripts/health_check.ps1`.

### Changed
- **Calibrated AI Risk Scoring:**
  - Updated `ai_engine/core/prediction.py` risk calculation formula: when zero deceptive indicators exist, ML probability is capped at 25% contribution to prevent false positives on multi-hyphen corporate domains.
  - Added false-positive guards for `.gov.in`, `.gov`, and `.mil` domains in `ai_engine/core/engine.py`.
  - Added legitimate banking OTP confirmation guard in `backend/app/services/sms_analysis_service.py`.
  - Extended SBI brand profile in `ai_engine/core/brand_impersonation.py` with keywords `sbi` and `sbinetbanking`.

### Fixed
- Fixed `UnboundLocalError` for `urlparse` in `ai_engine/core/engine.py`.
- Fixed `KeyError: 'has_malicious_url'` in `backend/app/services/central_risk_engine.py`.
- Fixed test suite schema discrepancies for `Device` and `SecurityIncident` models.

---

## [0.9.0] — 2026-11-09 (Phase B4.1 & B4)
- Implemented GroupKFold 5-fold cross-validation in `ai_engine/training/` with 0% domain leakage.
- Added RandomForest classifier for lexical/structural URL phishing detection.
- Added Brand Impersonation and Digital Arrest scam detection engines.

## [0.8.0] — 2026-11-08 (Phase B3.1 & B3)
- Implemented unified `SecurityEvent` schema and Central Risk Engine.
- Added row-level 403 device isolation and single-use 60s SSE ticket service.
- Implemented HMAC-SHA256 peppered message hashing with pepper rotation support.

## [0.7.0] — 2026-11-07 (Phase B1 & B2)
- Built native Android Kotlin application with Jetpack Compose.
- Implemented `SecureTokenManager` using `AndroidKeyStore` with `AES-256-GCM`.
- Built foundation for `CallScreeningService` and SMS fraud analysis UI.

## [0.5.0] — 2026-11-06 (Phase A1, A2, A3)
- Chrome Manifest V3 extension with Declarative Net Request (DNR) blocking.
- Threat intelligence synchronization with URLhaus API.
- Security notification and alert engine with SSE real-time streaming.
