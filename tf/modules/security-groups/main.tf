# NAT and Bastion Security Group
resource "aws_security_group" "nat_bastion_sg" {
  vpc_id = var.vpc_id
  name   = "${var.env}-nat-bastion-sg"

  ingress {
    description = "Allow SSH from specific IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${var.pc_ip}/32"]
  }

  ingress {
    description = "Allow all traffic from private subnet"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [var.private_cidr_block]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

# Application Security Group
resource "aws_security_group" "app_sg" {
  vpc_id = var.vpc_id
  name   = "${var.env}-app-sg"

  ingress {
    description     = "Allow SSH from NAT Security Group"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.nat_bastion_sg.id]
  }

  ingress {
    description = "Allow app traffic (Kubernetes/HTTP)"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

# ELB Security Group
resource "aws_security_group" "elb_sg" {
  vpc_id = var.vpc_id
  name   = "${var.env}-elb-sg"

  ingress {
    description = "Allow HTTPS traffic"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

# RDS Security Group
resource "aws_security_group" "rds_sg" {
  vpc_id = var.vpc_id
  name   = "${var.env}-rds-sg"

  ingress {
    description     = "Allow PostgreSQL traffic from App Security Group"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

# Redis Security Group
resource "aws_security_group" "cache_sg" {
  vpc_id = var.vpc_id
  name   = "${var.env}-cache-sg"

  ingress {
    description     = "Allow Redis traffic from App Security Group"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}


# Redis Security Group
resource "aws_security_group" "dynamic_testing" {
  vpc_id = var.vpc_id
  name   = "${var.env}-dynamic_testing-sg"

  ingress {
    description     = "Allow ssh traffic"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}
