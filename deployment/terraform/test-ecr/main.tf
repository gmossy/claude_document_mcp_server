terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = "us-gov-west-1"  # Your GovCloud region
  profile = "BAHSSO_419587590216_Admin-419587590216"  # Your AWS profile

  default_tags {
    tags = {
      Project     = "document-gateway"
      Environment = "test"
      ManagedBy   = "Terraform"
      TestRun     = "ecr-only"
    }
  }
}

data "aws_caller_identity" "current" {}

