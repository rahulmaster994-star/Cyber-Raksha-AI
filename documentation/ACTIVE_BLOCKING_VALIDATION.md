# Cyber Raksha AI — Active Blocking Capability Validation

**Audit Focus:** Analysis of Automated Blocking vs. User-Assisted Containment vs. Advisory  
**Evaluation Target:** Backend Gateway, API Routers, and Chromium Browser Extension  
**Auditor:** Senior Security Architect & Penetration Tester  
**Status:** **PARTIAL ACTIVE BLOCKING (GATEWAY & USER-TRIGGERED EXTENSION ONLY)**  

---

## 1. Executive Summary

This validation assesses where and how Cyber Raksha AI actively halts malicious activity. 

Active blocking is classified into three distinct layers:
1. **API / Gateway Perimeter:** **VERIFIED ACTIVE BLOCKING** (Autonomous)
2. **Browser Navigation:** **VERIFIED USER-ASSISTED BLOCKING** (Requires Context-Menu Trigger)
3. **Operating System & Network Stack:** **NOT IMPLEMENTED** (No packet filter, DNS proxy, or firewall hooks)

---

## 2. Layer-by-Layer Blocking Analysis

### Layer 1: API Gateway Perimeter (Autonomous Active Blocking)
- **Component:** `backend/app/core/security.py` (`validate_safe_url`, `_is_ssrf_host`)
- **Mechanism:** Deterministic regex, protocol parsing, and `ipaddress` network range filtering.
- **Autonomous Action:** When a client submits a URL targeting loopback (`127.0.0.1`), RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), AWS metadata (`169.254.169.254`), or dangerous schemes (`javascript:`, `file:`, `data:`), the gateway immediately terminates the request with **HTTP 400 Bad Request**.
- **Evidence:** Tested in `test_stage11_security_fixes.py` (`test_sec_007_ssrf_loopback_and_metadata_blocked`) and `test_stage12_e2e_demo.py` (`test_d1_08_ssrf_blocked`).
- **Verdict:** **VERIFIED ACTIVE BLOCKING**.

### Layer 2: Browser Extension Interception (User-Assisted Blocking)
- **Component:** `browser_extension/background.js` (lines 50–56), `warning.html`
- **Mechanism:**
  1. User right-clicks a hyperlink on any page.
  2. Selects "Check with Cyber Raksha AI".
  3. `background.js` executes `fetch('/api/v1/detection/url')`.
  4. If `risk_level` is `CRITICAL` or `HIGH`, the extension does **not** navigate to `targetUrl`.
  5. Instead, it creates a new tab loading `warning.html?url=...&level=CRITICAL`.
- **User Override:** On `warning.html`, clicking "Override & Proceed" prompts a modal confirmation (`confirm(...)`). Only upon explicit user confirmation does the browser proceed to the target URL.
- **Fail-Safe Behavior:** If the backend API is offline or returns an error, `background.js` opens `warning.html?reason=API_OFFLINE`. It explicitly avoids treating an unverified or failed scan as safe.
- **Limitations:**
  - Standard left-clicks on hyperlinks are **not** intercepted.
  - Manual entries into the browser address bar (omnibox) are **not** intercepted.
  - Interception requires user initiation via the context menu.
- **Verdict:** **VERIFIED USER-ASSISTED BLOCKING**.

### Layer 3: Operating System & Network Blocking (Not Implemented)
- **Evaluated Capabilities:**
  - DNS sinkholing / local `/etc/hosts` modification: **NOT IMPLEMENTED**.
  - Local VPN / Windows Filtering Platform (WFP) packet drop: **NOT IMPLEMENTED**.
  - Process termination of malicious software: **NOT IMPLEMENTED**.
  - Financial transaction / UPI API interception: **NOT IMPLEMENTED**.
- **Verdict:** **NOT IMPLEMENTED**.

---

## 3. Blocking Capability Comparison Table

| Threat Vector | Interception Point | Type of Action | Automated? | User Override? | Test Evidence |
|---|---|---|---|---|---|
| **SSRF Attacks** | FastAPI Gateway | Rejects request with HTTP 400 | **YES** | NO | Verified in 9 automated test vectors |
| **Dangerous Schemes (`javascript:`)** | FastAPI Gateway | Rejects request with HTTP 400 | **YES** | NO | Verified in test suite |
| **Rate Limit Violations** | RateLimiterMiddleware | Rejects with HTTP 429 Too Many Requests | **YES** | NO (Temporary cooldown) | Verified in `test_sec_001` & `test_security_hardening.py` |
| **Phishing Links (Context Menu)** | Browser Extension Service Worker | Halts tab creation; routes to `warning.html` | **NO** (User-initiated check) | **YES** (Via modal confirmation) | Verified in `background.js` & `warning.js` |
| **General Web Traffic (Omnibox / Left-click)** | Browser Network Stack | None | **NO** | N/A | Manifest lacks `declarativeNetRequest` |
| **Malicious SMS / WhatsApp** | Mobile OS | None | **NO** | N/A | PWA sandboxed from native telephony |
| **Bank Account Transfer** | Financial Provider | Advisory only | **NO** | N/A | Playbook recommendation to call 1930 |

