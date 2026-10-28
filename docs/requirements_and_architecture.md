# SENTINEL – Requirements & Architecture

## Project Goal
Detect malicious network flows in real‑time using the **CIC‑IDS2017** flow‑based CSV dataset and provide a full MLOps lifecycle (data versioning, reproducible pipelines, experiment tracking, model serving, CI/CD, monitoring, and optional low‑cost AWS deployment).

## Core Stack (local‑first)
- **Python 3.11** – pandas, NumPy, scikit‑learn, and XGBoost for the current champion.
- **DVC** – data & model versioning, pipeline orchestration.
- **MLflow** – experiment tracking, model registry.
- **FastAPI** – model inference service.
- **Streamlit** – interactive security dashboard.
- **Docker** – reproducible container for FastAPI + Streamlit.
- **GitHub Actions** – lint, unit tests, Docker build, sanity‑check.
- **AWS (optional, cost‑controlled)** – ECR for image, EC2 (t2.micro) for demo, CloudWatch logs.

## High‑Level Architecture
```mermaid
flowchart TD
    subgraph Local
        A[Raw CSVs (CIC‑IDS2017)] -->|DVC tracked| B[Data Validation]
        B --> C[Preprocessing & Feature Engineering]
        C --> D[Model Training]
        D --> E[MLflow Tracking]
        E --> F[Docker Image (FastAPI+Streamlit)]
    end
    subgraph OptionalAWS
        F --> G[ECR Repository]
        G --> H[EC2 Instance (t2.micro)]
        H --> I[FastAPI endpoint]
        H --> J[Streamlit UI]
    end
    style Local fill:#eef,stroke:#333,stroke-width:2px
    style OptionalAWS fill:#ffe,stroke:#333,stroke-width:2px
```

## Budget Guardrails
- Raw dataset (~52 GB) **never** uploaded; stored locally.
- Only the **Docker image** and small artefacts (model .joblib, JSON reports) are pushed to AWS; the serving image excludes training-only dependencies and raw datasets.
- EC2 runs are **started, health‑checked, then terminated** automatically to stay < $100.
- All secrets (AWS keys) are **never committed**; the script expects the user to run `aws configure` beforehand.

## Milestones & Acceptance Criteria (preview)
1. **Repository hygiene** – import shim fixed, tests pass, `sentinel` package tracked.
2. **Data audit** – schema, label distribution, missing‑value report stored in `docs/data_audit_summary.md`.
3. **DVC pipeline** – stages for validation, preprocessing, training, evaluation; `dvc repro` runs without error.
4. **MLflow experiment** – real run logged, metrics & confusion matrix saved, artefacts versioned.
5. **Explainability** – SHAP summary plot generated under `docs/evidence/shap_summary.png`.
6. **FastAPI** – health & predict endpoints functional; integration test passes.
7. **Streamlit UI** – dark futuristic theme, model info, confusion matrix placeholder replaced when metrics exist.
8. **Docker** – image builds, runs, serves both services on ports 8000 & 8501.
9. **CI/CD** – GitHub Actions executes lint, tests, Docker build, optional CD to AWS (via manual trigger).
10. **Monitoring & drift** – simple stats‑drift detector, logs warnings.
11. **Governance docs** – model card, risk register, governance linking to Git SHA, DVC rev, MLflow run.
12. **Poster & viva** – one‑slide PNG and Q&A markdown.
13. **Final Project Explanation** – comprehensive `PROJECT_EXPLANATION.md`.

All future work will follow the incremental protocol outlined in the system prompt.
