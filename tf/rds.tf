resource "aws_db_subnet_group" "app_db_subnet_group" {
  name        = "${local.env}-db-subnet-group"
  description = "DB Subnet Group for App"
  subnet_ids  = [aws_subnet.private_zone1.id, aws_subnet.private_zone2.id]

  tags = {
    Name = "${local.env}-db-subnet-group"
  }
}

resource "aws_db_instance" "app_rds" {
  identifier              = "app-db-instance"
  allocated_storage       = 20
  storage_type            = "gp2"
  engine                  = "postgres"
  engine_version          = "16.3"
  instance_class          = "db.t4g.micro"
  username                = "admin"
  password                = "guessit"
  db_name                 = "app_db"
  publicly_accessible     = false
  backup_retention_period = 7
  db_subnet_group_name    = aws_db_subnet_group.app_db_subnet_group.name
  vpc_security_group_ids  = [aws_security_group.app_db_sg.id]
  skip_final_snapshot     = true
  deletion_protection     = true

  tags = {
    Environment = "production"
    Critical    = "true"
  }
}
