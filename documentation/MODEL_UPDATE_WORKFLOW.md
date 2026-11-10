# CYBER RAKSHA AI — CONTROLLED MODEL UPDATE WORKFLOW
**Stage 9: 12-Step Governance Pipeline, Validation Gates & Rollback Protocol**

---

## 1. Principles of Controlled Model Updates

To maintain reliability and protect against regressions, model modifications in Cyber Raksha AI must follow a formal, human-gated lifecycle:
- **No live in-memory weight modification.**
- **No unvetted retraining from user feedback.**
- **Strict held-out validation against established benchmarks.**
- **Documented rollback procedure for every deployed version.**

---

## 2. The 12-Step Controlled Improvement Pipeline

```
[ 1. Data Collection ] ──> [ 2. Human Vetting ] ──> [ 3. Corpus Assembly ]
          │
          ▼
[ 4. Feature Extraction ] ─> [ 5. Offline Training ] ─> [ 6. Held-Out Evaluation ]
          │
          ▼
[ 7. Benchmark Gating ] ──> [ 8. Safety Scan ] ───> [ 9. Admin Sign-off ]
          │
          ▼
[ 10. Staged Canary ] ───> [ 11. Full Deployment ] ─> [ 12. Drift Monitoring ]
```

### Detailed Phase Definitions:
1. **Candidate Data Ingestion:** Accumulate vetted samples from analyst-confirmed feedback and updated threat feeds.
2. **Human Ground-Truth Verification:** Security analysts verify label correctness on 100% of candidate items.
3. **Corpus Assembly:** Merge vetted candidates into training/test datasets with balanced positive and negative ratios.
4. **Feature Extraction:** Transform raw inputs via standard feature extraction pipelines (25 lexical URL features, 5000 TF-IDF features, or 24 acoustic features).
5. **Offline Model Training:** Train candidate models on isolated staging compute environments.
6. **Held-Out Test Split Evaluation:** Benchmark candidate performance against the immutable golden test set.
7. **Benchmark Gate Enforcement:** The candidate model must satisfy all three promotion criteria:
   - F1-Score equal to or exceeding current production model.
   - False Positive Rate (FPR) does not increase by more than 0.5%.
   - Latency on standard test batch remains within the target envelope (< 50ms for URL, < 20ms for NLP).
8. **Security & Adversarial Robustness Check:** Verify the model cannot be trivially bypassed by character substitutions (e.g., zero-width spaces, Cyrillic homoglyphs).
9. **Formal Administrator Sign-off:** Lead cybersecurity engineer issues cryptographically recorded approval.
10. **Staged Canary Deployment:** Deploy candidate model artifact (`.joblib`) with feature flags enabled for 10% sample verification.
11. **Production Promotion:** Update model artifact on disk, record version metadata in `metadata.json`, and restart application workers.
12. **Post-Deployment Monitoring:** Monitor live input distribution drift and error rates for 72 hours.

---

## 3. Emergency Rollback Protocol

If a newly deployed model artifact exhibits anomalous false positive spikes or degraded latency in production:

1. **Activate Feature Flag or Fallback:**
   - In the Operations Center, toggle `enable_audio_analysis` or relevant flag, or trigger `POST /api/v1/admin/model/{model_id}/rollback`.
2. **Restore Previous Artifact:**
   ```bash
   cd ai_engine/models/<subsystem>/
   cp model.joblib.bak model.joblib
   cp metadata.json.bak metadata.json
   ```
3. **Restart Backend Worker:**
   ```bash
   # Restart uvicorn process
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
4. **Verify Subsystem Health:**
   Check `/api/v1/monitoring/health/detailed` to confirm the restored model reports `READY`.

