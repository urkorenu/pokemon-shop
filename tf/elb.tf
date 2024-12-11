resource "aws_lb" "app_lb" {
  name               = "app-load-balancer"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.elb_sg.id]
  subnets            = [aws_subnet.public_zone1.id, aws_subnet.public_zone2.id]

  tags = {
    Name = "${local.env}-app-lb"
  }
}

data "aws_acm_certificate" "app_cert" {
  domain   = "pika-card.store"
  statuses = ["ISSUED"]
}

resource "aws_lb_target_group" "app_target_group" {
  name        = "app-target-group"
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 2
  }

  tags = {
    Name = "${local.env}-app-target-group"
  }
}

resource "aws_lb_listener" "https_listener" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = data.aws_acm_certificate.app_cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_target_group.arn
  }
}

resource "aws_lb_target_group_attachment" "app_attachment" {
  target_group_arn = aws_lb_target_group.app_target_group.arn
  target_id        = aws_instance.app_instance.id
  port             = 5000
}
