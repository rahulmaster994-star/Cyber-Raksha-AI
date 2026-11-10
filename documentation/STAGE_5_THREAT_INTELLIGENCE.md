# CYBER RAKSHA AI — Stage 5 Documentation: Real-Time Threat Intelligence & Unified Risk Engine

## 1. Overview
Stage 5 introduces the Centralized Threat Intelligence and Unified Risk Assessment Engine into Cyber Raksha AI. It unifies all specialized detection subsystems:
- **Stage 2**: Phishing & Malicious URL Lexical Classifier
- **Stage 3**: Communication Fraud & Digital Arrest NLP Model
- **Stage 4**: Voice Cloning & Audio Deepfake Spectrogram Analyzer
- **Stage 5**: Threat Intelligence Feeds & Multi-Vector Correlator

---

## 2. Integrated Threat Intelligence Feeds

| Source | Integration Method | Verification Mechanism | Fallback Policy |
|---|---|---|---|
| **abuse.ch URLhaus** | REST JSON API / Online CSV | SHA256 & community reporter tags | Local cached active IoCs |
| **PhishTank** | Curated feed cache | Multi-analyst consensus verification | Local verified records |
| **OpenPhish** | Public community feeds | Autonomous lexical and DNS verification | Local verified records |
| **CERT-In / I4C** | Advisory intelligence extractions | Official government cybersecurity circulars | Hardened indicator list |

---

## 3. Database Schema Extensions

### `threat_indicators`
- `id` (Integer, Primary Key)
- `indicator_type` (String, Index: URL, DOMAIN, IP, HASH, KEYWORD)
- `indicator_value` (String, Index)
- `threat_type` (String: PHISHING, MALWARE_DOWNLOAD, C2, DIGITAL_ARREST)
- `severity` (String: LOW, MEDIUM, HIGH, CRITICAL)
- `confidence_score` (Float: 0.0 to 1.0)
- `source_name` (String, Index)
- `source_reference` (String)
- `description` (Text)
- `is_active` (Boolean, Index)
- `first_seen` (DateTime)
- `last_seen` (DateTime)

### `threat_feed_logs`
- `id` (Integer, Primary Key)
- `source_name` (String)
- `status` (String: SUCCESS, FAILED, OFFLINE_FALLBACK)
- `records_added` (Integer)
- `duration_seconds` (Float)
- `error_message` (Text)
- `fetched_at` (DateTime)

### `unified_risk_records`
- `id` (Integer, Primary Key)
- `submission_type` (String: SINGLE_VECTOR, MULTI_MODAL)
- `target_summary` (String)
- `overall_risk_level` (String)
- `overall_risk_score` (Float)
- `threat_category` (String)
- `corroboration_factor` (Float)
- `modules_involved` (String)
- `intelligence_matches_count` (Integer)
- `explanation` (Text)
- `recommended_action` (Text)
- `evidence_json` (Text)
- `created_at` (DateTime)

---

## 4. REST API Reference

- `GET /api/v1/intel/status`: Service telemetry, active count by type, and sources.
- `POST /api/v1/intel/search`: Query reputation of any URL, domain, or IP.
- `POST /api/v1/intel/feed/update`: Ingest recent malicious indicators from URLhaus API.
- `GET /api/v1/intel/indicators`: Query verified indicators with limit controls.
- `POST /api/v1/intel/unified/analyze`: Text and URL multi-vector correlation.
- `POST /api/v1/intel/unified/analyze-audio`: Multipart multi-modal voice and text inspection.
- `GET /api/v1/intel/events/live`: Real-time audit stream of platform security events.

---

## 5. Verification
- Pytest suite: `44 passed, 1 warning in 8.39s`
- Frontend build: `✓ 2061 modules transformed. built in 2.59s`

