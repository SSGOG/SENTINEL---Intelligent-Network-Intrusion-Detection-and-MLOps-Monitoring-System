#!/usr/bin/env bash
# Simple AWS deployment script for SENTINEL (budget‑constrained)
# Prerequisites: AWS CLI configured with credentials and sufficient permissions.
# This script creates a temporary ECR repository, pushes the Docker image,
# launches a t2.micro EC2, runs the container, verifies the service, then cleans up.

set -e

REPO_NAME="sentinel-temp-$(date +%s)"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 1. Create ECR repo
aws ecr create-repository --repository-name $REPO_NAME --region $REGION > /dev/null
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME"

# 2. Authenticate Docker to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# 3. Tag and push Docker image
docker tag sentinel:latest $ECR_URI:latest
docker push $ECR_URI:latest

# 4. Launch EC2 instance (t2.micro) with Docker installed via user-data script
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \ # Amazon Linux 2 (free tier)
    --instance-type t2.micro \
    --key-name my-key-pair \ # replace with your key
    --security-group-ids sg-xxxxxxxx \ # allow 8502 inbound
    --user-data "#!/bin/bash\n        yum update -y\n        amazon-linux-extras install docker -y\n        service docker start\n        docker run -d -p 8502:8502 $ECR_URI:latest streamlit run src/sentinel/dashboard.py --server.port 8502\n    " \
    --region $REGION \
    --query 'Instances[0].InstanceId' --output text)

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

# 5. Verify service (simple curl, retries)
for i in {1..10}; do
    if curl -s http://$PUBLIC_IP:8502 | grep -q "SENTINEL"; then
        echo "✅ Streamlit UI reachable at http://$PUBLIC_IP:8502"
        break
    fi
    sleep 5
done

# 6. Record IDs for evidence
echo "ECR repo: $ECR_URI" > docs/evidence/aws_deployment_log.txt
echo "EC2 instance ID: $INSTANCE_ID" >> docs/evidence/aws_deployment_log.txt
echo "Public IP: $PUBLIC_IP" >> docs/evidence/aws_deployment_log.txt

# 7. Cleanup – terminate EC2 and delete ECR repo
aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $REGION > /dev/null
aws ecr delete-repository --repository-name $REPO_NAME --region $REGION --force > /dev/null

echo "✅ Cleanup completed. Resources terminated."
