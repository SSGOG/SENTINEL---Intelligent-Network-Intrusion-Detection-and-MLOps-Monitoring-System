"""Shared inference and security evaluation service layer for SENTINEL."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd

MODELS_DIR = Path("models")
PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")

class SentinelInferenceEngine:
    """Thread-safe, decoupled inference client shared by FastAPI and Streamlit."""
    
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.feature_names = []
        self._load_artifacts()
        
    def _load_artifacts(self):
        model_path = MODELS_DIR / "champion_model.joblib"
        prep_path = MODELS_DIR / "preprocessor_bundle.joblib"
        if model_path.exists() and prep_path.exists():
            self.model = joblib.load(model_path)
            self.preprocessor = joblib.load(prep_path)
            self.feature_names = self.preprocessor.get("feature_names", [])

    def is_ready(self) -> bool:
        return self.model is not None and self.preprocessor is not None

    def predict_flow(self, flow_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Classify single network flow dictionary."""
        if not self.is_ready():
            return {"error": "Model engine not ready"}
        
        vec = []
        for f in self.feature_names:
            val = flow_dict.get(f, flow_dict.get(f.strip(), 0.0))
            try:
                val_float = float(val)
            except (ValueError, TypeError):
                val_float = 0.0
            vec.append(val_float)
            
        arr = np.array([vec])
        imputed = self.preprocessor["imputer"].transform(arr)
        scaled = self.preprocessor["scaler"].transform(imputed)
        
        pred = int(self.model.predict(scaled)[0])
        prob = float(self.model.predict_proba(scaled)[0][1]) if hasattr(self.model, "predict_proba") else (1.0 if pred == 1 else 0.0)
        
        return {
            "prediction": "MALICIOUS" if pred == 1 else "BENIGN",
            "is_malicious": pred,
            "probability": prob,
            "confidence": prob if pred == 1 else (1.0 - prob)
        }

    def predict_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Batch predict pandas DataFrame with schema normalization."""
        cleaned_df = df.copy()
        cleaned_df.columns = [c.strip() for c in cleaned_df.columns]
        
        # Build matrix
        matrix = []
        for f in self.feature_names:
            if f in cleaned_df.columns:
                series = pd.to_numeric(cleaned_df[f], errors="coerce").fillna(0.0)
                matrix.append(series.values)
            else:
                matrix.append(np.zeros(len(cleaned_df)))
                
        X_raw = np.column_stack(matrix)
        imputed = self.preprocessor["imputer"].transform(X_raw)
        scaled = self.preprocessor["scaler"].transform(imputed)
        
        preds = self.model.predict(scaled)
        probs = self.model.predict_proba(scaled)[:, 1] if hasattr(self.model, "predict_proba") else preds
        
        res_df = df.copy()
        res_df["SENTINEL_PREDICTION"] = ["MALICIOUS" if p == 1 else "BENIGN" for p in preds]
        res_df["MALICIOUS_PROBABILITY"] = [round(float(p), 4) for p in probs]
        
        stats = {
            "total": len(preds),
            "malicious": int((preds == 1).sum()),
            "benign": int((preds == 0).sum())
        }
        return res_df, stats

engine = SentinelInferenceEngine()
