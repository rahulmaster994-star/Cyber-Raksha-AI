# Cyber Raksha AI — Android & Mobile Protection Validation Report

**Component Audited:** Mobile Companion & Progressive Web Application (PWA)  
**Artifact Directory:** `frontend/public/manifest.json`, `frontend/public/sw.js`, `frontend/src/App.tsx`  
**Auditor:** Senior Android Security Engineer & Mobile App Architect  
**Status:** **WEB COMPANION / SHARE TARGET VERIFIED (NO NATIVE OS INTERCEPTION)**  

---

## 1. Mobile Implementation Architecture

Cyber Raksha AI delivers its mobile user experience via an installable **Progressive Web Application (PWA)** built on React and Vite:
- **Web App Manifest:** `frontend/public/manifest.json` (`display: "standalone"`, `orientation: "portrait"`).
- **Service Worker:** `frontend/public/sw.js` (Cache-first static assets, network-only for `/api` routes).
- **Web Share Target:** Defined in `manifest.json` (action `/`, method `GET`, params: `title`, `text`, `url`).
- **Native Android APK / Capacitor Shell:** **NOT PRESENT** in current codebase.

---

## 2. Eight-Point Mobile Protection Audit

| # | Evaluated Requirement | Current Capability | Platform / Sandbox Boundary | Verdict |
|---|---|---|---|---|
| 1 | **Receive user-shared suspicious URLs** | User taps "Share" in browser or chat app; selects "CyberRaksha"; `App.tsx` extracts `?url=` and pre-fills `PhishingDetectionPage`. | Supported via W3C Web Share Target API standard. | **VERIFIED PASS** |
| 2 | **Analyze user-submitted messages** | User inputs or shares SMS/WhatsApp text into `CommunicationThreatPage`. Runs TF-IDF analysis. | In-app user submission. | **VERIFIED PASS** |
| 3 | **Display real-time warnings while app is open** | Shows risk badges (`CRITICAL`, `HIGH`, `MEDIUM`) with animated telemetry and recommendations. | Standard DOM UI rendering. | **VERIFIED PASS** |
| 4 | **Receive background security events** | `sw.js` has no `push` or `sync` event listeners. No Web Push VAPID keys configured. | PWA does not receive background push events when closed. | **NOT IMPLEMENTED** |
| 5 | **Intercept SMS messages** | PWA runs in Chromium sandbox and cannot read incoming SMS messages. | Google Chromium sandbox strictly prohibits SMS access from web pages. | **NOT IMPLEMENTED** |
| 6 | **Monitor telephone calls** | PWA cannot listen to incoming call events or screen callers. | Android requires native `CallScreeningService` or `READ_PHONE_STATE`. | **NOT IMPLEMENTED** |
| 7 | **Detect suspicious installed apps** | PWA cannot inspect other packages installed on the device. | Android requires native `QUERY_ALL_PACKAGES` permission. | **NOT IMPLEMENTED** |
| 8 | **Block malicious apps or transactions** | Cannot freeze banking apps or halt background transactions. | Requires Android Device Policy Controller (DPC) or AccessibilityService. | **NOT IMPLEMENTED** |

---

## 3. Web Share Target Integration Verification

### Code Evidence in `frontend/src/App.tsx` (Lines 72–78):
```typescript
// PWA Share Target — handle incoming shared URLs/text from Android share sheet
// The PWA manifest registers share_target POST to /?title=&text=&url=
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const sharedUrl = params.get('url') || params.get('text');
  if (sharedUrl && sharedUrl.trim().length > 0) {
    setSharedContent(sharedUrl.trim());
    setCurrentPage('phishing');
  }
}, []);
```
When an Android user shares a suspicious link from WhatsApp, Chrome, or SMS to Cyber Raksha AI:
1. Android OS opens the standalone PWA with `/?url=https%3A%2F%2F...`.
2. `App.tsx` automatically switches navigation to the **Phishing Detection** page.
3. `PhishingDetectionPage` pre-fills the input field with the shared link and prompts the user to analyze it.

---

## 4. Mobile Threat Model & Platform Realities

To prevent unsupported claims, the following mobile security facts must be documented:

1. **Android Permission Isolation:**
   - No web application (PWA or website) can intercept SMS, read incoming calls, or monitor encrypted messaging platforms (WhatsApp, Telegram, Signal) without a native Android service.
2. **Google Play Store Policy:**
   - Google Play restricts `RECEIVE_SMS` and `READ_CALL_LOG` permissions to default SMS and Phone handler apps. Security tools must declare specific exemptions or distribute outside Google Play.
3. **Current Mobile Role:**
   - Cyber Raksha AI functions as a **Mobile Security Companion** where users forward suspicious content for instant AI verification and safety playbooks.

