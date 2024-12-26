# Application Load Balancer (ALB)
resource "aws_lb" "app_lb" {
  name               = var.lb_name
  internal           = var.internal
  load_balancer_type = "application"
  security_groups    = var.security_groups
  subnets            = var.subnets
  idle_timeout       = var.idle_timeout

  tags = merge(var.tags, { Name = var.lb_name })
}

# Fetch an ACM certificate
data "aws_acm_certificate" "app_cert" {
  domain   = var.acm_certificate_domain
  statuses = ["ISSUED"]
}

# Target Group
resource "aws_lb_target_group" "app_target_group" {
  name        = var.target_group_name
  port        = var.target_port
  protocol    = var.target_protocol
  vpc_id      = var.vpc_id
  target_type = var.target_type

  health_check {
    enabled             = var.health_check_enabled
    path                = var.health_check_path
    port                = var.health_check_port
    protocol            = var.health_check_protocol
    matcher             = var.health_check_matcher
    interval            = var.health_check_interval
    timeout             = var.health_check_timeout
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
  }

  tags = merge(var.tags, { Name = var.target_group_name })
}

# HTTPS Listener
resource "aws_lb_listener" "https_listener" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = var.listener_port
  protocol          = var.listener_protocol
  ssl_policy        = var.ssl_policy
  certificate_arn   = data.aws_acm_certificate.app_cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_target_group.arn
  }
}
