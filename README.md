# SENTINEL: Intelligent Network Intrusion Detection & MLOps Monitoring System

A reproducible, local-first, zero-budget MLOps framework designed for production network threat detection, continuous model evaluation, automated drift detection, gated retraining, and responsible AI governance on the CIC-IDS2017 dataset.

---

## 🛡️ Core Highlights
- **Local-First Zero-Budget Execution**: Trains and evaluates locally on the 8 CIC-IDS2017 flow CSVs without costly cloud-bound transfers.
- **Reproducible Data & Pipeline Tracking**: DVC versioning for feature pipelines and MLflow for tracking parameters, metrics, and models.
- **Production REST Serving**: FastAPI inference microservice with pydantic contract validation.
- **Professional Security Dashboard**: Interactive Streamlit application for single-flow inspection, batch triage, real-time drift metrics, and lineage tracking.
- **CI/CD Automation**: GitHub Actions workflow for DVC pipeline execution, test verification, and Docker image builds.
- **Responsible AI & Governance**: Rigorous error analysis, SHAP feature attribution, model card, risk register, and roll-back strategy.

## Documentation
- [Project report: architecture, methods, results, and limitations](PROJECT_EXPLANATION.md)
- [Run guide: local setup, DVC, MLflow, FastAPI, Streamlit, Docker, and AWS](RUN_GUIDE.md)
