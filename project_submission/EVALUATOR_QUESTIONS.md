# CYBER RAKSHA AI — EVALUATOR TECHNICAL QUESTIONS & DEFENSE
**Rigorous Technical Answers Reflecting Actual Implementation**

---

### Q1: What specific problem does Cyber Raksha AI solve that existing antivirus or web tools do not?
**Answer:**
Traditional antivirus focuses primarily on file-based binary signatures and known static malware hashes. However, modern cyber attacks in India (such as "digital arrest" extortion, WhatsApp courier scams, and OTP fraud) do not drop malware onto the disk—they use social engineering, manipulated communication, and dynamic phishing infrastructure.
Cyber Raksha AI addresses this gap by analyzing the *behavioral, structural, and semantic* content of URLs, text messages, and voice audio, unifying these indicators with live threat intelligence feeds and generating immediate containment playbooks.

---

### Q2: How is Cyber Raksha AI different from a general AI chatbot (e.g., ChatGPT, Claude)?
**Answer:**
1. **Deterministic Supervised Models vs Generative Text:** General chatbots generate text based on probabilistic token prediction, which can hallucinate safety advice or overlook subtle lexical anomalies. Cyber Raksha AI uses trained, deterministic supervised models (Random Forest, LinearSVC) that extract mathematical features (entropy, character ratios, acoustic spectral coefficients).
2. **Actual Feature Extraction:** We compute 25 structural URL features, TF-IDF urgency matrices, and 24 acoustic vocoder features.
3. **Structured System Actions:** Cyber Raksha AI logs incidents to a relational database, queries real-time IoC databases, and triggers browser extension warnings—capabilities outside the scope of a pure text chat interface.
4. **Privacy:** The platform runs locally and sanitizes sensitive PII (Aadhaar, credit cards, OTPs) before storage, whereas sending scam messages to cloud LLMs often breaches user data privacy.

---

### Q3: Which parts of the system use actual machine learning versus heuristics?
**Answer:**
- **Actual Machine Learning:**
  - *Phishing URL Classifier:* Supervised `RandomForestClassifier` (100 estimators) trained on 25 lexical/structural features extracted from verified phishing and benign datasets.
  - *Communication Scam Detector:* Calibrated `LinearSVC` with a 5,000-feature TF-IDF matrix trained on SMS spam and regional fraud corpora.
  - *Voice Deepfake Detector:* `RandomForestClassifier` trained on 24 acoustic spectral features (centroid, bandwidth, rolloff, zero-crossing rate) to distinguish vocoder synthesis artifacts from natural human speech.
- **Rule-Based & Heuristics:**
  - PII sanitization (Luhn algorithm for credit cards, regex for 12-digit UIDAI Aadhaar, OTP pattern matchers).
  - High-risk keyword matching for law enforcement impersonation ("CBI", "ED", "Customs", "Skype interrogation").
  - URL structural validators and protocol sanity checks.
- **Threat Intelligence:**
  - Direct exact and domain-level matching against live URLhaus and PhishTank indicators.

---

### Q4: How does the Unified Risk Engine calculate its final score?
**Answer:**
The Unified Risk Engine uses a multi-factor evidence fusion model:
1. **Base Component Weights:** Individual risk scores from URL analysis ($W_{url} = 0.35$), communication analysis ($W_{comm} = 0.35$), and audio analysis ($W_{audio} = 0.30$).
2. **Corroboration Multiplier:** When multiple independent modalities exhibit high risk simultaneously (e.g., an extortion message containing a phishing link), a non-linear corroboration bonus (+15 to +25 points) is added.
3. **Threat Intelligence Override:** A direct match with an active, fresh URLhaus/PhishTank IoC sets the risk floor to at least 85 (High Risk).
4. **Stale Intelligence Discount:** If threat feed data is older than 24 hours, its contribution is discounted by 20% to prevent stale reputation scores from skewing new analysis.
5. **Deduplication:** Overlapping signals (such as a URL detected inside a message) are processed as a single correlated entity to prevent double-counting.

---

### Q5: How does the system handle user feedback and prevent adversarial data poisoning?
**Answer:**
A major architectural risk in AI security is adversarial poisoning—malicious actors reporting known phishing domains as "safe" to manipulate classifiers.
Cyber Raksha AI strictly enforces a **Zero Automatic Retraining Policy**:
- User feedback submitted via `FeedbackModal.tsx` is stored in the `analysis_feedback` table with status `PENDING`.
- No live model weights or inference pathways are touched.
- Security analysts review tickets in the **Admin Operations Center** (`/admin`).
- Only human-confirmed samples are promoted into an isolated candidate dataset for offline training, benchmark verification against held-out splits, and staged deployment.

---

### Q6: What happens when the host device has no internet connection?
**Answer:**
Cyber Raksha AI is built to operate reliably in partitioned or air-gapped environments:
1. **Local ML Inference:** All Scikit-Learn models and feature extractors run in-process using local CPU compute. URL, text, and voice classifications function 100% offline.
2. **Local Threat Intelligence Cache:** The platform falls back to cached threat signatures in `cyber_raksha.db` without failing.
3. **PWA Offline Support:** The frontend service worker caches application assets, allowing the UI to open and function offline.

---

### Q7: What are the current operational limitations of this prototype?
**Answer:**
1. **Brand-New Zero-Day Domains:** Phishing sites registered within the last 2 hours may not appear in community feeds; detection relies solely on lexical ML heuristics.
2. **Audio Scope:** The voice detector identifies synthetic vocoder artifacts, not the biometric identity of the speaker.
3. **Database Scalability:** The current release uses SQLite, which is ideal for single-node deployments up to ~100k records, but multi-node enterprise deployments will require transitioning to PostgreSQL (supported natively via our SQLAlchemy models).

