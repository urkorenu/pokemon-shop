# Output the ID of the launch template
output "launch_template_id" {
  value = aws_launch_template.app.id
}

# Output the name of the Auto Scaling group
output "asg_name" {
  value = aws_autoscaling_group.asg.name
}