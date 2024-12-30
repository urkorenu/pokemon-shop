# NAT and Bastion Security Group
resource "aws_security_group" "nat_bastion_sg" {
  # VPC ID where the security group will be created
  vpc_id = var.vpc_id
  # Name of the security group
  name   = "${var.env}-nat-bastion-sg"

  ingress {
    # Allow SSH from specific IP
    description = "Allow SSH from specific IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${var.pc_ip}/32"]
  }

  ingress {
    # Allow all traffic from private subnet
    description = "Allow all traffic from private subnet"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [var.private_cidr_block]
  }

  egress {
    # Allow all outbound traffic
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Tags to apply to the security group
  tags = var.tags
}

# Application Security Group
resource "aws_security_group" "app_sg" {
  # VPC ID where the security group will be created
  vpc_id = var.vpc_id
  # Name of the security group
  name   = "${var.env}-app-sg"

  ingress {
    # Allow SSH from NAT Security Group
    description     = "Allow SSH from NAT Security Group"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.nat_bastion_sg.id]
  }

  ingress {
    # Allow app traffic (Kubernetes/HTTP)
    description = "Allow app traffic (Kubernetes/HTTP)"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    # Allow all outbound traffic
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Tags to apply to the security group
  tags = var.tags
}

# ELB Security Group
resource "aws_security_group" "elb_sg" {
  # VPC ID where the security group will be created
  vpc_id = var.vpc_id
  # Name of the security group
  name   = "${var.env}-elb-sg"

  ingress {
    # Allow HTTPS traffic
    description = "Allow HTTPS traffic"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    # Allow all outbound traffic
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Tags to apply to the security group
  tags = var.tags
}

# RDS Security Group
resource "aws_security_group" "rds_sg" {
  # VPC ID where the security group will be created
  vpc_id = var.vpc_id
  # Name of the security group
  name   = "${var.env}-rds-sg"

  ingress {
    # Allow PostgreSQL traffic from App Security Group
    description     = "Allow PostgreSQL traffic from App Security Group"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    # Allow all outbound traffic
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Tags to apply to the security group
  tags = var.tags
}

# Redis Security Group
resource "aws_security_group" "cache_sg" {
  # VPC ID where the security group will be created
  vpc_id = var.vpc_id
  # Name of the security group
  name   = "${var.env}-cache-sg"

  ingress {
    # Allow Redis traffic from App Security Group
    description     = "Allow Redis traffic from App Security Group"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    # Allow all outbound traffic
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Tags to apply to the security group
  tags = var.tags
}

# Dynamic Testing Security Group
resource "aws_security_group" "dynamic_testing" {
  # VPC ID where the security group will be created
  vpc_id = var.vpc_id
  # Name of the security group
  name   = "${var.env}-dynamic_testing-sg"

  ingress {
    # Allow SSH traffic
    description = "Allow ssh traffic"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    # Allow all outbound traffic
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Tags to apply to the security group
  tags = var.tags
}