"""Unit and integration tests for FastAPI endpoints."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from src.sentinel.api import app

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
    assert "HistGradientBoostingClassifier" in data["model_architecture"]
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
