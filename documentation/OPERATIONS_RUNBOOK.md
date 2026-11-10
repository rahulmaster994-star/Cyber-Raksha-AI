# CYBER RAKSHA AI — OPERATIONS RUNBOOK
**Stage 9: Day-2 Operational Procedures, Health Inspection & Incident Triage**

---

## 1. System Startup & Service Verification

### A. Start the Backend API Server
```bash
# Navigate to project root
cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha

# Activate virtual environment and start FastAPI
backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### B. Start the Frontend Development / Preview Server
```bash
cd frontend
npm run dev
# Accessible at http://localhost:5173
```

### C. Verify Basic Platform Health
```bash
curl -s http://localhost:8000/api/health | jq .
```
Expected output:
```json
{
  "status": "HEALTHY",
  "application": "Cyber Raksha AI",
  "database_connected": true,
  "stage": "Stage 1-9: Live Pilot Validation, Model & System Monitoring"
}
```

---

## 2. Routine Health Inspection & Daily Checks

1. **Check Subsystem Health:**
   Inspect `http://localhost:8000/api/v1/monitoring/health/detailed` to confirm API server, database, all 3 AI models, and feeds are marked `HEALTHY` or `READY`.
2. **Review Feed Freshness:**
   Check `http://localhost:8000/api/v1/monitoring/feeds` to ensure URLhaus feed is within the 24-hour window.
3. **Inspect Alert Status:**
   Open the Operations Center (`/admin` tab in frontend) and review any active alerts.

---

## 3. Operations Center Access & Authentication

Administrative routes are protected by the `X-Admin-Key` header:
- **Default Key:** Configured via `ADMIN_SECRET_KEY` in `backend/.env`.
- In the frontend, enter the key in the **Admin** tab. The key is securely stored in browser `sessionStorage` for the active session.

---

## 4. Emergency Subsystem Toggles (Feature Flags)

If a third-party service or model behaves anomalously during live pilot operations:

| Objective | Action |
|:---|:---|
| **Disable Audio Analysis** | Toggle `enable_audio_analysis` to `false` via `/admin` tab or `PATCH /api/v1/admin/feature-flags/enable_audio_analysis`. |
| **Halt Threat Intel Sync** | Toggle `enable_threat_intel_sync` to `false` to stop URLhaus pulls during external network outages. |
| **Pause Job Queue** | Toggle `enable_async_jobs` to `false` if thread pool exhaustion occurs. |
| **Activate Maintenance Mode** | Toggle `maintenance_mode` to `true`. Public endpoints return 503; health and admin endpoints remain accessible. |

---

## 5. Log Inspection & Troubleshooting

- **Server Logs:** Output directly to stdout/stderr in standard timestamped format.
- **Database Inspection:**
  ```bash
  sqlite3 cyber_raksha.db "SELECT count(*) FROM analysis_history;"
  sqlite3 cyber_raksha.db "SELECT count(*) FROM analysis_feedback WHERE review_status='PENDING';"
  ```
- **Clearing Acknowledged Alerts:**
  Trigger `POST /api/v1/admin/alerts/clear` with `X-Admin-Key` header.

