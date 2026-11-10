# CYBER RAKSHA AI — USER FEEDBACK & HUMAN REVIEW QUEUE
**Stage 9: Governance, Reporting Taxonomy, Reviewer Workflow & Privacy Safeguards**

---

## 1. Overview & Ethical Governance

User feedback is a vital signal for discovering false positives and novel threats. However, incorporating unvetted user input directly into model training weights creates significant vulnerability to **adversarial data poisoning** (e.g., attackers reporting genuine phishing links as "safe" to manipulate classifiers).

Cyber Raksha AI addresses this by establishing an isolated **Human Review Queue**:
1. Users submit feedback with structured categories and optional explanations.
2. Feedback records are stored with status `PENDING`.
3. Model weights and inference logic remain completely unchanged.
4. Security analysts review submissions in the protected Admin Operations Center.
5. Confirmed reports are isolated into controlled candidate pools for future offline retraining.

---

## 2. Feedback Category Taxonomy

When reporting on a detection result, users select from standard categories:

| Category | Description | Typical Use Case |
|:---|:---|:---|
| **`FALSE_POSITIVE`** | Benign resource incorrectly classified as a threat | Legitimate enterprise intranet or corporate login portal flagged as phishing |
| **`FALSE_NEGATIVE`** | Genuine threat incorrectly classified as legitimate/safe | Novel evasion technique or unlisted phishing campaign |
| **`CORRECT_THREAT`** | Accurate detection confirmed by user | User acknowledges malicious OTP harvesting attempt |
| **`INCORRECT_CATEGORY`** | Threat identified correctly, but classified under wrong vector | Lottery scam classified as courier delivery scam |
| **`UNSURE`** | User is uncertain and requests human confirmation | Ambiguous communication with unusual urgency |
| **`OTHER`** | Operational bugs or edge-case feedback | Rendering or formatting abnormalities |

---

## 3. Reviewer Workflow & Status Transitions

```
    [ User Submits Feedback ]
                │
                ▼
      ┌──────────────────┐
      │  Status: PENDING │
      └─────────┬────────┘
                │
                ▼
  [ Analyst Opens Admin Queue ]
                │
         ┌──────┴──────────────────────────┐
         │                                 │
         ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐
│ Status: CONFIRMED│             │ Status: REJECTED │
│ (Added to pool)  │             │ (Invalid report) │
└──────────────────┘             └──────────────────┘
```

- **`PENDING`**: Initial status upon user submission.
- **`UNDER_REVIEW`**: Analyst has claimed the ticket for triage.
- **`CONFIRMED`**: Analyst independently verified the inaccuracy. Record is promoted to the offline retraining candidate pool.
- **`REJECTED`**: Analyst determined the user submission was invalid or an attempted adversarial manipulation.
- **`INCONCLUSIVE`**: Insufficient evidence to verify or refute the user's assertion.

---

## 4. Privacy & Data Minimization

- User feedback records are scrubbed using the platform's PII Redactor (`text_preprocessor.py`).
- Credit card numbers (16-digit Luhn), Aadhaar IDs (12-digit UIDAI), and OTP tokens are sanitized before persistence in the `analysis_feedback` table.
- Submissions require no user sign-up or personal identity disclosure.

