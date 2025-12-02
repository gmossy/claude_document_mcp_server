# ============================================================================
# ELASTIC CONTAINER SERVICE (ECS) CONFIGURATION
# ============================================================================
# ECS cluster, task definitions, and services for running containers on Fargate.

# ============================================================================
# ECS CLUSTER
# ============================================================================

resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cluster"
  }
}

# ============================================================================
# CLOUDWATCH LOG GROUPS
# ============================================================================

resource "aws_cloudwatch_log_group" "api" {
  count             = var.enable_cloudwatch_logs ? 1 : 0
  name              = "/ecs/${var.project_name}-${var.environment}-api"
  retention_in_days = var.cloudwatch_retention_days

  tags = {
    Name = "${var.project_name}-${var.environment}-api-logs"
  }
}

resource "aws_cloudwatch_log_group" "nginx" {
  count             = var.enable_cloudwatch_logs ? 1 : 0
  name              = "/ecs/${var.project_name}-${var.environment}-nginx"
  retention_in_days = var.cloudwatch_retention_days

  tags = {
    Name = "${var.project_name}-${var.environment}-nginx-logs"
  }
}

# ============================================================================
# TASK DEFINITION: API
# ============================================================================

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-${var.environment}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.id

  container_definitions = jsonencode([
    {
      name  = "api"
      image = "${aws_ecr_repository.api.repository_url}:${var.ecr_image_tag}"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "DATABASE_URL"
          value = var.use_rds ? "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main[0].endpoint}/${var.db_name}" : "sqlite:////data/documents.db"
        },
        {
          name  = "STORAGE_DIR"
          value = "/data/document_storage"
        },
        {
          name  = "API_VERSION"
          value = var.api_version
        },
        {
          name  = "LOG_LEVEL"
          value = var.log_level
        },
        {
          name  = "ALLOW_ORIGINS"
          value = jsonencode(var.allowed_origins)
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "S3_BUCKET_NAME"
          value = aws_s3_bucket.documents.id
        },
        {
          name  = "BEDROCK_MODEL_ID"
          value = var.bedrock_model_id
        },
        {
          name  = "BEDROCK_REGION"
          value = var.bedrock_region
        }
      ]

      logConfiguration = var.enable_cloudwatch_logs ? {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api[0].name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      } : null

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz').read()\""]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      essential = true
    }
  ])

  tags = {
    Name = "${var.project_name}-${var.environment}-api-task"
  }
}

# ============================================================================
# TASK DEFINITION: NGINX
# ============================================================================

resource "aws_ecs_task_definition" "nginx" {
  family                   = "${var.project_name}-${var.environment}-nginx"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.nginx_cpu
  memory                   = var.nginx_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "nginx"
      image = "${aws_ecr_repository.nginx.repository_url}:${var.ecr_image_tag}"

      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "API_HOST"
          value = "localhost"
        },
        {
          name  = "API_PORT"
          value = "8000"
        }
      ]

      logConfiguration = var.enable_cloudwatch_logs ? {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.nginx[0].name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      } : null

      healthCheck = {
        command     = ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:80/healthz || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 10
      }

      essential = true
    }
  ])

  tags = {
    Name = "${var.project_name}-${var.environment}-nginx-task"
  }
}

# ============================================================================
# ECS SERVICE: API
# ============================================================================

resource "aws_ecs_service" "api" {
  name            = "${var.project_name}-${var.environment}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = local.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  # Service discovery (optional, for internal communication)
  # service_registries {
  #   registry_arn = aws_service_discovery_service.api.arn
  # }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  depends_on = [
    aws_lb_listener.nginx_http,
    aws_lb_listener.nginx_https
  ]

  tags = {
    Name = "${var.project_name}-${var.environment}-api-service"
  }
}

# ============================================================================
# ECS SERVICE: NGINX
# ============================================================================

resource "aws_ecs_service" "nginx" {
  name            = "${var.project_name}-${var.environment}-nginx"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.nginx.arn
  desired_count   = var.nginx_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = local.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.nginx.arn
    container_name   = "nginx"
    container_port   = 80
  }

  depends_on = [
    aws_lb_listener.nginx_http,
    aws_lb_listener.nginx_https
  ]

  tags = {
    Name = "${var.project_name}-${var.environment}-nginx-service"
  }
}

