"""
Cyber Raksha AI - AI Engine Configuration
Stage 2: Core AI Engine & Phishing Detection
"""
import os
from pathlib import Path

# Base Paths
AI_ENGINE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = AI_ENGINE_DIR.parent
DATASETS_DIR = AI_ENGINE_DIR / "datasets"
RAW_DATA_DIR = DATASETS_DIR / "raw"
PROCESSED_DATA_DIR = DATASETS_DIR / "processed"
MODELS_DIR = AI_ENGINE_DIR / "models"
PHISHING_MODEL_DIR = MODELS_DIR / "phishing"
URL_CLASSIFIER_DIR = MODELS_DIR / "url_classifier"
EVALUATION_DIR = AI_ENGINE_DIR / "evaluation"
REPORTS_DIR = EVALUATION_DIR / "reports"

# Ensure directories exist
for directory in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    PHISHING_MODEL_DIR,
    URL_CLASSIFIER_DIR,
    REPORTS_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)

# Random Seed for Reproducibility
RANDOM_STATE = 42

# Model Metadata
CURRENT_MODEL_VERSION = "v1.0.0-rf-lexical"
MODEL_FILENAME = "phishing_classifier.joblib"
PREPROCESSOR_FILENAME = "url_preprocessor.joblib"
METADATA_FILENAME = "model_metadata.json"

# Feature Names extracted from URLs
FEATURE_NAMES = [
    "url_length",
    "domain_length",
    "dot_count",
    "hyphen_count",
    "underscore_count",
    "slash_count",
    "question_mark_count",
    "equal_count",
    "at_symbol_count",
    "percent_count",
    "special_char_count",
    "subdomain_count",
    "has_ip_address",
    "is_https",
    "suspicious_keyword_count",
    "has_at_symbol",
    "has_suspicious_port",
    "path_length",
    "query_param_count",
    "digit_count",
    "letter_count",
    "digit_to_letter_ratio",
    "tld_length",
    "is_punycode_or_idn",
    "consecutive_char_run"
]

# Suspicious keyword terms commonly present in credential harvesting and phishing attacks
SUSPICIOUS_KEYWORDS = [
    "login", "signin", "verify", "verification", "secure", "security",
    "account", "banking", "update", "authenticate", "wallet", "support",
    "confirm", "service", "billing", "invoice", "paypal", "appleid",
    "microsoft", "netflix", "recover", "passcode", "credential", "suspend",
    "alert", "warning", "ebay", "amazon", "chase", "wellsfargo", "bofa"
]

# Risk Thresholds
RISK_THRESHOLDS = {
    "LOW": (0.0, 30.0),
    "MEDIUM": (30.0, 60.0),
    "HIGH": (60.0, 85.0),
    "CRITICAL": (85.0, 100.0)
}
