# Cyber Raksha AI — Threat Intelligence Automation Audit

**Module Audited:** Threat Intelligence & Feed Management Engine  
**Source Files:** `backend/app/services/threat_intel_service.py`, `ai_engine/threat_intelligence/feed_updater.py`, `ai_engine/threat_intelligence/threat_database.py`  
**Auditor:** Threat Intelligence Specialist & Backend QA Engineer  
**Status:** **ON-DEMAND REFRESH & AIR-GAPPED OFFLINE OPERATION VERIFIED (NO BACKGROUND CRON)**  

---

## 1. Architectural Distinction: Local Cache vs. Automated Sync

A rigorous distinction must be drawn between **locally seeded threat intelligence** and **automatically refreshed threat intelligence**:

- **Locally Seeded Database:** **VERIFIED ACTIVE**
  - Pre-populated with verified IOCs from abuse.ch URLhaus, PhishTank, and CERT-In advisories.
  - Stored in SQLite (`threat_indicators` table) and indexed in an in-memory dictionary for zero-latency lookups.
- **Automated Scheduled Background Refresh:** **NOT IMPLEMENTED**
  - There is no background cron job, `apscheduler` daemon, or timer thread continuously polling external feeds on a fixed schedule.
- **On-Demand / API-Triggered Refresh:** **VERIFIED IMPLEMENTED**
  - Invoking `POST /api/v1/intel/feed/update` initiates a live pull from the URLhaus recent threat feed (`https://urlhaus-api.abuse.ch/v1/urls/recent/limit/20/`).

---

## 2. Seven-Point Automation Audit

| # | Evaluated Requirement | Current Implementation Status | Code Evidence | Verdict |
|---|---|---|---|---|
| 1 | **Feeds refresh automatically** | Feeds do not refresh on automated timers. They refresh when triggered via API or admin action. | `backend/app/main.py:32` (Lifespan only initializes DB, does not start feed worker) | **PARTIALLY IMPLEMENTED** (On-demand only) |
| 2 | **Scheduled jobs actually run** | `/api/v1/jobs` manages asynchronous user analysis tasks (URL, Comm, Unified) in a `ThreadPoolExecutor`. It is not a recurring threat feed scheduler. | `backend/app/api/routes/jobs.py:15-109` | **VERIFIED FOR JOBS / NOT FOR FEEDS** |
| 3 | **Feed timestamps recorded** | When feed update runs, records `last_update` ISO timestamp and logs entry in `ThreatFeedLog` table. | `feed_updater.py:59`, `threat_intel_service.py:118-124` | **PASS** |
| 4 | **Stale indicators handled** | `ThreatIndicator` table has `is_active` boolean and `first_seen_at` / `last_seen_at` timestamps. | `backend/app/models/threat_intel.py:19-21` | **PASS** |
| 5 | **Failed updates trigger errors** | When network is unreachable or URLhaus API times out (5s timeout), catches exception and returns `status: "OFFLINE_FALLBACK"` without crashing. | `feed_updater.py:68-76` | **PASS** (Defensive error handling) |
| 6 | **New indicators reach detection engine** | Calling `add_indicator()` adds IOC to `threat_indicators` in-memory lookup cache and SQLite, immediately accessible to `ai_engine.predict_url()` (step 2b). | `ai_engine/core/engine.py:80-84` | **PASS** |
| 7 | **Works safely when offline** | When internet is disconnected, URL and communication detection models run 100% locally using offline weights and existing threat cache. | Verified in regression tests with bypass headers. | **PASS** (Air-gapped resilient) |

---

## 3. Feed Update Lifecycle & Data Flow

```
[Administrator / API Client]
             │
             ▼ POST /api/v1/intel/feed/update
[ThreatIntelService.trigger_feed_update(db)]
             │
             ▼
[feed_updater.update_urlhaus_feed()]
             │
     ┌───────┴────────────────────────┐
     ▼                                ▼
[Network Connected]          [Network Offline / Timeout]
  • GET urlhaus API            • Catch Exception
  • Parse recent 20 URLs       • Set status = "OFFLINE_FALLBACK"
  • add_indicator(...)         • Duration recorded
  • In-memory cache updated    • Local cache preserved (Safe)
     │                                │
     └───────┬────────────────────────┘
             ▼
[Log to ThreatFeedLog Table in SQLite]
             │
             ▼
[Record Telemetry in threat_intel_ops]
             │
             ▼ Return JSON summary
```

---

## 4. Recommendations for Full Automation

To achieve unattended threat intelligence synchronization:
1. **Background Job Scheduler:** Add `APScheduler` or an `asyncio` task to `backend/app/main.py` lifespan:
   ```python
   async def schedule_feed_updates():
       while True:
           await asyncio.sleep(3600)  # Every 1 hour
           feed_updater.update_urlhaus_feed()
   ```
2. **CERT-In Advisory Parser:** Expand beyond URLhaus by adding an RSS/XML parser for Indian CERT-In vulnerability bulletins.

