# ============================================================================
# APPLICATION LOAD BALANCER (ALB) CONFIGURATION
# ============================================================================
# ALB distributes incoming traffic across ECS tasks.

# ============================================================================
# APPLICATION LOAD BALANCER
# ============================================================================

resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = local.public_subnet_ids

  enable_deletion_protection = var.environment == "prod" ? true : false
  enable_http2               = true
  idle_timeout               = var.alb_idle_timeout

  tags = {
    Name = "${var.project_name}-${var.environment}-alb"
  }
}

# ============================================================================
# TARGET GROUPS
# ============================================================================

# Target group for API service
resource "aws_lb_target_group" "api" {
  name        = "${var.project_name}-${var.environment}-api-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = local.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/healthz"
    protocol            = "HTTP"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name = "${var.project_name}-${var.environment}-api-tg"
  }
}

# Target group for Nginx service
resource "aws_lb_target_group" "nginx" {
  name        = "${var.project_name}-${var.environment}-nginx-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = local.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/healthz"
    protocol            = "HTTP"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name = "${var.project_name}-${var.environment}-nginx-tg"
  }
}

# ============================================================================
# LOAD BALANCER LISTENERS
# ============================================================================

# HTTP listener (redirects to HTTPS if enabled)
resource "aws_lb_listener" "nginx_http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = var.alb_enable_https ? "redirect" : "forward"

    dynamic "redirect" {
      for_each = var.alb_enable_https ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    dynamic "forward" {
      for_each = var.alb_enable_https ? [] : [1]
      content {
        target_group {
          arn = aws_lb_target_group.nginx.arn
        }
      }
    }
  }
}

# HTTPS listener (if certificate provided)
resource "aws_lb_listener" "nginx_https" {
  count             = var.alb_enable_https && var.alb_certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn  = var.alb_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.nginx.arn
  }
}

