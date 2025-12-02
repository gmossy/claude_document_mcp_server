# ============================================================================
# ECR REPOSITORIES - TEST ONLY
# ============================================================================
# This creates only ECR repositories, no networking or other resources

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "document-gateway"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "test"
}

variable "ecr_image_retention_count" {
  description = "Number of images to retain"
  type        = number
  default     = 10
}

# ECR Repository: API
resource "aws_ecr_repository" "api" {
  name                 = "${var.project_name}-${var.environment}-api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Service = "api"
    Test    = "ecr-only"
  }
}

# ECR Repository: Nginx
resource "aws_ecr_repository" "nginx" {
  name                 = "${var.project_name}-${var.environment}-nginx"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Service = "nginx"
    Test    = "ecr-only"
  }
}

# ECR Repository: Frontend
resource "aws_ecr_repository" "frontend" {
  name                 = "${var.project_name}-${var.environment}-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Service = "frontend"
    Test    = "ecr-only"
  }
}

# Lifecycle Policies
resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last ${var.ecr_image_retention_count} images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = var.ecr_image_retention_count
      }
      action = {
        type = "expire"
      }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "nginx" {
  repository = aws_ecr_repository.nginx.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last ${var.ecr_image_retention_count} images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = var.ecr_image_retention_count
      }
      action = {
        type = "expire"
      }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "frontend" {
  repository = aws_ecr_repository.frontend.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last ${var.ecr_image_retention_count} images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = var.ecr_image_retention_count
      }
      action = {
        type = "expire"
      }
    }]
  })
}

