output "rds_endpoint" {
  value = aws_db_instance.db_instance.endpoint
}

output "db_name" {
  value = aws_db_instance.db_instance.db_name
}


output "db_instance_id" {
  value = aws_db_instance.db_instance.id
}

output "db_username" {
  value = aws_db_instance.db_instance.username
}

output "db_password" {
  value = aws_db_instance.db_instance.password
}

