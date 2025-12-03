# PostgreSQL Container Deployment Guide

This guide explains how to deploy PostgreSQL as a Docker container in ECS Fargate instead of using AWS RDS.

## Table of Contents

- [Overview](#overview)
- [PostgreSQL Container vs RDS](#postgresql-container-vs-rds)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Terraform Configuration](#terraform-configuration)
- [Deployment Steps](#deployment-steps)
- [Service Discovery](#service-discovery)
- [Connecting Applications](#connecting-applications)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)
- [Cost Comparison](#cost-comparison)

## Overview

Instead of using AWS RDS (managed PostgreSQL service), you can deploy PostgreSQL as a containerized service in ECS Fargate. This approach provides:

- **Lower Cost**: No RDS instance charges, only ECS + EFS costs
- **More Control**: Full control over PostgreSQL configuration
- **Easier Local Development**: Same container image for dev and prod
- **Flexibility**: Easy to customize and extend

## PostgreSQL Container vs RDS

| Feature | PostgreSQL Container | AWS RDS |
|---------|----------------------|---------|
| **Cost** | Lower (ECS + EFS only) | Higher (RDS pricing) |
| **Backups** | Manual (you manage) | Automated |
| **High Availability** | Manual setup required | Multi-AZ support |
| **Scaling** | Manual | Automated read replicas |
| **Maintenance** | You handle updates | AWS manages |
| **Control** | Full control | Limited |
| **Setup Complexity** | Higher (EFS, service discovery) | Lower |

### When to Use PostgreSQL Container

✅ **Use PostgreSQL Container if:**
- You want to minimize costs
- You need full control over PostgreSQL configuration
- You can handle backups and maintenance
- You're comfortable with container orchestration

❌ **Use RDS if:**
- You need automated backups and point-in-time recovery
- You require high availability with automatic failover
- You want managed maintenance and updates
- You prefer less operational overhead

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ECS Fargate Cluster                   │
│                                                           │
│  ┌──────────────────┐         ┌──────────────────┐     │
│  │  API Container   │────────▶│ PostgreSQL       │     │
│  │  (FastAPI)       │         │ Container        │     │
│  └──────────────────┘         └──────────────────┘     │
│                                    │                     │
│                                    ▼                     │
│                            ┌──────────────┐              │
│                            │  EFS Volume │              │
│                            │  (Persistent)│              │
│                            └──────────────┘              │
└─────────────────────────────────────────────────────────┘
```

**Key Components:**
- **PostgreSQL Container**: Official `postgres:15-alpine` image
- **EFS (Elastic File System)**: Persistent storage for database files
- **Service Discovery**: Internal DNS for service-to-service communication
- **Security Groups**: Network isolation and access control

## Prerequisites

1. Terraform >= 1.5.0
2. AWS CLI configured
3. Docker installed locally (for building images)
4. Existing VPC with private subnets (or Terraform will create them)

## Terraform Configuration

### 1. EFS File System (`efs.tf`)

Create `deployment/terraform/efs.tf`:

```hcl
# ============================================================================
# ELASTIC FILE SYSTEM (EFS) FOR POSTGRESQL DATA
# ============================================================================
# EFS provides persistent storage for PostgreSQL database files

# ============================================================================
# EFS FILE SYSTEM
# ============================================================================

resource "aws_efs_file_system" "postgres_data" {
  creation_token = "${var.project_name}-${var.environment}-postgres-data"
  
  performance_mode = "generalPurpose"
  throughput_mode  = "provisioned"
  provisioned_throughput_in_mibps = 100

  encrypted = true

  tags = {
    Name = "${var.project_name}-${var.environment}-postgres-data"
  }
}

# ============================================================================
# EFS MOUNT TARGETS
# ============================================================================

resource "aws_efs_mount_target" "postgres_data" {
  count           = length(local.private_subnet_ids)
  file_system_id  = aws_efs_file_system.postgres_data.id
  subnet_id       = local.private_subnet_ids[count.index]
  security_groups = [aws_security_group.efs.id]
}

# ============================================================================
# EFS ACCESS POINT
# ============================================================================

resource "aws_efs_access_point" "postgres_data" {
  file_system_id = aws_efs_file_system.postgres_data.id

  posix_user {
    gid = 999  # postgres group
    uid = 999  # postgres user
  }

  root_directory {
    path = "/postgres"
    creation_info {
      owner_gid   = 999
      owner_uid   = 999
      permissions = "755"
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-postgres-access"
  }
}

# ============================================================================
# SECURITY GROUP FOR EFS
# ============================================================================

resource "aws_security_group" "efs" {
  name        = "${var.project_name}-${var.environment}-efs-sg"
  description = "Security group for EFS mount targets"
  vpc_id      = local.vpc_id

  ingress {
    description     = "NFS from ECS tasks"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-efs-sg"
  }
}
```

### 2. Service Discovery (`service_discovery.tf`)

Create `deployment/terraform/service_discovery.tf`:

```hcl
# ============================================================================
# SERVICE DISCOVERY FOR INTERNAL DNS
# ============================================================================
# Enables containers to discover PostgreSQL by hostname

# Service discovery namespace
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "${var.project_name}.local"
  description = "Service discovery namespace for ${var.project_name}"
  vpc         = local.vpc_id
}

# Service discovery service for PostgreSQL
resource "aws_service_discovery_service" "postgres" {
  name = "postgres"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }
  }

  health_check_grace_period_seconds = 30
}
```

### 3. PostgreSQL Task Definition (`ecs.tf` - Add to existing file)

Add to `deployment/terraform/ecs.tf`:

```hcl
# ============================================================================
# CLOUDWATCH LOG GROUP: POSTGRESQL
# ============================================================================

resource "aws_cloudwatch_log_group" "postgres" {
  count             = var.enable_cloudwatch_logs ? 1 : 0
  name              = "/ecs/${var.project_name}-${var.environment}-postgres"
  retention_in_days = var.cloudwatch_retention_days

  tags = {
    Name = "${var.project_name}-${var.environment}-postgres-logs"
  }
}

# ============================================================================
# TASK DEFINITION: POSTGRESQL
# ============================================================================

resource "aws_ecs_task_definition" "postgres" {
  family                   = "${var.project_name}-${var.environment}-postgres"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.postgres_cpu
  memory                   = var.postgres_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  # Mount EFS for persistent storage
  volume {
    name = "postgres-data"
    efs_volume_configuration {
      file_system_id          = aws_efs_file_system.postgres_data.id
      root_directory          = "/"
      transit_encryption      = "ENABLED"
      transit_encryption_port = 2049
      authorization_config {
        access_point_id = aws_efs_access_point.postgres_data.id
        iam             = "ENABLED"
      }
    }
  }

  container_definitions = jsonencode([
    {
      name  = "postgres"
      image = "postgres:15-alpine"  # Official PostgreSQL image

      environment = [
        {
          name  = "POSTGRES_DB"
          value = var.db_name
        },
        {
          name  = "POSTGRES_USER"
          value = var.db_username
        },
        {
          name  = "POSTGRES_PASSWORD"
          value = var.db_password
        },
        {
          name  = "PGDATA"
          value = "/var/lib/postgresql/data/pgdata"
        }
      ]

      portMappings = [
        {
          containerPort = 5432
          protocol      = "tcp"
        }
      ]

      mountPoints = [
        {
          sourceVolume  = "postgres-data"
          containerPath = "/var/lib/postgresql/data"
          readOnly      = false
        }
      ]

      logConfiguration = var.enable_cloudwatch_logs ? {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.postgres[0].name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      } : null

      healthCheck = {
        command     = ["CMD-SHELL", "pg_isready -U ${var.db_username} -d ${var.db_name}"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      essential = true
    }
  ])

  tags = {
    Name = "${var.project_name}-${var.environment}-postgres-task"
  }
}

# ============================================================================
# ECS SERVICE: POSTGRESQL
# ============================================================================

resource "aws_ecs_service" "postgres" {
  name            = "${var.project_name}-${var.environment}-postgres"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.postgres.arn
  desired_count   = 1  # Single instance for PostgreSQL
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = local.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  # Service discovery for internal DNS
  service_registries {
    registry_arn = aws_service_discovery_service.postgres.arn
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-postgres-service"
  }
}
```

### 4. Update API Task Definition

Modify the API task definition in `ecs.tf` to use service discovery:

```hcl
# In aws_ecs_task_definition.api container_definitions
environment = [
  # ... existing vars ...
  {
    name  = "DATABASE_URL"
    value = var.use_rds ? 
      "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main[0].endpoint}/${var.db_name}" : 
      "postgresql://${var.db_username}:${var.db_password}@postgres.${var.project_name}.local:5432/${var.db_name}"
  }
]
```

### 5. Update Security Group

Add PostgreSQL access rule to `networking.tf` in the `aws_security_group.ecs_tasks` resource:

```hcl
# Add to existing ingress rules
ingress {
  description     = "PostgreSQL from API containers"
  from_port       = 5432
  to_port         = 5432
  protocol        = "tcp"
  security_groups = [aws_security_group.ecs_tasks.id]  # Self-reference for same SG
}
```

### 6. IAM Permissions for EFS (`iam.tf`)

Add to `iam.tf`:

```hcl
# Add EFS access to task execution role
resource "aws_iam_role_policy" "ecs_task_execution_efs" {
  name = "${var.project_name}-${var.environment}-ecs-task-execution-efs"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticfilesystem:ClientMount",
          "elasticfilesystem:ClientWrite",
          "elasticfilesystem:ClientRootAccess"
        ]
        Resource = aws_efs_file_system.postgres_data.arn
        Condition = {
          StringEquals = {
            "elasticfilesystem:AccessPointArn" = aws_efs_access_point.postgres_data.arn
          }
        }
      }
    ]
  })
}
```

### 7. Variables (`variables.tf`)

Add to `variables.tf`:

```hcl
# POSTGRESQL CONTAINER CONFIGURATION
variable "postgres_cpu" {
  description = "CPU units for PostgreSQL container (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "postgres_memory" {
  description = "Memory for PostgreSQL container in MB"
  type        = number
  default     = 1024
}
```

### 8. Outputs (`outputs.tf`)

Add to `outputs.tf`:

```hcl
# POSTGRESQL CONTAINER OUTPUTS
output "postgres_service_name" {
  description = "Name of the PostgreSQL ECS service"
  value       = aws_ecs_service.postgres.name
}

output "efs_postgres_file_system_id" {
  description = "EFS file system ID for PostgreSQL data"
  value       = aws_efs_file_system.postgres_data.id
}

output "postgres_endpoint" {
  description = "PostgreSQL connection endpoint (via service discovery)"
  value       = "postgres.${var.project_name}.local:5432"
}
```

## Deployment Steps

### Step 1: Configure Terraform Variables

Ensure `terraform.tfvars` has:

```hcl
use_rds = false  # Set to false to use container instead
db_name = "documentgateway"
db_username = "admin"
db_password = "YOUR_SECURE_PASSWORD"  # Use AWS Secrets Manager in production
postgres_cpu = 512
postgres_memory = 1024
```

### Step 2: Initialize and Plan

```bash
cd deployment/terraform
terraform init
terraform plan
```

Review the plan to ensure:
- EFS file system will be created
- Service discovery namespace will be created
- PostgreSQL task definition will be created
- Security groups allow PostgreSQL access

### Step 3: Apply Terraform

```bash
terraform apply
```

This will create:
- EFS file system and mount targets
- Service discovery namespace and service
- PostgreSQL ECS task definition
- PostgreSQL ECS service
- Required IAM permissions

### Step 4: Verify Deployment

```bash
# Check PostgreSQL service status
aws ecs describe-services \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --services $(terraform output -raw postgres_service_name) \
  --region us-gov-west-1

# Check EFS mount targets
aws efs describe-mount-targets \
  --file-system-id $(terraform output -raw efs_postgres_file_system_id) \
  --region us-gov-west-1
```

### Step 5: Test Connection

From an API container or bastion host:

```bash
# Get PostgreSQL endpoint
POSTGRES_ENDPOINT=$(terraform output -raw postgres_endpoint)

# Test connection (requires psql client)
psql -h postgres.document-gateway.local -U admin -d documentgateway
```

## Service Discovery

Service discovery enables containers to find PostgreSQL by hostname instead of IP address.

### How It Works

1. **Namespace**: Creates a private DNS namespace (e.g., `document-gateway.local`)
2. **Service**: Registers PostgreSQL service as `postgres.document-gateway.local`
3. **DNS Resolution**: Containers in the same VPC can resolve the hostname
4. **Automatic Updates**: DNS automatically updates when the service IP changes

### Connection String Format

```
postgresql://username:password@postgres.document-gateway.local:5432/dbname
```

Replace `document-gateway` with your `project_name`.

## Connecting Applications

### Update API Container

The API container should use the service discovery endpoint:

```python
# In your application config
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:password@postgres.document-gateway.local:5432/documentgateway"
)
```

### Environment Variables

Set in the API task definition:

```hcl
{
  name  = "DATABASE_URL"
  value = "postgresql://${var.db_username}:${var.db_password}@postgres.${var.project_name}.local:5432/${var.db_name}"
}
```

## Backup and Recovery

### Manual Backup

```bash
# Connect to PostgreSQL container
aws ecs execute-command \
  --cluster <cluster-name> \
  --task <task-id> \
  --container postgres \
  --command "pg_dump -U admin documentgateway" \
  --interactive

# Or use AWS Systems Manager Session Manager
```

### Automated Backup Script

Create `scripts/backup-postgres.sh`:

```bash
#!/bin/bash
set -e

CLUSTER_NAME="document-gateway-test-cluster"
SERVICE_NAME="document-gateway-test-postgres"
S3_BUCKET="your-backup-bucket"
DATE=$(date +%Y%m%d_%H%M%S)

# Get running task
TASK_ARN=$(aws ecs list-tasks \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --query 'taskArns[0]' \
  --output text)

# Execute backup
aws ecs execute-command \
  --cluster $CLUSTER_NAME \
  --task $TASK_ARN \
  --container postgres \
  --command "pg_dump -U admin documentgateway" \
  --interactive | \
  aws s3 cp - s3://$S3_BUCKET/postgres-backup-$DATE.sql

echo "Backup completed: s3://$S3_BUCKET/postgres-backup-$DATE.sql"
```

### Restore from Backup

```bash
# Download backup from S3
aws s3 cp s3://your-backup-bucket/postgres-backup-20240101_120000.sql - | \
  psql -h postgres.document-gateway.local -U admin -d documentgateway
```

## Troubleshooting

### PostgreSQL Container Won't Start

**Check logs:**
```bash
aws logs tail /ecs/document-gateway-test-postgres --follow
```

**Common issues:**
- EFS mount target not accessible (check security groups)
- Insufficient memory (increase `postgres_memory`)
- Database initialization failed (check CloudWatch logs)

### Cannot Connect from API Container

**Verify service discovery:**
```bash
# From API container
nslookup postgres.document-gateway.local
```

**Check security groups:**
- ECS tasks security group must allow port 5432
- Both containers must be in the same security group

**Test connection:**
```bash
# From API container
psql -h postgres.document-gateway.local -U admin -d documentgateway
```

### EFS Mount Issues

**Check mount targets:**
```bash
aws efs describe-mount-targets \
  --file-system-id <efs-id>
```

**Verify security group:**
- EFS security group must allow NFS (port 2049) from ECS tasks

**Check IAM permissions:**
- Task execution role must have EFS permissions

### Performance Issues

**EFS Performance:**
- Use `provisioned` throughput mode for better performance
- Consider increasing `provisioned_throughput_in_mibps`
- Use `maxIO` performance mode for high I/O workloads

**Container Resources:**
- Increase CPU/memory if database is slow
- Monitor CloudWatch metrics

## Cost Comparison

### PostgreSQL Container (ECS + EFS)

**Monthly Costs (estimated):**
- ECS Fargate: ~$15-30 (512 CPU, 1GB RAM, 24/7)
- EFS Storage: ~$0.30/GB/month
- EFS Throughput: ~$6.00/month (100 MiB/s provisioned)
- Data Transfer: ~$0.01/GB

**Total: ~$25-40/month** (for small workloads)

### RDS PostgreSQL

**Monthly Costs (estimated):**
- db.t3.micro: ~$15/month
- Storage (20GB gp3): ~$2/month
- Backup storage: ~$0.095/GB/month

**Total: ~$20-25/month** (for small workloads)

**Note:** RDS becomes more expensive with larger instances, while ECS scales more linearly.

## Migration from RDS to Container

If you're currently using RDS and want to migrate:

1. **Export data from RDS:**
   ```bash
   pg_dump -h <rds-endpoint> -U admin documentgateway > backup.sql
   ```

2. **Deploy PostgreSQL container** (using this guide)

3. **Import data:**
   ```bash
   psql -h postgres.document-gateway.local -U admin -d documentgateway < backup.sql
   ```

4. **Update application** to use new endpoint

5. **Verify and switch traffic**

6. **Decommission RDS** after verification

## Best Practices

1. **Use AWS Secrets Manager** for database passwords
2. **Enable CloudWatch Logs** for monitoring
3. **Set up automated backups** (daily recommended)
4. **Monitor EFS storage** usage
5. **Use service discovery** for internal communication
6. **Enable EFS encryption** (already configured)
7. **Regular security updates** for PostgreSQL image
8. **Test disaster recovery** procedures

## Additional Resources

- [AWS EFS Documentation](https://docs.aws.amazon.com/efs/)
- [ECS Service Discovery](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-discovery.html)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [EFS Performance Modes](https://docs.aws.amazon.com/efs/latest/ug/performance.html)

## Support

For issues or questions:
1. Check CloudWatch Logs
2. Review ECS service events
3. Verify security group rules
4. Test network connectivity
5. Review this troubleshooting guide

