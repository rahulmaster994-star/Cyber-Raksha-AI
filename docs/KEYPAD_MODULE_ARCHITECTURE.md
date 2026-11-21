# Keypad User Protection — System Architecture & Data Flow

## 1. Architectural Philosophy: Guardian-Assisted Family Shield
Traditional keypad feature phones (Nokia 105, Samsung Guru, itel Magic, Lava Hero, Jio Bharat) run closed proprietary Real-Time Operating Systems (RTOS) or locked KaiOS environments. They lack background service multitasking, third-party telephony APIs, and background TCP/IP daemon access.

Therefore, Cyber Raksha AI implements a **Guardian-Assisted Family Shield** model:
* Guardians use their modern Android smartphones to register elderly dependents, inspect suspicious messages, verify incoming caller reputation, review incidents, and guide elderly relatives.
* The elderly citizen operates their familiar keypad phone without confusing apps, complex permissions, or hardware dongles.

```
+-------------------------------------------------------------------------------+
|                        KEYPAD USER PROTECTION ARCHITECTURE                    |
+-------------------------------------------------------------------------------+
|                                                                               |
|  [ Traditional Keypad Phone ] (Elderly Citizen)                              |
|         |                                                                     |
|         | Receives SMS / Call via 2G/4G Cellular Network                      |
|         v                                                                     |
|  [ Verbal / Manual Handoff ]                                                  |
|         | (Elder reads SMS or unknown caller number to Guardian)              |
|         v                                                                     |
|  [ Cyber Raksha Android App ] (Guardian Smartphone)                           |
|         |                                                                     |
|         +--> KeypadProtectionScreen (Jetpack Compose, 7 Tabs)                |
|         +--> KeypadProtectionViewModel (StateFlow & Coroutines)               |
|         +--> KeypadProtectionRepository (Retrofit2 & OkHttp)                  |
|         |                                                                     |
|         | HTTPS / REST (Authorization: Bearer <JWT>)                          |
|         v                                                                     |
|  [ FastAPI Backend Engine ]                                                   |
|         |                                                                     |
|         +--> /api/v1/keypad/family (Dependent CRUD & Masking)                 |
|         +--> /api/v1/keypad/check-sms (Phishing & Fraud Regex Engine)         |
|         +--> /api/v1/keypad/check-call (Anti-Sybil Reputation Check)          |
|         +--> /api/v1/keypad/report-scam (Intelligence Ingestion)             |
|         +--> /api/v1/keypad/alerts (Incident Tracking & Review)               |
|         +--> /api/v1/keypad/education (Trilingual Education Dictionary)       |
|         +--> /api/v1/keypad/helpdesks (Sanchar Saathi & 1930 Guidance)        |
|         |                                                                     |
|         v                                                                     |
|  [ PostgreSQL / SQLite Database ]                                             |
|         |                                                                     |
|         +--> keypad_elderly_users (Protected Family Profiles)                 |
|         +--> keypad_scam_reports (De-duplicated Intelligence Audit)          |
|         +--> keypad_incidents (Real-time Threat Incidents)                    |
|         +--> phone_reputation (Central Threat Score Cache)                    |
|                                                                               |
+-------------------------------------------------------------------------------+
```

## 2. Anti-Sybil Reputation Flow
To prevent weaponized or coordinated false reporting against innocent phone numbers:
1. When Guardian A reports number `+919876500001`, a row is inserted in `keypad_scam_reports`. Unique reporter count = 1. Status is `COMMUNITY_UNVERIFIED` (Risk capped at `MEDIUM` 35.0).
2. If Guardian A submits another report for the same number, the system updates Guardian A's existing evidence rather than adding a second row. Unique reporter count remains 1.
3. Only when Guardian B (a distinct authenticated user) submits a report does unique reporter count reach 2, escalating status to `CORROBORATED` (Risk 55.0+).
4. Official government feeds (e.g., DoT/Chakshu import) carry `is_verified_authority = True`, escalating status immediately to `OFFICIAL_AUTHORITY_VERIFIED` (Risk 90.0+ / Critical).

