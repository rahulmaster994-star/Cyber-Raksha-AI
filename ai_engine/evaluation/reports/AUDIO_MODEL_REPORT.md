# Stage 4: Voice Deepfake & Synthetic Audio Detection Model Report

## 1. Overview
- **Model Name:** `voice_deepfake_detector`
- **Algorithm:** `RandomForestClassifier`
- **Stage:** `STAGE_4`
- **Evaluation Date:** `2026-11-07T16:00:31.352649Z`
- **Total Features:** `68` (MFCCs, spectral moments, pitch regularity, HNR)

---

## 2. Dataset Provenance & Methodology
- **Source:** Calibrated Procedural Proxy Speech Corpus (scipy/numpy)
- **Sample Rate:** 16000 Hz
- **Total Samples:** 400 (200 Human-like, 200 Synthetic-like)
- **Train/Test Split:** 80% Train (320 clips) / 20% Test (80 clips)

> **Dataset Limitation Disclosure:**
> Academic deepfake benchmarks (ASVspoof 2019/2021, WaveFake) require institutional registration
> or multi-gigabyte downloads. This model is trained on a calibrated acoustic proxy dataset simulating
> established TTS artifact profiles (spectral flatness, pitch regularity, formant unnaturalness,
> bandwidth limitation). It serves as a fully functional, reproducible pipeline.

---

## 3. Test Evaluation Metrics

| Metric | Score |
|---|---|
| **5-Fold CV Accuracy** | **100.00% (+/- 0.00%)** |
| **Test Accuracy** | **100.00%** |
| **Test Precision** | **100.00%** |
| **Test Recall** | **100.00%** |
| **Test F1-Score** | **100.00%** |
| **Test ROC-AUC** | **1.0000** |

### Confusion Matrix
- **True Negatives (Human correctly identified):** 40
- **False Positives (Human flagged as Synthetic):** 0
- **False Negatives (Synthetic missed):** 0
- **True Positives (Synthetic correctly identified):** 40

---

## 4. Top Feature Importances

| Rank | Feature | Importance |
|---|---|---|
| 1 | `mfcc_9_std` | 0.0600 |
| 2 | `spectral_flatness_std` | 0.0500 |
| 3 | `delta_mfcc_5_std` | 0.0500 |
| 4 | `rms_std` | 0.0400 |
| 5 | `mfcc_0_mean` | 0.0400 |
| 6 | `delta_mfcc_3_std` | 0.0400 |
| 7 | `delta_mfcc_10_std` | 0.0400 |
| 8 | `delta_mfcc_11_std` | 0.0400 |
| 9 | `pitch_regularity` | 0.0400 |
| 10 | `mfcc_10_std` | 0.0400 |

---

## 5. Architectural Safeguards
1. **No 100% Accuracy Claim:** Detection outputs include confidence intervals and explicitly warn about false positives.
2. **Short Audio Guard:** Clips under 0.8 seconds return `INCONCLUSIVE` rather than guessing.
3. **Multi-layer Analysis:** Combines ML probability (60%) with acoustic spectral heuristics (40%).
4. **Zero-Retention:** Uploaded audio is processed purely in-memory / temporary buffer; raw audio is never written to disk or database.
