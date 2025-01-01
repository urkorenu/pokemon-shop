# DB Subnet Group
resource "aws_db_subnet_group" "db_subnet_group" {
  # Name of the DB subnet group
  name        = var.db_subnet_group_name
  # Description of the DB subnet group
  description = var.db_subnet_group_description
  # List of subnet IDs for the DB subnet group
  subnet_ids  = var.subnet_ids

  # Tags to apply to the DB subnet group
  tags = var.tags
}

# RDS Instance
resource "aws_db_instance" "db_instance" {
  # Identifier for the RDS instance
  identifier              = var.db_identifier
  # Allocated storage size (in GB) for the RDS instance
  allocated_storage       = var.allocated_storage
  # Storage type for the RDS instance (e.g., standard, gp2, io1)
  storage_type            = var.storage_type
  # Database engine for the RDS instance (e.g., MySQL, PostgreSQL)
  engine                  = var.engine
  # Version of the database engine
  engine_version          = var.engine_version
  # Instance class for the RDS instance (e.g., db.t2.micro)
  instance_class          = var.instance_class
  # Master username for the RDS instance
  username                = var.username
  # Master password for the RDS instance
  password                = var.password
  # Name of the initial database to create
  db_name                 = var.db_name
  # Whether the RDS instance is publicly accessible
  publicly_accessible     = var.publicly_accessible
  # Backup retention period (in days) for the RDS instance
  backup_retention_period = var.backup_retention_period
  # Name of the DB subnet group to associate with the RDS instance
  db_subnet_group_name    = aws_db_subnet_group.db_subnet_group.name
  # List of VPC security group IDs to associate with the RDS instance
  vpc_security_group_ids  = var.vpc_security_group_ids
  # Whether to skip the final snapshot before deleting the RDS instance
  skip_final_snapshot     = var.skip_final_snapshot
  # Whether to enable deletion protection for the RDS instance
  deletion_protection     = var.deletion_protection
  # Identifier of the DB snapshot to restore from
  snapshot_identifier     = var.snapshot_identifier

  lifecycle {
    # Ignore changes to the username and password
    ignore_changes = [username, password]
  }

  # Tags to apply to the RDS instance, including the Name tag
  tags = merge(var.tags, { Name = var.db_identifier })
}