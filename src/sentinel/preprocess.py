# Preprocessing pipeline for CIC-IDS2017 CSVs
"""
This script consumes the audited dataset (validated by data_validation.py) and produces
- NumPy feature matrices for train / validation / test splits
- A JSON schema describing the feature columns (type, original name)
All steps are deterministic and logged. Missing values are imputed with the median.
Non‑numeric columns (e.g., IP addresses) are dropped for the baseline model.
The target label is binarised: BENIGN → 0, any other attack → 1.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
RAW_DIR = Path("MachineLearningCSV/MachineLearningCVE")
MANIFEST_PATH = Path("reports/data_quality/dataset_manifest.json")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_RATIO = 0.8
VAL_RATIO = 0.1  # of total (so test also 0.1)
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def load_all_csvs() -> pd.DataFrame:
    """Read all CSV files in RAW_DIR, concatenate them, and return a single DataFrame.
    The function uses a modest chunksize to keep memory usage reasonable.
    """
    csv_paths = sorted(list(RAW_DIR.glob("*.csv")))
    logger.info(f"Loading {len(csv_paths)} CSV files from {RAW_DIR}")
    dfs: List[pd.DataFrame] = []
    for path in csv_paths:
        logger.info(f"Reading {path.name}")
        # Use low_memory=False to ensure proper dtype inference.
        df = pd.read_csv(path, low_memory=False, encoding="cp1252")
        dfs.append(df)
    full = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined dataframe shape: {full.shape}")
    return full

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Drop non‑numeric columns, standardise the label column, and impute missing values."""
    # Identify label column (case‑insensitive)
    label_candidates = [c for c in df.columns if c.strip().lower() == "label"]
    if not label_candidates:
        raise ValueError("No column named 'Label' found in dataset")
    label_col = label_candidates[0]
    logger.info(f"Using column '{label_col}' as target label")

    # Binarise label: BENIGN → 0, everything else → 1
    df[label_col] = df[label_col].astype(str).str.strip()
    df["target"] = (df[label_col] != "BENIGN").astype(int)
    df = df.drop(columns=[label_col])

    # Keep only numeric columns (int, float) for the baseline model
    numeric_df = df.select_dtypes(include=["number"]).copy()
    logger.info(f"Numeric feature count after dropping non‑numeric columns: {numeric_df.shape[1]}")

    # Impute missing numeric values with median
    for col in numeric_df.columns:
        if numeric_df[col].isna().any():
            median = numeric_df[col].median()
            numeric_df[col].fillna(median, inplace=True)
            logger.info(f"Imputed missing values in column '{col}' with median={median}")

    # Ensure no infinite values remain
    numeric_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    if numeric_df.isna().any().any():
        # Should not happen after median imputation, but safeguard
        numeric_df = numeric_df.fillna(0)
        logger.warning("Remaining NaNs after imputation; filled with 0")

    return numeric_df

def split_and_save(features: pd.DataFrame, targets: pd.Series) -> None:
    """Perform train/val/test split and save NumPy arrays to OUT_DIR."""
    X_temp, X_test, y_temp, y_test = train_test_split(
        features,
        targets,
        test_size=1 - (TRAIN_RATIO + VAL_RATIO),
        random_state=RANDOM_STATE,
        stratify=targets,
    )
    # Now split the remaining temp into train and val
    val_frac_of_temp = VAL_RATIO / (TRAIN_RATIO + VAL_RATIO)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp,
        y_temp,
        test_size=val_frac_of_temp,
        random_state=RANDOM_STATE,
        stratify=y_temp,
    )

    logger.info(f"Split sizes -> train: {X_train.shape[0]}, val: {X_val.shape[0]}, test: {X_test.shape[0]}")

    # Save as .npy (features only) and keep targets alongside for downstream evaluation
    np.save(OUT_DIR / "X_train.npy", X_train.values)
    np.save(OUT_DIR / "y_train.npy", y_train.values)
    np.save(OUT_DIR / "X_val.npy", X_val.values)
    np.save(OUT_DIR / "y_val.npy", y_val.values)
    np.save(OUT_DIR / "X_test.npy", X_test.values)
    np.save(OUT_DIR / "y_test.npy", y_test.values)

    # Also write a simple JSON schema for downstream consumers
    schema = {
        "feature_names": list(X_train.columns),
        "feature_order": list(X_train.columns),  # alias for API compatibility
        "feature_count": X_train.shape[1],
        "target_name": "target",
        "description": "Baseline numeric features from CIC-IDS2017, binarised label",
    }
    with open(OUT_DIR / "feature_schema.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    logger.info(f"Saved feature schema to {OUT_DIR / 'feature_schema.json'}")

def main() -> None:
    # Verify that the data validation manifest exists (simple sanity check)
    if not MANIFEST_PATH.exists():
        logger.error(f"Dataset manifest not found at {MANIFEST_PATH}. Run data_validation first.")
        return
    df = load_all_csvs()
    # Preserve the target separately
    clean_df = clean_dataframe(df)
    # The target column created in clean_dataframe is named 'target'
    y = clean_df.pop("target")
    X = clean_df
    split_and_save(X, y)
    logger.info("Preprocessing completed successfully")

if __name__ == "__main__":
    main()
