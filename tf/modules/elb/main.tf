# Application Load Balancer (ALB)
resource "aws_lb" "app_lb" {
  # Name of the load balancer
  name               = var.lb_name
  # Whether the load balancer is internal
  internal           = var.internal
  # Type of the load balancer
  load_balancer_type = "application"
  # Security groups associated with the load balancer
  security_groups    = var.security_groups
  # Subnets associated with the load balancer
  subnets            = var.subnets
  # Idle timeout for the load balancer
  idle_timeout       = var.idle_timeout

  # Tags to assign to the load balancer
  tags = merge(var.tags, { Name = var.lb_name })
}

# Fetch an ACM certificate
data "aws_acm_certificate" "app_cert" {
  # Domain name for the ACM certificate
  domain   = var.acm_certificate_domain
  # Statuses to filter the ACM certificates
  statuses = ["ISSUED"]
}

# Target Group
resource "aws_lb_target_group" "app_target_group" {
  # Name of the target group
  name        = var.target_group_name
  # Port on which the target group is listening
  port        = var.target_port
  # Protocol used by the target group
  protocol    = var.target_protocol
  # VPC ID associated with the target group
  vpc_id      = var.vpc_id
  # Type of targets in the target group
  target_type = var.target_type

  # Health check configuration for the target group
  health_check {
    # Whether health checks are enabled
    enabled             = var.health_check_enabled
    # Path for the health check
    path                = var.health_check_path
    # Port for the health check
    port                = var.health_check_port
    # Protocol for the health check
    protocol            = var.health_check_protocol
    # Matcher for the health check
    matcher             = var.health_check_matcher
    # Interval between health checks
    interval            = var.health_check_interval
    # Timeout for the health check
    timeout             = var.health_check_timeout
    # Number of successful checks before considering the target healthy
    healthy_threshold   = var.health_check_healthy_threshold
    # Number of failed checks before considering the target unhealthy
    unhealthy_threshold = var.health_check_unhealthy_threshold
  }

  # Tags to assign to the target group
  tags = merge(var.tags, { Name = var.target_group_name })
}

# HTTPS Listener
resource "aws_lb_listener" "https_listener" {
  # ARN of the load balancer to attach the listener to
  load_balancer_arn = aws_lb.app_lb.arn
  # Port on which the listener is listening
  port              = var.listener_port
  # Protocol used by the listener
  protocol          = var.listener_protocol
  # SSL policy for the listener
  ssl_policy        = var.ssl_policy
  # ARN of the ACM certificate for the listener
  certificate_arn   = data.aws_acm_certificate.app_cert.arn

  # Default action for the listener
  default_action {
    # Type of action (forwarding to target group)
    type             = "forward"
    # ARN of the target group to forward requests to
    target_group_arn = aws_lb_target_group.app_target_group.arn
  }
}