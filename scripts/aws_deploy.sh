#!/usr/bin/env bash
# =============================================================================
# AWS Deployment Script for SENTINEL
# =============================================================================
# Budget-constrained "prove-it-works" deployment.
# Prerequisites:
#   - AWS CLI v2 configured with valid credentials (aws configure)
#   - Docker daemon running locally
#   - The SENTINEL Docker image already built: docker build -t sentinel:latest .
#   - An EC2 key pair created in the target region
#   - A security group that allows inbound TCP on ports 8000 and 8501
#   - An EC2 instance profile named ecrReadOnly with ECR pull permissions
#   - Permission to read the public Amazon Linux 2023 AMI parameter (unless --ami is supplied)
#
# Usage:
#   chmod +x scripts/aws_deploy.sh
#   ./scripts/aws_deploy.sh --key-name <your-key> --sg <sg-xxxxxxxx> [--region us-east-1]
# =============================================================================

set -euo pipefail

# --------------- Parse arguments ---------------
KEY_NAME=""
SG_ID=""
REGION="us-east-1"
AMI_ID=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --key-name) KEY_NAME="$2"; shift 2 ;;
        --sg)       SG_ID="$2";   shift 2 ;;
        --region)   REGION="$2";  shift 2 ;;
        --ami)      AMI_ID="$2";  shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$KEY_NAME" || -z "$SG_ID" ]]; then
    echo "Usage: $0 --key-name <key> --sg <sg-id> [--region us-east-1]"
    exit 1
fi

REPO_NAME="sentinel-temp-$(date +%s)"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [[ -z "$AMI_ID" ]]; then
    AMI_ID=$(aws ssm get-parameter \
        --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
        --region "${REGION}" \
        --query 'Parameter.Value' \
        --output text)
fi
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}"

echo "🔧 Region:     ${REGION}"
echo "🔧 Account:    ${ACCOUNT_ID}"
echo "🔧 AMI:        ${AMI_ID}"
echo "🔧 ECR Repo:   ${REPO_NAME}"

# --------------- 1. Create ECR repository ---------------
echo "📦 Creating ECR repository..."
aws ecr create-repository \
    --repository-name "${REPO_NAME}" \
    --region "${REGION}" > /dev/null

# --------------- 2. Authenticate Docker to ECR ---------------
echo "🔑 Authenticating Docker to ECR..."
aws ecr get-login-password --region "${REGION}" \
    | docker login --username AWS --password-stdin \
      "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# --------------- 3. Tag and push Docker image ---------------
echo "🚀 Pushing image to ECR..."
docker tag sentinel:latest "${ECR_URI}:latest"
docker push "${ECR_URI}:latest"

# --------------- 4. Compose user-data bootstrap script ---------------
USER_DATA=$(cat <<BOOTSTRAP
#!/bin/bash
set -euo pipefail
dnf update -y
dnf install -y docker
systemctl enable --now docker
usermod -aG docker ec2-user

# Authenticate to ECR from the instance
aws ecr get-login-password --region ${REGION} \
    | docker login --username AWS --password-stdin \
      ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Pull and run the SENTINEL container (both ports)
docker pull ${ECR_URI}:latest
docker run -d --restart unless-stopped \
    -p 8000:8000 \
    -p 8501:8501 \
    --name sentinel \
    ${ECR_URI}:latest
BOOTSTRAP
)

# --------------- 5. Launch EC2 instance ---------------
echo "🖥️  Launching EC2 instance (t2.micro)..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "${AMI_ID}" \
    --instance-type t2.micro \
    --key-name "${KEY_NAME}" \
    --security-group-ids "${SG_ID}" \
    --user-data "${USER_DATA}" \
    --iam-instance-profile Name=ecrReadOnly \
    --region "${REGION}" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "   Instance ID: ${INSTANCE_ID}"

# --------------- 6. Wait for instance to be running ---------------
echo "⏳ Waiting for instance to enter running state..."
aws ec2 wait instance-running \
    --instance-ids "${INSTANCE_ID}" \
    --region "${REGION}"

PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "${INSTANCE_ID}" \
    --region "${REGION}" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "   Public IP:   ${PUBLIC_IP}"

# --------------- 7. Verify service (retries) ---------------
echo "🔍 Verifying Streamlit UI (may take 60-90 s for Docker pull)..."
SERVICE_UP=false
for i in {1..20}; do
    if curl -sf "http://${PUBLIC_IP}:8501" | grep -q "SENTINEL"; then
        SERVICE_UP=true
        break
    fi
    sleep 10
done

if ${SERVICE_UP}; then
    echo "✅ Streamlit UI reachable at http://${PUBLIC_IP}:8501"
    echo "✅ FastAPI health at       http://${PUBLIC_IP}:8000/health"
else
    echo "⚠️  Service not yet reachable — check instance logs with:"
    echo "   ssh -i ${KEY_NAME}.pem ec2-user@${PUBLIC_IP} 'docker logs sentinel'"
fi

# --------------- 8. Record evidence ---------------
mkdir -p docs/evidence
cat > docs/evidence/aws_deployment_log.txt <<EOF
Deployment Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
ECR Repository:       ${ECR_URI}
EC2 Instance ID:      ${INSTANCE_ID}
Public IP:            ${PUBLIC_IP}
Region:               ${REGION}
Streamlit URL:        http://${PUBLIC_IP}:8501
FastAPI Health URL:   http://${PUBLIC_IP}:8000/health
EOF

echo ""
echo "📄 Deployment log saved to docs/evidence/aws_deployment_log.txt"

# --------------- 9. Cleanup prompt ---------------
echo ""
echo "⚠️  REMEMBER TO CLEAN UP when done to avoid charges:"
echo "   aws ec2 terminate-instances --instance-ids ${INSTANCE_ID} --region ${REGION}"
echo "   aws ecr delete-repository --repository-name ${REPO_NAME} --region ${REGION} --force"
