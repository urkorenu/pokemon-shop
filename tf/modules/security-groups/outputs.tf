# Output the ID of the NAT and Bastion Security Group
output "nat_bastion_sg_id" {
  value = aws_security_group.nat_bastion_sg.id
}

# Output the ID of the Application Security Group
output "app_sg_id" {
  value = aws_security_group.app_sg.id
}

# Output the ID of the ELB Security Group
output "elb_sg_id" {
  value = aws_security_group.elb_sg.id
}

# Output the ID of the RDS Security Group
output "rds_sg_id" {
  value = aws_security_group.rds_sg.id
}

# Output the ID of the Redis Security Group
output "cache_sg_id" {
  value = aws_security_group.cache_sg.id
}