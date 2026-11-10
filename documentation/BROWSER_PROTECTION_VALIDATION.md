# Cyber Raksha AI — Browser Protection Validation Report

**Component Audited:** Chromium Browser Extension (Manifest V3)  
**Artifact Directory:** `browser_extension/`  
**Auditor:** Senior Browser Security Engineer & Chromium Extension Specialist  
**Status:** **USER-ASSISTED PROTECTION VERIFIED (CONTEXT MENU & POPUP SCANNING)**  

---

## 1. Extension Architecture & Permissions Audit

### Manifest V3 Configuration (`manifest.json`):
```json
{
  "manifest_version": 3,
  "name": "Cyber Raksha AI — Browser Shield",
  "version": "1.0.0",
  "permissions": [
    "activeTab",
    "contextMenus",
    "storage"
  ],
  "background": {
    "service_worker": "background.js"
  }
}
```

### Critical Permission & API Analysis:
| API / Permission | Present in Manifest? | Security Implication |
|---|---|---|
| `contextMenus` | **YES** | Allows creating right-click menus on link elements. |
| `activeTab` | **YES** | Allows reading the current tab URL when popup is clicked. |
| `storage` | **YES** | Persists backend API base URL setting across sessions. |
| `declarativeNetRequest` | **NO** | Cannot modify or block network requests across the browser in the background. |
| `webNavigation` | **NO** | Cannot receive pre-navigation events (`onBeforeNavigate`) across arbitrary tabs. |
| `tabs` (full permission) | **NO** | Cannot monitor background tabs without user invocation. |
| Host Permissions (`<all_urls>`) | **NO** | Cannot inject content scripts across arbitrary domains. |

---

## 2. Nine-Point Browser Protection Verification

| # | Evaluated Requirement | Verified Behavior | Code Location | Verdict |
|---|---|---|---|---|
| 1 | **Detects navigation to a suspicious URL** | Only when user explicitly right-clicks a hyperlink and selects "Check with Cyber Raksha AI". | `background.js:13-16` | **PARTIAL** (Not automated on left-click) |
| 2 | **Checks URL before destination loads** | When triggered via context menu, the destination tab is not created until the API responds. | `background.js:29-67` | **PASS** (Pre-load verification in context-menu flow) |
| 3 | **Communicates with backend** | Sends `POST /api/v1/detection/url` with target URL payload. | `background.js:30-37` | **PASS** |
| 4 | **Receives actual risk results** | Parses `risk_level`, `risk_score`, `classification`, and `recommendation` from backend. | `background.js:47-48` | **PASS** |
| 5 | **Blocks confirmed malicious destinations** | For `CRITICAL` or `HIGH` risk, the target URL is halted; only `warning.html` is opened. | `background.js:50-56` | **PASS** (User-Assisted Blocking) |
| 6 | **Displays warning interstitial** | Opens `warning.html` displaying risk level, classification badge, and guidance. | `warning.html`, `warning.js` | **PASS** |
| 7 | **Allows explicit user override** | `btnOverride` prompts `confirm(...)` modal. Only upon explicit OK does it redirect to the target. | `warning.js:30-38` | **PASS** |
| 8 | **Handles backend disconnection safely** | Network timeout or HTTP failure routes to `warning.html?reason=API_OFFLINE`. | `background.js:68-73` | **PASS** |
| 9 | **Avoids treating failed analysis as SAFE** | When offline, the warning page displays: "Protection service unavailable — this URL has not been verified." Does not open destination. | `warning.js:15-18` | **PASS** (Defensive fail-safe) |

---

## 3. Workflow Distinctions

```
Standard Left-Click / Omnibox:
User Clicks Link ───────────────────────────────► Destination Loads (NO INTERCEPTION)

User-Assisted Context-Menu Flow:
User Right-Clicks Link ──► "Check with Cyber Raksha"
                                     │
                                     ▼
                        POST /api/v1/detection/url
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
             Level: LOW / SAFE              Level: HIGH / CRITICAL
                     │                               │
                     ▼                               ▼
            chrome.tabs.create(targetUrl)    chrome.tabs.create(warning.html)
                                                     │
                                                     ▼
                                          [Return Safe] or [Override]
```

### Key Technical Distinction:
- **URL Scanning:** **VERIFIED** (Via popup "Scan Current Page URL" and "Manual URL Check").
- **Navigation Monitoring:** **NOT IMPLEMENTED** (No listener on `chrome.tabs.onUpdated` or `webNavigation`).
- **Warning Display:** **VERIFIED** (`warning.html` fully rendered).
- **Navigation Blocking:** **USER-ASSISTED** (Halts navigation in right-click context menu workflow; not in general browsing).

---

## 4. Technical Requirements for Full Active Web Protection

To achieve autonomous, browser-wide active navigation protection without requiring user context-menu actions, the following enhancements are required:
1. **Add `declarativeNetRequest` and `<all_urls>` host permissions** to `manifest.json`.
2. **Implement local rule compilation:** Export high-confidence phishing domains from the threat intelligence database to Chromium `declarativeNetRequest` dynamic rules.
3. **Register `webNavigation.onBeforeNavigate` listener:** For un-cached domains, asynchronously evaluate lexical risk and redirect to `warning.html` before the first byte of the malicious page is fetched.

