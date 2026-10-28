# src/sentinel/data_split.py
"""
Data split utility for SENTINEL.
Splits the preprocessed feature matrix into train, validation, and test sets.
Outputs:
  - data/processed/train.npy
  - data/processed/val.npy
  - data/processed/test.npy
  - data/processed/splits.json (metadata about split sizes and random seed)
"""
import numpy as np
import json
import os
from sklearn.model_selection import train_test_split

def main():
    # Load feature matrix and labels (assume they are stored together as a tuple in a .npz file
    matrix_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "feature_matrix.npy"))
    labels_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "labels.npy"))
    X = np.load(matrix_path)
    y = np.load(labels_path)

    # reproducible split
    seed = 42
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.4, random_state=seed, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=seed, stratify=y_temp
    )

    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
    np.save(os.path.join(out_dir, "train.npy"), X_train)
    np.save(os.path.join(out_dir, "val.npy"), X_val)
    np.save(os.path.join(out_dir, "test.npy"), X_test)
    np.save(os.path.join(out_dir, "train_labels.npy"), y_train)
    np.save(os.path.join(out_dir, "val_labels.npy"), y_val)
    np.save(os.path.join(out_dir, "test_labels.npy"), y_test)

    meta = {
        "seed": seed,
        "train_samples": int(X_train.shape[0]),
        "val_samples": int(X_val.shape[0]),
        "test_samples": int(X_test.shape[0]),
    }
    with open(os.path.join(out_dir, "splits.json"), "w") as f:
        json.dump(meta, f, indent=2)

if __name__ == "__main__":
    main()
