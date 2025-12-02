# ============================================================================
# S3 BUCKET CONFIGURATION
# ============================================================================
# S3 buckets for document storage and other application data.
# Note: In GovCloud, bucket names must be globally unique.

# ============================================================================
# S3 BUCKET: DOCUMENT STORAGE
# ============================================================================

resource "aws_s3_bucket" "documents" {
  bucket = "${var.project_name}-${var.environment}-documents-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-documents"
    Purpose     = "Document storage"
    Environment = var.environment
  }
}

# Enable versioning
resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = var.s3_enable_versioning ? "Enabled" : "Disabled"
  }
}

# Enable encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  count  = var.s3_enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy      = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy (move to Glacier after specified days)
resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  count  = var.s3_lifecycle_days > 0 ? 1 : 0
  bucket = aws_s3_bucket.documents.id

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    transition {
      days          = var.s3_lifecycle_days
      storage_class = "GLACIER"
    }
  }

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# ============================================================================
# S3 BUCKET POLICY
# ============================================================================
# Allow ECS tasks to read/write documents

resource "aws_s3_bucket_policy" "documents" {
  bucket = aws_s3_bucket.documents.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowECSReadWrite"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.ecs_task_execution.arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.documents.arn,
          "${aws_s3_bucket.documents.arn}/*"
        ]
      }
    ]
  })
}

