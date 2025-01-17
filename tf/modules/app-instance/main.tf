# Define an IAM policy document for assuming a role
data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# Define a launch template for EC2 instances
resource "aws_launch_template" "app" {
  name          = var.name
  instance_type = var.instance_type
  image_id      = var.ami_id

  # Specify the IAM instance profile
  iam_instance_profile {
    name = aws_iam_instance_profile.app_profile.name
  }

  # Configure network interfaces
  network_interfaces {
    subnet_id                   = var.subnet_id
    associate_public_ip_address = var.associate_public_ip
    security_groups             = var.security_groups
  }

  key_name  = var.key_name
  user_data = var.user_data
  tags      = var.tags
}

# Define an Auto Scaling group
resource "aws_autoscaling_group" "asg" {
  mixed_instances_policy {
    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.app.id
        version            = "$Latest"
      }
    }

    instances_distribution {
      on_demand_base_capacity                = var.on_demand_base_capacity
      on_demand_percentage_above_base_capacity = var.on_demand_percentage
      spot_allocation_strategy               = var.spot_allocation_strategy
    }
  }

  name             = "pokemon-shop-asg"
  min_size         = var.min_size
  max_size         = var.max_size
  desired_capacity = var.desired_capacity
  vpc_zone_identifier = var.subnet_ids
  target_group_arns   = var.target_group_arns

  tag {
    key                 = "Name"
    value               = var.name
    propagate_at_launch = true
  }
}

# Define an IAM role
resource "aws_iam_role" "role" {
  name = var.iam_role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
}

# Define an IAM instance profile
resource "aws_iam_instance_profile" "app_profile" {
  name = "app-instance-profile"
  role = aws_iam_role.role.name
}

# Attach the Amazon S3 full access policy to the IAM role
resource "aws_iam_role_policy_attachment" "s3" {
  role       = aws_iam_role.role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# Attach the AmazonSSMManagedInstanceCore policy to allow EC2 instance to connect to Systems Manager
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}