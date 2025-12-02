# ============================================================================
# TERRAFORM VARIABLES
# ============================================================================
# Define all input variables for the Terraform configuration.
# These can be set via terraform.tfvars, environment variables, or CLI.

# ============================================================================
# AWS CONFIGURATION
# ============================================================================

variable "aws_region" {
  description = "AWS GovCloud region to deploy resources"
  type        = string
  default     = "us-gov-west-1"
  validation {
    condition = contains([
      "us-gov-east-1",
      "us-gov-west-1"
    ], var.aws_region)
    error_message = "Must be a valid AWS GovCloud region."
  }
}

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "document-gateway"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# ============================================================================
# NETWORKING CONFIGURATION
# ============================================================================

variable "use_existing_vpc" {
  description = "Use an existing VPC instead of creating a new one"
  type        = bool
  default     = false
}

variable "existing_vpc_id" {
  description = "ID of existing VPC to use (required if use_existing_vpc is true)"
  type        = string
  default     = ""
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC (only used if creating new VPC)"
  type        = string
  default     = "10.0.0.0/16"
}

variable "existing_public_subnet_ids" {
  description = "List of existing public subnet IDs (required if use_existing_vpc is true)"
  type        = list(string)
  default     = []
}

variable "existing_private_subnet_ids" {
  description = "List of existing private subnet IDs (required if use_existing_vpc is true)"
  type        = list(string)
  default     = []
}

variable "existing_database_subnet_ids" {
  description = "List of existing database subnet IDs for RDS (optional, will use private subnets if not provided)"
  type        = list(string)
  default     = []
}

variable "existing_internet_gateway_id" {
  description = "ID of existing Internet Gateway (optional, will be detected automatically)"
  type        = string
  default     = ""
}

variable "existing_nat_gateway_id" {
  description = "ID of existing NAT Gateway (optional, will create one if not provided and enable_nat_gateway is true)"
  type        = string
  default     = ""
}

variable "availability_zones" {
  description = "List of availability zones to use (leave empty to use all available, only used if creating new VPC)"
  type        = list(string)
  default     = []
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets (required for ECS tasks to pull images). Only used if creating new VPC or if existing_nat_gateway_id is not provided."
  type        = bool
  default     = true
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for AWS services (reduces NAT Gateway costs)"
  type        = bool
  default     = true
}

# ============================================================================
# ECR CONFIGURATION
# ============================================================================

variable "ecr_image_tag" {
  description = "Docker image tag to deploy (default: latest)"
  type        = string
  default     = "latest"
}

variable "ecr_image_retention_count" {
  description = "Number of images to retain in ECR repositories"
  type        = number
  default     = 10
}

# ============================================================================
# ECS CONFIGURATION
# ============================================================================

variable "api_cpu" {
  description = "CPU units for API container (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "Memory for API container in MB"
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "Desired number of API tasks"
  type        = number
  default     = 2
}

variable "nginx_cpu" {
  description = "CPU units for Nginx container (1024 = 1 vCPU)"
  type        = number
  default     = 256
}

variable "nginx_memory" {
  description = "Memory for Nginx container in MB"
  type        = number
  default     = 512
}

variable "nginx_desired_count" {
  description = "Desired number of Nginx tasks"
  type        = number
  default     = 2
}

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

variable "api_version" {
  description = "API version string"
  type        = string
  default     = "0.1.0"
}

variable "log_level" {
  description = "Application log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
  type        = string
  default     = "INFO"
}

variable "allowed_origins" {
  description = "List of allowed CORS origins"
  type        = list(string)
  default     = ["*"]
}

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

variable "use_rds" {
  description = "Use RDS PostgreSQL instead of SQLite (recommended for production)"
  type        = bool
  default     = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "RDS database name"
  type        = string
  default     = "documentgateway"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

# ============================================================================
# S3 CONFIGURATION
# ============================================================================

variable "s3_enable_versioning" {
  description = "Enable versioning on S3 buckets"
  type        = bool
  default     = true
}

variable "s3_enable_encryption" {
  description = "Enable encryption on S3 buckets"
  type        = bool
  default     = true
}

variable "s3_lifecycle_days" {
  description = "Days before moving objects to Glacier (0 to disable)"
  type        = number
  default     = 90
}

# ============================================================================
# BEDROCK CONFIGURATION
# ============================================================================

variable "bedrock_model_id" {
  description = "Bedrock model ID to use (e.g., anthropic.claude-v2)"
  type        = string
  default     = "anthropic.claude-v2"
}

variable "bedrock_region" {
  description = "Bedrock region (may differ from main region)"
  type        = string
  default     = "us-gov-west-1"
}

# ============================================================================
# LOAD BALANCER CONFIGURATION
# ============================================================================

variable "alb_certificate_arn" {
  description = "ARN of SSL certificate for HTTPS (ACM or imported)"
  type        = string
  default     = ""
}

variable "alb_enable_https" {
  description = "Enable HTTPS listener on ALB"
  type        = bool
  default     = false
}

variable "alb_idle_timeout" {
  description = "ALB idle timeout in seconds"
  type        = number
  default     = 60
}

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Restrict in production!
}

variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch Logs for containers"
  type        = bool
  default     = true
}

variable "cloudwatch_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 30
}

