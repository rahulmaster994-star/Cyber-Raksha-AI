# CYBER RAKSHA AI — FINAL ANDROID VERIFICATION REPORT
## Native Android Mobile Fraud Protection Build & Architecture Audit

**Date:** 2026-11-14  
**Application ID:** `com.cyberraksha.ai`  
**Version:** 1.0.0 (versionCode: 1)  
**Target SDK:** 36 (Android 16) | **Min SDK:** 26 (Android 8.0 Oreo)  
**Build Status:** ✅ BUILD SUCCESSFUL (Debug APK 21.4 MB)  
**Unit Tests:** ✅ ALL PASSED (UP-TO-DATE)  

---

## 1. Application Architecture

The Cyber Raksha AI Android application is developed with native Kotlin 2.0 and modern Android Jetpack libraries:
- **UI Toolkit:** Jetpack Compose with Material 3 theming.
- **Architecture Pattern:** Clean MVVM with Unidirectional Data Flow (StateFlow / Coroutines).
- **Persistence:** Room 2.6 (`AppDatabase`) for offline notifications, threats, and sync states.
- **Preferences:** Jetpack DataStore Preferences with AES-GCM encrypted tokens via `SecureTokenManager`.
- **Networking:** Retrofit 2.11 with OkHttp 4.12. Configured to log headers only to protect user message confidentiality.
- **Background Synchronization:** WorkManager (`SyncWorker`) running periodic telemetry sync.
- **Telephony Shield:** Subclasses `android.telecom.CallScreeningService` (`CyberRakshaCallScreeningService`).

---

## 2. Implemented Capabilities & Verification

### 2.1 Telecom Call Screening (`CyberRakshaCallScreeningService`)
- Implements `onScreenCall(callDetails: Call.Details)` on Android 10+ (API 29+).
- Normalizes incoming caller telephone numbers and queries backend `/api/v1/mobile/check-number`.
- **Fail-Open Policy:** Bound by a strict 3,000 ms coroutine timeout (`withTimeoutOrNull(3000L)`). If backend response times out, network is disconnected, or number is unknown, the service invokes `allowCall(callDetails)`.
- **Automatic Rejection:** Restricts automatic call rejection (`setDisallowCall(true)`, `setRejectCall(true)`) exclusively to authoritative `CRITICAL` confirmed digital arrest or extortion numbers.
- **Dynamic Device Identity:** Dynamically reads the registered device ID and cloud base URL from `AppPreferences`.

### 2.2 Privacy-Preserving Manual SMS Scanner (`SmsProtectionScreen`)
- Adheres to a strict user-controlled workflow: the user inputs or pastes an SMS text.
- Connects to `/api/v1/mobile/analyze-message` or `/api/v1/communication/analyze`.
- Detects financial fraud, fake banking alerts, lottery scams, OTP theft, and coercive police/court impersonation.
- Explains detected indicators (e.g. artificial urgency, payment solicitations, authority claims).
- Emits a device-scoped `SecurityEvent` when threat score exceeds threshold, updating the central dashboard.

### 2.3 Device Registration & Authentication
- Automatically provisions a unique UUIDv4 installation token upon first launch.
- Registers with the cloud backend via `POST /api/v1/devices/register`.
- Securely stores the returned 256-bit token in encrypted storage.
- Attaches `X-Device-Token` header to all outgoing mobile API calls.

---

## 3. Build & Packaging Verification

Executed build with Gradle wrapper:
```bash
./gradlew testDebugUnitTest assembleDebug
```

Output:
```
BUILD SUCCESSFUL in 53s
39 actionable tasks: 3 executed, 36 up-to-date
Output APK: android/app/build/outputs/apk/debug/app-debug.apk (21,424,795 bytes)
```

---

## 4. Physical Device Verification Status

- **Automated Unit & Build Verification:** ✅ **COMPLETE**
- **Physical Device Interactive Verification:** ⚠️ **PENDING USER INSTALLATION**
  - To install on a physical Android device:
    1. Connect device via USB with **USB Debugging** enabled.
    2. Run: `adb install -r android/app/build/outputs/apk/debug/app-debug.apk`
    3. Launch **Cyber Raksha AI**.
    4. Set as Default Caller ID & Spam App in Android Settings -> Apps -> Default Apps -> Caller ID & Spam.
    5. Test manual SMS inspection with synthetic test messages.
