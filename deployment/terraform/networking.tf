# ============================================================================
# NETWORKING CONFIGURATION
# ============================================================================
# Creates VPC, subnets, security groups, and networking components
# required for ECS Fargate deployment.
# Supports both creating new VPC or using existing VPC.

# ============================================================================
# VPC - Data Source for Existing VPC
# ============================================================================

data "aws_vpc" "existing" {
  count = var.use_existing_vpc ? 1 : 0
  id    = var.existing_vpc_id
}

# ============================================================================
# VPC - Create New VPC
# ============================================================================

resource "aws_vpc" "main" {
  count                = var.use_existing_vpc ? 0 : 1
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

# ============================================================================
# VPC - Local Value for VPC ID
# ============================================================================

locals {
  vpc_id = var.use_existing_vpc ? data.aws_vpc.existing[0].id : aws_vpc.main[0].id
  vpc_cidr_block = var.use_existing_vpc ? data.aws_vpc.existing[0].cidr_block : aws_vpc.main[0].cidr_block
}

# ============================================================================
# INTERNET GATEWAY - Data Source for Existing
# ============================================================================

data "aws_internet_gateway" "existing" {
  count = var.use_existing_vpc && var.existing_internet_gateway_id != "" ? 1 : 0
  internet_gateway_id = var.existing_internet_gateway_id
}

# Auto-detect existing Internet Gateway if not specified
data "aws_internet_gateways" "existing" {
  count = var.use_existing_vpc && var.existing_internet_gateway_id == "" ? 1 : 0
  filter {
    name   = "attachment.vpc-id"
    values = [local.vpc_id]
  }
}

# ============================================================================
# INTERNET GATEWAY - Create New
# ============================================================================

resource "aws_internet_gateway" "main" {
  count  = var.use_existing_vpc ? 0 : 1
  vpc_id = aws_vpc.main[0].id

  tags = {
    Name = "${var.project_name}-${var.environment}-igw"
  }
}

# ============================================================================
# INTERNET GATEWAY - Local Value
# ============================================================================

locals {
  internet_gateway_id = var.use_existing_vpc ? (
    var.existing_internet_gateway_id != "" ? var.existing_internet_gateway_id : (
      length(data.aws_internet_gateways.existing) > 0 && length(data.aws_internet_gateways.existing[0].ids) > 0 ? data.aws_internet_gateways.existing[0].ids[0] : ""
    )
  ) : aws_internet_gateway.main[0].id
}

# ============================================================================
# AVAILABILITY ZONES
# ============================================================================

locals {
  # Use provided AZs or default to available AZs (only for new VPC)
  availability_zones = length(var.availability_zones) > 0 ? var.availability_zones : slice(data.aws_availability_zones.available.names, 0, 2)
}

# ============================================================================
# SUBNETS - Data Sources for Existing Subnets
# ============================================================================

data "aws_subnet" "existing_public" {
  count = var.use_existing_vpc ? length(var.existing_public_subnet_ids) : 0
  id    = var.existing_public_subnet_ids[count.index]
}

data "aws_subnet" "existing_private" {
  count = var.use_existing_vpc ? length(var.existing_private_subnet_ids) : 0
  id    = var.existing_private_subnet_ids[count.index]
}

data "aws_subnet" "existing_database" {
  count = var.use_existing_vpc && var.use_rds && length(var.existing_database_subnet_ids) > 0 ? length(var.existing_database_subnet_ids) : 0
  id    = var.existing_database_subnet_ids[count.index]
}

# ============================================================================
# PUBLIC SUBNETS - Create New
# ============================================================================
# Public subnets for load balancer and NAT gateway

resource "aws_subnet" "public" {
  count             = var.use_existing_vpc ? 0 : length(local.availability_zones)
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = local.availability_zones[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-${var.environment}-public-${count.index + 1}"
    Type = "public"
  }
}

# ============================================================================
# PRIVATE SUBNETS - Create New
# ============================================================================
# Private subnets for ECS tasks (more secure)

resource "aws_subnet" "private" {
  count             = var.use_existing_vpc ? 0 : length(local.availability_zones)
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = local.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-${var.environment}-private-${count.index + 1}"
    Type = "private"
  }
}

# ============================================================================
# DATABASE SUBNETS - Create New (if using RDS)
# ============================================================================

resource "aws_subnet" "database" {
  count             = var.use_existing_vpc || !var.use_rds ? 0 : length(local.availability_zones)
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 20)
  availability_zone = local.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-${var.environment}-database-${count.index + 1}"
    Type = "database"
  }
}

# ============================================================================
# SUBNET - Local Values
# ============================================================================

locals {
  public_subnet_ids = var.use_existing_vpc ? var.existing_public_subnet_ids : aws_subnet.public[*].id
  private_subnet_ids = var.use_existing_vpc ? var.existing_private_subnet_ids : aws_subnet.private[*].id
  database_subnet_ids = var.use_existing_vpc ? (
    length(var.existing_database_subnet_ids) > 0 ? var.existing_database_subnet_ids : var.existing_private_subnet_ids
  ) : (var.use_rds ? aws_subnet.database[*].id : [])
}

# ============================================================================
# ROUTE TABLES
# ============================================================================

# Public route table (only create if not using existing VPC)
resource "aws_route_table" "public" {
  count  = var.use_existing_vpc ? 0 : 1
  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-public-rt"
  }
}

# Public subnet associations (only create if not using existing VPC)
resource "aws_route_table_association" "public" {
  count          = var.use_existing_vpc ? 0 : length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

# ============================================================================
# NAT GATEWAY (for private subnet internet access)
# ============================================================================

# NAT Gateway - Data Source for Existing
data "aws_nat_gateway" "existing" {
  count = var.use_existing_vpc && var.existing_nat_gateway_id != "" ? 1 : 0
  id    = var.existing_nat_gateway_id
}

# Auto-detect existing NAT Gateway if not specified
data "aws_nat_gateways" "existing" {
  count = var.use_existing_vpc && var.existing_nat_gateway_id == "" ? 1 : 0
  filter {
    name   = "vpc-id"
    values = [local.vpc_id]
  }
}

resource "aws_eip" "nat" {
  count  = var.use_existing_vpc || !var.enable_nat_gateway ? 0 : 1
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-${var.environment}-nat-eip"
  }

  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  count         = var.use_existing_vpc || !var.enable_nat_gateway ? 0 : 1
  allocation_id = aws_eip.nat[0].id
  subnet_id     = local.public_subnet_ids[0]

  tags = {
    Name = "${var.project_name}-${var.environment}-nat"
  }

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateway - Local Value
locals {
  nat_gateway_id = var.use_existing_vpc ? (
    var.existing_nat_gateway_id != "" ? var.existing_nat_gateway_id : (
      length(data.aws_nat_gateways.existing) > 0 && length(data.aws_nat_gateways.existing[0].ids) > 0 ? data.aws_nat_gateways.existing[0].ids[0] : ""
    )
  ) : (var.enable_nat_gateway && length(aws_nat_gateway.main) > 0 ? aws_nat_gateway.main[0].id : "")
}

# Private route table (only create if not using existing VPC and NAT is enabled)
resource "aws_route_table" "private" {
  count  = var.use_existing_vpc || !var.enable_nat_gateway || local.nat_gateway_id == "" ? 0 : 1
  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[0].id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-private-rt"
  }
}

# Private subnet associations (only create if not using existing VPC)
resource "aws_route_table_association" "private" {
  count          = var.use_existing_vpc || !var.enable_nat_gateway || local.nat_gateway_id == "" ? 0 : length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[0].id
}

# ============================================================================
# SECURITY GROUPS
# ============================================================================

# Security group for ALB (allows HTTP/HTTPS from internet)
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = local.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-alb-sg"
  }
}

# Security group for ECS tasks (allows traffic from ALB only)
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = local.vpc_id

  ingress {
    description     = "Allow traffic from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description     = "Allow traffic from ALB (Nginx)"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  }
}

# Security group for RDS (if enabled)
resource "aws_security_group" "rds" {
  count       = var.use_rds ? 1 : 0
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = local.vpc_id

  ingress {
    description     = "PostgreSQL from ECS tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-rds-sg"
  }
}

# ============================================================================
# VPC ENDPOINTS (optional, reduces NAT Gateway costs)
# ============================================================================

# ECR API endpoint
resource "aws_vpc_endpoint" "ecr_api" {
  count             = var.enable_vpc_endpoints ? 1 : 0
  vpc_id            = local.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.ecr.api"
  vpc_endpoint_type = "Interface"
  subnet_ids        = local.private_subnet_ids

  security_group_ids = [aws_security_group.vpc_endpoint[0].id]

  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-ecr-api-endpoint"
  }
}

# ECR DKR endpoint
resource "aws_vpc_endpoint" "ecr_dkr" {
  count             = var.enable_vpc_endpoints ? 1 : 0
  vpc_id            = local.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.ecr.dkr"
  vpc_endpoint_type = "Interface"
  subnet_ids        = local.private_subnet_ids

  security_group_ids = [aws_security_group.vpc_endpoint[0].id]

  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-ecr-dkr-endpoint"
  }
}

# S3 Gateway endpoint (free, always recommended)
resource "aws_vpc_endpoint" "s3" {
  count        = var.enable_vpc_endpoints ? 1 : 0
  vpc_id       = local.vpc_id
  service_name = "com.amazonaws.${var.aws_region}.s3"
  route_table_ids = var.use_existing_vpc ? [] : concat(
    length(aws_route_table.public) > 0 ? [aws_route_table.public[0].id] : [],
    length(aws_route_table.private) > 0 ? [aws_route_table.private[0].id] : []
  )

  tags = {
    Name = "${var.project_name}-${var.environment}-s3-endpoint"
  }
}

# CloudWatch Logs endpoint
resource "aws_vpc_endpoint" "logs" {
  count             = var.enable_vpc_endpoints ? 1 : 0
  vpc_id            = local.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.logs"
  vpc_endpoint_type = "Interface"
  subnet_ids        = local.private_subnet_ids

  security_group_ids = [aws_security_group.vpc_endpoint[0].id]

  private_dns_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-logs-endpoint"
  }
}

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoint" {
  count       = var.enable_vpc_endpoints ? 1 : 0
  name        = "${var.project_name}-${var.environment}-vpc-endpoint-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = local.vpc_id

  ingress {
    description     = "HTTPS from ECS tasks"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc-endpoint-sg"
  }
}

