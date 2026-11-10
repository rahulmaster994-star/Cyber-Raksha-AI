# Cyber Raksha AI — Phishing Detection Model Evaluation Report
**Model Version**: `v1.0.0-rf-lexical`  
**Algorithm Selected**: `RandomForest`  
**Evaluation Date**: `2026-11-07T14:23:17.925939+00:00`  

---

## 1. Algorithm Comparison Benchmarks (Validation Set)

| Candidate Model | Accuracy | Precision | Recall (Sensitivity) | F1-Score | False Negative Rate (FNR) | Training Time |
|---|---|---|---|---|---|---|
| **RandomForest** | 99.17% | 100.00% | 98.33% | 99.16% | 1.67% | 0.718s |
| **GradientBoosting** | 99.17% | 100.00% | 98.33% | 99.16% | 1.67% | 0.959s |
| **DecisionTree** | 97.51% | 100.00% | 95.00% | 97.44% | 5.00% | 0.011s |
| **LogisticRegression** | 98.76% | 100.00% | 97.50% | 98.73% | 2.50% | 0.054s |

---

## 2. Independent Test Set Evaluation (Holdout Set)
*Evaluated on 240 unseen test samples (120 Phishing / 120 Legitimate).*

| Evaluation Metric | Measured Value | Security Criterion |
|---|---|---|
| **Accuracy** | **99.17%** | Overall classification correctness |
| **Precision** | **100.00%** | Fidelity of flagged phishing events |
| **Recall (Sensitivity)** | **98.33%** | Detection coverage of real phishing attacks |
| **F1-Score** | **99.16%** | Harmonic balance between Precision & Recall |
| **False Negative Rate (FNR)** | **1.67%** | Escaped threats (Critical in cybersecurity) |
| **False Positive Rate (FPR)** | **0.00%** | Legitimate sites blocked falsely |
| **ROC-AUC** | **0.9996** | Class discriminability index |

---

## 3. Confusion Matrix
```
                         PREDICTED LEGITIMATE    PREDICTED PHISHING
ACTUAL LEGITIMATE             120                    0          (False Alarms)
ACTUAL PHISHING               2                      118        (Threats Neutralized)
```

---

## 4. Dataset Provenance and Integrity
- **Phishing Sources**: PhishTank Validated Feeds & OpenPhish Community Repositories.
- **Legitimate Sources**: Top-domain Web Ecosystem Corpus (Universities, Tech, Financial, Government).
- **Data Leakage Safeguards**: Preprocessor scaling was fitted strictly on `X_train` with stratified holdout partitioning.
