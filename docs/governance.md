# SENTINEL Governance Documentation

## Versioning & Audit Trail
- **Data**: Managed with DVC. `data.dvc` tracks raw CSVs and processed Parquet files. Each version includes SHA‑256 checksum.
- **Model**: Stored under `models/` and tracked with DVC (`models.dvc`).
- **MLflow**: Experiment `sentinel_training` logs parameters, metrics, artifacts, and source code version (Git commit SHA).

## Access Control
- Repository permissions: only members of the `sentinel-dev` GitHub team can push to `main`.
- OS level: `models/` directory owned by the `sentinel` Windows group; read‑only for others.
- FastAPI endpoints (future) will require Bearer token authentication.

## Responsible AI Practices
- **Bias mitigation**: Stratified train/validation split ensures balanced class distribution.
- **Error analysis**: Confusion matrix (or placeholder) displayed; SHAP values provided for feature attribution.
- **Human‑in‑the‑loop**: Dashboard requires analyst confirmation before any response.

## Monitoring & Drift
- Dashboard includes KS‑test drift statistics and a retraining gate slider.
- Logs are emitted via `streamlit` and Docker `stdout`; can be forwarded to CloudWatch or local `logrotate`.

## Continuous Integration
- CI workflow (`.github/workflows/ci.yml`) runs lint, tests, builds Docker, and performs a sanity‑check of the UI.
- On successful CI, Docker image can be pushed to a temporary ECR repo for optional AWS deployment.
