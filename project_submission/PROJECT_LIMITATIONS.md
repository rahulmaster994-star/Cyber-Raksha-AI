# CYBER RAKSHA AI — PROJECT LIMITATIONS & BOUNDARIES
**Realistic Disclosure of Operational Scope, Model Constraints & Infrastructure Boundaries**

---

## 1. Machine Learning & Detection Model Limitations

### A. Phishing URL Classifier
- **Evasion via URL Shorteners:** Multi-hop redirections through custom URL shortening services (e.g., bit.ly, tinyurl) mask destination domain lexical features unless live network resolution is followed.
- **Novel TLDs:** Newly created top-level domains not represented in training datasets may produce lower confidence scores.
- **Legitimate Compromised Subdomains:** Legitimate high-reputation domains (e.g., Google Forms, Notion, GitHub Pages) hosting malicious content exhibit legitimate root domain features and rely heavily on keyword heuristics and user reporting.

### B. Communication Scam Detector
- **Obfuscated / Leetspeak Text:** Severe deliberate phonetic or leetspeak substitutions (e.g., "K.Y.C_u-p-d-a-t-e", Cyrillic lookalike glyphs) may degrade TF-IDF token matching.
- **Multilingual Regional Dialects:** The current NLP model is primarily trained on Indian English and Romanized Hindi/Hinglish fraud patterns. Pure vernacular regional scripts (e.g., Tamil, Telugu, Bengali) currently match on extracted numeric and URL entities rather than full semantic nuance.

### C. Voice Deepfake Impersonation Detector
- **No Biometric Speaker Verification:** The model evaluates acoustic spectral distributions and vocoder artifacts; it does **not** identify *who* is speaking or match voices against an enrolled biometric database.
- **Low-Bandwidth Audio Degradation:** Audio transmitted over low-bitrate GSM cellular calls (8kHz AMR codec) suffers spectral compression that can obscure high-frequency vocoder synthesis artifacts.

---

## 2. Threat Intelligence Feed Limitations

- **Community Ingestion Lag:** Crowdsourced feeds (URLhaus, PhishTank) depend on researcher reporting and automated sandbox confirmation. Newly weaponized infrastructure may experience a 2 to 6 hour detection delay before appearing in external feeds.
- **Rate Limit Constraints:** To remain 100% free and compliant with community terms of service, live queries to URLhaus are throttled at 10 requests per minute.
- **Regional Indian Threat Gaps:** Global threat intelligence feeds often under-index localized Indian banking phishing kits (e.g., SBI YONO, PNB One, e-Challan payment scams). Cyber Raksha's internal curated IoC table mitigates this for vetted patterns, but requires continuous operational updates.

---

## 3. Infrastructure & Deployment Limitations

- **Single-Node SQLite Storage:** The default storage engine is SQLite. While zero-configuration and zero-budget, SQLite does not support distributed multi-master writes. For multi-server enterprise clustering, the database URL must be configured for PostgreSQL.
- **Browser Extension Platform Restrictions:** The Chromium extension requires Manifest V3. In accordance with Chrome security policies, scanning requires explicit active-tab permission and does not intercept system-wide network sockets.
- **No Native Android Background Packet Capture:** The Android companion runs as an installable PWA with Web Share Target support. It does not inspect third-party app memory or perform root-level packet inspection, as doing so would violate Android platform sandbox security boundaries.

