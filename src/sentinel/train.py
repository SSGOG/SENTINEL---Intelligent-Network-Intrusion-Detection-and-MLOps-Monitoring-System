# -*- coding: utf-8 -*-
"""Training script for SENTINEL.

- Loads preprocessed NumPy arrays from ``data/processed``.
- Fits a ``HistGradientBoostingClassifier`` (binary benign/malicious).
- Uses a ``StandardScaler`` as a lightweight preprocessing wrapper (fit on training data only).
- Logs parameters, metrics, and artifacts to a local MLflow tracking server.
- Saves the trained model (joblib) and the fitted scaler to ``models/``.

The script is intended to be executed via DVC stage ``train``.
"""

import json
import logging
import os
from pathlib import Path

import joblib
import os
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
import mlflow
import os
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
import mlflow.sklearn
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, confusion_matrix
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths – keep them relative to repository root
DATA_DIR = Path("data/processed")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)
SCHEMA_PATH = DATA_DIR / "feature_schema.json"

def load_data():
    X_train = np.load(DATA_DIR / "X_train.npy")
    y_train = np.load(DATA_DIR / "y_train.npy")
    X_val = np.load(DATA_DIR / "X_val.npy")
    y_val = np.load(DATA_DIR / "y_val.npy")
    X_test = np.load(DATA_DIR / "X_test.npy")
    y_test = np.load(DATA_DIR / "y_test.npy")
    # Alias for compatibility with older variable names
    X_va = X_val
    y_va = y_val
    return X_train, y_train, X_val, y_val, X_test, y_test

def main():
    logger.info("Loading data...")
    X_train, y_train, X_va, y_va, X_test, y_test = load_data()
    # Data is already imputed and scaled by preprocess stage
    logger.info("Training XGBoost classifier on preprocessed data...")
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
    y_va_pred = model.predict(X_va)
    val_acc = accuracy_score(y_va, y_va_pred)
    val_f1 = f1_score(y_va, y_va_pred)
    # For XGB, predict_proba returns probability of class 1
    val_auc = roc_auc_score(y_va, model.predict_proba(X_va)[:, 1])
    cm = confusion_matrix(y_va, y_va_pred)
    logger.info(f"Validation ACC={val_acc:.4f}, F1={val_f1:.4f}, AUC={val_auc:.4f}")
    logger.info(f"Confusion matrix:\n{cm}")
    # Log to MLflow (local tracking dir "mlruns")
    mlflow.set_tracking_uri("mlruns")
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
        cm_path = MODELS_DIR / "val_confusion_matrix.json"
        with open(cm_path, "w", encoding="utf-8") as f:
            json.dump({"tn": int(cm[0,0]), "fp": int(cm[0,1]), "fn": int(cm[1,0]), "tp": int(cm[1,1])}, f, indent=2)
        mlflow.log_artifact(str(cm_path), "metrics")
        # Save model artifact
        model_path = MODELS_DIR / "champion_model.joblib"
        joblib.dump(model, model_path)
        mlflow.log_artifact(str(model_path), "model")
        # Ensure preprocessor bundle exists for provenance
        preprocessor_path = MODELS_DIR / "preprocessor_bundle.joblib"
        if not preprocessor_path.exists():
            raise FileNotFoundError(f"Preprocessor bundle not found at {preprocessor_path}")
        mlflow.log_artifact(str(preprocessor_path), "model")
        # Record git commit SHA and DVC revision for provenance
        try:
            commit_sha = os.popen("git rev-parse HEAD").read().strip()
            mlflow.log_param("git_commit", commit_sha)
        except Exception:
            commit_sha = None
        dvc_rev = os.popen("dvc rev-parse HEAD").read().strip()
        if dvc_rev:
            mlflow.log_param("dvc_rev", dvc_rev)
        manifest_path = Path("reports/metrics/model_selection_manifest.json")
        manifest = {
            "model_path": str(model_path),
            "preprocessor_path": str(preprocessor_path),
            "validation_accuracy": val_acc,
            "validation_f1": val_f1,
            "validation_auc": val_auc,
            "git_commit": commit_sha,
            "dvc_rev": dvc_rev if dvc_rev else None,
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        mlflow.log_artifact(str(manifest_path), "metrics")
    logger.info(f"MLflow run completed – ID: {run.info.run_id}")
    logger.info("Model saved to 'models/' directory.")
    logger.info("Loading data...")
    X_train, y_train, X_va, y_va, X_test, y_test = load_data()

    logger.info("Fitting StandardScaler on training data")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_va_scaled = scaler.transform(X_va)
    X_test_scaled = scaler.transform(X_test)

    # Model hyper‑parameters – use XGBoost for better performance on imbalanced data
    from xgboost import XGBClassifier
    # Calculate scale_pos_weight = (negative samples) / (positive samples)
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
    model = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, random_state=42)
    logger.info("Training HistGradientBoostingClassifier...")
    model.fit(X_train_scaled, y_train)

    # Validation metrics
    y_va_pred = model.predict(X_va_scaled)
    val_acc = accuracy_score(y_va, y_va_pred)
    val_f1 = f1_score(y_va, y_va_pred)
    val_auc = roc_auc_score(y_va, model.predict_proba(X_va_scaled)[:, 1])
    cm = confusion_matrix(y_va, y_va_pred)
    logger.info(f"Validation ACC={val_acc:.4f}, F1={val_f1:.4f}, AUC={val_auc:.4f}")
    logger.info(f"Confusion matrix:\n{cm}")

    # Log to MLflow (local tracking dir "mlruns")
    # Set MLflow tracking to a relative local directory (Windows-friendly)
    mlflow.set_tracking_uri("mlruns")
    mlflow.set_experiment("SENTINEL")
    with mlflow.start_run(run_name="histgradientboosting-baseline") as run:
        # Parameters
        mlflow.log_param("model", "HistGradientBoostingClassifier")
        mlflow.log_param("max_iter", 200)
        mlflow.log_param("learning_rate", 0.1)
        mlflow.log_param("random_state", 42)
        # Metrics
        mlflow.log_metric("val_accuracy", val_acc)
        mlflow.log_metric("val_f1", val_f1)
        mlflow.log_metric("val_auc", val_auc)
        # Confusion matrix as JSON artifact
        cm_path = MODELS_DIR / "val_confusion_matrix.json"
        with open(cm_path, "w", encoding="utf-8") as f:
            json.dump({"tn": int(cm[0,0]), "fp": int(cm[0,1]), "fn": int(cm[1,0]), "tp": int(cm[1,1])}, f, indent=2)
        mlflow.log_artifact(str(cm_path), "metrics")
        # Save model and scaler as artifacts
        model_path = MODELS_DIR / "champion_model.joblib"
        preprocessor_path = MODELS_DIR / "preprocessor_bundle.joblib"
    # Save only the bundle (already saved by preprocess stage). No need to duplicate.
    # Ensure the bundle exists for provenance.
    if not preprocessor_path.exists():
        raise FileNotFoundError(f"Preprocessor bundle not found at {preprocessor_path}")
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        mlflow.log_artifact(str(model_path), "model")
        mlflow.log_artifact(str(scaler_path), "model")
        # Record git commit SHA and DVC revision for provenance
        try:
            commit_sha = os.popen("git rev-parse HEAD").read().strip()
            mlflow.log_param("git_commit", commit_sha)
        except Exception:
            commit_sha = None
        # DVC revision (if any)
        dvc_rev = os.popen("dvc rev-parse HEAD").read().strip()
        if dvc_rev:
            mlflow.log_param("dvc_rev", dvc_rev)
        # Create a model selection manifest JSON for DVC tracking
        manifest_path = Path("reports/metrics/model_selection_manifest.json")
        manifest = {
            "model_path": str(model_path),
            "scaler_path": str(scaler_path),
            "validation_accuracy": val_acc,
            "validation_f1": val_f1,
            "validation_auc": val_auc,
            "git_commit": commit_sha,
            "dvc_rev": dvc_rev if dvc_rev else None,
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        mlflow.log_artifact(str(manifest_path), "metrics")
    logger.info(f"MLflow run completed – ID: {run.info.run_id}")
    logger.info("Model and scaler saved to 'models/' directory.")

if __name__ == "__main__":
    main()
