# CYBER RAKSHA AI — Stage 6 Documentation: Proactive Threat Prevention & Incident Response Engine

## 1. Overview
Stage 6 shifts Cyber Raksha AI from passive threat analysis to proactive containment, evidence-based playbooks, and guided incident recovery.

---

## 2. Architecture & Components

- **Prevention Engine Subsystem (`ai_engine/prevention/`)**:
  - `protection_rules.py`: Canonical incident response playbooks (`PHISHING_CLICKED`, `MONEY_TRANSFERRED_SCAM`, `DIGITAL_ARREST_EXTORTION`, `VOICE_CLONING_IMPERSONATION`) and verified Indian emergency resources (Helpline 1930, cybercrime.gov.in, Chakshu).
  - `recommendation_engine.py`: Dynamic mitigation planner generating immediate, short-term, long-term, and reporting actions based on threat indicators.
  - `recovery_assistant.py`: Security Guidance Assistant explaining immediate actions for shared OTPs, money transfers, fake police calls, and compromised credentials.
  - `prevention_engine.py`: Central prevention engine coordinator.

- **Incident Response Service (`backend/app/services/incident_service.py`)**:
  - Incident tracking through full containment lifecycles (`NEW`, `ACTION_REQUIRED`, `CONTAINMENT_IN_PROGRESS`, `RESOLVED`, `CLOSED`).
  - Action checklists with user-confirmed completion tracking.
  - Defensive Posture Score calculation.

---

## 3. Database Schema Extensions

### `security_incidents`
- `id` (Integer, Primary Key)
- `incident_number` (String, Unique Index: `CR-INC-YYYY-XXXX`)
- `category` (String: `PHISHING`, `FINANCIAL_FRAUD`, `DIGITAL_ARREST`, `VOICE_CLONING`, `ACCOUNT_COMPROMISE`)
- `title` (String)
- `severity` (String: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `status` (String, Index: `NEW`, `ACTION_REQUIRED`, `CONTAINMENT_IN_PROGRESS`, `RESOLVED`, `CLOSED`)
- `summary` (Text)
- `related_analysis_id` (Integer)
- `evidence_references` (Text)
- `resolution_notes` (Text)
- `resolved_at` (DateTime)
- `created_at` / `updated_at` (DateTime)

### `incident_actions`
- `id` (Integer, Primary Key)
- `incident_id` (ForeignKey: `security_incidents.id`)
- `action_key` (String)
- `title` (String)
- `description` (Text)
- `priority` (String: `IMMEDIATE`, `SHORT_TERM`, `LONG_TERM`)
- `is_completed` (Boolean)
- `completed_at` (DateTime)

---

## 4. FastAPI Endpoints Mounted

- `POST /api/v1/incidents`: Register security incidents with automated containment actions.
- `GET /api/v1/incidents`: Retrieve open and historical incidents with status filtering.
- `GET /api/v1/incidents/{id}`: Detailed incident inspection with recovery checklist.
- `PATCH /api/v1/incidents/{id}`: Update incident status and add resolution notes.
- `POST /api/v1/prevention/actions/{action_id}/complete`: Complete a guided mitigation action.
- `POST /api/v1/prevention/recommendations`: Dynamic threat recommendations generation.
- `GET /api/v1/prevention/playbooks`: List structured guided response playbooks.
- `GET /api/v1/protection/overview`: Personal Security Center aggregate telemetry.
- `POST /api/v1/assistant/security-guidance`: Consult the AI Security Guidance Assistant.

---

## 5. Verification Results
- **Pytest**: `51 passed, 1 warning in 17.58s`
- **Frontend Build**: `✓ 2062 modules transformed. built in 2.55s (0 TypeScript errors)`

