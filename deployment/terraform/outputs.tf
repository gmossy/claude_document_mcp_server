# ============================================================================
# TERRAFORM OUTPUTS
# ============================================================================
# Output values that can be used by other Terraform configurations or
# displayed after deployment.

# ============================================================================
# ECR OUTPUTS
# ============================================================================

output "ecr_api_repository_url" {
  description = "URL of the API ECR repository"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_nginx_repository_url" {
  description = "URL of the Nginx ECR repository"
  value       = aws_ecr_repository.nginx.repository_url
}

output "ecr_frontend_repository_url" {
  description = "URL of the Frontend ECR repository"
  value       = aws_ecr_repository.frontend.repository_url
}

# ============================================================================
# ECS OUTPUTS
# ============================================================================

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "api_service_name" {
  description = "Name of the API ECS service"
  value       = aws_ecs_service.api.name
}

output "nginx_service_name" {
  description = "Name of the Nginx ECS service"
  value       = aws_ecs_service.nginx.name
}

# ============================================================================
# LOAD BALANCER OUTPUTS
# ============================================================================

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "application_url" {
  description = "URL to access the application"
  value       = var.alb_enable_https ? "https://${aws_lb.main.dns_name}" : "http://${aws_lb.main.dns_name}"
}

# ============================================================================
# S3 OUTPUTS
# ============================================================================

output "s3_documents_bucket_name" {
  description = "Name of the S3 bucket for document storage"
  value       = aws_s3_bucket.documents.id
}

output "s3_documents_bucket_arn" {
  description = "ARN of the S3 bucket for document storage"
  value       = aws_s3_bucket.documents.arn
}

# ============================================================================
# DATABASE OUTPUTS
# ============================================================================

output "rds_endpoint" {
  description = "RDS instance endpoint (if RDS is enabled)"
  value       = var.use_rds ? aws_db_instance.main[0].endpoint : null
}

output "rds_database_url" {
  description = "RDS database connection URL (if RDS is enabled)"
  value       = var.use_rds ? "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main[0].endpoint}/${var.db_name}" : null
  sensitive   = true
}

# ============================================================================
# NETWORKING OUTPUTS
# ============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = local.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = local.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = local.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = local.private_subnet_ids
}

# ============================================================================
# BEDROCK OUTPUTS
# ============================================================================

output "bedrock_model_id" {
  description = "Bedrock model ID being used"
  value       = var.bedrock_model_id
}

output "bedrock_region" {
  description = "Bedrock region"
  value       = var.bedrock_region
}

