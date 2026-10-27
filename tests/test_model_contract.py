"""Unit tests for model contract, evaluation outputs, and SHAP artifacts."""

from pathlib import Path
import json
import joblib
import pytest

CHAMPION_PATH = Path("models/champion_model.joblib")
EVAL_PATH = Path("reports/metrics/test_holdout_evaluation.json")
SHAP_PATH = Path("reports/figures/shap_summary.json")
SELECTION_PATH = Path("reports/metrics/model_selection_manifest.json")

def test_champion_model_contract():
    assert CHAMPION_PATH.exists(), "Champion model artifact must be persisted."
    model = joblib.load(CHAMPION_PATH)
    assert hasattr(model, "predict"), "Model must implement predict()"
    assert hasattr(model, "predict_proba"), "Model must implement predict_proba()"

def test_evaluation_metrics_thresholds():
    assert EVAL_PATH.exists(), "Evaluation manifest must exist."
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    
    assert metrics["accuracy"] > 0.95, f"Expected accuracy > 95%, got {metrics['accuracy']}"
    assert metrics["macro_f1"] > 0.90, f"Expected Macro-F1 > 90%, got {metrics['macro_f1']}"
    assert metrics["precision"] > 0.90
    assert metrics["recall"] > 0.90

def test_shap_explanations_contract():
    assert SHAP_PATH.exists(), "SHAP explanation summary must exist."
    with open(SHAP_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["top_predictive_features"]) >= 10
    assert "Init_Win_bytes_forward" in [f["feature"] for f in data["top_predictive_features"]]
