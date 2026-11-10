# 📘 CYBER RAKSHA AI — USER MANUAL & OPERATIONAL GUIDE
**A Digital Protection Guide for Indian Citizens & Cybersecurity Analysts**

---

## 1. Navigating the Platform

Cyber Raksha AI provides 11 dedicated functional views accessible via the top navigation bar and the mobile bottom navigation bar:

1. **Overview (Landing Page):** Platform vision, security capabilities, and architecture summary.
2. **Control Center (Dashboard):** Live operational telemetry, total scans, threat counts, active incidents, and recent detections.
3. **Phishing Detection:** Supervised machine-learning scanner analyzing URLs for credential theft and deceptive spoofing.
4. **Message Threats:** Natural language analysis of SMS, WhatsApp, and email messages for financial urgency and fraud coercion.
5. **Digital Arrest:** Specialized detection of fake CBI, ED, Police warrants, and Skype/WhatsApp interrogation scams.
6. **Voice Shield:** Acoustic spectrogram analysis detecting AI voice cloning and telephonic deepfake impersonation.
7. **Threat Intel:** Searchable indicator of compromise (IoC) database synced with open-source threat blacklists.
8. **Unified Risk:** Multi-vector threat correlation analyzing combined messages, URLs, and audio recordings.
9. **Protection Center:** Incident response management, containment playbooks, and interactive guidance assistant.
10. **Security Modules:** Complete technical registry of the 6 core security detection engines.
11. **System Info:** Live backend connectivity status, database ping latency, and development stage metadata.

---

## 2. How to Analyze a Suspicious URL

1. Click **Phishing Detection** in the top navigation bar.
2. Enter the full URL (e.g. `http://secure-login-hdfcbank.serveo.net/verify`).
3. Click **Scan Target URL**.
4. Review the results:
   - **Risk Level:** `LOW` (Green), `MEDIUM` (Amber), `HIGH` (Rose), or `CRITICAL` (Red).
   - **Risk Score:** 0 to 100 calculated by the RandomForest model.
   - **Detected Indicators:** Specific structural warning signals (e.g. non-HTTPS, IP address hostname, high entropy).
   - **Recommendation:** Actionable guidance on safe handling.

---

## 3. How to Check a Digital Arrest or Coercive Message

1. Click **Digital Arrest** in the navigation bar.
2. Paste the suspicious message text into the input field.
3. Click **Analyze Message**.
4. The system inspects for known extortion markers:
   - Fake FIR / CBI / ED / Police references.
   - Coercive demands to join Skype / WhatsApp video calls.
   - Threats of immediate physical arrest unless a "security deposit" is paid.
5. If classified as a scam, immediate reporting steps are displayed:
   - Call the **1930** national helpline.
   - File an incident at **cybercrime.gov.in**.
   - Block the caller on the DoT **Chakshu** portal.

---

## 4. How to Analyze a Suspicious Voice Recording

1. Click **Voice Shield**.
2. Upload a WAV format audio recording of the suspicious call or voicemail.
3. Click **Analyze Voice Recording**.
4. The acoustic engine calculates spectral boundary artifacts and returns:
   - **Classification:** `LIKELY_NATURAL`, `LIKELY_SYNTHETIC`, or `INCONCLUSIVE`.
   - **Vocoder Artifacts:** High-frequency cutoffs, unnatural phase variance.
   - **Important Notice:** The platform assesses acoustic synthesis; it does not claim biometric speaker identification.

---

## 5. Using the Browser Extension

1. Load the extension in Chrome/Edge via `chrome://extensions` (Developer Mode -> Load unpacked -> select `browser_extension/`).
2. **Popup Scan:** Click the 🛡️ toolbar icon to scan the current tab's URL or enter any link manually.
3. **Context Menu:** Right-click any hyperlink on a webpage -> select **"Check with Cyber Raksha AI"**.
4. If the link is rated **HIGH** or **CRITICAL**, the extension intercepts navigation and displays a warning page.
5. Users can safely close the tab or confirm an explicit override if proceeding.

---

## 6. Official Indian Emergency Helplines

| Organization / Resource | Helpline / Web Portal | Purpose |
|---|---|---|
| **National Cyber Crime Helpline** | **1930** | Financial fraud reporting & fund freeze requests |
| **National Cyber Crime Portal** | **cybercrime.gov.in** | Formal cybercrime complaint filing |
| **Department of Telecommunications (Chakshu)** | **sancharsaathi.gov.in** | Reporting fraud WhatsApp numbers & SMS senders |
| **CERT-In (Indian Computer Emergency Response Team)** | **cert-in.org.in** | Vulnerability & cyber incident disclosure |
| **Emergency Services** | **112** | Local police emergency response |

