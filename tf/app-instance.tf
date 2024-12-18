# Define an IAM role for the application instance
resource "aws_iam_role" "app_instance_role" {
  name = "k8s-instance-role"

  # Policy that allows EC2 to assume this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Principal = { Service = "ec2.amazonaws.com" },
      Effect    = "Allow",
    }]
  })
}

# Attach the AmazonSSMManagedInstanceCore policy to the IAM role
resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.app_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Attach the AmazonS3FullAccess policy to the IAM role
resource "aws_iam_role_policy_attachment" "s3_policy" {
  role       = aws_iam_role.app_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# Define a network interface for the application instance
resource "aws_network_interface" "app_interface" {
  subnet_id       = aws_subnet.private_zone1.id
  security_groups = [aws_security_group.app_sg.id]

  tags = {
    Name = "${local.env}-app-interface"
  }
}

# Define the EC2 instance for the application
resource "aws_instance" "app_instance" {
  ami                    = "ami-0fcbdd3ee4f67a0a0"
  instance_type          = "t3.micro"
  iam_instance_profile   = aws_iam_instance_profile.app_profile.name
  key_name               = "kafka"

  # Attach the network interface to the instance
  network_interface {
    network_interface_id = aws_network_interface.app_interface.id
    device_index         = 0
  }

  tags = {
    Name = "${local.env}-app-instance"
  }

  # Lifecycle configuration to ignore certain changes
  lifecycle {
    ignore_changes = [
      security_groups,
      user_data,
      root_block_device,
      tags
    ]
  }
}

# Define an IAM instance profile for the application instance
resource "aws_iam_instance_profile" "app_profile" {
  name = "app-instance-profile"
  role = aws_iam_role.app_instance_role.name
}
