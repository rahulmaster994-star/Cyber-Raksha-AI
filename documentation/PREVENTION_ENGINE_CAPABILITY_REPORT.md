# Cyber Raksha AI — Prevention Engine Capability Report

**Module Audited:** Proactive Threat Prevention & Incident Response  
**Source Files:** `backend/app/services/incident_service.py`, `ai_engine/prevention/prevention_engine.py`, `ai_engine/prevention/protection_rules.py`  
**Auditor:** Senior Incident Response Architect & Security Operations Auditor  
**Status:** **USER-ASSISTED CONTAINMENT & PLAYBOOK ADVISORY VERIFIED**  

---

## 1. Action Taxonomy & Execution Classifications

To ensure absolute technical precision, every prevention capability in Cyber Raksha AI is classified into one of four execution categories:

1. **AUTOMATIC (Zero user interaction required)**
2. **USER-CONFIRMED (Executed by system only after user explicit prompt)**
3. **RECOMMENDATION ONLY (Advisory guidance; physical action executed by user)**
4. **NOT IMPLEMENTED (No capability exists)**

---

## 2. Prevention & Incident Response Capability Audit Table

| Action / Capability | Execution Type | Implemented Mechanism | Code Evidence | Real-World Operational Scope |
|---|---|---|---|---|
| **Block confirmed malicious browser destination** | **USER-CONFIRMED** | Intercepts link opening via context menu; loads `warning.html` instead of target URL. | `browser_extension/background.js:52-56` | Halts Chromium navigation during right-click scans. Overridable by user confirmation. |
| **Display immediate security warnings** | **AUTOMATIC** | Renders high-visibility badges (`CRITICAL`, `HIGH`, `MEDIUM`) with warning explanations. | Frontend UI & `warning.html` | Displays real-time risk alerts in both web dashboard and browser extension. |
| **Create incident automatically on high threat** | **RECOMMENDATION / IN-APP** | Detection endpoints return recommendations; incidents can be registered via `POST /api/v1/incidents`. | `incident_service.py:27-96` | Inserts incident record into SQLite database with associated recovery playbook steps. |
| **Generate structured recovery playbooks** | **AUTOMATIC** | Auto-populates guided containment steps based on threat category (Phishing, Digital Arrest, Voice Cloning). | `prevention_engine.py:14-20`, `protection_rules.py` | Generates 4 to 6 ordered action steps with priority levels (`IMMEDIATE`, `HIGH`, `NORMAL`). |
| **Notify user through in-app channels** | **AUTOMATIC** | Creates in-app `Notification` and `SecurityEvent` database entries. | `app/models/notification.py`, `app/models/security_event.py` | Visible in the notification bell and security events live stream. No external push/SMS. |
| **Execute user-authorized containment actions** | **USER-ASSISTED CHECKLIST** | User marks action as completed (`PUT /incidents/{id}/actions/{action_id}/complete`). | `incident_service.py:136-140` | Marks database flag `is_completed = true`. Does NOT autonomously call external bank APIs. |
| **Change account passwords automatically** | **NOT IMPLEMENTED** | Advisory only. Playbook instructs user to visit official service settings and rotate credentials. | Playbook Step: `RESET_PASSWORD` | No identity provider (IdP) or password manager write APIs exist. |
| **Block fraudulent bank transfers automatically** | **NOT IMPLEMENTED** | Advisory only. Playbook provides official customer care phone numbers and UPI freeze instructions. | Playbook Step: `FREEZE_BANK_ACCOUNT` | No banking core API / NPCI payment gateway integration exists. |
| **Report to law enforcement automatically** | **NOT IMPLEMENTED** | Advisory only. Playbook provides national cyber crime portal URL (`cybercrime.gov.in`) and helpline `1930`. | Playbook Step: `LODGE_POLICE_COMPLAINT` | No automated CIPA/NCRB API integration exists. |

---

## 3. Incident Playbook Mapping

Cyber Raksha AI ships with four pre-configured incident response playbooks in `ai_engine/prevention/protection_rules.py`:

```
Incident Triggered
        │
        ├──────────────────────────┼──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼                          ▼
 [PHISHING_CLICKED]     [DIGITAL_ARREST_EXTORTION]   [MONEY_TRANSFERRED_SCAM]   [VOICE_CLONING_IMPERSONATION]
  1. Disconnect Session   1. Terminate Video Call     1. Call Bank Fraud Desk    1. Hang Up Phone Call
  2. Change Password      2. Note Badge Numbers       2. Dial 1930 Cyber Helpline 2. Contact Person Directly
  3. Scan Device          3. Refuse Money Transfer    3. Save Transaction UTR    3. Alert Family Members
  4. Notify Security      4. File 1930 Portal Report  4. File FIR at Police      4. Report Number to Telecom
```

### Technical Boundaries Acknowledged:
- **No Third-Party Credentials Stored:** Cyber Raksha AI never requests, stores, or transmits user banking credentials, passwords, or session tokens.
- **No Autonomous Financial Access:** The platform acts strictly as a defensive analytical barrier and guided recovery assistant. It does not possess authority or capability to move money, revoke bank accounts, or impersonate law enforcement agencies.

