# DB Subnet Group
resource "aws_db_subnet_group" "db_subnet_group" {
  name        = var.db_subnet_group_name
  description = var.db_subnet_group_description
  subnet_ids  = var.subnet_ids

  tags = var.tags
}

# RDS Instance
resource "aws_db_instance" "db_instance" {
  identifier              = var.db_identifier
  allocated_storage       = var.allocated_storage
  storage_type            = var.storage_type
  engine                  = var.engine
  engine_version          = var.engine_version
  instance_class          = var.instance_class
  username                = var.username
  password                = var.password
  db_name                 = var.db_name
  publicly_accessible     = var.publicly_accessible
  backup_retention_period = var.backup_retention_period
  db_subnet_group_name    = aws_db_subnet_group.db_subnet_group.name
  vpc_security_group_ids  = var.vpc_security_group_ids
  skip_final_snapshot     = var.skip_final_snapshot
  deletion_protection     = var.deletion_protection
  snapshot_identifier     = var.snapshot_identifier

  lifecycle {
    ignore_changes = [username, password]
  }

  tags = merge(var.tags, { Name = var.db_identifier })
}
