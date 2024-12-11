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

resource "aws_iam_role_policy_attachment" "ssm_readonly" {
  role       = aws_iam_role.app_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "s3_policy" {
  role       = aws_iam_role.app_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_instance" "app_instance" {
  ami                    = "ami-0fcbdd3ee4f67a0a0"
  instance_type          = "t3.medium"
  subnet_id              = aws_subnet.private_zone1.id
  iam_instance_profile   = aws_iam_instance_profile.app_profile.name
  key_name               = "kafka"
  security_groups        = [aws_security_group.app_sg.id]
  associate_public_ip_address = false

  tags = {
    Name = "${local.env}-app-instance"
  }
}


resource "aws_iam_instance_profile" "app_profile" {
  name = "k8s-instance-profile"
  role = aws_iam_role.app_instance_role.name
}
