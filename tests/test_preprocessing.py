"""Unit tests for leakage-free preprocessing pipeline and feature schema."""

from pathlib import Path
import json
import joblib
import numpy as np
import pytest

PREPROCESSOR_PATH = Path("models/preprocessor_bundle.joblib")
SCHEMA_PATH = Path("data/processed/feature_schema.json")
MODEL_PATH = Path("models/champion_model.joblib")
TRAIN_X = Path("data/processed/X_train.npy")
VAL_X = Path("data/processed/X_val.npy")
TEST_X = Path("data/processed/X_test.npy")

def test_pipeline_assets_exist():
    assert PREPROCESSOR_PATH.exists(), "Fitted preprocessor artifact must exist."
    assert SCHEMA_PATH.exists(), "Feature schema must exist."
    assert TRAIN_X.exists() and VAL_X.exists() and TEST_X.exists()

def test_preprocessor_structure():
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    model = joblib.load(MODEL_PATH)

    assert schema["feature_count"] == len(schema["feature_order"])
    assert model.n_features_in_ == schema["feature_count"]
    if isinstance(preprocessor, dict):
        assert len(preprocessor["feature_names"]) == schema["feature_count"]
    else:
        assert preprocessor.n_features_in_ == schema["feature_count"]

def test_no_nan_or_inf_in_processed_splits():
    X_tr = np.load(TRAIN_X)
    X_va = np.load(VAL_X)
    X_te = np.load(TEST_X)
    
    for split_name, arr in [("Train", X_tr), ("Val", X_va), ("Test", X_te)]:
        assert not np.isnan(arr).any(), f"NaN found in {split_name} split!"
        assert not np.isinf(arr).any(), f"Inf found in {split_name} split!"
        assert arr.ndim == 2
