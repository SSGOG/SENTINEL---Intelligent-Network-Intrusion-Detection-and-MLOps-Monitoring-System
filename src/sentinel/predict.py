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
        self.feature_names: List[str] = []
        self._load_artifacts()

    def _load_artifacts(self):
        model_path = MODELS_DIR / "champion_model.joblib"
        schema_path = PROCESSED_DIR / "feature_schema.json"
        if model_path.exists() and schema_path.exists():
            self.model        = joblib.load(model_path)
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            self.feature_names = [
                str(name).strip()
                for name in schema.get("feature_order", schema.get("feature_names", []))
            ]
            expected = getattr(self.model, "n_features_in_", len(self.feature_names))
            if not self.feature_names or len(self.feature_names) != expected:
                raise ValueError(
                    "Model feature contract mismatch: "
                    f"schema has {len(self.feature_names)} features, model expects {expected}"
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def is_ready(self) -> bool:
        return self.model is not None and bool(self.feature_names)

    # ------------------------------------------------------------------
    # Single-flow inference
    # ------------------------------------------------------------------
    def predict_flow(self, flow_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Classify one flow using the model's canonical raw-feature order."""
        if not self.is_ready():
            return {"error": "Model engine not ready"}

        vec: List[float] = []
        for f in self.feature_names:
            val = flow_dict.get(f, flow_dict.get(f.strip(), 0.0))
            try:
                val_float = float(val)
            except (ValueError, TypeError):
                val_float = 0.0
            vec.append(val_float)

        arr = np.array([vec], dtype=float)

        pred = int(self.model.predict(arr)[0])
        prob = (
            float(self.model.predict_proba(arr)[0][1])
            if hasattr(self.model, "predict_proba")
            else (1.0 if pred == 1 else 0.0)
        )

        return {
            "prediction": "MALICIOUS" if pred == 1 else "BENIGN",
            "is_malicious": pred,
            "probability": prob,
            "confidence": prob if pred == 1 else (1.0 - prob),
        }

    # ------------------------------------------------------------------
    # Batch inference
    # ------------------------------------------------------------------
    def predict_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Batch predict pandas DataFrame with schema normalization."""
        if not self.is_ready():
            raise RuntimeError("Model engine not ready")

        cleaned_df = df.copy()
        cleaned_df.columns = [c.strip() for c in cleaned_df.columns]

        matrix = []
        for f in self.feature_names:
            if f in cleaned_df.columns:
                series = pd.to_numeric(cleaned_df[f], errors="coerce").fillna(0.0)
                matrix.append(series.values)
            else:
                matrix.append(np.zeros(len(cleaned_df)))

        X_raw = np.column_stack(matrix).astype(float, copy=False)

        preds = self.model.predict(X_raw)
        probs = (
            self.model.predict_proba(X_raw)[:, 1]
            if hasattr(self.model, "predict_proba")
            else preds
        )

        res_df = df.copy()
        res_df["SENTINEL_PREDICTION"] = ["MALICIOUS" if p == 1 else "BENIGN" for p in preds]
        res_df["MALICIOUS_PROBABILITY"] = [round(float(p), 4) for p in probs]

        stats = {
            "total": len(preds),
            "malicious": int((preds == 1).sum()),
            "benign": int((preds == 0).sum()),
        }
        return res_df, stats


engine = SentinelInferenceEngine()
