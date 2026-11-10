# 🏛️ CYBER RAKSHA AI — UNIFIED SYSTEM ARCHITECTURE
**Stage 8: Final System Integration, Security Hardening & Deployment**

---

## 1. High-Level Architecture Diagram

```
+---------------------------------------------------------------------------------------------------------+
|                                              USER INPUT LAYER                                           |
|  [ Web Browser App ]     [ Browser Extension (MV3) ]     [ Android / Mobile PWA ]     [ Direct API ]   |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v (HTTPS / REST)
+---------------------------------------------------------------------------------------------------------+
|                                         SECURITY & API GATEWAY                                          |
|   SecurityHeadersMiddleware  |  RateLimiterMiddleware (120r/m)  |  CORS Guard  |  Input Validation      |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                            APPLICATION LAYER                                            |
|  - Detection Routes       - Communication Routes    - Audio Routes       - Threat Intel Routes          |
|  - Prevention Routes      - System & Health Routes  - Privacy Routes     - Dashboard Analytics          |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                 +-----------------------------------+-----------------------------------+
                 |                                                                       |
                 v                                                                       v
+-----------------------------------+                               +-----------------------------------+
|          AI DETECTION ENGINES     |                               |      PERSISTENCE & STORAGE        |
|                                   |                               |                                   |
| 1. URL Phishing Detector (RF)     |                               | Relational Database (SQLite)      |
|    - 25-dim structural features   |                               | 11 SQLAlchemy Models:             |
|    - RandomForest Classifier      |                               | - users                           |
|                                   |                               | - system_configs                  |
| 2. Communication NLP Engine (SVC) |                               | - security_events                 |
|    - TF-IDF N-gram feature matrix |                               | - analysis_history                |
|    - LinearSVC Text Classifier    |                               | - notifications                   |
|    - Digital Arrest Scam Rules    |                               | - threat_indicators               |
|                                   |                               | - threat_feed_logs                |
| 3. Audio Deepfake Detector (RF)   |                               | - unified_risk_records            |
|    - WAV header validator         |                               | - security_incidents              |
|    - Mel-spectrogram & vocoder    |                               | - incident_actions                |
|    - Spectral boundary analysis   |                               | - user_protection_settings        |
|                                   |                               |                                   |
| 4. Threat Intelligence Engine     |                               | Automated Backup Engine:          |
|    - URLhaus feed harvester       |                               | - backup_db.py (Integrity check)  |
|    - In-memory fast IoC cache     |                               | - restore_db.py (Safe restore)    |
+-----------------------------------+                               +-----------------------------------+
                 |
                 v
+---------------------------------------------------------------------------------------------------------+
|                                    CENTRAL UNIFIED RISK ENGINE                                          |
|                                                                                                         |
| - Multi-Vector Corroboration: Boosts score when independent channels confirm attack (+15 pts)          |
| - Verified Threat Intel Match: Overrides heuristic low scores (+25-30 pts, min 80.0 score)             |
| - Factual vs Prediction Segregation: Separates verified IoCs from ML probability estimates              |
| - Conflict Resolution: Explicitly documents discrepancies between heuristics and external intelligence   |
| - Limitation & Uncertainty Engine: Discloses absence of biometric identification and negative bounds    |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                      PROACTIVE PROTECTION LAYER                                         |
|                                                                                                         |
| - Dynamic Prevention Recommendations (Immediate, Short-term, Long-term containment steps)               |
| - Incident Response Playbooks (Phishing, Digital Arrest, Voice Impersonation, Financial Fraud)          |
| - Incident Lifecycle Tracking (NEW -> ACTION_REQUIRED -> CONTAINED -> RESOLVED -> CLOSED)               |
| - Interactive Security Guidance Assistant (Official Indian authorities: 1930 / cybercrime.gov.in)       |
| - User Privacy Controller: Configurable retention limits & on-demand history purging                    |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Core Subsystems

### A. AI Detection Layer
1. **Phishing URL Detection Engine (`ai_engine/core/`):**
   - Lexical features: length, domain length, path length, dot counts, hyphen counts, numeric token ratios, entropy.
   - Structural indicators: IP address host detection, sensitive keywords (`login`, `verify`, `banking`), suspicious TLDs, non-HTTPS protocols.
   - Classifier: `RandomForestClassifier` trained on verified benign and phishing datasets. Output: 0.0 to 100.0 risk score.
2. **Communication Fraud Engine (`ai_engine/communication/`):**
   - Natural language processing using TF-IDF word & character n-grams.
   - Classification: `LinearSVC` with calibrated Platt scaling for probability estimation.
   - Pattern matching: Digital-arrest coercion signatures (fake CBI/ED warrants, Supreme Court threats, Skype video interrogation demands, safe account deposits).
   - Privacy redaction: Automatic masking of OTPs, Aadhaar numbers, and credit cards before logging.
3. **Voice Cloning & Audio Deepfake Engine (`ai_engine/audio/`):**
   - Format validation: Strictly WAV format with canonical RIFF/WAVE header validation.
   - Spectral analysis: Mel-frequency cepstral coefficients (MFCCs), spectral centroid, roll-off, zero-crossing rate, and vocoder phase continuity artifacts.
   - Classifier: `RandomForestClassifier`. Discloses limitations: detects acoustic synthesis, does NOT claim speaker identity.
4. **Threat Intelligence Engine (`ai_engine/threat_intelligence/`):**
   - Inbound feed updater from URLhaus with local cached indexing by indicator type (URL, DOMAIN, IP, HASH).
   - Exact indicator matching.

### B. Unified Risk Assessment Engine
- Implemented in `ai_engine/threat_intelligence/intelligence_engine.py` and `threat_correlator.py`.
- **Scoring Formula:**
  $$\text{Final Risk Score} = \min(100.0, \, \max(\text{Base Score}, \, \text{IoC Floor}) + \text{Corroboration Boost})$$
  - Base score = $\max(\text{URL Score}, \text{Comm Score}, \text{Audio Score})$
  - IoC Floor = $80.0$ if verified match exists in active threat blacklist
  - Corroboration Boost = $+15.0$ if two independent vectors corroborate (e.g. phishing link inside coercive message)
- **Defensive Transparency:**
  - Segregates `factual_evidence` (IoC blacklist hits, detected IP, non-HTTPS) from `model_predictions` (RandomForest probabilities).
  - Explicitly records `negative_findings` and `unavailable_information`.
  - Discloses known limitations with zero manufactured certainty.

### C. Proactive Protection Layer
- Response playbooks mapped to Indian legal and reporting frameworks:
  - Immediate helpline: **1930** (National Cyber Crime Reporting Helpline).
  - Online reporting: **cybercrime.gov.in**.
  - Telecom fraud: **DoT Sanchar Saathi / Chakshu**.
  - Technical advisory: **CERT-In**.

