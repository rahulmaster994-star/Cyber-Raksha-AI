# Physical Device Test Checklist: Realme P4 Power 5G (Android 16)

**Device Model:** realme P4 Power 5G  
**OS Version:** Android 16 (Developer Preview / Vanilla Ice Cream / Baklava)  
**Target Package:** `com.cyberraksha.ai`  
**Test Artifact:** `android/app/build/outputs/apk/debug/app-debug.apk` (SHA-256: `E42FA27D596C2CD4CE196F368546919B17E4C59C42F8370A24661B20518D9C0A`)  

---

## 1. Pre-Requisites & Installation

### Step A: Enable Developer Mode & USB Debugging
1. Open **Settings** > **About Device** > **Version** on realme P4 Power 5G.
2. Tap **Build number** 7 times until prompted "You are now in Developer mode".
3. Return to **Settings** > **System Settings / Additional Settings** > **Developer options**.
4. Enable **USB Debugging** and **Install via USB**.

### Step B: Install via ADB or Direct Sideload
- **Option 1 (via ADB):**
  ```powershell
  adb install -r C:\Users\RAHUL\OneDrive\Desktop\cyberRaksha\android\app\build\outputs\apk\debug\app-debug.apk
  ```
- **Option 2 (Direct file transfer):**
  Transfer `app-debug.apk` via USB Cable, open Realme File Manager, tap APK, and allow "Install unknown apps".

---

## 2. 15-Point Functional Checklist

| # | Test Item | Action / Test Procedure | Expected Result | Pass/Fail | Notes |
|---|---|---|---|---|---|
| **TC-01** | **App Installation** | Install `app-debug.apk` onto realme P4 Power 5G. | Installs without package parsing or signature conflicts. | [ ] | Check Android 16 permission prompts |
| **TC-02** | **Cold Launch** | Launch Cyber Raksha AI from App Drawer. | Splash screen renders cleanly; app enters Login or Dashboard. | [ ] | Confirm no crash on startup |
| **TC-03** | **Guardian Authentication** | Log in using registered credentials or register new guardian. | JWT access token received and stored securely in SharedPreferences. | [ ] | Auth interceptor attaches token to all requests |
| **TC-04** | **Dashboard Keypad Tile** | Inspect Dashboard screen. | "Keypad Protection" / "Senior Family Shield" card is prominently visible. | [ ] | Verify card badge and title |
| **TC-05** | **Navigation to Keypad Module** | Tap on "Keypad Protection" launcher. | Navigates to `KeypadProtectionScreen` with 7 tabs visible. | [ ] | Smooth transition, no jank |
| **TC-06** | **Disclaimer Visibility** | Check header on Keypad Protection screen. | Clear banner: *"Guardian-Assisted Protection: Manual analysis only. No software runs on keypad phone."* | [ ] | Verify legibility |
| **TC-07** | **Family Registration** | In "Family" tab, enter Name: "Grandfather", Phone: "+919876543210", Relation: "Grandfather", Consent: Checked. | Member appears in list with relation tag and phone mask. | [ ] | If consent unchecked, button must be disabled or reject |
| **TC-08** | **SMS Risk Analysis (Scam)** | Paste: *"Electricity power will be disconnected tonight. Call officer at 9876543210 immediately."* | Risk Score: **HIGH (80-95)**, Red warning banner, highlights urgency and disconnection threats. | [ ] | Shows manual advice for senior |
| **TC-09** | **SMS Risk Analysis (Safe)** | Paste: *"Your bank OTP for INR 500 is 123456. Do not share."* or simple family message. | Risk Score: **LOW / MEDIUM**, clear explanation that no suspicious URL/pressure detected. | [ ] | Clean guidance displayed |
| **TC-10** | **Call Risk Check** | In "Call Check" tab, enter suspected scam number. | Returns reputation status (Known scammer / Unverified), report count, and guidance. | [ ] | Labels unverified numbers explicitly |
| **TC-11** | **Report Scam Number** | Report an incoming scam number with category "Electricity Threat". | Report submitted successfully; confirmation snackbar/toast shown. | [ ] | Verify deduplication behavior |
| **TC-12** | **Incident Alert Feed** | Navigate to "Alerts" tab after running High-Risk SMS check. | New alert appears with timestamp, risk level, and "Acknowledge" action button. | [ ] | Tap acknowledge updates state |
| **TC-13** | **Trilingual Fraud Education** | Open "Education" tab; toggle English, Kannada (ಕನ್ನಡ), and Hindi (हिन्दी). | Content dynamically updates to native language guides on OTP, Digital Arrest, and KYC scams. | [ ] | Check font rendering |
| **TC-14** | **Helpdesk & Reporting Guidance** | Open "Helpline" tab. | Direct tap-to-call for 1930; links to Chakshu and National Cybercrime Portal. | [ ] | Verifies external intent actions |
| **TC-15** | **Offline Graceful Handling** | Toggle Airplane mode on realme P4 Power 5G and trigger an SMS scan. | App displays friendly error: *"Network error: Unable to connect to server. Please check internet."* (No crash). | [ ] | Handled cleanly |

---

## 3. Physical Keypad Verification Scenario (Dual Device)

### Test Setup:
- **Device A:** Traditional Keypad Phone (Nokia 105 / Samsung Guru / itel) with Senior SIM card.
- **Device B:** realme P4 Power 5G with Cyber Raksha AI installed (Guardian).

### Test Flow:
1. Senior receives an SMS on Device A: *"Your SBI account KYC blocked. Click http://bit.ly/sbi-update or call 9123456789."*
2. Senior reads SMS to Guardian or Guardian inspects Device A screen.
3. Guardian opens Cyber Raksha AI on Device B > Keypad Protection > SMS Scan.
4. Guardian types message into analysis box and taps **Analyze SMS**.
5. Within 1 second, Device B displays:
   - **Risk Score: 92/100 (HIGH RISK)**
   - **Detected Tactics:** Fake KYC, phishing link, threat of blockage.
   - **Recommended Action for Senior:** *"Do not open link. Do not call number. Banks never block accounts via SMS."*
6. Guardian taps **Report Scam** to add number `9123456789` to community intelligence.
7. Alert is permanently recorded under the Family Member's incident log.

