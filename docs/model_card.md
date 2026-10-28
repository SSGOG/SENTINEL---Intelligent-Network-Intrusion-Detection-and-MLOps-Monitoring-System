# SENTINEL Model Card (v1.0)

## Intended Use
- Binary network‑flow intrusion detection (benign vs malicious).
- Decision‑support for SOC analysts; not an automated blocking system.

## Data
- **Source**: CIC‑IDS2017 (8 CSV files, ~52 GB).
- **Versioning**: Tracked with DVC; each raw file has SHA‑256 checksum stored in `data.dvc`.
- **Pre‑processing**: Numeric features are median-imputed before the train/validation/test split artifacts are written. The model consumes those raw imputed feature values; inference does not apply the retained legacy scaler.

## Model
- **Algorithm**: `XGBClassifier` (XGBoost).
- **Performance** (hold‑out test):
  - Accuracy: 99.92 %
  - Precision: 99.62 %
  - Recall: 99.98 %
  - Macro‑F1: 99.88 %
- **Explainability**: SHAP summary values provided in `reports/figures/shap_summary.json`.

## Responsible AI
- **Bias analysis**: No class imbalance after stratified split; class distribution shown in `reports/metrics/class_distribution.json`.
- **Error analysis**: Confusion matrix (or placeholder) displayed in the dashboard.
- **Mitigations**: Manual analyst review required before any mitigation action.

## Governance
- **Versioning**: Model artifacts stored under `models/` with DVC tracking.
- **Audit trail**: MLflow experiment `sentinel_training` logs parameters, metrics, and artifacts.
- **Access control**: Local‑first file permissions; only users in the `sentinel` OS group can modify `models/`.

## Deployment
- Docker image `sentinel:latest` (see `Dockerfile`).
- Served via FastAPI (`/predict`) and Streamlit UI.
- CI pipeline builds, tests, and pushes the image to a temporary ECR repo.
