# Cyber Raksha AI — B4.1 Detection Intelligence Audit

**Audit Date**: November 2026  
**Lead Evaluator**: Senior AI/ML Engineer & Threat Intelligence Lead  
**Model Under Audit**: `v1.0.0-rf-lexical` (RandomForestClassifier, 100 estimators, 25 lexical/structural dimensions)

---

## 1. Executive Summary & Verification of Prior Reported 99.17% Accuracy

The previous B4 report claimed a test accuracy of **99.17%** with **100% precision**, **98.33% recall**, and **0.00% False Positive Rate** on a 240-sample test set.

Our independent audit confirmed the following:
1. **Model Artifacts**: Real, locally serialized model artifacts exist at `ai_engine/models/phishing/phishing_classifier.joblib` (456 KB) and `url_preprocessor.joblib` (2 KB). Model inference is completely offline and CPU-executable.
2. **Dataset Provenance**: The raw dataset exists at `ai_engine/datasets/raw/` containing 800 real phishing URLs (sourced from OpenPhish community feeds and verified PhishTank community exports) and 800 curated legitimate URLs (Alexa/Tranco top domains, public institutions, and developer services).
3. **Domain Leakage Discovery**:
   - The legitimate set contained 800 URLs derived across only 90 unique domain hosts with varying sub-paths.
   - When split randomly (70% train / 15% validation / 15% test), **72 of the 183 test domains (39.3%) were already present in the training set**.
   - This domain leakage slightly inflated the reported test accuracy to 99.17%.

---

## 2. Rigorous Domain-Separated Evaluation (Zero Leakage)

To eliminate domain leakage, we performed a strict **5-Fold GroupKFold Cross-Validation**, grouping strictly by registrable domain name. In this evaluation, no domain present in the test fold ever appeared in the training fold.

### Domain-Separated 5-Fold Performance Metrics:

| Metric | GroupKFold (Zero Domain Overlap) | Random Split (Reported Baseline) | Delta / Interpretation |
|---|---|---|---|
| **Accuracy** | **98.44% ± 1.54%** | 99.17% | -0.73% (True generalizability across unseen domains) |
| **Precision** | **98.29% ± 1.91%** | 100.0% | -1.71% (Slight false positive rate on unusual benign domains) |
| **Recall** | **0.9862 ± 1.36%** | 98.33% | +0.29% (Consistent high detection of true phishing) |
| **F1-Score** | **98.45% ± 1.53%** | 99.16% | -0.71% |
| **ROC-AUC** | **0.9978 ± 0.0028** | 0.9987 | Robust discriminator capability |

### Confusion Matrix (Aggregated across 1,600 samples):
```
                       Actual Legitimate (800)    Actual Phishing (800)
Predicted Legitimate             786                        11
Predicted Phishing                14                       789
```
- **False Positive Rate (FPR)**: 1.75% (14 / 800)
- **False Negative Rate (FNR)**: 1.38% (11 / 800)
- **Specificity**: 98.25%

---

## 3. Adversarial & Edge-Case Stress Testing

We subjected the detector to 13 distinct adversarial, deceptive, and edge-case attack profiles:

| Test Case Name | Sample URL Evaluated | Indicators Triggered | Classification | Composite Risk | Verdict |
|---|---|:---:|:---:|:---:|:---:|
| **Homoglyph & Punycode** | `http://xn--gogle-qta.com/signin` | Punycode / IDN homograph | `SUSPICIOUS` | 66.7 (MEDIUM) | **DETECTED** |
| **Raw IP Hostname** | `http://192.168.1.100:8080/login.php` | Raw IP address, Insecure port | `PHISHING` | 78.6 (HIGH) | **DETECTED** |
| **Misleading Subdomain** | `http://paypal.com.crypto-wallet-verify.net/` | Deceptive brand token | `PHISHING` | 84.5 (HIGH) | **DETECTED** |
| **Extremely Long URL** | `http://service.org/` + 250 `'a'`s | Anomalous URL length | `PHISHING` | 75.8 (HIGH) | **DETECTED** |
| **URL Shortener** | `https://bit.ly/3xY9kLm` | Obfuscating shortener | `SUSPICIOUS` | 55.1 (MEDIUM) | **WARNED** |
| **Hex-Encoded Characters** | `http://portal.com/%2e%2e/%2flogin?auth=***` | Obfuscated directory traversal | `PHISHING` | 84.5 (HIGH) | **DETECTED** |
| **Suspicious Open Redirect** | `http://portal.com/view?redirect=http://evil.com` | Open redirect param | `SUSPICIOUS` | 69.7 (MEDIUM) | **WARNED** |
| **Unusual TCP Port** | `http://portal-service.org:9999/status` | Non-standard web port | `PHISHING` | 76.8 (HIGH) | **DETECTED** |
| **Brand Impersonation (SBI)** | `http://sbi-netbanking-update.xyz/verify` | Brand Impersonation, Bad TLD | `PHISHING` | 96.8 (CRITICAL) | **DETECTED** |
| **Brand Impersonation (HDFC)** | `http://hdfc-bank-netbanking-verify.xyz/login`| Brand Impersonation, Bad TLD | `PHISHING` | 96.1 (CRITICAL) | **DETECTED** |
| **Legit with Security Word** | `https://en.wikipedia.org/wiki/Phishing_investigation` | None | `LEGITIMATE` | 4.2 (SAFE) | **CLEARED** |
| **Legit Official Bank** | `https://onlinesbi.sbi/portal` | None (Authorized domain) | `LEGITIMATE` | 0.7 (SAFE) | **CLEARED** |
| **Unseen Multi-Hyphen Benign** | `https://acme-cyber-solutions-2026.org/products` | None | `LEGITIMATE` | 16.1 (LOW) | **CLEARED** |

---

## 4. Elimination of Static Whitelists & Defense-in-Depth Calibration

### The Problem With Hardcoded Whitelists
Previously, a hardcoded rule blindly bypassed domains ending in `.gov.in`, `.nic.in`, `.gov`, or `.mil`. This violated core defense-in-depth principles:
- Compromised government web portals (e.g. vulnerable CMS hosting malicious files or open redirects) would be unconditionally trusted.
- Attackers registering lookalike subdomains on third-party infrastructure could exploit prefix confusion.

### The Solution: Corroborated Evidence-Based Calibration
In `ai_engine/core/prediction.py`, we replaced static TLD whitelisting with **corroborated evidence weighting**:
1. When a URL exhibits **zero** structural deception markers (no brand impersonation, no raw IP, no bad port, no punycode, no malicious keyword), lexical ML probability is capped so that unusual domain length or hyphens alone cannot produce a `PHISHING` false positive.
2. If a `.gov.in` or legitimate domain contains a verified threat indicator or credential harvesting path, the indicator triggers normally and flags the threat.
3. Legitimate banking and institutional portals (`onlinesbi.sbi`, `legitimate-bank-portal.gov.in`) are preserved as `SAFE` / `LOW` risk without artificial whitelists.

