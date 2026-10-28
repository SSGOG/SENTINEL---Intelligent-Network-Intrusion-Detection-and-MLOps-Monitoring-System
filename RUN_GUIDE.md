# SENTINEL Run Guide

This guide covers setup and operation of SENTINEL on Windows/PowerShell, including DVC, MLflow, FastAPI, Streamlit, Docker, and the optional AWS demo. Run project commands from the repository root unless a step says otherwise.

## 1. What must be available

### Local software

- Python 3.11
- Git
- Docker Desktop for container use
- DVC (`pip install dvc`) for pipeline commands
- AWS CLI v2 and Git Bash or WSL only if using the AWS deployment script

### Model and sample artifacts

The serving application needs:

- `models/champion_model.joblib`
- `data/processed/feature_schema.json`
- `data/sample/demo_flows_sample.csv`

The champion model and schema are small serving assets; the bulk raw dataset and processed NumPy splits are not stored in Git. For DVC training/evaluation, the eight primary CIC-IDS2017 CSVs and the audited secondary data directory must be present locally. The current `.dvc/config` points to the machine-specific local remote `E:\sentinel_dvc_remote`; that path is not a shared GitHub artifact store. On another machine, configure a reachable DVC remote and provide the data or run the pipeline from locally available source CSVs.

## 2. First-time setup

Clone the repository and enter it:

```powershell
git clone https://github.com/SSGOG/SENTINEL---Intelligent-Network-Intrusion-Detection-and-MLOps-Monitoring-System.git
Set-Location SENTINEL---Intelligent-Network-Intrusion-Detection-and-MLOps-Monitoring-System
```

Create and activate a Python 3.11 virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

For development, tests, DVC, and MLflow:

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest dvc
```

If PowerShell prevents venv activation, use the Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The Docker image uses the smaller serving-only `requirements-runtime.txt`; it does not install training, MLflow, or SHAP dependencies.

## 3. Get the CIC-IDS2017 data

The raw archives are intentionally excluded from Git because of their size. If the archives are present in the repository root, extract them there:

```powershell
if (-not (Test-Path .\MachineLearningCSV\MachineLearningCVE)) {
    Expand-Archive -Path .\MachineLearningCSV.zip -DestinationPath . -Force
}
if (-not (Test-Path .\GeneratedLabelledFlows\TrafficLabelling)) {
    Expand-Archive -Path .\GeneratedLabelledFlows.zip -DestinationPath . -Force
}
```

Confirm the required directories and primary CSV inputs exist:

```powershell
Test-Path .\MachineLearningCSV\MachineLearningCVE
Get-ChildItem .\MachineLearningCSV\MachineLearningCVE -Filter *.csv | Measure-Object
Test-Path .\GeneratedLabelledFlows\TrafficLabelling
```

The data-validation stage expects both locations. Do not copy the large extracted datasets into Git; retain them locally or configure a shared DVC remote for your team.

## 4. DVC pipeline

### 4.1 Check DVC configuration and data

```powershell
dvc --version
dvc remote list
dvc status
```

The checked-in configuration currently names a local remote at `E:\sentinel_dvc_remote`. On this same workstation, that remote is usable only if the path exists and contains the corresponding DVC cache. On another machine, point the remote at an accessible DVC-supported location. Example for a shared remote:

```powershell
dvc remote add -d teamstorage <DVC_REMOTE_URL>
```

Use the URL appropriate to your configured storage (for example, an S3 bucket or shared storage location). Keep credentials in the user's DVC-local configuration/environment or cloud identity, not in Git. Then retrieve cached outputs if the remote contains them:

```powershell
dvc pull
```

Without a reachable remote or local source CSVs, `dvc pull`/`dvc repro` cannot recreate the data.

### 4.2 Reproduce all declared stages

With the required raw inputs available:

```powershell
dvc repro
```

The declared stages validate the dataset, preprocess and split the data, train the XGBoost model, evaluate the held-out test split, and run the additional model-metrics stage. This is a data-heavy workflow: preprocessing loads and concatenates the source CSVs, and training can take substantial time and memory. It is not required just to launch the already-saved model.

Useful commands:

```powershell
dvc dag
dvc status
dvc metrics show
```

The pipeline currently applies median imputation before splitting the rows. This can leak validation/test distribution information into preprocessing; see [PROJECT_EXPLANATION.md](./PROJECT_EXPLANATION.md) before treating the test score as an unbiased generalization estimate.

### 4.3 Regenerate individual artifacts

From the repository root, the evaluation and explanation scripts can also be run directly after their required model/data files exist:

```powershell
python .\src\sentinel\evaluate.py
python .\src\sentinel\explain.py
```

## 5. MLflow

Training logs an MLflow run to the local `mlruns` directory. Run training through DVC:

```powershell
dvc repro train
```

Or, after preprocessing has generated the arrays:

```powershell
python .\src\sentinel\train.py
```

Open a second PowerShell window, activate the same environment, change to the repository root, and launch the tracking UI:

```powershell
mlflow ui --backend-store-uri .\mlruns --host 127.0.0.1 --port 5000
```

Browse to `http://127.0.0.1:5000`. The tracking store is local and is excluded from Git. It is not a hosted tracking service, and another machine will not see these runs unless the store is moved or shared deliberately.

## 6. FastAPI

Start the API from the repository root in its own PowerShell window:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.sentinel.api:app --host 127.0.0.1 --port 8000
```

Check readiness and interactive API documentation:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Start-Process http://127.0.0.1:8000/docs
```

The health response should report `model_loaded: true` and `features_configured: 78`.

Example one-flow request:

```powershell
$body = @{
    features = @{
        "Destination Port" = 80
        "Flow Duration" = 12000
        "Total Fwd Packets" = 5
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post `
    -Uri http://127.0.0.1:8000/predict `
    -ContentType "application/json" `
    -Body $body
```

The API constructs the model's 78-feature vector in schema order. Omitted values currently default to zero; for meaningful predictions, send a complete feature record rather than a sparse example.

Batch requests use `POST /predict-batch` with a `flows` array and are limited to 1,000 flows per request.

## 7. Streamlit dashboard

Keep the API window running. Open a second PowerShell window, activate the environment, and run:

```powershell
Set-Location <repository-root>
.\.venv\Scripts\Activate.ps1
python -m streamlit run .\src\sentinel\dashboard.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. Pages 3, 4, 5, and 7 depend on the packaged sample, evaluation JSON, SHAP summary, and lineage evidence respectively. The batch page can use `data/sample/demo_flows_sample.csv` or a CSV with the expected numeric columns.

Page 6's drift readings and retraining simulation, and some overview telemetry, are illustrative dashboard content. They are not measurements from a live network monitor.

## 8. Tests

For the full local test suite, first make sure the model, schema, processed split arrays, sample, and data-audit manifest are present. The split arrays and data manifest are generated by DVC:

```powershell
dvc repro
python -m pytest -q
```

The GitHub Actions workflow runs the serving/API and dashboard navigation tests against committed serving artifacts and builds/smoke-tests the container. It does not reproduce the full DVC training pipeline because the raw CIC-IDS2017 data and the current workstation-local DVC cache are not included in the repository.

## 9. Docker

Docker Desktop must be running. From the repository root:

```powershell
docker build -t sentinel:latest .
docker run --rm --name sentinel `
    -p 8000:8000 `
    -p 8501:8501 `
    sentinel:latest
```

Check both services in another PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-WebRequest http://127.0.0.1:8501/ -UseBasicParsing
```

The container uses a non-root account and starts FastAPI plus Streamlit through `start.sh`. The final locally built image was approximately 1.16 GB. It passed a local smoke check with the model loaded and Streamlit returning HTTP 200. Review Docker logs for runtime warnings:

```powershell
docker logs sentinel
```

Stop the foreground container with `Ctrl+C`. If started detached, use `docker stop sentinel`.

## 10. Optional AWS demo deployment

The AWS deployment script is a cloud-resource-creating demo, not a local setup step. It was not run or validated against an AWS account as part of this work.

### 10.1 Requirements and safety checks

Before deploying, arrange:

- AWS CLI v2 authenticated to the intended account and region.
- Docker Desktop running and a successful local image build.
- An EC2 key pair in the region.
- A security group allowing TCP 8000 and 8501. Restrict source CIDRs to your own trusted IPs; do not expose this unauthenticated, unencrypted demo publicly.
- An EC2 instance profile named `ecrReadOnly` with permission to pull from ECR.
- Permissions for ECR repository creation/push, EC2 launch/describe/wait/terminate, and SSM parameter read for the current Amazon Linux 2023 AMI (unless `--ami` is passed).

The script launches a `t2.micro`, pushes an image to ECR, and creates billable resources. The current serving image is large and runs two Python services; the `t2.micro` memory limit may be tight and could cause startup failures. Check EC2 system logs and `docker logs sentinel`; use an appropriately sized instance if it runs out of memory. AWS networking, IAM, quotas, image pull, and billing are account/region-specific and cannot be guaranteed by local tests.

### 10.2 Build and deploy

Build the exact tag expected by the script:

```powershell
docker build -t sentinel:latest .
```

Run the script from Git Bash or WSL at the repository root:

```bash
aws sts get-caller-identity
bash scripts/aws_deploy.sh --key-name <your-ec2-key-name> --sg <sg-xxxxxxxx> --region us-east-1
```

The script resolves the latest Amazon Linux 2023 x86_64 AMI unless `--ami <ami-id>` is supplied. It creates a timestamped ECR repository, authenticates Docker to ECR, pushes `sentinel:latest`, launches the EC2 instance, and reports the public IP. It writes deployment details to `docs/evidence/aws_deployment_log.txt`.

After launch, verify both endpoints from a machine allowed by the security group:

```text
http://<public-ip>:8000/health
http://<public-ip>:8501/
```

The script's Streamlit check is only an HTTP reachability probe; it does not verify every page or prove that the API is healthy. Inspect the API health response and instance/container logs as well.

### 10.3 Cleanup

The script prints cleanup commands at completion but does not automatically delete the resources. Terminate the EC2 instance and delete the temporary ECR repository when finished:

```bash
aws ec2 terminate-instances --instance-ids <instance-id> --region us-east-1
aws ecr delete-repository --repository-name <sentinel-temp-repository> --region us-east-1 --force
```

Also verify that the instance reaches `terminated` and that no other billable resources were created.

## 11. Troubleshooting

| Symptom | Check |
|---|---|
| API says model is not ready | Confirm `models/champion_model.joblib` and `data/processed/feature_schema.json` exist in the current working tree/container. |
| Model expects a different feature count | Compare model `n_features_in_` with `feature_schema.json` `feature_count`; use matching model and schema artifacts. |
| DVC cannot find inputs | Ensure both expected dataset directories and all required CSVs are present; check the configured DVC remote and `dvc status`. |
| DVC uses an unavailable path | Replace the workstation-local `E:\sentinel_dvc_remote` configuration with a reachable team remote. |
| Streamlit sample missing | Confirm `data/sample/demo_flows_sample.csv` exists and was copied into the Docker image. |
| Docker build cannot copy the model | Confirm the champion file exists locally and is included in the Git release/artifacts used as build context. |
| Docker starts but AWS does not | Check EC2 instance status/system log, IAM instance profile, ECR pull permissions, security-group ingress, architecture/AMI, disk space, and memory. |
| AWS UI is reachable but unsafe | Restrict inbound CIDRs and put authentication/TLS behind an appropriate gateway before any broader exposure. |

For current architecture, evaluation results, and methodological caveats, see [PROJECT_EXPLANATION.md](./PROJECT_EXPLANATION.md).
