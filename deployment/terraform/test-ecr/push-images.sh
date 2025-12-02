#!/bin/bash
set -e

REGION="us-gov-west-1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$SCRIPT_DIR"

echo "=== Getting ECR repository URLs ==="
API_REPO=$(terraform output -raw ecr_api_repository_url)
NGINX_REPO=$(terraform output -raw ecr_nginx_repository_url)
FRONTEND_REPO=$(terraform output -raw ecr_frontend_repository_url)

echo "API: $API_REPO"
echo "Nginx: $NGINX_REPO"
echo "Frontend: $FRONTEND_REPO"

echo -e "\n=== Logging into ECR ==="
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region $REGION)
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

echo -e "\n=== Building images ==="
cd "$PROJECT_ROOT"
docker build -f backend/app/Dockerfile -t document-gateway-api:latest .
docker build -f nginx/Dockerfile -t document-gateway-nginx:latest .
docker build -f frontend/Dockerfile.frontend -t document-gateway-frontend:latest ./frontend

echo -e "\n=== Tagging images ==="
docker tag document-gateway-api:latest ${API_REPO}:latest
docker tag document-gateway-nginx:latest ${NGINX_REPO}:latest
docker tag document-gateway-frontend:latest ${FRONTEND_REPO}:latest

echo -e "\n=== Pushing images to ECR ==="
docker push ${API_REPO}:latest
docker push ${NGINX_REPO}:latest
docker push ${FRONTEND_REPO}:latest

echo -e "\n=== Verifying images ==="
aws ecr describe-images --repository-name document-gateway-test-api --region $REGION --query 'imageDetails[0].[imageTags[0],imagePushedAt]' --output table
aws ecr describe-images --repository-name document-gateway-test-nginx --region $REGION --query 'imageDetails[0].[imageTags[0],imagePushedAt]' --output table
aws ecr describe-images --repository-name document-gateway-test-frontend --region $REGION --query 'imageDetails[0].[imageTags[0],imagePushedAt]' --output table

echo -e "\n=== Done! Images pushed successfully ==="

