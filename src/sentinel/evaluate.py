"""Evaluate the champion model on the held-out test split."""

import json
import logging
from pathlib import Path
import joblib
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = Path("models")
PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports/metrics")
EVIDENCE_DIR = Path("docs/evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

def evaluate_on_test_holdout():
    model_path = MODELS_DIR / "champion_model.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"Champion model not found at {model_path}")
    model = joblib.load(model_path)
    
    X_test = np.load(PROCESSED_DIR / "X_test.npy")
    y_test = np.load(PROCESSED_DIR / "y_test.npy")
    
    logger.info(f"Evaluating champion model on held-out test split: {len(X_test):,} flows")

    expected_features = getattr(model, "n_features_in_", X_test.shape[1])
    if X_test.shape[1] != expected_features:
        raise ValueError(
            f"Test data has {X_test.shape[1]} features; model expects {expected_features}"
        )
    
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None
    
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    auc = float(roc_auc_score(y_test, y_prob)) if y_prob is not None else 0.5
    cm = confusion_matrix(y_test, y_pred).tolist()
    class_rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    
    results = {
        "model_name": type(model).__name__,
        "dataset_split": "Held-Out Test Split (10%)",
        "sample_count": int(len(X_test)),
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "macro_f1": macro_f1,
        "auc": auc,
        "confusion_matrix": cm,
        "classification_report": class_rep
    }
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    for report_path in (
        REPORTS_DIR / "test_holdout_evaluation.json",
        REPORTS_DIR / "histgradientboosting_eval.json",
    ):
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
    with open(EVIDENCE_DIR / "model_evaluation_summary.md", "w", encoding="utf-8") as f:
        f.write("# Champion Model Holdout Evaluation\n\n")
        f.write(
            f"Model: `{type(model).__name__}`. Evaluated on the held-out "
            f"10% test split ({len(X_test):,} flows) using the raw imputed feature "
            "values consumed during training and serving.\n\n"
        )
        f.write("| Accuracy | Precision | Recall | F1-Score | Macro-F1 | ROC-AUC |\n")
        f.write("|---:|---:|---:|---:|---:|---:|\n")
        f.write(
            f"| {acc*100:.3f}% | {prec*100:.3f}% | {rec*100:.3f}% | "
            f"{f1*100:.3f}% | {macro_f1*100:.3f}% | {auc*100:.3f}% |\n\n"
        )
        f.write("## Test Holdout Confusion Matrix\n\n")
        f.write(f"- True Negatives (Benign as Benign): {cm[0][0]:,}\n")
        f.write(f"- False Positives (Benign as Malicious): {cm[0][1]:,}\n")
        f.write(f"- False Negatives (Malicious as Benign): {cm[1][0]:,}\n")
        f.write(f"- True Positives (Malicious as Malicious): {cm[1][1]:,}\n\n")
        f.write("## Operational Error Rates\n")
        f.write(f"- **False Alarm Rate**: {cm[0][1] / (cm[0][0] + cm[0][1]) * 100:.3f}%\n")
        f.write(f"- **Missed Intrusion Rate (FN)**: {cm[1][0] / (cm[1][0] + cm[1][1]) * 100:.3f}%\n")
        f.write("Review false positives and false negatives as part of operational monitoring.\n")
        
    logger.info(f"Test holdout evaluation complete: Acc={acc:.4f}, Macro-F1={macro_f1:.4f}")
    return results

if __name__ == "__main__":
    evaluate_on_test_holdout()
