# Cyber Raksha AI — Chromium Browser Shield (Phase A1)

**Version:** 1.1.0 (Manifest V3)  
**Protection Architecture:** Native Declarative Net Request (DNR) Dynamic Rules + Threat Intelligence Sync + Context-Menu AI Inspection.

---

## 1. Overview & Capabilities

Cyber Raksha AI Browser Shield protects Chromium-based browsers (Chrome, Edge, Brave, Opera) against phishing, fraud, credential harvesting, and malware delivery.

### Key Capabilities in Phase A1:
1. **Automated Declarative Network Request (DNR) Blocking:**
   - Evaluates URL navigations directly inside Chromium's native C++ network engine.
   - Blocks confirmed malicious destinations **before** the request reaches the server or the first byte of page content is downloaded.
   - Redirects blocked navigations to `warning.html` with full threat intelligence evidence.
2. **Dynamic Threat Intelligence Synchronization:**
   - Synchronizes verified threat indicators from the Cyber Raksha AI backend (`/api/v1/intel/indicators`).
   - Automatically schedules hourly refreshes via `chrome.alarms`.
   - Supports manual synchronization from popup and options UI.
   - **Fail-Safe Offline Mode:** If the backend is unreachable, previously installed dynamic rules remain active in the browser.
3. **Explicit User Override with Session Allow Rules:**
   - If a user chooses "Proceed Anyway (Unsafe Override)", a high-priority session allow rule (`priority: 100`) is installed to permit navigation without an infinite redirect loop.
4. **Preserved On-Demand AI Scanning:**
   - Retains right-click "Check with Cyber Raksha AI" on any link.
   - Popup provides real-time active tab scanning and manual link analysis against the Random Forest ML classifier.

---

## 2. Browser Permissions & Privacy Justification

| Permission | Purpose | Privacy Impact |
|---|---|---|
| `declarativeNetRequest` | Enables local Chromium dynamic rule evaluation to block known malicious destinations before page load. | High efficiency; rules evaluate locally without sending browsing history to external servers. |
| `activeTab` | Grants temporary access to the active tab URL only when the user explicitly clicks the popup icon or context menu. | Restricts access to user-initiated actions; no background tab snooping. |
| `contextMenus` | Adds the right-click "Check with Cyber Raksha AI" option to link elements. | None; only invoked when user right-clicks a hyperlink. |
| `storage` | Persists user settings (API URL) and threat indicator metadata locally. | Stored strictly in local browser profile. |
| `alarms` | Triggers periodic (hourly) threat intelligence synchronization from the local backend. | Background timer for automated feed freshness. |
| `host_permissions: ["*://*/*"]` | Required by Chromium Manifest V3 to permit Declarative Net Request rules to redirect matching navigations to `warning.html`. | Strictly used for redirecting blocked malicious destinations to the local warning interstitial. |

---

## 3. Installation & Loading Instructions

1. **Start Backend Server:**
   ```powershell
   cd c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha
   $env:PYTHONPATH="c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha;c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\backend"
   .\backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Open Extensions Page:**
   - Open Chrome or Edge and navigate to `chrome://extensions/` (or `edge://extensions/`).

3. **Enable Developer Mode:**
   - Toggle the **Developer mode** switch in the top-right corner.

4. **Load Unpacked Extension:**
   - Click the **Load unpacked** button.
   - Select the folder: `c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\browser_extension`.

5. **Verify Installation:**
   - The extension card "Cyber Raksha AI — Browser Shield v1.1.0" appears.
   - Click the extension icon in the toolbar:
     - Status shows `● ONLINE`.
     - Active rules count reflects synchronized threat indicators (e.g. `6 Rules Active`).

---

## 4. Threat Intelligence Synchronization Workflow

```
[Local Backend: /api/v1/intel/indicators]
                   │
                   ▼ GET (Hourly Alarm or Manual Trigger)
     [validateIndicator() in rules_manager.js]
        • Validates type (DOMAIN, URL, IP)
        • Enforces confidence >= 0.80
        • Protects multi-tenant shared domains (github.com, drive.google.com)
                   │
                   ▼
       [syncRulesDelta() Algorithm]
        • Deduplicates incoming indicators
        • Identifies expired/revoked rules to remove
        • Compiles Chrome DNR redirect rules (regexFilter + regexSubstitution)
                   │
                   ▼
 [chrome.declarativeNetRequest.updateDynamicRules]
        • Applied atomically into Chromium engine
        • Rules persist across browser restarts
        • If backend offline: Keep cached rules active!
```

---

## 5. Automated & Manual Verification Procedures

### Automated Tests:
1. **Rules Manager Node.js Test Suite:**
   ```bash
   node browser_extension/tests/test_rules_manager.js
   ```
   *Expected Result:* `11 PASSED / 0 FAILED` covering blocking, safe domains, deduplication, revocation, shared hosting protection, and override rules.

2. **Backend Integration Pytest Suite:**
   ```powershell
   .\backend\venv\Scripts\python.exe -m pytest backend/tests/test_stage13_browser_protection.py -v
   ```
   *Expected Result:* `7 passed` verifying format compatibility, shared domain protection, and telemetry.

### Manual Verification Procedure:
1. Open the extension popup -> Note the active rules count.
2. Visit a seeded malicious indicator domain (or simulated mock test domain e.g. `http://cbi-digital-arrest-warrant.com`):
   - **Expected Result:** Chromium intercepts the navigation immediately and loads `warning.html` displaying:
     - Threat Classification: `DIGITAL_ARREST_EXTORTION`
     - Risk Level: `CRITICAL RISK`
     - Source: `Cyber Raksha Threat Feed`
     - Mode: `Pre-Load Declarative Block`
3. Click **"Return to Safety"**: Tab closes or navigates back.
4. Click **"Proceed Anyway (Unsafe Override)"**:
   - Native confirmation dialog prompts user.
   - Confirming installs a high-priority session allow rule and navigates to the destination.
5. Right-click any normal hyperlink and select **"Check with Cyber Raksha AI"**:
   - Executes deep Random Forest analysis on demand.

---

## 6. Known Technical Boundaries & Limitations

1. **Unknown Websites:**
   - Websites not present in local threat intelligence feeds are **not** blocked automatically by declarative rules.
   - Users can invoke on-demand ML inspection via the right-click context menu or popup.
2. **Shared Hosting Protection:**
   - Multi-tenant domains (e.g. `github.com`, `drive.google.com`, `vercel.app`) are protected against whole-domain blocking. Individual suspicious paths can be blocked, but the entire domain is never blocked.
3. **Regex Rule Quota:**
   - Chromium imposes a cap of 1,000 regex rules (`MAX_NUMBER_OF_REGEX_RULES`). Feeds exceeding 900 rules are prioritized by severity and confidence.

