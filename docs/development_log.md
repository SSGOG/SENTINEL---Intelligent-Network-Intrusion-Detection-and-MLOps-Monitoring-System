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

## [M5] DVC Reproducible Pipeline & MLflow Lineage Verification
- **Date**: 2026-10-27
- **Objective**: Configure DVC multi-stage pipeline (`audit` -> `preprocess` -> `train` -> `evaluate`), verify dependencies, outputs, DAG representation, execute `dvc repro`, and document MLflow provenance links.
- **Commands Executed**:
  - `python -m dvc dag`
  - `python -m dvc repro`
  - `python -m dvc status`
- **Results**:
  - Full pipeline reproduced from start to finish via `dvc repro`.
  - Generated and validated `dvc.lock`.
  - `dvc status` verified: "Data and pipelines are up to date."
  - Saved evidence to `docs/evidence/dvc_pipeline_results.txt` and `docs/evidence/mlflow_experiment_summary.md`.
- **Status**: Completed and Verified.


---

## [M4] Model Training, MLflow Experiment Tracking & Explainability
- **Date**: 2026-10-27
- **Objective**: Execute multi-model comparative suite (Dummy Baseline, Logistic Regression, HistGradientBoosting), log parameters, metrics, artifacts, git SHAs to MLflow, evaluate on untouched test holdout, and compute SHAP explanations.
- **Commands Executed**:
  - `python src/sentinel/train.py`
  - `python src/sentinel/evaluate.py`
  - `python src/sentinel/explain.py`
  - `pytest tests/test_model_contract.py -v`
- **Results**:
  - Dummy Baseline: Accuracy 80.26%, Macro-F1 44.52% (Fails threat detection completely).
  - Logistic Regression: Accuracy 94.18%, Macro-F1 91.44%.
  - HistGradientBoosting (Selected Champion): Accuracy 99.87%, Macro-F1 99.79%, Recall 99.74%, Precision 99.48% on untouched test holdout (21,231 flows).
  - SHAP TreeExplainer attributions computed and validated in `reports/figures/shap_summary.json`. Top features: `Init_Win_bytes_forward`, `Destination Port`, `Bwd Packet Length Min`.
  - All 3 model contract tests passed.
- **Status**: Completed and Verified.

---

## [M5] DVC Reproducible Pipeline & MLflow Lineage Verification
- **Date**: 2026-10-27
- **Objective**: Configure DVC multi-stage pipeline (`audit` -> `preprocess` -> `train` -> `evaluate`), verify dependencies, outputs, DAG representation, execute `dvc repro`, and document MLflow provenance links.
- **Commands Executed**:
  - `python -m dvc dag`
  - `python -m dvc repro`
  - `python -m dvc status`
- **Results**:
  - Full pipeline reproduced from start to finish via `dvc repro`.
  - Generated and validated `dvc.lock`.
  - `dvc status` verified: "Data and pipelines are up to date."
  - Saved evidence to `docs/evidence/dvc_pipeline_results.txt` and `docs/evidence/mlflow_experiment_summary.md`.
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

## [M5] DVC Reproducible Pipeline & MLflow Lineage Verification
- **Date**: 2026-10-27
- **Objective**: Configure DVC multi-stage pipeline (`audit` -> `preprocess` -> `train` -> `evaluate`), verify dependencies, outputs, DAG representation, execute `dvc repro`, and document MLflow provenance links.
- **Commands Executed**:
  - `python -m dvc dag`
  - `python -m dvc repro`
  - `python -m dvc status`
- **Results**:
  - Full pipeline reproduced from start to finish via `dvc repro`.
  - Generated and validated `dvc.lock`.
  - `dvc status` verified: "Data and pipelines are up to date."
  - Saved evidence to `docs/evidence/dvc_pipeline_results.txt` and `docs/evidence/mlflow_experiment_summary.md`.
- **Status**: Completed and Verified.


---

## [M4] Model Training, MLflow Experiment Tracking & Explainability
- **Date**: 2026-10-27
- **Objective**: Execute multi-model comparative suite (Dummy Baseline, Logistic Regression, HistGradientBoosting), log parameters, metrics, artifacts, git SHAs to MLflow, evaluate on untouched test holdout, and compute SHAP explanations.
- **Commands Executed**:
  - `python src/sentinel/train.py`
  - `python src/sentinel/evaluate.py`
  - `python src/sentinel/explain.py`
  - `pytest tests/test_model_contract.py -v`
- **Results**:
  - Dummy Baseline: Accuracy 80.26%, Macro-F1 44.52% (Fails threat detection completely).
  - Logistic Regression: Accuracy 94.18%, Macro-F1 91.44%.
  - HistGradientBoosting (Selected Champion): Accuracy 99.87%, Macro-F1 99.79%, Recall 99.74%, Precision 99.48% on untouched test holdout (21,231 flows).
  - SHAP TreeExplainer attributions computed and validated in `reports/figures/shap_summary.json`. Top features: `Init_Win_bytes_forward`, `Destination Port`, `Bwd Packet Length Min`.
  - All 3 model contract tests passed.
- **Status**: Completed and Verified.

---

## [M5] DVC Reproducible Pipeline & MLflow Lineage Verification
- **Date**: 2026-10-27
- **Objective**: Configure DVC multi-stage pipeline (`audit` -> `preprocess` -> `train` -> `evaluate`), verify dependencies, outputs, DAG representation, execute `dvc repro`, and document MLflow provenance links.
- **Commands Executed**:
  - `python -m dvc dag`
  - `python -m dvc repro`
  - `python -m dvc status`
- **Results**:
  - Full pipeline reproduced from start to finish via `dvc repro`.
  - Generated and validated `dvc.lock`.
  - `dvc status` verified: "Data and pipelines are up to date."
  - Saved evidence to `docs/evidence/dvc_pipeline_results.txt` and `docs/evidence/mlflow_experiment_summary.md`.
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

## [M5] DVC Reproducible Pipeline & MLflow Lineage Verification
- **Date**: 2026-10-27
- **Objective**: Configure DVC multi-stage pipeline (`audit` -> `preprocess` -> `train` -> `evaluate`), verify dependencies, outputs, DAG representation, execute `dvc repro`, and document MLflow provenance links.
- **Commands Executed**:
  - `python -m dvc dag`
  - `python -m dvc repro`
  - `python -m dvc status`
- **Results**:
  - Full pipeline reproduced from start to finish via `dvc repro`.
  - Generated and validated `dvc.lock`.
  - `dvc status` verified: "Data and pipelines are up to date."
  - Saved evidence to `docs/evidence/dvc_pipeline_results.txt` and `docs/evidence/mlflow_experiment_summary.md`.
- **Status**: Completed and Verified.


---

## [M4] Model Training, MLflow Experiment Tracking & Explainability
- **Date**: 2026-10-27
- **Objective**: Execute multi-model comparative suite (Dummy Baseline, Logistic Regression, HistGradientBoosting), log parameters, metrics, artifacts, git SHAs to MLflow, evaluate on untouched test holdout, and compute SHAP explanations.
- **Commands Executed**:
  - `python src/sentinel/train.py`
  - `python src/sentinel/evaluate.py`
  - `python src/sentinel/explain.py`
  - `pytest tests/test_model_contract.py -v`
- **Results**:
  - Dummy Baseline: Accuracy 80.26%, Macro-F1 44.52% (Fails threat detection completely).
  - Logistic Regression: Accuracy 94.18%, Macro-F1 91.44%.
  - HistGradientBoosting (Selected Champion): Accuracy 99.87%, Macro-F1 99.79%, Recall 99.74%, Precision 99.48% on untouched test holdout (21,231 flows).
  - SHAP TreeExplainer attributions computed and validated in `reports/figures/shap_summary.json`. Top features: `Init_Win_bytes_forward`, `Destination Port`, `Bwd Packet Length Min`.
  - All 3 model contract tests passed.
- **Status**: Completed and Verified.

---

## [M5] DVC Reproducible Pipeline & MLflow Lineage Verification
- **Date**: 2026-10-27
- **Objective**: Configure DVC multi-stage pipeline (`audit` -> `preprocess` -> `train` -> `evaluate`), verify dependencies, outputs, DAG representation, execute `dvc repro`, and document MLflow provenance links.
- **Commands Executed**:
  - `python -m dvc dag`
  - `python -m dvc repro`
  - `python -m dvc status`
- **Results**:
  - Full pipeline reproduced from start to finish via `dvc repro`.
  - Generated and validated `dvc.lock`.
  - `dvc status` verified: "Data and pipelines are up to date."
  - Saved evidence to `docs/evidence/dvc_pipeline_results.txt` and `docs/evidence/mlflow_experiment_summary.md`.
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

## [M5] DVC Reproducible Pipeline & MLflow Lineage Verification
- **Date**: 2026-10-27
- **Objective**: Configure DVC multi-stage pipeline (`audit` -> `preprocess` -> `train` -> `evaluate`), verify dependencies, outputs, DAG representation, execute `dvc repro`, and document MLflow provenance links.
- **Commands Executed**:
  - `python -m dvc dag`
  - `python -m dvc repro`
  - `python -m dvc status`
- **Results**:
  - Full pipeline reproduced from start to finish via `dvc repro`.
  - Generated and validated `dvc.lock`.
  - `dvc status` verified: "Data and pipelines are up to date."
  - Saved evidence to `docs/evidence/dvc_pipeline_results.txt` and `docs/evidence/mlflow_experiment_summary.md`.
- **Status**: Completed and Verified.


---

## [M4] Model Training, MLflow Experiment Tracking & Explainability
- **Date**: 2026-10-27
- **Objective**: Execute multi-model comparative suite (Dummy Baseline, Logistic Regression, HistGradientBoosting), log parameters, metrics, artifacts, git SHAs to MLflow, evaluate on untouched test holdout, and compute SHAP explanations.
- **Commands Executed**:
  - `python src/sentinel/train.py`
  - `python src/sentinel/evaluate.py`
  - `python src/sentinel/explain.py`
  - `pytest tests/test_model_contract.py -v`
- **Results**:
  - Dummy Baseline: Accuracy 80.26%, Macro-F1 44.52% (Fails threat detection completely).
  - Logistic Regression: Accuracy 94.18%, Macro-F1 91.44%.
  - HistGradientBoosting (Selected Champion): Accuracy 99.87%, Macro-F1 99.79%, Recall 99.74%, Precision 99.48% on untouched test holdout (21,231 flows).
  - SHAP TreeExplainer attributions computed and validated in `reports/figures/shap_summary.json`. Top features: `Init_Win_bytes_forward`, `Destination Port`, `Bwd Packet Length Min`.
  - All 3 model contract tests passed.
- **Status**: Completed and Verified.

---

## [M5] DVC Reproducible Pipeline & MLflow Lineage Verification
- **Date**: 2026-10-27
- **Objective**: Configure DVC multi-stage pipeline (`audit` -> `preprocess` -> `train` -> `evaluate`), verify dependencies, outputs, DAG representation, execute `dvc repro`, and document MLflow provenance links.
- **Commands Executed**:
  - `python -m dvc dag`
  - `python -m dvc repro`
  - `python -m dvc status`
- **Results**:
  - Full pipeline reproduced from start to finish via `dvc repro`.
  - Generated and validated `dvc.lock`.
  - `dvc status` verified: "Data and pipelines are up to date."
  - Saved evidence to `docs/evidence/dvc_pipeline_results.txt` and `docs/evidence/mlflow_experiment_summary.md`.
- **Status**: Completed and Verified.




