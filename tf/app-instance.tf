resource "aws_iam_role" "app_instance_role" {
  name = "k8s-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Principal = { Service = "ec2.amazonaws.com" },
      Effect    = "Allow",
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.app_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "s3_policy" {
  role       = aws_iam_role.app_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_network_interface" "app_interface" {
  subnet_id       = aws_subnet.private_zone1.id
  security_groups = [aws_security_group.app_sg.id]

  tags = {
    Name = "${local.env}-app-interface"
  }
}

resource "aws_instance" "app_instance" {
  ami                    = "ami-0fcbdd3ee4f67a0a0"
  instance_type          = "t3.medium"
  iam_instance_profile   = aws_iam_instance_profile.app_profile.name
  key_name               = "kafka"

  network_interface {
    network_interface_id = aws_network_interface.app_interface.id
    device_index         = 0
  }

  tags = {
    Name = "${local.env}-app-instance"
  }

  lifecycle {
    ignore_changes = [
      security_groups,
      user_data,
      root_block_device,
      tags
    ]
  }
}



resource "aws_iam_instance_profile" "app_profile" {
  name = "app-instance-profile"
  role = aws_iam_role.app_instance_role.name
}
