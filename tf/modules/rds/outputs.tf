# Output the endpoint address of the RDS instance
output "rds_endpoint" {
  value = aws_db_instance.db_instance.address
}

# Output the name of the database
output "db_name" {
  value = aws_db_instance.db_instance.db_name
}

# Output the ID of the RDS instance
output "db_instance_id" {
  value = aws_db_instance.db_instance.id
}

# Output the master username for the RDS instance
output "db_username" {
  value = aws_db_instance.db_instance.username
}

# Output the master password for the RDS instance
output "db_password" {
  value = aws_db_instance.db_instance.password
}