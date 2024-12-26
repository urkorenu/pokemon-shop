output "nat_bastion_sg_id" {
  value = aws_security_group.nat_bastion_sg.id
}

output "app_sg_id" {
  value = aws_security_group.app_sg.id
}

output "elb_sg_id" {
  value = aws_security_group.elb_sg.id
}

output "rds_sg_id" {
  value = aws_security_group.rds_sg.id
}

output "cache_sg_id" {
  value = aws_security_group.cache_sg.id
}
