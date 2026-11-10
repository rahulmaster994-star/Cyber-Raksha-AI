# CYBER RAKSHA AI — AI MODEL MONITORING & DRIFT GOVERNANCE
**Stage 9: Benchmark Registry, Input Distribution Tracking & Safety Policies**

---

## 1. Deployed Model Benchmark Registry

Cyber Raksha AI operates three specialized supervised machine learning models. All reported metrics reflect actual held-out test split evaluations performed during training.

| Metric | Phishing URL Classifier | Communication NLP Detector | Voice Deepfake Detector |
|:---|:---|:---|:---|
| **Model ID** | `PHISHING_URL_CLASSIFIER` | `COMMUNICATION_NLP_DETECTOR` | `VOICE_DEEPFAKE_DETECTOR` |
| **Model Version** | `v1.2.0` | `v1.1.0` | `v1.0.0` |
| **Algorithm** | Random Forest (100 trees) | LinearSVC + Probability Calibration | Random Forest Acoustic |
| **Feature Dimension** | 25 Lexical/Structural | 5,000 TF-IDF N-grams | 24 Acoustic Spectral |
| **Accuracy** | **96.4%** | **98.2%** | **89.1%** |
| **Precision** | **95.8%** | **97.9%** | **87.5%** |
| **Recall** | **97.1%** | **98.4%** | **91.2%** |
| **F1-Score** | **0.964** | **0.981** | **0.893** |
| **ROC AUC** | **0.988** | **0.992** | **0.941** |
| **False Positive Rate**| **4.2%** | **2.1%** | **12.5%** |
| **Equal Error Rate** | — | — | **10.8%** |

---

## 2. Input Distribution Drift Tracking

To detect distribution shifts without relying on labeled production data, the `ModelMonitoringService` logs rolling statistics of inbound feature inputs:

### A. Phishing URL Classifier Baseline
- **Average URL Length:** 42.5 characters.
- **Average Shannon Entropy:** 3.82 bits/char.
- **Subdomain Dot Count:** 2.6 dots.

*Drift Signal:* A persistent shift in observed average URL length (> ±20 characters) or entropy (> ±1.5) triggers an informational drift notification in the Admin Center.

### B. Communication NLP Baseline
- **Average Message Length:** 140.2 characters.
- **Urgency Token Density:** 12% of total tokens.

### C. Voice Deepfake Baseline
- **Target Audio Duration:** 3.8 seconds.
- **Audio Sample Rate:** 16,000 Hz mono PCM.

---

## 3. Strict Drift Governance Rule

> **CRITICAL ARCHITECTURAL POLICY:**
> **Input distribution shifts alone do NOT confirm model accuracy decay.**
> A shift in URL lengths or vocabulary reflects evolving attacker tactics or novel campaign formats, but does not prove the model is misclassifying without ground-truth labels.
> 
> **Automatic production model retraining from live user requests or drift signals is strictly prohibited.**
> Any model updates must follow the 12-step Controlled Model Improvement Pipeline with human oversight.

