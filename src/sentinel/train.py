"""Model training, baseline comparison, and MLflow experiment tracking for SENTINEL."""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict
import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports/metrics")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

EXPERIMENT_NAME = "SENTINEL_Network_Intrusion_Detection"
mlflow.set_experiment(EXPERIMENT_NAME)

def get_git_commit_sha() -> str:
    """Retrieve current Git commit SHA for provenance tracking."""
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        return sha
    except Exception:
        return "UNKNOWN_GIT_SHA"

def train_and_evaluate_model(
    model_name: str,
    estimator: Any,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    git_sha: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """Train estimator, evaluate class-sensitive metrics, and log complete run to MLflow."""
    logger.info(f"--- Training {model_name} ---")
    
    with mlflow.start_run(run_name=model_name) as run:
        run_id = run.info.run_id
        
        # Log parameters & Provenance
        mlflow.log_params(params)
        mlflow.log_param("model_name", model_name)
        mlflow.set_tag("git_commit_sha", git_sha)
        mlflow.set_tag("dataset_version", "CIC-IDS2017-8Files-Stratified-v1.0")
        mlflow.set_tag("author", "MLOps Engineer")
        
        # Fit estimator
        estimator.fit(X_train, y_train)
        
        # Predictions
        y_pred = estimator.predict(X_val)
        y_prob = None
        if hasattr(estimator, "predict_proba"):
            y_prob = estimator.predict_proba(X_val)[:, 1]
        
        # Metrics computation
        acc = float(accuracy_score(y_val, y_pred))
        prec = float(precision_score(y_val, y_pred, zero_division=0))
        rec = float(recall_score(y_val, y_pred, zero_division=0))
        f1 = float(f1_score(y_val, y_pred, zero_division=0))
        macro_f1 = float(f1_score(y_val, y_pred, average="macro", zero_division=0))
        
        auc = 0.5
        if y_prob is not None:
            try:
                auc = float(roc_auc_score(y_val, y_prob))
            except Exception:
                auc = 0.5

        cm = confusion_matrix(y_val, y_pred).tolist()
        class_rep = classification_report(y_val, y_pred, output_dict=True, zero_division=0)
        
        # Log metrics to MLflow
        mlflow.log_metric("val_accuracy", acc)
        mlflow.log_metric("val_precision", prec)
        mlflow.log_metric("val_recall", rec)
        mlflow.log_metric("val_f1_score", f1)
        mlflow.log_metric("val_macro_f1", macro_f1)
        mlflow.log_metric("val_roc_auc", auc)
        
        # Save evaluation artifacts locally & to MLflow
        eval_artifact = {
            "model_name": model_name,
            "run_id": run_id,
            "git_commit_sha": git_sha,
            "metrics": {
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1_score": f1,
                "macro_f1": macro_f1,
                "roc_auc": auc
            },
            "confusion_matrix": cm,
            "classification_report": class_rep
        }
        
        artifact_path = REPORTS_DIR / f"{model_name.lower().replace(' ', '_')}_eval.json"
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(eval_artifact, f, indent=2)
            
        mlflow.log_artifact(str(artifact_path))
        
        # Log model artifact with trusted types for modern scikit-learn tree predictors
        try:
            mlflow.sklearn.log_model(
                estimator, 
                name=model_name.lower().replace(" ", "_"),
                skops_trusted_types=["sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor"]
            )
        except Exception:
            # Fallback to standard joblib logging if skops throws restriction
            model_joblib_path = REPORTS_DIR / f"{model_name.lower().replace(' ', '_')}.joblib"
            joblib.dump(estimator, model_joblib_path)
            mlflow.log_artifact(str(model_joblib_path))
        
        logger.info(
            f"Finished {model_name} [Run ID: {run_id}] -> Acc: {acc:.4f}, Prec: {prec:.4f}, Rec: {rec:.4f}, F1: {f1:.4f}, Macro-F1: {macro_f1:.4f}"
        )
        return eval_artifact

def run_experiment_suite() -> Dict[str, Any]:
    """Execute comparative evaluation between Dummy Baseline, Logistic Regression, and HistGradientBoosting."""
    git_sha = get_git_commit_sha()
    
    # Load processed splits
    X_train = np.load(PROCESSED_DIR / "X_train.npy")
    y_train = np.load(PROCESSED_DIR / "y_train.npy")
    X_val = np.load(PROCESSED_DIR / "X_val.npy")
    y_val = np.load(PROCESSED_DIR / "y_val.npy")
    
    results = {}
    
    # 1. Dummy Baseline
    dummy_params = {"strategy": "most_frequent"}
    dummy = DummyClassifier(**dummy_params)
    results["Dummy Baseline"] = train_and_evaluate_model(
        "Dummy Baseline", dummy, X_train, y_train, X_val, y_val, git_sha, dummy_params
    )
    
    # 2. Logistic Regression (Linear Interpretable Baseline)
    lr_params = {"max_iter": 500, "random_state": 42, "class_weight": "balanced"}
    lr = LogisticRegression(**lr_params)
    results["Logistic Regression"] = train_and_evaluate_model(
        "Logistic Regression", lr, X_train, y_train, X_val, y_val, git_sha, lr_params
    )
    
    # 3. High-Performance Candidate: HistGradientBoosting (Fast, robust to tabular features, native NaN handling)
    hgb_params = {"max_iter": 100, "random_state": 42, "learning_rate": 0.1, "class_weight": "balanced"}
    hgb = HistGradientBoostingClassifier(**hgb_params)
    results["HistGradientBoosting"] = train_and_evaluate_model(
        "HistGradientBoosting", hgb, X_train, y_train, X_val, y_val, git_sha, hgb_params
    )
    
    # Model Selection Gate: Select highest validation Macro-F1
    best_model_name = max(results.keys(), key=lambda k: results[k]["metrics"]["macro_f1"])
    best_result = results[best_model_name]
    logger.info(f"🏆 Best Model Selected by Selection Gate: {best_model_name} (Macro-F1: {best_result['metrics']['macro_f1']:.4f})")
    
    # Persist the chosen model locally for production bundle
    if best_model_name == "HistGradientBoosting":
        chosen_estimator = hgb
    elif best_model_name == "Logistic Regression":
        chosen_estimator = lr
    else:
        chosen_estimator = dummy
        
    joblib.dump(chosen_estimator, MODELS_DIR / "champion_model.joblib")
    
    # Save Model Selection Decision Manifest
    selection_manifest = {
        "selected_model": best_model_name,
        "run_id": best_result["run_id"],
        "git_commit_sha": git_sha,
        "selection_criteria": "Max validation Macro-F1 with Class-Sensitive Penalization",
        "selected_metrics": best_result["metrics"],
        "all_candidate_metrics": {k: v["metrics"] for k, v in results.items()}
    }
    with open(REPORTS_DIR / "model_selection_manifest.json", "w", encoding="utf-8") as f:
        json.dump(selection_manifest, f, indent=2)
        
    return results

if __name__ == "__main__":
    run_experiment_suite()
