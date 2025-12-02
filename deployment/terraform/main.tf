# ============================================================================
# MAIN TERRAFORM CONFIGURATION
# ============================================================================
# This file configures the Terraform provider for AWS GovCloud and sets up
# the basic configuration for deploying the Document Management System.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Optional: Configure remote state backend (S3, DynamoDB for locking)
  # Uncomment and configure for team collaboration
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "document-gateway/terraform.tfstate"
  #   region         = "us-gov-west-1"
  #   dynamodb_table = "terraform-state-lock"
  #   encrypt        = true
  # }
}

# ============================================================================
# AWS PROVIDER CONFIGURATION
# ============================================================================
# Configure AWS provider for GovCloud region
# GovCloud regions: us-gov-east-1, us-gov-west-1

provider "aws" {
  region = var.aws_region

  # GovCloud endpoints (automatically handled, but can be explicit)
  # endpoints {
  #   ecr      = "https://ecr.us-gov-west-1.amazonaws.com"
  #   ecs      = "https://ecs.us-gov-west-1.amazonaws.com"
  #   s3       = "https://s3.us-gov-west-1.amazonaws.com"
  #   bedrock  = "https://bedrock.us-gov-west-1.amazonaws.com"
  # }

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Application = "Document-Gateway"
    }
  }
}

# ============================================================================
# DATA SOURCES
# ============================================================================
# Fetch current AWS account and region information

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# Get availability zones for the region
data "aws_availability_zones" "available" {
  state = "available"
}

# Get latest Amazon Linux 2 ECS-optimized AMI for Fargate
data "aws_ami" "ecs_optimized" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-ecs-hvm-*-x86_64-ebs"]
  }
}

