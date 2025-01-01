# Output the ARN of the load balancer
output "lb_arn" {
  value = aws_lb.app_lb.arn
}

# Output the DNS name of the load balancer
output "lb_dns_name" {
  value = aws_lb.app_lb.dns_name
}

# Output the ARN of the target group
output "target_group_arn" {
  value = aws_lb_target_group.app_target_group.arn
}

# Output the zone ID of the load balancer
output "lb_zone_id" {
  value = aws_lb.app_lb.zone_id
}