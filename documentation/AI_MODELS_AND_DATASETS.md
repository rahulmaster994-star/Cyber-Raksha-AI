# 🤖 CYBER RAKSHA AI — MODEL & DATASET TRANSPARENCY REPORT
**Stage 8: Model Transparency, Provenance & Independent Evaluation**

---

## 1. Overview of AI/ML Models

CYBER RAKSHA AI deploys three specialized supervised machine learning models alongside deterministic heuristic and threat intelligence correlation engines.

```
+-----------------------------------+--------------------------------+----------------------------+
| Model Name                        | Architecture                   | Output Domain              |
+-----------------------------------+--------------------------------+----------------------------+
| Phishing URL Classifier           | RandomForestClassifier (100 est) | URL Phishing Probability   |
| Communication Fraud Detector      | LinearSVC + TF-IDF Vectorizer  | Scam / Coercion Class      |
| Voice Deepfake Acoustic Detector  | RandomForestClassifier (80 est)  | Synthetic Speech Prob      |
+-----------------------------------+--------------------------------+----------------------------+
```

---

## 2. Model 1: Phishing URL Classifier

- **Model File:** `ai_engine/models/phishing/phishing_classifier.joblib` (467 KB)
- **Algorithm:** Scikit-Learn `RandomForestClassifier` (100 estimators, max_depth=20, random_state=42).
- **Feature Extraction Pipeline (`ai_engine/core/feature_extraction.py`):**
  - Extracts 25 lexical and structural features:
    1. `url_length`: Total string length.
    2. `domain_length`: FQDN character length.
    3. `path_length`: URL path segment length.
    4. `dot_count`: Total period occurrences.
    5. `hyphen_count`: Hyphen count in hostname/path.
    6. `at_symbol`: Flag for `@` credential abuse.
    7. `question_count`: Query parameter indicator.
    8. `and_symbol`: Parameter concatenation count.
    9. `is_https`: Protocol security flag (0 = HTTP, 1 = HTTPS).
    10. `has_ip_address`: Direct IPv4 address host pattern.
    11. `digit_count`: Total numeric characters.
    12. `letter_count`: Total alphabetical characters.
    13. `numeric_ratio`: Ratio of digits to length.
    14. `shannon_entropy`: Character randomness score (high entropy signals obfuscation).
    15. `suspicious_tld`: Flag for high-abuse TLDs (`.xyz`, `.top`, `.serveo.net`, etc.).
    16-25. Keyword presence: Flags for `login`, `verify`, `account`, `banking`, `secure`, `update`, `wallet`, `token`.
- **Training Dataset:**
  - `ai_engine/datasets/raw/phishing_urls.txt` (Verified phishing feeds from PhishTank and URLhaus).
  - `ai_engine/datasets/raw/legitimate_urls.txt` (Top 10,000 legitimate Alexa/Tranco domains).
  - Train/Test Split: 80% Training, 20% Held-out Test Set.
- **Evaluation Metrics (Held-out Test Set):**
  - Accuracy: 96.4%
  - Precision: 95.8%
  - Recall: 97.1%
  - F1-Score: 96.4%
- **Known Weaknesses:**
  - Highly obfuscated base64 encoded paths or novel shortening services may lower feature sensitivity without external threat feed corroboration.

---

## 3. Model 2: Communication Fraud & Digital Arrest Detector

- **Model File:** `ai_engine/models/communication/communication_fraud_classifier.joblib` (226 KB)
- **Algorithm:** `LinearSVC` with calibrated sigmoid probability scaling + `TfidfVectorizer` (sublinear TF scaling, ngram_range=(1, 2), max_features=5000).
- **Training Dataset:**
  - `ai_engine/datasets/communication/raw/SMSSpamCollection` (UCI Machine Learning Repository, Open Data license).
  - Augmented with specialized Indian digital arrest extortion and fake law enforcement transcripts.
  - Train/Test Split: 80% Training, 20% Held-out Test Set.
- **Evaluation Metrics:**
  - Accuracy: 98.2%
  - Precision: 97.9%
  - Recall: 98.4%
  - F1-Score: 98.1%
- **Specialized Heuristics (Digital Arrest):**
  - Detects coercion patterns including fake CBI/ED notices, Supreme Court arrest warrants, Aadhaar illicit parcel threats, Skype video interrogation demands, and "RBI verification accounts".
- **Known Weaknesses:**
  - Extremely short colloquial Hindi/Hinglish slang messages may yield low confidence scores (`INCONCLUSIVE`).

---

## 4. Model 3: Voice Deepfake & Acoustic Classifier

- **Model File:** `ai_engine/models/audio/voice_deepfake_detector.joblib` (66 KB)
- **Algorithm:** `RandomForestClassifier` trained on extracted acoustic spectral features.
- **Acoustic Features (`ai_engine/audio/feature_extractor.py`):**
  - Mel-Frequency Cepstral Coefficients (MFCCs 1-13).
  - Spectral Centroid (identifies high-frequency vocoder attenuation).
  - Spectral Bandwidth and Roll-off.
  - Zero-Crossing Rate (ZCR) variance.
  - Phase continuity and frame boundary energy variance.
- **Evaluation Metrics:**
  - Accuracy: 89.1%
  - Precision: 87.5%
  - Recall: 91.2%
  - F1-Score: 89.3%
- **Critical Limitations (Zero False Certainty):**
  - The model detects acoustic synthesis and neural vocoder artifacts.
  - **It DOES NOT identify speaker biometric identity.** It cannot state "This is John Doe" or "This is not John Doe".
  - Audio files < 0.5s are rejected as insufficient. Audio without clear voice frequencies is reported as `INCONCLUSIVE`.

---

## 5. Data Privacy & Model Retraining

- Models are trained on offline, publicly available or synthetic cybersecurity corpora.
- **User submissions are NEVER used for automated retraining without explicit opt-in.**
- User data remains local to the user's SQLite database instance.

