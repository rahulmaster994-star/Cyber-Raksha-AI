# Cyber Raksha AI — AI Subsystem Architecture

## Overview
The `ai_engine` directory houses the modular machine learning and deep learning subsystems for the Cyber Raksha AI platform.

## Directory Structure
- `datasets/`: Dataset storage, ingest pipelines, and data cataloging.
- `preprocessing/`: Input normalization, tokenization, acoustic feature extraction, and URL parsing.
- `models/`: Neural network definitions, model registry, and checkpoint management.
- `training/`: Training routines, hyperparameter schedules, and checkpoint exports.
- `evaluation/`: Benchmark verification, ROC/AUC metrics, precision/recall analysis.
- `inference/`: Low-latency runtime engine serving predictions to the FastAPI backend.

## Implementation Roadmap
- **Stage 1 (Current)**: Architecture scaffolded and validated. No models loaded.
- **Stage 2**: Phishing NLP models and Lexical URL classifiers.
- **Stage 3**: Audio deepfake detection (spectrogram ResNet / Whisper embeddings) and communication risk analysis.
- **Stage 4**: Real-time Threat Intelligence and Multi-layer Fraud Scoring.
- **Stage 5**: Explainable AI (SHAP/LIME) attribution and Android edge optimizations.
