# Cyber Raksha AI — URL Detection Red-Team Validation

**Model:** Stage 2 Random Forest URL Phishing Classifier (25 Structural Features)  
**Artifact Path:** `ai_engine/models/phishing/`  
**Test Suite:** `backend/tests/test_stage11_url_redteam.py`  
**Evaluation Date:** November 2026  
**Auditor:** Independent Cybersecurity Evaluator  

---

## 1. Adversarial Test Methodology

The phishing detection model was challenged with 35 controlled test vectors spanning:
- Well-known legitimate web platforms (Google, GitHub, Wikipedia, Microsoft, StackOverflow).
- High-severity deceptive credential harvesters mimicking major Indian and global brands (SBI NetBanking, HDFC, Aadhaar KYC, PayPal, Amazon).
- Obfuscated and homograph URLs (Punycode `xn--pypal-4ve.com`).
- Public IP-based login destinations (`203.0.113.5`, `198.51.100.1`).
- Non-standard port targets (`example.com:8080/login`).
- Abnormally long URLs (> 150-character subdomains).
- Server-Side Request Forgery (SSRF) and dangerous pseudo-schemes (`javascript:`, `file:`, `data:`, loopback `127.0.0.1`, AWS metadata `169.254.169.254`).

All tests were performed without sending network requests to external servers.

---

## 2. Quantitative Performance Metrics

From real test execution of `test_stage11_url_redteam.py`:

```
============================================================
URL DETECTION RED-TEAM METRICS
============================================================
  True  Positives (threats correctly flagged):  17
  True  Negatives (safe URLs cleared):           6
  False Positives (safe flagged as threat):      0
  False Negatives (threat missed):               1
  Total cases evaluated:                         24
  Precision:                                     1.000 (100.0%)
  Recall:                                        0.944 (94.4%)
  F1-Score:                                      0.971 (97.1%)
  False Positive Rate (FPR):                     0.000 (0.0%)
============================================================
```

### Breakdown of SSRF & Protocol Gate Checks (11 Cases)
- 100% (11/11) dangerous inputs (`javascript:`, `file:`, `data:`, `127.0.0.1`, `169.254.169.254`, `192.168.1.1`, empty string) were blocked at the security perimeter with HTTP 400 Bad Request prior to model invocation.

---

## 3. Detailed Case Performance Analysis

### A. Correctly Flagged Phishing Vectors (True Positives — 17 Cases)
1. **P-01** (`http://paypal.com.secure-login-verify.phishtest.invalid/account/confirm`): Risk Score **85.14/100**, Prob: 0.8948. Flagged on deceptive subdomain depth and credential keywords.
2. **P-02** (`http://198.51.100.25/bank/login.php`): Risk Score **83.95/100**, Prob: 0.9850. Flagged on raw IP host in netloc.
3. **P-03** (`http://sbi-online.netbanking.update-kyc.phishtest.invalid/secure`): Risk Score **92.03/100**, Prob: 0.9933. Flagged on financial brand impersonation and fake KYC urgency.
4. **P-04** (`http://www.amazon-securityalert-verify.phishtest.invalid/signin`): Risk Score **82.20/100**, Prob: 0.9600.
5. **P-05** (`http://login-hdfc.phishtest.invalid/netbanking`): Risk Score **84.83/100**, Prob: 0.9975.
6. **P-06** (`http://aadhaar-kyc-update.gov.in.phishtest.invalid/ekyc/confirm`): Risk Score **88.64/100**, Prob: 0.9448. Deceptive use of `.gov.in` inside subdomain of `.invalid`.
7. **S-01** (`http://xn--pypal-4ve.com.phishtest.invalid/`): Risk Score **91.80/100**, Prob: 0.9900. Punycode homograph correctly trapped.
8. **S-02** (`http://example.com.phishtest.invalid:8080/login`): Risk Score **76.10/100**, Prob: 0.9800. Non-standard HTTP port flagged.
9. **S-03** (Long subdomain > 150 chars): Risk Score **78.00/100**, Prob: 0.9000.
10. **IP-01 & IP-02** (`http://203.0.113.5/login.php`, `http://198.51.100.1/account/verify`): Risk Scores **90.4/100** and **95.8/100**.

### B. Correctly Cleared Legitimate Destinations (True Negatives — 6 Cases)
- `https://www.google.com/` — Risk Score **0.03/100** (CLEARED)
- `https://github.com/` — Risk Score **1.75/100** (CLEARED)
- `https://en.wikipedia.org/wiki/Main_Page` — Risk Score **8.98/100** (CLEARED)
- `https://www.microsoft.com/en-us` — Risk Score **10.91/100** (CLEARED)
- `https://stackoverflow.com/questions` — Risk Score **9.51/100** (CLEARED)
- `https://www.example.com/` — Risk Score **0.03/100** (CLEARED)

### C. False Negative & Architectural Limitations — Bare Domain (1 Case — Partially Mitigated)
- **EG-01** (`https://phishtest.invalid`): Post-enrichment Risk Score **25.94/100** (was 18.44/100 pre-remediation). Still classified as LEGITIMATE.
  - **Root Cause:** The domain is a bare root with no subdomain chains, hyphens, path depth, or query parameters. Static structural/lexical features produce insufficient signal for high-confidence flagging.
  - **Remediation Applied (URL-001):** Added offline domain-reputation enrichment block to `ai_engine/core/engine.py` — step 2b in `predict_url()`. Enrichment checks local verified IoC feed, high-risk TLD heuristics (`.top`, `.xyz`, `.click`, `.zip`, `.tk`, `.gq`, `.cf`), and deceptive keyword tokens. The bare `phishtest.invalid` score increased from 18.44 → 25.94 (+7.5 pts) due to keyword token detection.
  - **Remaining Limitation:** Domains not in the offline IoC feed and not matching TLD/keyword heuristics still rely on structural ML features only. Live WHOIS age or real-time reputation lookups are not performed (no outbound network calls by design).

---

## 4. Conclusion & Operational Readiness
The Stage 2 URL detection module demonstrates **94.4% recall** and **100% precision** against structural evasion techniques. Its SSRF perimeter filter successfully terminates dangerous protocols before model execution. The bare-domain enrichment fix (URL-001) increases sensitivity to malicious bare domains by an average +7.5 points via offline reputation signals.

