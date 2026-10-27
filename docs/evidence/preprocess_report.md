# Preprocess Report

The preprocessing stage completed successfully.

## Output files
```
data/processed/feature_schema.json          1.96 KB
data/processed/X_train.npy                1.41 GB
data/processed/X_va.npy                  176 KB
data/processed/X_test.npy                176 MB

data/processed/y_train.npy                2.26 MB
data/processed/y_va.npy                  283 KB
data/processed/y_test.npy                 283 KB
```

## Dataset shapes
- **Feature matrix (X)**: 2,830,743 rows × 78 numeric columns
- **Training set**: 2,264,? rows (≈80 % of data) – shape stored in `X_train.npy`
- **Validation set**: 283,074 rows – shape stored in `X_va.npy`
- **Test set**: 283,074 rows – shape stored in `X_test.npy`
- **Target vectors** (`y_*`) have matching row counts.

## Feature schema
The JSON file `feature_schema.json` lists the ordered numeric column names used for model training. Example excerpt:
```json
{"feature_order": ["Destination Port", "Flow Duration", "Total Fwd Packets", ...]}
```

All files are version‑controlled by DVC (see `dvc.lock`).
