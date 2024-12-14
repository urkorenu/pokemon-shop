# Run the script to fetch the current IP address
resource "null_resource" "fetch_ip" {
  provisioner "local-exec" {
    command = "./fetch_ip.sh"
  }
}

# Load the IP address from the file
data "local_file" "ip" {
  filename = "ip.tfvars"
  depends_on = [null_resource.fetch_ip]
}

# Parse the IP address from the file
locals {
  pc_ip = regex("pc_ip = \"(.*)\"", data.local_file.ip.content)[0]
}

# Security Group for NAT Instance and Bastion Host
resource "aws_security_group" "nat_bastion_sg" {
  vpc_id = aws_vpc.main.id  # VPC ID
  name   = "${local.env}-nat-bastion-sg"  # Security Group name

  ingress {
    description = "Allow SSH from anywhere"  # Description of the rule
    from_port   = 22  # Starting port
    to_port     = 22  # Ending port
    protocol    = "tcp"  # Protocol type
    cidr_blocks = ["${local.pc_ip}/32"] # Allowed CIDR blocks
  }
  # Allow all traffic from private subnet (for NAT forwarding)
  ingress {
    description = "Allow all traffic from private subnet"  # Description of the rule
    from_port   = 0  # Starting port
    to_port     = 65535  # Ending port
    protocol    = "tcp"  # Protocol type
    cidr_blocks = ["10.0.0.0/16"]  # Allowed CIDR blocks
  }

  egress {
    description = "Allow all outbound traffic"  # Description of the rule
    from_port   = 0  # Starting port
    to_port     = 0  # Ending port
    protocol    = "-1"  # Protocol type (all)
    cidr_blocks = ["0.0.0.0/0"]  # Allowed CIDR blocks
  }

  tags = {
    Name = "${local.env}-nat-bastion-sg"  # Tag name
  }
}

# Security Group for Kubernetes Nodes
resource "aws_security_group" "app_sg" {
  vpc_id = aws_vpc.main.id  # VPC ID
  name   = "${local.env}-app-sg"  # Security Group name

  ingress {
    description = "Allow SSH access from NAT instance"  # Description of the rule
    from_port   = 22  # Starting port
    to_port     = 22  # Ending port
    protocol    = "tcp"  # Protocol type
    security_groups = [aws_security_group.nat_bastion_sg.id]  # Allowed security groups
  }

  ingress {
    description = "Allow all Kubernetes traffic"  # Description of the rule
    from_port   = 5000  # Starting port
    to_port     = 5000  # Ending port
    protocol    = "tcp"  # Protocol type
    cidr_blocks = ["0.0.0.0/0"]  # Allowed CIDR blocks
  }

  egress {
    description = "Allow all outbound traffic"  # Description of the rule
    from_port   = 0  # Starting port
    to_port     = 0  # Ending port
    protocol    = "-1"  # Protocol type (all)
    cidr_blocks = ["0.0.0.0/0"]  # Allowed CIDR blocks
  }

  tags = {
    Name = "${local.env}-app-sg"  # Tag name
  }
}

# Security Group for ELB
resource "aws_security_group" "elb_sg" {
  vpc_id = aws_vpc.main.id  # VPC ID
  name   = "${local.env}-elb-sg"  # Security Group name

  ingress {
    description = "Allow HTTPS traffic"  # Description of the rule
    from_port   = 443  # Starting port
    to_port     = 443  # Ending port
    protocol    = "tcp"  # Protocol type
    cidr_blocks = ["0.0.0.0/0"]  # Allowed CIDR blocks
  }

  egress {
    description = "Allow all outbound traffic"  # Description of the rule
    from_port   = 0  # Starting port
    to_port     = 0  # Ending port
    protocol    = "-1"  # Protocol type (all)
    cidr_blocks = ["0.0.0.0/0"]  # Allowed CIDR blocks
  }

  tags = {
    Name = "${local.env}-elb-sg"  # Tag name
  }
}

# Security Group for RDS Instance
resource "aws_security_group" "app_db_sg" {
  vpc_id = aws_vpc.main.id  # VPC ID

  ingress {
    description = "Allow PostgreSQL access from App Security Group"  # Description of the rule
    from_port   = 5432  # Starting port
    to_port     = 5432  # Ending port
    protocol    = "tcp"  # Protocol type
    security_groups = [aws_security_group.app_sg.id]  # Allowed security groups
  }

  egress {
    description = "Allow all outbound traffic"  # Description of the rule
    from_port   = 0  # Starting port
    to_port     = 0  # Ending port
    protocol    = "-1"  # Protocol type (all)
    cidr_blocks = ["0.0.0.0/0"]  # Allowed CIDR blocks
  }

  tags = {
    Name = "${local.env}-app-db-sg"  # Tag name
  }
}