# Cyber Raksha AI — Phase B4: Machine Learning Model Evaluation Report

## 1. Model Identification & Architecture

- **Model Identifier**: `v1.0.0-rf-lexical`
- **Algorithm**: `RandomForestClassifier` (100 estimators, random_state=42)
- **Feature Space**: 25 continuous and binary lexical/structural features
- **Inference Mode**: Local CPU-bound scikit-learn pipeline (Zero GPU/Cloud requirement)
- **Artifacts on Disk**:
  - Model: `ai_engine/models/phishing/phishing_classifier.joblib` (~456 KB)
  - Preprocessor: `ai_engine/models/phishing/url_preprocessor.joblib` (~2 KB)
  - Metadata: `ai_engine/models/phishing/model_metadata.json`

---

## 2. Benchmark Dataset Provenance

The model was trained and evaluated on the curated **Cyber Raksha Phishing Detection Benchmark Dataset**:
- **Total Records**: 1,600 balanced samples (1:1 class ratio)
  - Legitimate URLs: 800
  - Phishing URLs: 800
- **Partitioning**: Stratified 70% Train (1,120) / 15% Validation (240) / 15% Test (240)
- **Sources**:
  1. *OpenPhish Community Feed*: Verified zero-day phishing feeds.
  2. *PhishTank Online Valid Database*: Community-verified credential harvesting targets.
  3. *Curated Benign Domain Corpus*: Top Alexa/Tranco domains and authorized government/banking services.

---

## 3. Algorithm Comparative Evaluation

During model selection, four representative classification families were benchmarked under identical stratified validation partitions (240 samples):

| Metric | Random Forest (Selected) | Gradient Boosting | Decision Tree | Logistic Regression |
|---|---|---|---|---|
| **Accuracy** | **99.17%** | 99.17% | 97.51% | 98.76% |
| **Precision** | **1.0000** | 1.0000 | 1.0000 | 1.0000 |
| **Recall** | **0.9833** | 0.9833 | 0.9500 | 0.9750 |
| **F1-Score** | **0.9916** | 0.9916 | 0.9744 | 0.9873 |
| **False Positive Rate** | **0.00%** | 0.00% | 0.00% | 0.00% |
| **ROC-AUC** | **0.9987** | 0.9989 | 0.9895 | 0.9908 |
| **Training Time** | **0.718 s** | 0.959 s | 0.011 s | 0.054 s |
| **Average Latency** | **< 2.5 ms** | < 3.2 ms | < 1.0 ms | < 0.8 ms |

### Architectural Decision Rationale:
`RandomForest` was selected due to its ensemble resistance to single-feature gaming (e.g. an attacker manipulating URL length alone cannot evade the forest) while maintaining sub-3 millisecond inference on commodity laptop CPUs.

---

## 4. Test Partition Confusion Matrix (240 Samples)

```
                       Actual Benign      Actual Phishing
Predicted Benign            120                 2
Predicted Phishing           0                118
```

- **True Negatives (TN)**: 120 (100% of benign test URLs correctly cleared)
- **False Positives (FP)**: 0 (Zero benign URLs mistakenly flagged)
- **False Negatives (FN)**: 2 (0.83% missed subtle phishing URLs)
- **True Positives (TP)**: 118 (98.33% detection rate on real phishing)

---

## 5. Performance Telemetry & Operational Characteristics

- **Cold-Start Load Time**: ~120 ms (loaded once and held in memory via singleton `ModelManager`)
- **Per-Sample Inference Latency**:
  - Feature Extraction: 1.2 ms - 2.1 ms
  - Model Inference: 0.6 ms - 1.1 ms
  - Total End-to-End Latency: **~2.8 ms**
- **Memory Footprint**: < 15 MB RAM consumed by model artifacts in-memory
- **Resource Compatibility**: Optimized for lightweight laptop execution (16 GB RAM environment).

---

## 6. Known Limitations & Mitigation Measures

1. **Shortened URLs (`bit.ly`, `tinyurl`)**:
   - *Limitation*: Lexical features of a shortener redirect convey zero information about the eventual destination.
   - *Mitigation*: The feature extractor flags shorteners (`is_shortener: True`), contributing +20.0 risk and generating clear advisory warnings to expand the URL prior to credential entry.
2. **Homoglyph & Internationalized Domain Names (IDN)**:
   - *Limitation*: Unicode characters imitating Latin scripts (e.g., Cyrillic 'a').
   - *Mitigation*: Punycode detection (`xn--` prefix search and `idna` normalization) flags spoofed scripts as high-risk.
3. **Compromised Legitimate Subdomains**:
   - *Limitation*: Attackers hosting malicious forms on compromised legitimate domains (e.g. `docs.google.com/forms/...`).
   - *Mitigation*: Multi-vector correlation engine combines ML inference with URLhaus threat indicators and path-level pattern matching.

