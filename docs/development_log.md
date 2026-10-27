# SENTINEL Development Log

This document records chronological development milestones, git commit SHAs, executed commands, experimental results, and governance verifications for SENTINEL.

---

## [M1] Project Initialization & Directory Conventions
- **Date**: 2026-10-27
- **Objective**: Establish local-first repository, .gitignore for zero-budget data safety, directory structure, and DVC/MLflow initialization.
- **Commands Executed**:
  - `git init; git branch -M main`
  - `python -m dvc init`
  - `pip install dvc mlflow shap`
  - Directory scaffold: `src/sentinel`, `configs`, `tests`, `docs`, `reports`, `models`, `data`
- **Results**:
  - Python 3.13.5 environment detected with scikit-learn, XGBoost, pandas, FastAPI, Streamlit, MLflow 3.17.2, DVC 3.67.1, SHAP 0.52.0.
  - Raw 52 GB PCAPs and extracted CSV directories explicitly excluded in `.gitignore`.
- **Status**: Completed and Verified.

---

## [M3] Leakage-Free Preprocessing Pipeline & Feature Schema
- **Date**: 2026-10-27
- **Objective**: Implement train/val/test splitting before transform fitting, train SimpleImputer and StandardScaler strictly on training set, generate feature schema, and extract representative 500-flow demo sample.
- **Commands Executed**:
  - `python src/sentinel/preprocess.py`
  - `pytest tests/test_preprocessing.py -v`
- **Results**:
  - Sampled 141,536 stratified flow records across all 8 files.
  - Split counts: Train = 99,074, Validation = 21,231, Test = 21,231 (15% untouched holdout).
  - Saved fitted pipeline to `models/preprocessor.joblib`, schema to `data/processed/feature_schema.json`, and demo sample to `data/sample/demo_flows_sample.csv`.
  - Zero NaN or Inf values across all transformed splits.
  - All 3 unit tests passed.
- **Status**: Completed and Verified.


---

## [M2] Dataset Audit & Integrity Verification
- **Date**: 2026-10-27
- **Objective**: Independently audit all 8 CIC-IDS2017 `MachineLearningCSV` files, compute SHA-256 hashes, verify labels, duplicate columns, and investigate the historical Thursday WebAttacks/Infiltration issue.
- **Commands Executed**:
  - `python src/sentinel/data_validation.py`
  - `pytest tests/test_data_validation.py -v`
- **Results**:
  - Audited 2,830,743 total flow records across all 8 primary files.
  - Exactly 0 blank labels in the primary `MachineLearningCSV` archive.
  - Identified the exact flaw in the separate `GeneratedLabelledFlows` archive: exactly 288,602 blank rows concatenated into Thursday WebAttacks matching the row count of Infiltration.
  - Documented complete manifest in `reports/data_quality/dataset_manifest.json` and summary in `docs/evidence/data_audit_summary.md`.
  - All 3 automated validation tests passed.
- **Status**: Completed and Verified.

---

## [M3] Leakage-Free Preprocessing Pipeline & Feature Schema
- **Date**: 2026-10-27
- **Objective**: Implement train/val/test splitting before transform fitting, train SimpleImputer and StandardScaler strictly on training set, generate feature schema, and extract representative 500-flow demo sample.
- **Commands Executed**:
  - `python src/sentinel/preprocess.py`
  - `pytest tests/test_preprocessing.py -v`
- **Results**:
  - Sampled 141,536 stratified flow records across all 8 files.
  - Split counts: Train = 99,074, Validation = 21,231, Test = 21,231 (15% untouched holdout).
  - Saved fitted pipeline to `models/preprocessor.joblib`, schema to `data/processed/feature_schema.json`, and demo sample to `data/sample/demo_flows_sample.csv`.
  - Zero NaN or Inf values across all transformed splits.
  - All 3 unit tests passed.
- **Status**: Completed and Verified.


