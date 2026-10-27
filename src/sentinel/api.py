"""FastAPI inference microservice and prediction engine for SENTINEL."""

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = Path("models")
PROCESSED_DIR = Path("data/processed")

app = FastAPI(
    title="SENTINEL Intrusion Detection API",
    description="Production-ready REST microservice for real-time network flow threat classification.",
    version="1.0.0"
)

# Load Champion Model and Preprocessor Bundle
champion_model = None
preprocessor = None
feature_names = []

def load_serving_assets():
    """Load model, preprocessor bundle, and feature schema.
    The preprocessor bundle is a dict containing:
      - "imputer": a fitted SimpleImputer or similar
      - "scaler": a fitted StandardScaler
      - "feature_names": list of feature names in order
    """
    global champion_model, preprocessor, feature_names
    model_path = MODELS_DIR / "champion_model.joblib"
    bundle_path = MODELS_DIR / "preprocessor_bundle.joblib"
    schema_path = PROCESSED_DIR / "feature_schema.json"
    if model_path.exists() and bundle_path.exists() and schema_path.exists():
        champion_model = joblib.load(model_path)
        preprocessor = joblib.load(bundle_path)  # dict with keys
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        feature_names = schema.get("feature_order", [])
        logger.info(f"Loaded champion model and {len(feature_names)} features.")
    else:
        logger.warning("Model, preprocessor bundle, or schema not found.")

    
load_serving_assets()

class SingleFlowRequest(BaseModel):
    features: Dict[str, float] = Field(..., description="Map of network flow feature names to numeric values")

class BatchFlowRequest(BaseModel):
    flows: List[Dict[str, float]] = Field(..., description="List of flow feature dictionaries")

class PredictionResponse(BaseModel):
    request_id: str
    prediction: str
    is_malicious: int
    malicious_probability: float
    model_version: str

class BatchPredictionResponse(BaseModel):
    request_id: str
    total_processed: int
    malicious_count: int
    benign_count: int
    predictions: List[PredictionResponse]

@app.get("/health")
def health_check():
    """Service liveness and readiness probe."""
    return {
        "status": "HEALTHY",
        "service": "SENTINEL Intrusion Detection API",
        "model_loaded": champion_model is not None,
        "features_configured": len(feature_names)
    }

@app.get("/model-info")
def model_info():
    """Model provenance and metadata inspection."""
    manifest_path = Path("reports/metrics/model_selection_manifest.json")
    selection_info = {}
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            selection_info = json.load(f)
            
    return {
        "model_architecture": "HistGradientBoostingClassifier",
        "task": "Binary Network Intrusion Classification (Benign vs Malicious)",
        "features_expected": len(feature_names),
        "target_mapping": {"0": "BENIGN", "1": "MALICIOUS"},
        "provenance": selection_info
    }

def format_and_impute_input(flow_dict: Dict[str, float]) -> np.ndarray:
    """Format single dict into ordered feature vector and run bundled preprocessor."""
    vector = []
    for f in feature_names:
        # Match case-insensitively or stripped
        val = flow_dict.get(f, flow_dict.get(f.strip(), 0.0))
        try:
            val_float = float(val)
        except (ValueError, TypeError):
            val_float = 0.0
        vector.append(val_float)
        
    vec_arr = np.array([vector])
    # Apply imputer then scaler
    imputed = preprocessor["imputer"].transform(vec_arr)
    scaled = preprocessor["scaler"].transform(imputed)
    return scaled

@app.post("/predict", response_model=PredictionResponse)
def predict_single(request: SingleFlowRequest):
    """Predict intrusion class for a single network flow."""
    if champion_model is None or preprocessor is None:
        raise HTTPException(status_code=503, detail="Model service not ready.")
    
    req_id = str(uuid.uuid4())
    X_scaled = format_and_impute_input(request.features)
    
    pred = int(champion_model.predict(X_scaled)[0])
    prob = float(champion_model.predict_proba(X_scaled)[0][1]) if hasattr(champion_model, "predict_proba") else (1.0 if pred == 1 else 0.0)
    
    label = "MALICIOUS" if pred == 1 else "BENIGN"
    
    return PredictionResponse(
        request_id=req_id,
        prediction=label,
        is_malicious=pred,
        malicious_probability=round(prob, 4),
        model_version="SENTINEL-v1.0"
    )

@app.post("/predict-batch", response_model=BatchPredictionResponse)
def predict_batch(request: BatchFlowRequest):
    """Predict intrusion class for a batch of flows (bounded to 1,000 for rate safety)."""
    if champion_model is None:
        raise HTTPException(status_code=503, detail="Model service not ready.")
    
    if len(request.flows) > 1000:
        raise HTTPException(status_code=400, detail="Batch size exceeded. Max allowable is 1,000 flows.")
        
    batch_preds = []
    mal_count = 0
    ben_count = 0
    
    for f in request.flows:
        res = predict_single(SingleFlowRequest(features=f))
        batch_preds.append(res)
        if res.is_malicious == 1:
            mal_count += 1
        else:
            ben_count += 1
            
    return BatchPredictionResponse(
        request_id=str(uuid.uuid4()),
        total_processed=len(batch_preds),
        malicious_count=mal_count,
        benign_count=ben_count,
        predictions=batch_preds
    )
