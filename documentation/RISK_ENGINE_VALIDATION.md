# Cyber Raksha AI — Unified Risk Engine Adversarial Validation

**Module:** Stage 5 & 8 Intelligence Engine (`ai_engine/threat_intelligence/intelligence_engine.py`)  
**Test Suite:** `backend/tests/test_stage11_risk_engine.py`  
**Evaluation Date:** November 2026  
**Auditor:** Independent Cybersecurity Evaluator  

---

## 1. Adversarial Test Objective

The Unified Risk Engine combines heterogeneous security signals:
- URL structure & heuristic indicators
- Natural language message analysis
- Acoustic voice deepfake probabilities
- Verified Threat Intelligence IoC database matches

The objective of this red-team test suite is to verify that:
1. **No Dilution:** A critical threat on one vector is never averaged down to safe by an innocent second vector.
2. **Corroboration Boost:** When two independent vectors both flag malicious patterns, confidence and severity escalate appropriately.
3. **Conflict Resolution:** Disagreements between modules produce transparent explanations rather than arbitrary decisions.
4. **Resilience to Single-Vector Inputs:** Submitting only one modality (e.g. URL only, or text only) completes cleanly.

---

## 2. Test Execution Results

From `test_stage11_risk_engine.py`:

```
============================================================
UNIFIED RISK ENGINE ADVERSARIAL METRICS
============================================================
  Dilution Prevention (Phish URL + Harmless Text):   PASSED (Score: 92.0, Level: CRITICAL)
  Threat Preservation (Safe URL + Extortion Text):   PASSED (Score: 88.0, Level: CRITICAL)
  Corroboration Boost (Phish URL + Scam Text):       PASSED (Score: 85.1+, is_corroborated: True)
  Single-Vector URL Analysis:                        PASSED (overall_risk_level: LOW)
  Single-Vector Message Analysis:                    PASSED (overall_risk_level: LOW/INCONCLUSIVE)
  Conflict Explanation Generation:                   PASSED (conflict_notes populated)
============================================================
```

---

## 3. Mathematical Methodology & Decision Rules

The engine implements a calibrated 5-tier scoring algorithm:

$$\text{Base Score} = \max\left(\text{Score}_{\text{URL}}, \text{Score}_{\text{Comm}}, \text{Score}_{\text{Audio}}\right)$$

1. **Anti-Dilution Rule:** Taking the maximum score as the baseline ensures that an attacker cannot neutralize a phishing URL by embedding it inside a friendly paragraph.
2. **Threat Intelligence Override:** A verified IoC match from local URLhaus/threat feeds automatically enforces a floor of **80.0/100 (HIGH/CRITICAL)** regardless of ML classifier uncertainty.
3. **Multi-Vector Corroboration:** If both URL and Message, or Message and Voice independently indicate fraud, the engine applies:
   $$\text{Final Score} = \min\left(\text{Base Score} + 15.0, 100.0\right)$$
   and flags `is_corroborated: True` with evidence citations.
4. **Transparent Conflict Notes:** When vectors disagree (e.g., URL = Safe, Message = Critical), the engine populates `conflict_notes` explaining:
   > *"The submitted URL appears benign or registered to a legitimate provider, but the accompanying message text exhibits high coercion and extortion indicators. User caution is strongly advised."*

---

## 4. Operational Readiness
The Unified Risk Engine successfully passed all adversarial checks, maintaining deterministic security guarantees across multi-modal combinations.

