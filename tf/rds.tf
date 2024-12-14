# Define a DB Subnet Group for the application
resource "aws_db_subnet_group" "app_db_subnet_group" {
  name        = "${local.env}-db-subnet-group"  # Name of the DB Subnet Group
  description = "DB Subnet Group for App"       # Description of the DB Subnet Group
  subnet_ids  = [aws_subnet.private_zone1.id, aws_subnet.private_zone2.id]  # List of subnet IDs

  # Add tags to the DB Subnet Group
  tags = {
    Name = "${local.env}-db-subnet-group"
  }
}

# Define an RDS instance for the application
resource "aws_db_instance" "app_rds" {
  identifier              = "app-db-instance"  # Identifier for the RDS instance
  allocated_storage       = 20                 # Allocated storage in GB
  storage_type            = "gp2"              # Storage type
  engine                  = "postgres"         # Database engine
  engine_version          = "16.3"             # Database engine version
  instance_class          = "db.t4g.micro"     # Instance class
  username                = "admin"            # Master username
  password                = "guessit"          # Master password
  db_name                 = "app_db"           # Database name
  publicly_accessible     = false              # Whether the instance is publicly accessible
  backup_retention_period = 7                  # Backup retention period in days
  db_subnet_group_name    = aws_db_subnet_group.app_db_subnet_group.name  # DB Subnet Group name
  vpc_security_group_ids  = [aws_security_group.app_db_sg.id]  # List of VPC security group IDs
  skip_final_snapshot     = true               # Skip final snapshot before deletion
  deletion_protection     = true               # Enable deletion protection

  # Add tags to the RDS instance
  tags = {
    Environment = "production"  # Environment tag
    Critical    = "true"        # Critical tag
  }
}