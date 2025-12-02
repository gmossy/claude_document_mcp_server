# ============================================================================
# RELATIONAL DATABASE SERVICE (RDS) CONFIGURATION
# ============================================================================
# PostgreSQL database for production use (optional, can use SQLite for dev).

# ============================================================================
# DB SUBNET GROUP
# ============================================================================

resource "aws_db_subnet_group" "main" {
  count      = var.use_rds ? 1 : 0
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = local.database_subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  }
}

# ============================================================================
# RDS PARAMETER GROUP
# ============================================================================

resource "aws_db_parameter_group" "main" {
  count  = var.use_rds ? 1 : 0
  family = "postgres15"
  name   = "${var.project_name}-${var.environment}-db-params"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-db-params"
  }
}

# ============================================================================
# RDS INSTANCE
# ============================================================================

resource "aws_db_instance" "main" {
  count = var.use_rds ? 1 : 0

  identifier     = "${var.project_name}-${var.environment}-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main[0].name
  vpc_security_group_ids = [aws_security_group.rds[0].id]
  parameter_group_name   = aws_db_parameter_group.main[0].name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  skip_final_snapshot       = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${var.project_name}-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null
  deletion_protection        = var.environment == "prod"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true

  tags = {
    Name = "${var.project_name}-${var.environment}-db"
  }
}

