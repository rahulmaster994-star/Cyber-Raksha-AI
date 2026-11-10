# Cyber Raksha AI — Known Technical & Architectural Limitations

This document provides a candid, technically accurate disclosure of known limitations in the **Cyber Raksha AI** platform. These limitations are intentional engineering trade-offs or documented boundaries.

---

## 1. Machine Learning & Detection Boundaries

### 1.1 Bare-Domain Lexical Blindness (URL Detection)
- **Description:** Bare root domains (e.g. `https://phishtest.invalid`) with no subdomain nesting, paths, hyphens, or query parameters lack the structural signals that the Random Forest URL classifier relies on.
- **Observed Impact:** In adversarial tests, a bare mock root domain scored `25.94/100` (`LEGITIMATE/LOW`).
- **Remediation & Mitigation:** Offline threat intelligence IoC lookup and high-risk TLD heuristics add up to +30 risk points when the domain or TLD appears in threat feeds. Fully novel, bare domains on neutral TLDs require dynamic sandboxing or domain age lookups for high-confidence identification.

### 1.2 Subtle Social Engineering Scams (Communication Detection)
- **Description:** Non-coercive, low-urgency scam formats (e.g. routine lottery claims, unpaid electricity bills, informal part-time task offers) produce lower TF-IDF feature weights than acute digital-arrest extortion.
- **Observed Impact:** Scenarios `FS-03`, `FS-04`, and `FS-05` were classified as `MEDIUM / SUSPICIOUS` (scores 32–56/100) rather than `CRITICAL`.
- **Engineering Rationale:** To maintain a 0.0% false positive rate on legitimate banking and delivery notices, the model reserves `HIGH/CRITICAL` determinations for messages with high-urgency keywords, coercive threats, or direct credential harvesting.

### 1.3 Audio Forensic Scope (No Biometric Identification)
- **Description:** The Stage 4 Voice Shield engine inspects acoustic and vocoder synthesis artifacts (zero-crossing rate, spectral flatness, phase inconsistencies). It does **not** perform biometric voiceprint comparison.
- **User Disclosure:** Both the API schemas (`biometric_identity_supported: false`) and frontend UI display an explicit disclaimer that the engine cannot verify the legal identity of a speaker.

---

## 2. Infrastructure & Architectural Boundaries

### 2.1 Content Security Policy Style Directive
- **Directive:** `style-src 'self' 'unsafe-inline'` and `style-src-attr 'unsafe-inline'`
- **Reason:** Tailwind CSS utilities and React dynamic runtime style computations require inline styles. Eliminating `'unsafe-inline'` from style-src without an ahead-of-time CSS hash extraction pipeline would disrupt frontend rendering.
- **Security Posture:** `script-src 'self'` has been strictly enforced without `'unsafe-inline'`, preventing arbitrary inline script injection.

### 2.2 Local Threat Intelligence & Zero-Budget Public Community Feeds
- **Description:** Cyber Raksha AI utilizes verified local signature caches and zero-budget community feeds (such as abuse.ch URLhaus and CERT-In advisories). User navigation data is strictly evaluated inside the browser via Declarative Net Request rules and never exfiltrated to remote cloud APIs during browsing.
- **Benefit:** Preserves user privacy (no browsing destinations leave the client) and eliminates paid third-party API dependencies.
- **Synchronization:** Automated background polling updates verified community indicators periodically (default: 60 minutes) with TTL expiration for stale records.

### 2.3 Mobile Deployment Architecture (Phase B1 Foundation)
- **Description:** Mobile capabilities are provided across two tiers: a responsive Progressive Web Application (PWA) for lightweight browser access, and a production-ready Native Android application (`com.cyberraksha.ai`) built with Kotlin, Jetpack Compose, Material 3, Room, WorkManager, and Retrofit.
- **Phase B1 Scope:** Phase B1 establishes the client-server foundation, device onboarding, secure app-generated installation UUID registration, local Room caching, periodic WorkManager synchronization, native notification channels (Critical, High, General), and the mobile security posture dashboard.
- **Deferred Phase B2 Capabilities:** Inbound SMS scan/interception (`RECEIVE_SMS`), Call fraud screening (`READ_CALL_LOG` / `READ_PHONE_STATE`), and real-time screen content accessibility analysis are explicitly scheduled for Phase B2 and are not active in Phase B1.

### 2.4 Browser Extension Automated Protection Scope (Phase A1)
- **Description:** Following Phase A1, the Chromium extension automatically intercepts and blocks all navigations to **cached known verified malicious indicators** via Declarative Net Request (DNR) dynamic rules before page loading.
- **Limitation on Unknown Domains:** For completely novel or unknown websites not present in the synchronized threat intelligence cache, automated pre-load blocking is not executed (to avoid synchronous network latency and false-positive interruptions on legitimate browsing). Users retain the ability to manually inspect any link or active tab on demand using the Random Forest ML classifier via the right-click context menu or toolbar popup.

### 2.5 Automated Threat Intelligence Synchronization (Phase A2)
- **Description:** Phase A2 introduces the asynchronous `ThreatIntelScheduler` background worker running inside the FastAPI lifecycle. It performs periodic synchronization (default: 60 minutes) against URLhaus public feeds, prunes dynamic indicators older than 30 days (`THREAT_INDICATOR_TTL_DAYS`), and persists execution logs in `threat_feed_logs`.
- **Offline Fallback Resilience:** When external feeds are unreachable or network connectivity is severed, the scheduler enters `OFFLINE_FALLBACK` status without raising unhandled exceptions or disrupting server uptime, allowing previously cached rules to remain fully operational.

### 2.6 Intelligent Security Notification & Alert Engine Scope (Phase A3)
- **Description:** Phase A3 establishes an event-driven notification engine bridging threat detection, risk classification, browser desktop notifications, and the real-time security dashboard.
- **Domain Cooldown & Rate Limiting:** To prevent alert fatigue and notification flooding during aggressive web crawling or multi-resource attacks, notifications are rate-limited to a 30-second cooldown window per unique target domain.
- **Severity Escalation Priority:** If a subsequent event on a throttled domain escalates in severity (e.g., from `LOW`/`MEDIUM` to `HIGH` or `CRITICAL`), the deduplication window is immediately bypassed to ensure emergency alerts reach the user.
- **Native OS / Browser Permission Dependency:** Native desktop popups rely on Chromium's `"notifications"` permission. If the user dismisses or revokes browser-level OS notifications or enables "Do Not Disturb", alerts are preserved in the in-app notification center and real-time dashboard feed without loss of forensic data.
- **Real-Time Stream Resilience:** Real-time updates utilize Server-Sent Events (`/api/v1/notifications/stream`). If the SSE connection drops due to network sleep or transient interruptions, the frontend client automatically falls back to periodic heartbeat polling to ensure zero notification loss.
- **Asynchronous Telemetry & Zero Latency:** Browser threat-blocked telemetry is dispatched asynchronously (`fetch` with non-blocking error absorption) to the backend API (`POST /api/v1/notifications`). Threat navigation blocking via Declarative Net Request never waits for backend network roundtrips.

### 2.7 Native Android Foundation & Emulator Networking Boundaries (Phase B1)
- **Loopback IP Specification:** In the standard Android Emulator environment, the host workstation loopback is reachable at `http://10.0.2.2:8000` rather than `http://localhost:8000`. The debug build configuration and network security config (`res/xml/network_security_config.xml`) default to `10.0.2.2` with cleartext HTTP permitted exclusively for local development and private subnets (`10.0.0.0/8`, `192.168.0.0/16`, `127.0.0.1`).
- **Physical Device Networking:** When running on physical hardware, users must configure the backend URL in onboarding/settings to match the developer machine's LAN IP address (e.g. `http://192.168.1.X:8000`).
- **Device Identification Privacy Compliance:** The application uses exclusively client-generated cryptographically secure UUID tokens (Installation IDs) stored in encrypted DataStore. The backend schema strictly validates and rejects any submission resembling hardware IMEIs (14–16 digits) or phone number strings with HTTP 422 Unprocessable Content.
- **Background Sync Granularity:** Background threat alert synchronization is managed via Android `WorkManager` with a 15-minute minimum periodic interval (enforced by the Android OS battery optimization subsystem) and exponential backoff retry criteria. Urgent real-time push relies on native system notification channels when the app is active or synchronized.
- **Headless Build Environment:** In CI/CD or headless workstation environments where no hardware-accelerated Android Virtual Device (AVD) is running, automated unit tests execute in the JVM layer via Robolectric/JUnit4/MockK with 100% pass rate, while full APK binaries (`app-debug.apk`) compile directly from source without emulator dependencies.
