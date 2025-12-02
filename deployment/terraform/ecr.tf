# ============================================================================
# ELASTIC CONTAINER REGISTRY (ECR) CONFIGURATION
# ============================================================================
# ECR repositories store Docker images for the three services:
# - API (FastAPI backend)
# - Nginx (reverse proxy)
# - Frontend (React application)

# ============================================================================
# ECR REPOSITORY: API
# ============================================================================

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
  }
}

# ============================================================================
# ECR REPOSITORY: NGINX
# ============================================================================

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
  }
}

# ============================================================================
# ECR REPOSITORY: FRONTEND
# ============================================================================

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
  }
}

# ============================================================================
# ECR LIFECYCLE POLICIES
# ============================================================================
# Automatically clean up old images to save storage costs

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

