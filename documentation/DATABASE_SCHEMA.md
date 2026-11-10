# Cyber Raksha AI — Database Schema Specification

## Database Architecture
- **Engine**: SQLite (default local file `cyber_raksha.db`)
- **ORM**: SQLAlchemy 2.0
- **PostgreSQL Compatibility**: All models use standard SQL data types (`Integer`, `String`, `Text`, `Boolean`, `DateTime`, `Float`), allowing 1-click migration to PostgreSQL.

---

## Tables and Data Dictionary

### 1. `users`
Stores user identities, analysts, and access controls.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto Increment | Unique user identifier |
| `email` | String(255) | Unique, Index, Not Null | User login email address |
| `username` | String(100) | Unique, Index, Not Null | Unique username |
| `hashed_password` | String(255) | Not Null | Salted hash of credentials |
| `full_name` | String(255) | Nullable | Real name of analyst |
| `is_active` | Boolean | Default True, Not Null | Account status |
| `is_superuser` | Boolean | Default False, Not Null | Elevated permissions flag |
| `role` | String(50) | Default 'analyst', Not Null | Role: analyst, admin, auditor |
| `created_at` | DateTime | Default UTC now, Not Null | Account creation timestamp |
| `updated_at` | DateTime | OnUpdate UTC now, Not Null | Last update timestamp |

---

### 2. `system_configs`
Stores runtime parameters, alert thresholds, and integration switches.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto Increment | Unique record ID |
| `config_key` | String(100) | Unique, Index, Not Null | Configuration lookup key |
| `config_value` | Text | Not Null | Configuration value |
| `description` | String(255) | Nullable | Parameter explanation |
| `is_encrypted` | Boolean | Default False, Not Null | Flag for sensitive tokens |
| `created_at` | DateTime | Default UTC now, Not Null | Parameter creation timestamp |
| `updated_at` | DateTime | OnUpdate UTC now, Not Null | Last modified timestamp |

---

### 3. `security_events`
Stores security audit logs, incident flags, and system security events.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto Increment | Unique event ID |
| `event_type` | String(100) | Index, Not Null | Event type (e.g. AUTH, THREAT_DETECTION) |
| `severity` | String(50) | Default 'INFO', Not Null | Severity: INFO, LOW, MEDIUM, HIGH, CRITICAL |
| `source_ip` | String(45) | Nullable | Origin IPv4 or IPv6 address |
| `source_component`| String(100) | Not Null | Originating subsystem |
| `description` | Text | Not Null | Event details |
| `raw_payload` | Text | Nullable | Raw JSON payload or request headers |
| `is_resolved` | Boolean | Default False, Not Null | Resolution status flag |
| `created_at` | DateTime | Default UTC now, Not Null | Event occurrence timestamp |

---

### 4. `analysis_history`
Stores records of executed security scans and threat analyses.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto Increment | Unique analysis ID |
| `module_code` | String(50) | Index, Not Null | Module code (PHISH_DETECT, URL_DETECT, etc.) |
| `target_identifier`| String(255)| Not Null | Identifier scanned (URL, file hash, text snippet) |
| `status` | String(50) | Default 'PENDING', Not Null | PENDING, ANALYZING, COMPLETED, FAILED |
| `risk_score` | Float | Nullable | Numerical threat score (0.0 - 100.0) |
| `threat_category` | String(100) | Nullable | Identified classification |
| `summary` | Text | Nullable | Brief scan summary |
| `explanation` | Text | Nullable | Explainable AI rationale |
| `metadata_json` | Text | Nullable | Technical diagnostic parameters |
| `created_at` | DateTime | Default UTC now, Not Null | Timestamp scan was initiated |

---

### 5. `notifications`
Stores system alerts, analyst messages, and operational notifications.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto Increment | Unique notification ID |
| `title` | String(200) | Not Null | Notification title |
| `message` | Text | Not Null | Detailed notification message |
| `notification_type`| String(50) | Default 'INFO', Not Null | INFO, WARNING, ALERT, CRITICAL |
| `is_read` | Boolean | Default False, Not Null | Read/unread flag |
| `recipient_role` | String(50) | Default 'analyst', Not Null| Targeted analyst role |
| `created_at` | DateTime | Default UTC now, Not Null | Notification dispatch timestamp |
