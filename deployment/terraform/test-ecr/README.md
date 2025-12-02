# ECR Test Configuration

This is a minimal Terraform configuration that **only creates ECR repositories**. It does not modify any VPC, networking, or other AWS resources.

## Purpose

Test ECR repository creation and Docker image pushing without affecting your existing infrastructure.

## Quick Start

### 1. Initialize Terraform

```bash
cd deployment/terraform/test-ecr
terraform init
```

### 2. Review What Will Be Created

```bash
terraform plan
```

This will show you:
- 3 ECR repositories (api, nginx, frontend)
- 3 lifecycle policies
- **No VPC or networking changes**

### 3. Create ECR Repositories

```bash
terraform apply
```

Type `yes` when prompted.

### 4. Get Repository URLs

```bash
terraform output
```

Or get individual URLs:
```bash
terraform output ecr_api_repository_url
terraform output ecr_nginx_repository_url
terraform output ecr_frontend_repository_url
```

## Build and Push Docker Images

### Step 1: Login to ECR

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region us-gov-west-1)
REGION="us-gov-west-1"

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
```

### Step 2: Get Repository URLs

```bash
API_REPO=$(terraform output -raw ecr_api_repository_url)
NGINX_REPO=$(terraform output -raw ecr_nginx_repository_url)
FRONTEND_REPO=$(terraform output -raw ecr_frontend_repository_url)

echo "API: $API_REPO"
echo "Nginx: $NGINX_REPO"
echo "Frontend: $FRONTEND_REPO"
```

### Step 3: Build Docker Images

From the project root directory:

```bash
# Build API image
docker build -f backend/app/Dockerfile -t document-gateway-api:latest .

# Build Nginx image
docker build -f nginx/Dockerfile -t document-gateway-nginx:latest .

# Build Frontend image
docker build -f frontend/Dockerfile.frontend -t document-gateway-frontend:latest ./frontend
```

### Step 4: Tag Images for ECR

```bash
# Tag images
docker tag document-gateway-api:latest ${API_REPO}:latest
docker tag document-gateway-nginx:latest ${NGINX_REPO}:latest
docker tag document-gateway-frontend:latest ${FRONTEND_REPO}:latest
```

### Step 5: Push to ECR

```bash
# Push images
docker push ${API_REPO}:latest
docker push ${NGINX_REPO}:latest
docker push ${FRONTEND_REPO}:latest
```

## Verify Images

```bash
# List images in repositories
aws ecr describe-images --repository-name document-gateway-test-api --region us-gov-west-1
aws ecr describe-images --repository-name document-gateway-test-nginx --region us-gov-west-1
aws ecr describe-images --repository-name document-gateway-test-frontend --region us-gov-west-1
```

## Complete Script

Save this as `push-images.sh` in the test-ecr directory:

```bash
#!/bin/bash
set -e

REGION="us-gov-west-1"
cd "$(dirname "$0")"

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
cd ../..
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

echo -e "\n=== Done! ==="
```

Make it executable and run:
```bash
chmod +x push-images.sh
./push-images.sh
```

## Cleanup

To remove the test ECR repositories:

```bash
terraform destroy
```

Type `yes` when prompted.

## What This Creates

- ✅ 3 ECR repositories (api, nginx, frontend)
- ✅ 3 lifecycle policies (keep last 10 images)
- ✅ Image scanning enabled
- ✅ Encryption enabled

## What This Does NOT Create

- ❌ No VPC changes
- ❌ No networking changes
- ❌ No security groups
- ❌ No other AWS resources

This is completely safe to run and won't affect your existing infrastructure!

