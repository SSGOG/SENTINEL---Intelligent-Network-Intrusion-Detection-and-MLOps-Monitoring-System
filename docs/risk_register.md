# SENTINEL Risk Register

## Overview
The risk register documents identified risks, their potential impact, likelihood, and mitigation strategies for the SENTINEL intrusion‑detection pipeline.

| Risk ID | Description | Category | Likelihood | Impact | Mitigation |
|--------|-------------|----------|------------|--------|------------|
| R1 | Model drift due to evolving network traffic patterns. | Production Readiness | Medium | High (degraded detection) | Continuous drift monitoring (`src/sentinel/monitor.py`) and automated retraining gate in UI. |
| R2 | Unauthorized access to model artifacts. | Governance | Low | High (model tampering) | OS‑level ACLs on `models/` folder, GitHub team permissions, future token‑based API auth. |
| R3 | Bias in predictions for under‑represented traffic types. | Responsible AI | Low | Medium | Stratified data split, bias analysis in `model_card.md`, SHAP explanations for feature importance. |
| R4 | Failure of Docker container (resource exhaustion). | Production Readiness | Medium | Medium | Resource limits in Dockerfile, health‑check endpoint, logs captured in `docs/evidence/docker_runtime.txt`. |
| R5 | Exposure of AWS credentials during deployment. | Security | Low | High | Deployment script reads credentials from environment variables / IAM role, no hard‑coded keys. |

*All risks are reviewed after each CI run and updated as needed.*