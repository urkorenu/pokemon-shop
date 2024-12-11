# Security Group for NAT Instance and Bastion Host
resource "aws_security_group" "nat_bastion_sg" {
  vpc_id = aws_vpc.main.id
  name   = "${local.env}-nat-bastion-sg"

  ingress {
    description = "Allow SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # Allow all traffic from private subnet (for NAT forwarding)
  ingress {
    description = "Allow all traffic from private subnet"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]  # Update based on your VPC CIDR block
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.env}-nat-bastion-sg"
  }
}

# Security Group for Kubernetes Nodes
resource "aws_security_group" "k8s_sg" {
  vpc_id = aws_vpc.main.id
  name   = "${local.env}-k8s-sg"

  ingress {
    description = "Allow SSH access from NAT instance"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    security_groups = [aws_security_group.nat_bastion_sg.id]
  }

  ingress {
    description = "Allow all Kubernetes traffic"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.env}-k8s-sg"
  }
}

# Security Group for ELB
resource "aws_security_group" "elb_sg" {
  vpc_id = aws_vpc.main.id
  name   = "${local.env}-elb-sg"

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

  tags = {
    Name = "${local.env}-elb-sg"
  }
}
