# Cyber Raksha AI — Browser Extension Test Checklist

Manual test cases for the Chromium MV3 browser extension.  
Run these after loading the extension via **chrome://extensions → Load unpacked**.

---

## Prerequisites

| Requirement | Check |
|-------------|-------|
| Backend running: `uvicorn app.main:app --reload` at `http://127.0.0.1:8000` | ✅ |
| Extension loaded via "Load unpacked" pointing to `browser_extension/` | ✅ |
| Extension ID visible in chrome://extensions | ✅ |

---

## 1. Extension Load Tests

| TC# | Test Case | Expected Result | Status |
|-----|-----------|-----------------|--------|
| T01 | Load extension via "Load unpacked" | No errors in Extensions page, icon appears in toolbar | ☐ |
| T02 | Click toolbar icon | Popup opens with Cyber Raksha AI branding | ☐ |
| T03 | Open `chrome://extensions` → Extension detail | Options page link present and opens `options.html` | ☐ |

---

## 2. Popup — Backend Connectivity

| TC# | Test Case | Expected Result | Status |
|-----|-----------|-----------------|--------|
| T04 | Backend ONLINE: Open popup | Status pill shows ● ONLINE in green | ☐ |
| T05 | Backend OFFLINE: Stop server, open popup | Status pill shows ● OFFLINE in red | ☐ |
| T06 | Backend OFFLINE: Attempt URL scan | Shows "Backend Offline" error, does NOT crash | ☐ |

---

## 3. Popup — URL Scanning

| TC# | Test Case | Input URL | Expected Risk | Status |
|-----|-----------|-----------|---------------|--------|
| T07 | Scan current tab (legitimate) | `https://www.google.com` | LOW (green) | ☐ |
| T08 | Scan manually entered legitimate URL | `https://en.wikipedia.org/wiki/Phishing` | LOW (green) | ☐ |
| T09 | Scan known phishing URL | `http://account-verification-support.paypal.com.crypto-wallet-verify.net/login.php` | HIGH or CRITICAL (red) | ☐ |
| T10 | Scan suspicious deceptive domain | `http://secure-login-hdfcbank.serveo.net/verify` | HIGH or CRITICAL (red) | ☐ |
| T11 | Unknown/neutral URL | `http://192.168.1.1/router` | MEDIUM or LOW (AI-determined) | ☐ |
| T12 | Invalid URL — no scheme | `google.com` | Alert: "Please enter a valid URL including http:// or https://" | ☐ |
| T13 | Empty URL field, click Scan | Alert: "Please enter a URL to scan" | ☐ |

---

## 4. Popup — Result Display

| TC# | Test Case | Expected Result | Status |
|-----|-----------|-----------------|--------|
| T14 | LOW risk result | Green badge, shield icon, safe message | ☐ |
| T15 | HIGH risk result | Red badge, warning icon, threat details shown | ☐ |
| T16 | Result shows confidence score | Percentage shown in result panel | ☐ |
| T17 | Result shows threat categories | Tags/badges for detected threat types | ☐ |
| T18 | "Open in Cyber Raksha AI" button | Opens full web app URL in new tab | ☐ |

---

## 5. Context Menu — Link Checking

| TC# | Test Case | Expected Result | Status |
|-----|-----------|-----------------|--------|
| T19 | Right-click a hyperlink on a webpage | "Check with Cyber Raksha AI" menu item appears | ☐ |
| T20 | Right-click link → LOW risk backend result | Link opens normally in new tab | ☐ |
| T21 | Right-click link → HIGH/CRITICAL risk backend result | Redirected to `warning.html` warning page | ☐ |
| T22 | Right-click `javascript:alert(1)` scheme link | Silently blocked — no fetch, no navigation | ☐ |
| T23 | Right-click `data:` URI link | Silently blocked — no fetch, no navigation | ☐ |
| T24 | Right-click non-link (plain text) | Context menu item does NOT appear | ☐ |

---

## 6. Warning Page

| TC# | Test Case | Expected Result | Status |
|-----|-----------|-----------------|--------|
| T25 | Warning page loads for HIGH risk URL | Displays URL, risk level, threat details from query params | ☐ |
| T26 | "Go Back to Safety" button | Closes warning tab / navigates to previous safe page | ☐ |
| T27 | "Override — Visit Anyway" button | Shows confirmation modal | ☐ |
| T28 | Confirm override | Navigates to the original URL in same tab | ☐ |
| T29 | Cancel override | Stays on warning page | ☐ |

---

## 7. Options Page

| TC# | Test Case | Expected Result | Status |
|-----|-----------|-----------------|--------|
| T30 | Open Options page | Loads with current API URL prefilled | ☐ |
| T31 | Change API URL to custom backend | Saves to `chrome.storage.sync` | ☐ |
| T32 | "Test Connection" with valid backend | Shows ✅ Connection Successful | ☐ |
| T33 | "Test Connection" with wrong URL | Shows ❌ Connection Failed | ☐ |
| T34 | Reload extension, open Options | Custom API URL persisted | ☐ |

---

## 8. Privacy Verification

| TC# | Test Case | Expected Result | Status |
|-----|-----------|-----------------|--------|
| T35 | Open `chrome://extensions` → Extension permissions | Only: `activeTab`, `contextMenus`, `storage` — no broad host permissions | ☐ |
| T36 | Passive browsing (no interaction) | Extension makes NO network requests | ☐ |
| T37 | URL scan via popup | ONLY the URL scanned is sent to backend — no cookies, no history | ☐ |

---

## Notes

- Risk levels: **LOW** (green/emerald) · **MEDIUM** (amber) · **HIGH** (red) · **CRITICAL** (red, critical badge)
- Backend endpoint used: `POST /api/v1/detection/url`
- Warning page URL format: `warning.html?url=<encoded>&risk=<level>&score=<0-100>`
- Context menu is registered once in `background.js` via `chrome.runtime.onInstalled`

