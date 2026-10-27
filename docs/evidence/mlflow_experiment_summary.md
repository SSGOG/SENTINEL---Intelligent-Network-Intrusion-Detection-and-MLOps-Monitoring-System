# MLflow Experiment Tracking Evidence & Lineage

All experiments were executed with real parameters and logged directly into MLflow tracking sqlite/file store.

## 1. Experiment Overview
- **Experiment Name**: `SENTINEL_Network_Intrusion_Detection`
- **Logged Models**:
  - `Dummy Baseline` (Run ID: `874b6a096b944cf495203a84a9e7b46a`) -> Macro-F1: 0.4452
  - `Logistic Regression` (Run ID: `3d3329ed8474475286f9517c249842e0`) -> Macro-F1: 0.9144
  - `HistGradientBoosting` (Run ID: `a052237c2b6a413ebb52adcca9be534d`) -> Macro-F1: 0.9975 [CHAMPION]

## 2. Lineage Provenance
- **Dataset Version**: `CIC-IDS2017-8Files-Stratified-v1.0` (DVC-reproducible pipeline)
- **Champion Model Artifact**: `models/champion_model.joblib`
- **Preprocessor Artifact**: `models/preprocessor.joblib`
- **Evaluation Set**: Untouched holdout (21,231 flows)
- **Holdout Test Metrics**: Accuracy 99.87%, Precision 99.48%, Recall 99.74%, Macro-F1 99.79%
