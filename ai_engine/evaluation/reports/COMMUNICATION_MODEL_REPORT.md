# Cyber Raksha AI — Communication Fraud Detection Model Evaluation Report
**Model Version**: `v1.0.0-tfidf-linear-svc`  
**Algorithm Selected**: `LinearSVC`  
**Evaluation Date**: `2026-11-07T15:15:23.281043+00:00`  

---

## 1. Candidate Algorithm Benchmarks (Validation Set)

| Candidate Model | Accuracy | Precision | Recall | F1-Score |
|---|---|---|---|---|
| **LinearSVC** | 98.07% | 97.70% | 86.73% | 91.89% |
| **LogisticRegression** | 96.13% | 100.00% | 69.39% | 81.93% |
| **MultinomialNB** | 96.39% | 100.00% | 71.43% | 83.33% |

---

## 2. Independent Test Set Performance (Holdout Set)
*Evaluated on 776 unseen test samples (98 Fraud / 678 Legitimate).*

| Evaluation Metric | Measured Value | Security Criterion |
|---|---|---|
| **Accuracy** | **98.45%** | Overall classification correctness |
| **Precision** | **97.78%** | Fidelity of flagged fraud attempts |
| **Recall (Sensitivity)** | **89.80%** | Detection coverage of fraudulent messages |
| **F1-Score** | **93.62%** | Harmonic balance between Precision & Recall |
| **False Negative Rate (FNR)** | **10.20%** | Escaped scam attempts |
| **False Positive Rate (FPR)** | **0.29%** | Legitimate messages falsely flagged |

---

## 3. Confusion Matrix
```
                         PREDICTED LEGITIMATE    PREDICTED FRAUD/SPAM
ACTUAL LEGITIMATE             676                    2          (False Alarms)
ACTUAL FRAUD/SPAM             10                     88         (Neutralized)
```
