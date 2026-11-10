# CYBER RAKSHA AI — PROJECT OVERVIEW
**Intelligent Digital Fraud Protection & Real-Time Incident Response Platform**
*Release Candidate: v1.0.0-rc.1 | Stage 10 Handover*

---

## 1. Project Title & Identification
- **Project Name:** Cyber Raksha AI (साइबर रक्षा AI)
- **Tagline:** Intelligent Digital Fraud Protection
- **Version:** `v1.0.0-rc.1`
- **Release Status:** Release Candidate Ready / Demonstration Ready
- **Repository Structure:** Monorepo containing Backend (FastAPI), AI Engine (Scikit-Learn/NLP), Frontend (React/Vite), Browser Extension (Chromium MV3), and PWA Companion.

---

## 2. Problem Statement
Digital fraud in India and globally has evolved beyond simple spam emails into sophisticated, multi-vector social engineering campaigns. Citizens and organizations face severe threats including:
1. **Targeted Phishing Links:** Homoglyphs, dynamic subdomains, and credential harvesting landing pages disguised as banking or tax portals.
2. **Communication Fraud & Impersonation:** SMS/WhatsApp scams exploiting fake KYC deactivations, electricity bill cutoff ultimatums, and lottery fraud.
3. **"Digital Arrest" Extortion Schemes:** Organized syndicates posing as CBI, ED, Telecom Department (DoT), or State Police, extorting victims through coercive video calls and fabricated warrants.
4. **Voice Cloning & Audio Deepfakes:** Synthetic speech generation used to mimic relatives in manufactured distress or executives requesting wire transfers.
5. **Fragmented, Reactive Response:** Traditional antivirus tools only flag files, while chatbots offer generic advice without analyzing the actual evidence or generating structured incident response playbooks.

---

## 3. Proposed Solution
Cyber Raksha AI transforms threat detection from passive warning dialogs into an integrated, end-to-end proactive defense platform:
- **Multi-Vector Detection Engines:** Independent, specialized machine-learning models evaluate URLs (25 lexical features), messages (TF-IDF NLP), and voice notes (acoustic spectral markers).
- **Unified Risk Corroboration:** Cross-correlates indicators across vectors, factoring in real-time threat intelligence (URLhaus/PhishTank) while avoiding double-counting and handling missing or contradictory signals.
- **Proactive Protection & Incident Playbooks:** Generates context-specific, immediate safety instructions, containment steps, emergency helpline numbers (e.g., 1930 National Cyber Crime Reporting Portal), and formal incident logging.
- **Omnichannel Protection:** Accessible via Responsive Desktop Web, Chromium Browser Extension, Android PWA Share Target, and a secure Administrator Operations Center.

---

## 4. Target Users
1. **General Internet Users & Families:** Individuals vulnerable to financial fraud, phishing SMS messages, and digital-arrest intimidation.
2. **Small Business Operators:** Organizations lacking a 24/7 Security Operations Center (SOC) requiring rapid verification of suspicious vendor invoices or emails.
3. **Cyber Crime First-Responders & Helpdesks:** Analysts triaging user reports and executing structured containment playbooks.

---

## 5. Core Objectives
- Deliver zero-budget, open-source-first security tooling without requiring paid commercial API subscriptions.
- Provide fully offline-capable inference using locally hosted Scikit-Learn models.
- Ensure strict privacy governance: sanitize PII (credit cards, Aadhaar numbers, OTPs) and prohibit unvetted automatic model retraining.
- Offer demonstrable, verifiable cybersecurity utility with zero fake statistics or simulated results.

---

## 6. Key Advantages Over General Chatbots
| Feature | General AI Chatbot | Cyber Raksha AI |
|:---|:---|:---|
| **Underlying ML** | Generative text prediction (prone to hallucination) | Deterministic supervised ML classifiers trained on vetted threat corpora |
| **Evidence Extraction**| Generic text summary | 25 lexical URL features, TF-IDF urgency weights, acoustic vocoder artifacts |
| **Threat Intelligence**| Static training cutoff | Live synchronization with verified threat feeds (URLhaus, PhishTank) |
| **Incident Management**| Plain text advice | Structured incident lifecycle, containment playbooks, and SQLite audit records |
| **Integrations** | Web chat only | Chromium Browser Extension, Android PWA Share Target, Admin Operations Center |
| **Data Safety** | Prompts often sent to third-party clouds | Local inference; PII sanitized before local persistence |

---

## 7. Known System Limitations
- Zero-day phishing domains registered within < 2 hours may not appear in threat feeds until community ingestion occurs.
- Voice deepfake classifier is optimized for acoustic vocoder artifact detection; it does **not** perform biometric speaker verification.
- Threat feed synchronization requires periodic internet connectivity to refresh signatures; offline operation relies on cached IoCs.

