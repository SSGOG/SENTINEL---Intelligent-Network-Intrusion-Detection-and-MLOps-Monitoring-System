# -*- coding: utf-8 -*-
"""Train and log the SENTINEL XGBoost classifier using the imputed feature arrays."""

import json
import logging
import os
import subprocess
from pathlib import Path

import joblib
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
import mlflow
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, confusion_matrix, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths – keep them relative to repository root
DATA_DIR = Path("data/processed")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    X_train = np.load(DATA_DIR / "X_train.npy")
    y_train = np.load(DATA_DIR / "y_train.npy")
    X_val = np.load(DATA_DIR / "X_val.npy")
    y_val = np.load(DATA_DIR / "y_val.npy")
    return X_train, y_train, X_val, y_val

def main():
    logger.info("Loading data...")
    X_train, y_train, X_val, y_val = load_data()
    logger.info("Training XGBoost classifier on median-imputed raw features...")
    from xgboost import XGBClassifier
    # Compute class imbalance weight
    neg, pos = np.bincount(y_train)
    scale_pos_weight = (neg / pos) if pos > 0 else 1.0
    model = XGBClassifier(
        n_estimators=300,
        learning_rate=0.1,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='binary:logistic',
        eval_metric='logloss',
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
    )
    logger.info("Fitting model...")
    model.fit(X_train, y_train)
    # Validation metrics
    y_val_pred = model.predict(X_val)
    val_acc = accuracy_score(y_val, y_val_pred)
    val_f1 = f1_score(y_val, y_val_pred)
    # For XGB, predict_proba returns probability of class 1
    val_auc = roc_auc_score(y_val, model.predict_proba(X_val)[:, 1])
    val_precision = precision_score(y_val, y_val_pred)
    val_recall = recall_score(y_val, y_val_pred)
    cm = confusion_matrix(y_val, y_val_pred)
    logger.info(f"Validation ACC={val_acc:.4f}, F1={val_f1:.4f}, AUC={val_auc:.4f}, Precision={val_precision:.4f}, Recall={val_recall:.4f}")
    logger.info(f"Confusion matrix:\n{cm}")
    
    mlflow.set_tracking_uri("mlruns")
    # Ensure the experiment exists; create if needed
    try:
        mlflow.set_experiment("SENTINEL")
    except Exception:
        mlflow.create_experiment("SENTINEL")
        mlflow.set_experiment("SENTINEL")
    with mlflow.start_run(run_name="xgboost-baseline") as run:
        mlflow.log_param("model", "XGBClassifier")
        mlflow.log_param("n_estimators", 300)
        mlflow.log_param("learning_rate", 0.1)
        mlflow.log_param("max_depth", 6)
        mlflow.log_param("scale_pos_weight", scale_pos_weight)
        mlflow.log_param("random_state", 42)
        mlflow.log_metric("val_accuracy", val_acc)
        mlflow.log_metric("val_f1", val_f1)
        mlflow.log_metric("val_auc", val_auc)
        mlflow.log_metric("val_precision", val_precision)
        mlflow.log_metric("val_recall", val_recall)
        cm_path = MODELS_DIR / "val_confusion_matrix.json"
        with open(cm_path, "w", encoding="utf-8") as f:
            json.dump({"tn": int(cm[0,0]), "fp": int(cm[0,1]), "fn": int(cm[1,0]), "tp": int(cm[1,1])}, f, indent=2)
        mlflow.log_artifact(str(cm_path), "metrics")
        # Save model artifact
        model_path = MODELS_DIR / "champion_model.joblib"
        joblib.dump(model, model_path)
        mlflow.log_artifact(str(model_path), "model")
        # Retain the historical scaler artifact for compatibility; the XGBoost
        # model is trained and served with the raw, already-imputed features.
        scaler = StandardScaler()
        scaler.fit(X_train)
        preprocessor_path = MODELS_DIR / "preprocessor_bundle.joblib"
        joblib.dump(scaler, preprocessor_path)
        mlflow.log_artifact(str(preprocessor_path), "model")
        # Record the Git revision for provenance.
        try:
            commit_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            mlflow.log_param("git_commit", commit_sha)
        except (OSError, subprocess.CalledProcessError) as e:
            logger.warning("Could not capture Git revision: %s", e)
            commit_sha = None
        manifest_path = Path("reports/metrics/model_selection_manifest.json")
        manifest = {
            "model_name": type(model).__name__,
            "model_path": str(model_path),
            "preprocessor_path": str(preprocessor_path),
            "inference_preprocessing": "none; raw median-imputed feature values",
            "feature_count": int(X_train.shape[1]),
            "validation_accuracy": val_acc,
            "validation_f1": val_f1,
            "validation_precision": val_precision,
            "validation_recall": val_recall,
            "validation_auc": val_auc,
            "git_commit": commit_sha,
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        mlflow.log_artifact(str(manifest_path), "metrics")
    logger.info(f"MLflow run completed – ID: {run.info.run_id}")
    logger.info("Model saved to 'models/' directory.")

if __name__ == "__main__":
    main()
