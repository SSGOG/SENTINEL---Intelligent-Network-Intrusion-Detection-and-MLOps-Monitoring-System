# -*- coding: utf-8 -*-
"""
Evaluation script that loads *all* model artifacts in the `models/` directory,
computes a full set of metrics on the validation set, and writes a consolidated
JSON report plus individual confusion‑matrix files.
"""
import json
import logging
import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    confusion_matrix,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Directories (relative to repo root)
DATA_DIR = Path("data/processed")
MODELS_DIR = Path("models")
OUT_DIR = Path("reports/metrics")
OUT_DIR.mkdir(parents=True, exist_ok=True)
CONF_MAT_DIR = OUT_DIR / "confusion_matrices"
CONF_MAT_DIR.mkdir(parents=True, exist_ok=True)

def load_validation_data():
    X_val = np.load(DATA_DIR / "X_val.npy")
    y_val = np.load(DATA_DIR / "y_val.npy")
    return X_val, y_val

def evaluate_model(model_path, X_val, y_val, name_suffix=""):
    model = joblib.load(model_path)
    # If the model expects scaled data, assume preprocessing already happened in the pipeline.
    y_pred = model.predict(X_val)
    # Some models (e.g., XGB) provide predict_proba; guard against missing method.
    try:
        y_proba = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_proba)
    except Exception:
        auc = None
    metrics = {
        "accuracy": accuracy_score(y_val, y_pred),
        "f1": f1_score(y_val, y_pred),
        "precision": precision_score(y_val, y_pred),
        "recall": recall_score(y_val, y_pred),
        "macro_f1": f1_score(y_val, y_pred, average="macro"),
    }
    if auc is not None:
        metrics["auc"] = auc
    # Confusion matrix as a dict for easier JSON serialisation
    cm = confusion_matrix(y_val, y_pred)
    cm_dict = {"tn": int(cm[0, 0]), "fp": int(cm[0, 1]), "fn": int(cm[1, 0]), "tp": int(cm[1, 1])}
    # Write individual confusion matrix file
    cm_path = CONF_MAT_DIR / f"{model_path.stem}{name_suffix}_confusion.json"
    with open(cm_path, "w", encoding="utf-8") as f:
        json.dump(cm_dict, f, indent=2)
    logger.info(f"Evaluated {model_path.name}: {metrics}")
    return metrics

def main():
    logger.info("Loading validation data...")
    X_val, y_val = load_validation_data()

    all_metrics = {}
    for model_file in MODELS_DIR.glob("*.joblib"):
        # Skip the preprocessor bundle – it is not a classifier
        if "preprocessor" in model_file.name:
            continue
        model_name = model_file.stem
        logger.info(f"Evaluating model {model_name}...")
        metrics = evaluate_model(model_file, X_val, y_val, name_suffix="")
        all_metrics[model_name] = metrics

    # Save consolidated JSON report
    out_path = OUT_DIR / "all_models_metrics.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)
    logger.info(f"All model metrics written to {out_path}")

if __name__ == "__main__":
    main()
