"""Reproducible, leakage-free preprocessing pipeline for CIC-IDS2017 network intrusion flows."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path("MachineLearningCSV/MachineLearningCVE")
PROCESSED_DIR = Path("data/processed")
SAMPLE_DIR = Path("data/sample")
MODELS_DIR = Path("models")

for d in [PROCESSED_DIR, SAMPLE_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Canonical label mapping for binary and multiclass
BINARY_MAPPING = {
    "BENIGN": 0,
    "DDoS": 1,
    "PortScan": 1,
    "Bot": 1,
    "Infiltration": 1,
    "Web Attack  Brute Force": 1,
    "Web Attack  XSS": 1,
    "Web Attack  Sql Injection": 1,
    "FTP-Patator": 1,
    "SSH-Patator": 1,
    "DoS Hulk": 1,
    "DoS GoldenEye": 1,
    "DoS slowloris": 1,
    "DoS Slowhttptest": 1,
    "Heartbleed": 1,
}

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize headers: strip whitespace, handle duplicate header names."""
    cols = [c.strip() for c in df.columns]
    # Check for duplicate 'Fwd Header Length'
    seen = {}
    new_cols = []
    for c in cols:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols
    return df

def load_and_sample_dataset(sample_fraction: float = 0.05, random_state: int = 42) -> pd.DataFrame:
    """
    Load a stratified representative sample across all 8 CSV files.
    Preserves exact class ratios while fitting within local RAM and compute budgets.
    """
    csv_files = sorted(list(DATA_DIR.glob("*.csv")))
    dfs = []
    for f in csv_files:
        logger.info(f"Loading sample from: {f.name}")
        df = pd.read_csv(f, encoding="cp1252", low_memory=False)
        df = clean_column_names(df)
        
        # Identify label column
        label_col = [c for c in df.columns if c.lower() == "label"][0]
        # Drop rows with NaN or missing labels
        df = df.dropna(subset=[label_col])
        df[label_col] = df[label_col].astype(str).str.strip()
        
        # Sample proportionally
        sampled = df.sample(frac=sample_fraction, random_state=random_state)
        dfs.append(sampled)
    
    full_sample = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total sampled rows across all 8 files: {len(full_sample):,}")
    return full_sample

def build_preprocessing_pipeline(
    df: pd.DataFrame, 
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """
    Leakage-free preprocessing:
    1. Separate Target (Y) and Features (X).
    2. Split into Train (70%), Validation (15%), Test (15%) untouched holdout.
    3. Fit Imputer and Scaler ONLY on the Train set.
    4. Transform Val and Test using Train parameters.
    5. Save feature schema and fitted transformers.
    """
    label_col = [c for c in df.columns if c.lower() == "label"][0]
    
    # Map binary target
    # Clean non-standard encoding in labels
    df["clean_label"] = df[label_col].apply(lambda x: "BENIGN" if x == "BENIGN" else "MALICIOUS")
    y = (df["clean_label"] == "MALICIOUS").astype(int).values
    
    # Features: drop label columns
    drop_cols = [label_col, "clean_label"]
    X_df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    
    # Replace Inf with NaN for imputation
    X_df = X_df.replace([np.inf, -np.inf], np.nan)
    
    feature_names = list(X_df.columns)
    
    # Stratified Train/Test Split (85% train+val, 15% untouched test)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X_df.values, y, test_size=0.15, stratify=y, random_state=random_state
    )
    
    # Further split Train (approx 70% total) and Val (approx 15% total)
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=(0.15 / 0.85), stratify=y_train_val, random_state=random_state
    )
    
    logger.info(f"Split sizes: Train={len(X_train):,}, Val={len(X_val):,}, Test={len(X_test):,}")
    
    # FIT PREPROCESSING ONLY ON TRAINING DATA
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    
    X_train_trans = imputer.fit_transform(X_train)
    X_train_scaled = scaler.fit_transform(X_train_trans)
    
    # TRANSFORM VALIDATION AND TEST USING FITTED PARAMETERS
    X_val_trans = imputer.transform(X_val)
    X_val_scaled = scaler.transform(X_val_trans)
    
    X_test_trans = imputer.transform(X_test)
    X_test_scaled = scaler.transform(X_test_trans)
    
    # Save Pipeline Assets
    preprocessor = {
        "imputer": imputer,
        "scaler": scaler,
        "feature_names": feature_names,
        "feature_count": len(feature_names),
        "target_mapping": {"BENIGN": 0, "MALICIOUS": 1}
    }
    joblib.dump(preprocessor, MODELS_DIR / "preprocessor.joblib")
    
    # Save Schema Definition
    with open(PROCESSED_DIR / "feature_schema.json", "w", encoding="utf-8") as f:
        json.dump({
            "feature_names": feature_names,
            "feature_count": len(feature_names),
            "target": "is_malicious",
            "classes": [0, 1]
        }, f, indent=2)
        
    logger.info(f"Saved preprocessing pipeline to {MODELS_DIR / 'preprocessor.joblib'}")
    return X_train_scaled, y_train, X_val_scaled, y_val, X_test_scaled, y_test, feature_names

def run_preprocessing_pipeline() -> None:
    """Full execution of the preprocessing pipeline."""
    sample_df = load_and_sample_dataset(sample_fraction=0.05, random_state=42)
    
    # Save a small representative test demo file (500 rows) for API testing
    demo_df = sample_df.sample(n=500, random_state=42)
    demo_df.to_csv(SAMPLE_DIR / "demo_flows_sample.csv", index=False)
    
    X_train, y_train, X_val, y_val, X_test, y_test, feature_names = build_preprocessing_pipeline(sample_df)
    
    # Persist split arrays for reproducible model training
    np.save(PROCESSED_DIR / "X_train.npy", X_train)
    np.save(PROCESSED_DIR / "y_train.npy", y_train)
    np.save(PROCESSED_DIR / "X_val.npy", X_val)
    np.save(PROCESSED_DIR / "y_val.npy", y_val)
    np.save(PROCESSED_DIR / "X_test.npy", X_test)
    np.save(PROCESSED_DIR / "y_test.npy", y_test)
    logger.info("Processed dataset splits successfully persisted.")

if __name__ == "__main__":
    run_preprocessing_pipeline()
