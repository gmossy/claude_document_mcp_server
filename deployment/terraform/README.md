# Terraform Deployment for Document Gateway

This directory contains Terraform configurations for deploying the Document Gateway application to AWS GovCloud.

## Architecture

- **ECR**: Container registries for API, Nginx, and Frontend images
- **ECS Fargate**: Container orchestration
- **ALB**: Application Load Balancer for traffic distribution
- **RDS PostgreSQL**: Database (optional, can use SQLite)
- **S3**: Document storage
- **Bedrock**: LLM services for document processing
- **VPC**: Isolated network environment
- **CloudWatch**: Logging and monitoring

## Prerequisites

1. AWS CLI configured for GovCloud
2. Terraform >= 1.5.0
3. Docker images pushed to ECR (see deployment steps)

## Quick Start

1. **Copy and configure variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

   **For existing VPC (vpc-0f3105b0797e0c715):**
   - Set `use_existing_vpc = true`
   - Set `existing_vpc_id = "vpc-0f3105b0797e0c715"`
   - Set `existing_public_subnet_ids` with your subnet IDs
   - Set `enable_nat_gateway = false` (since all subnets are public)

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

3. **Review the plan:**
   ```bash
   terraform plan
   ```

4. **Apply the configuration:**
   ```bash
   terraform apply
   ```

## Deployment Steps

### 1. Build and Push Docker Images

```bash
# Login to ECR
aws ecr get-login-password --region us-gov-west-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-gov-west-1.amazonaws.com

# Build and tag images
docker build -f backend/app/Dockerfile -t document-gateway-api:latest .
docker build -f nginx/Dockerfile -t document-gateway-nginx:latest .
docker build -f frontend/Dockerfile.frontend -t document-gateway-frontend:latest ./frontend

# Tag for ECR
docker tag document-gateway-api:latest <ECR_API_REPO_URL>:latest
docker tag document-gateway-nginx:latest <ECR_NGINX_REPO_URL>:latest
docker tag document-gateway-frontend:latest <ECR_FRONTEND_REPO_URL>:latest

# Push to ECR
docker push <ECR_API_REPO_URL>:latest
docker push <ECR_NGINX_REPO_URL>:latest
docker push <ECR_FRONTEND_REPO_URL>:latest
```

### 2. Configure Bedrock Access

Bedrock model access must be granted through the AWS Console:
1. Go to Bedrock console
2. Request access to the model (e.g., Claude)
3. Wait for approval

### 3. Deploy Infrastructure

```bash
terraform apply
```

### 4. Access the Application

After deployment, get the ALB DNS name:
```bash
terraform output application_url
```

## File Organization

- `main.tf`: Provider and main configuration
- `variables.tf`: Input variables
- `outputs.tf`: Output values
- `ecr.tf`: Container registries
- `networking.tf`: VPC, subnets, security groups
- `s3.tf`: S3 buckets
- `iam.tf`: IAM roles and policies
- `ecs.tf`: ECS cluster, tasks, services
- `alb.tf`: Load balancer
- `bedrock.tf`: Bedrock configuration
- `rds.tf`: Database (optional)
- `cloudwatch.tf`: Monitoring

## Important Notes

1. **GovCloud**: Ensure you're using GovCloud endpoints and regions
2. **Secrets**: Use AWS Secrets Manager for sensitive values (db_password, etc.)
3. **HTTPS**: Configure ACM certificate for production
4. **Costs**: NAT Gateway and VPC endpoints have costs - monitor usage
5. **Backups**: RDS backups are configured automatically

## Service Communication

**Important**: The nginx service needs to communicate with the API service. Since both services are in the same VPC and security group, they can communicate. However, you need to configure nginx to reach the API:

1. **Option 1 - Service Discovery** (Recommended): Set up AWS Service Discovery so nginx can resolve the API service by name
2. **Option 2 - Internal ALB**: Configure nginx to use the API target group's internal DNS
3. **Option 3 - Environment Variable**: Pass the API service endpoint as an environment variable to nginx

The current configuration creates both services, but you'll need to update the nginx configuration to point to the API service endpoint.

## Troubleshooting

- Check CloudWatch Logs for container logs
- Verify security group rules allow traffic
- Ensure ECR images are pushed and accessible
- Check ALB target group health
- Verify Bedrock model access is granted
- Ensure nginx can reach the API service (check service discovery or networking)

## Cost Optimization

- Use VPC endpoints to reduce NAT Gateway data transfer costs
- Enable S3 lifecycle policies to move old documents to Glacier
- Use ECR lifecycle policies to clean up old images
- Consider using Spot instances for non-production environments

## Security Best Practices

1. **Never commit `terraform.tfvars`** - it contains sensitive data
2. Use AWS Secrets Manager for database passwords
3. Restrict `allowed_cidr_blocks` to your network
4. Enable encryption on S3 buckets
5. Use least-privilege IAM policies
6. Enable CloudWatch Container Insights for monitoring
7. Enable RDS encryption and automated backups

Created the Terraform deployment structure. Summary:
Created Files
All Terraform configuration files are in /deployment/terraform/:
Core Configuration Files
main.tf - Provider configuration and data sources
variables.tf - Input variables with descriptions
outputs.tf - Output values for deployment information
terraform.tfvars.example - Example variables file (copy to terraform.tfvars)
Service-Specific Files
ecr.tf - ECR repositories for API, Nginx, and Frontend images
networking.tf - VPC, subnets, security groups, NAT Gateway, VPC endpoints
s3.tf - S3 bucket for document storage with encryption and lifecycle policies
iam.tf - IAM roles and policies for ECS tasks
ecs.tf - ECS cluster, task definitions, and services
alb.tf - Application Load Balancer with HTTP/HTTPS listeners
rds.tf - PostgreSQL RDS instance (optional)
bedrock.tf - Bedrock LLM configuration documentation
cloudwatch.tf - CloudWatch alarms for monitoring
Documentation
README.md - Deployment guide and documentation
.gitignore - Terraform-specific gitignore
Features
AWS GovCloud compatible (us-gov-east-1, us-gov-west-1)
Organized by service with documentation
Security: encrypted S3, private subnets, security groups
Scalable: ECS Fargate with configurable task counts
Monitoring: CloudWatch logs and alarms
Cost optimization: VPC endpoints, S3 lifecycle policies, ECR lifecycle policies
Next Steps
Copy terraform.tfvars.example to terraform.tfvars and configure your values
Set database credentials (consider AWS Secrets Manager for production)
Build and push Docker images to ECR
Request Bedrock model access in the AWS Console
Run terraform init and terraform plan to review
Run terraform apply to deploy
The configuration is ready for deployment. All files include documentation explaining each component.
