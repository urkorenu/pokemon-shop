output "lb_arn" {
  value = aws_lb.app_lb.arn
}

output "lb_dns_name" {
  value = aws_lb.app_lb.dns_name
}

output "target_group_arn" {
  value = aws_lb_target_group.app_target_group.arn
}

output "lb_zone_id" {
  value = aws_lb.app_lb.zone_id
}
