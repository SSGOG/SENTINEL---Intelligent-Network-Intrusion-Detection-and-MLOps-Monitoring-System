"""Unit and integration tests for FastAPI endpoints."""

import json
import pandas as pd
from fastapi.testclient import TestClient
from src.sentinel.api import app, champion_model
from sentinel.predict import engine

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["model_loaded"] is True
    assert data["features_configured"] > 70

def test_model_info_endpoint():
    response = client.get("/model-info")
    assert response.status_code == 200
    data = response.json()
    assert data["model_architecture"] == type(champion_model).__name__
    assert "provenance" in data

def test_predict_single_flow():
    # Construct synthetic flow payload
    sample_payload = {
        "features": {
            "Destination Port": 80.0,
            "Flow Duration": 12000.0,
            "Total Fwd Packets": 5.0,
            "Total Backward Packets": 4.0,
            "Init_Win_bytes_forward": 29200.0
        }
    }
    response = client.post("/predict", json=sample_payload)
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["prediction"] in ["BENIGN", "MALICIOUS"]
    assert 0.0 <= data["malicious_probability"] <= 1.0
    assert data["model_version"] == "SENTINEL-v1.0"

def test_predict_batch_flows():
    batch_payload = {
        "flows": [
            {"Destination Port": 80.0, "Flow Duration": 5000.0},
            {"Destination Port": 443.0, "Flow Duration": 15000.0}
        ]
    }
    response = client.post("/predict-batch", json=batch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 2
    assert len(data["predictions"]) == 2

def test_serving_uses_raw_model_features():
    with open("data/processed/feature_schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)
    sample = pd.read_csv("data/sample/demo_flows_sample.csv", nrows=1, low_memory=False)
    normalized_sample = sample.rename(columns=lambda column: column.strip())
    ordered_features = [name.strip() for name in schema["feature_order"]]
    test_features = normalized_sample[ordered_features].to_numpy()
    expected_prediction = int(champion_model.predict(test_features)[0])
    payload = {
        "features": dict(zip(ordered_features, test_features[0].tolist()))
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json()["is_malicious"] == expected_prediction
    assert engine.predict_flow(payload["features"])["is_malicious"] == expected_prediction

def test_batch_csv_uses_canonical_feature_order():
    with open("data/processed/feature_schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)
    sample = pd.read_csv("data/sample/demo_flows_sample.csv", nrows=3, low_memory=False)
    normalized_sample = sample.rename(columns=lambda column: column.strip())
    ordered_features = [name.strip() for name in schema["feature_order"]]
    expected = champion_model.predict(normalized_sample[ordered_features].to_numpy())

    results, stats = engine.predict_dataframe(sample)

    actual = (results["SENTINEL_PREDICTION"] == "MALICIOUS").astype(int).to_numpy()
    assert actual.tolist() == expected.tolist()
    assert stats["total"] == len(sample)
