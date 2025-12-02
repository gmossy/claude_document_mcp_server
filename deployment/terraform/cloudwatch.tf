# ============================================================================
# CLOUDWATCH CONFIGURATION
# ============================================================================
# CloudWatch alarms and dashboards for monitoring.

# ============================================================================
# CLOUDWATCH ALARMS: ECS SERVICE
# ============================================================================

# Alarm for high CPU utilization on API service
resource "aws_cloudwatch_metric_alarm" "api_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-api-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This metric monitors API service CPU utilization"
  alarm_actions       = [] # Add SNS topic ARN for notifications

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.api.name
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-api-cpu-high"
  }
}

# Alarm for high memory utilization on API service
resource "aws_cloudwatch_metric_alarm" "api_memory_high" {
  alarm_name          = "${var.project_name}-${var.environment}-api-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This metric monitors API service memory utilization"
  alarm_actions       = []

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.api.name
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-api-memory-high"
  }
}

# Alarm for unhealthy target count
resource "aws_cloudwatch_metric_alarm" "api_unhealthy_targets" {
  alarm_name          = "${var.project_name}-${var.environment}-api-unhealthy-targets"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "This metric monitors unhealthy API targets"
  alarm_actions       = []

  dimensions = {
    TargetGroup  = aws_lb_target_group.api.arn_suffix
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-api-unhealthy-targets"
  }
}

