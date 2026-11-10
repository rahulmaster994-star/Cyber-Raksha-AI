# CYBER RAKSHA AI — THREAT INTELLIGENCE OPERATIONS
**Stage 9: Feed Management, Freshness Ratings, Rate Limiting & Known Constraints**

---

## 1. Threat Intelligence Feed Registry

Cyber Raksha AI integrates three primary threat intelligence sources to maintain an active database of known malicious domains, phishing infrastructure, and indicators of compromise (IoCs):

| Source Key | Source Name | Protocol | Data Type | Refresh Window |
|:---|:---|:---|:---|:---|
| **`URLHAUS`** | URLhaus (abuse.ch) | HTTP REST CSV | Malware & Phishing URLs | 6 to 12 Hours |
| **`PHISHTANK`** | PhishTank Community | Batch JSON Export | Verified Phishing URLs | 24 Hours / Cached |
| **`INTERNAL_VERIFIED`** | Cyber Raksha Curated IoCs | Relational Cache | Indian Banking & Extortion Portals | Instant Local Sync |

---

## 2. Feed Freshness Rating Methodology

Threat indicators decay rapidly in operational utility. The platform evaluates feed freshness based on the elapsed time since the latest successful synchronization:

```
                  Latest Successful Sync (T_last)
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
      < 24 Hours           24 - 72 Hours           > 72 Hours
          │                     │                     │
          ▼                     ▼                     ▼
     [ FRESH ]              [ STALE ]         [ CRITICAL_STALE ]
   Full Confidence       Confidence Penalty     Warning Attached
```

- **`FRESH (< 24h)`**: IoC signatures receive full corroboration weight in the Unified Risk Engine.
- **`STALE (24h - 72h)`**: Indicators remain active but trigger a confidence discount in multi-vector scoring.
- **`CRITICAL_STALE (> 72h)`**: Administrative warnings are triggered; indicators are treated as historical rather than active infrastructure.

---

## 3. Rate Limiting & Safe Access Policies

To prevent accidental denial-of-service against open community feeds and maintain compliance with free zero-budget tiers:

1. **URLhaus:** Enforces a hard limit of 10 requests per minute with a 15-second network timeout.
2. **PhishTank:** Supports batch export synchronization; live per-request lookups fall back to local relational cache when rate limits or quotas are approached.
3. **Internal IoC Repository:** Synchronized instantly with zero network overhead.

---

## 4. Known Feed Limitations & Operational Caveats

1. **Zero-Day Blindspot:** Community crowdsourced feeds operate on reported and vetted domains. Phishing sites registered within the last 2 hours may not yet appear in URLhaus feeds; the ML lexical classifier provides first-line defense.
2. **Regional Indian Scams:** International feeds under-report region-specific Indian scams (e.g., fake CBI/Mumbai Police Skype summons, regional electricity board APKs). Cyber Raksha's `INTERNAL_VERIFIED` repository provides curated protection for these vectors.
3. **Transient Network Partitions:** In offline or air-gapped environments, feed synchronization gracefully enters STANDBY mode while local cached signatures remain fully functional.

