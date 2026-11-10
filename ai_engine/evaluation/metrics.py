"""
Cyber Raksha AI - Evaluation Metrics Utilities
Calculates Accuracy, Precision, Recall, F1, FPR, FNR, and ROC-AUC.
"""
from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    classification_report
)


def compute_binary_metrics(true_positives: int, false_positives: int, true_negatives: int, false_negatives: int) -> Dict[str, float]:
    """Computes basic binary evaluation metrics."""
    total = true_positives + false_positives + true_negatives + false_negatives
    if total == 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "accuracy": 0.0}
    prec = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    rec = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
    acc = (true_positives + true_negatives) / total
    return {"precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4), "accuracy": round(acc, 4)}


def evaluate_model_performance(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray = None
) -> Dict[str, Any]:
    """
    Computes a comprehensive suite of binary classification metrics.
    Label 1 = Phishing, Label 0 = Legitimate.
    """
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    # False Positive Rate: FP / (FP + TN)
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    # False Negative Rate: FN / (FN + TP) -- critical in cybersecurity!
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    roc_auc = None
    if y_prob is not None:
        try:
            roc_auc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            roc_auc = None

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else "N/A",
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        },
        "support": {
            "total_samples": len(y_true),
            "phishing_samples": int(np.sum(y_true == 1)),
            "legitimate_samples": int(np.sum(y_true == 0))
        }
    }
