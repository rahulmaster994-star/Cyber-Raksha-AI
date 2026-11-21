# Cyber Raksha AI - Known Technical Limitations

This document provides a rigorous, technically honest breakdown of the physical, architectural, and telecommunication boundaries governing the **Keypad User Protection System** in Cyber Raksha AI.

---

## 1. Traditional Keypad Phone Operating Environment

### Target Devices
- **Hardware:** Nokia 105, Samsung Guru 1200, itel 2163, Lava A1, Jio Bharat, etc.
- **Operating Systems:** RTOS (Real-Time Operating Systems) such as MediaTek Nucleus OS, Spreadtrum MOCOR OS, or KaiOS (in limited 4G variants).

### Inherent Constraints
1. **No Third-Party Application Execution:**
   - Standard 2G/4G feature phones do not possess an application store, Java ME / MIDP runtime, or APK execution environment.
   - Users cannot install Cyber Raksha AI or any agent software onto the keypad phone itself.
2. **No Background Daemons or System Hooking:**
   - RTOS architectures do not permit background daemons, accessibility services, or notification listener hooks.
3. **No Dynamic Telephony API Access:**
   - Even on phones that run basic J2ME or KaiOS, the core telephony stack (radio interface layer) is proprietary and closed to third-party code for security and regulatory reasons.

---

## 2. Cellular Network Architecture & Radio Protocols (3GPP)

### Why Automatic Call/SMS Interception Is Physically Impossible Without Telecom Operator Core Integration

1. **Incoming Call Delivery (3GPP TS 24.008):**
   - When a call is placed to a keypad phone, the Mobile Switching Centre (MSC) or IP Multimedia Subsystem (IMS) routes the call via SS7 / ISUP or SIP INVITE directly to the Base Transceiver Station (BTS).
   - The BTS pages the keypad phone's cellular baseband over the Paging Channel (PCH).
   - The phone's baseband processor alerts the user via hardware ringer immediately.
   - **Conclusion:** There is zero software layer on the phone or over the air that can intercept, inspect, or drop an incoming call before it rings, unless integrated directly at the cellular operator's MSC/HLR level.

2. **Incoming SMS Delivery (3GPP TS 23.040):**
   - An SMS travels from the Short Message Service Center (SMSC) directly to the keypad phone's baseband processor via the cellular signaling channel (SS7 MAP forwardSM or IMS SIP MESSAGE).
   - The message is written directly to the SIM memory or baseband NVRAM.
   - **Conclusion:** No device-independent external consumer software can read, filter, or delete this message prior to the senior user seeing it without carrier-level SMS firewalls.

3. **No Carrier SS7/IMS Partnership:**
   - Under project constraints, no telecom operator (Jio, Airtel, Vi, BSNL) partnerships or private telecom APIs are available.
   - Therefore, automatic network-level filtering cannot be claimed.

---

## 3. The Guardian-Assisted Architecture (Technical Truth)

To resolve the impossible problem of protecting senior keypad phone users without hardware or telecom modification, Cyber Raksha AI uses a **Guardian-Assisted Protection Model**:

| Capability | Automated on Keypad Phone? | Real-World Implementation in Cyber Raksha AI |
|---|---|---|
| **SMS Fraud Detection** | **No** (Impossible without carrier/hardware) | **Guardian Manual Scan:** Guardian inputs suspicious SMS text via the Android application; NLP engine classifies threats and returns actionable advice. |
| **Incoming Call Identification** | **No** (Impossible without carrier/hardware) | **Guardian Call Check:** Guardian looks up missed or received caller numbers against the community reputation database. |
| **Call Blocking** | **No** (Impossible without hardware) | **Manual Phone Blocklist or DoT Sanchar Saathi:** App instructs guardian how to block the number in the feature phone's built-in 10-number reject list, or report to Chakshu. |
| **Incident Alerts** | **No** (No autonomous phone agent) | **Event-Driven Guardian Alerts:** Alerts are generated when an SMS or Call check is submitted through the API. |
| **Fraud Education** | **Yes** (Delivered via Guardian App) | **Trilingual Fraud Modules:** Kannada, Hindi, and English guides explain common scams in plain language. |

---

## 4. Distinction Between Sanchar Saathi / DoT Reporting and Local Software Blocking

- **Cyber Raksha Local Intelligence:** Maintains a decentralized reputation database based on multi-guardian reports. It provides immediate risk scores to guardians checking numbers.
- **Department of Telecommunications (DoT) Sanchar Saathi (Chakshu):** The Government of India portal where citizens report fraudulent numbers for carrier-wide IMEI/SIM deactivation.
- **Critical Distinction:** Cyber Raksha AI guides users to Chakshu and 1930 for official enforcement; it does not claim to disconnect carrier numbers autonomously.
