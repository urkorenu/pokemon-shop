# Data source to fetch the latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"] # Amazon Linux 2
  }
}

# Launch Template
resource "aws_launch_template" "app_launch_template" {
  name          = "${local.env}-app-launch-template"
  instance_type = "t3.micro"
  image_id      = data.aws_ami.amazon_linux.id

  iam_instance_profile {
    name = aws_iam_instance_profile.app_profile.name
  }

  network_interfaces {
    subnet_id                   = aws_subnet.private_zone1.id
    associate_public_ip_address = false
    security_groups             = [aws_security_group.app_sg.id]
  }
  key_name = "pokemon-app"

user_data = base64encode(<<-EOT
#!/bin/bash
# Update and install required packages
yum update -y
yum install -y docker git
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Start Docker service
systemctl start docker
systemctl enable docker

# Set environment variables
cat <<EOF > /etc/environment
DB_USERNAME=${aws_db_instance.app_rds.username}
DB_PASSWORD=${aws_db_instance.app_rds.password}
DB_HOST=${aws_db_instance.app_rds.address}
DB_NAME=${aws_db_instance.app_rds.db_name}
AWS_ACCESS_KEY_ID=${local.aws_access_key_id}
AWS_SECRET_ACCESS_KEY=${local.aws_secret_access_key}
AWS_REGION=${local.aws_region}
S3_BUCKET=${data.aws_s3_bucket.pokemon_pics.id}
API_KEY=${local.api_key}
ADMIN_MAIL=${local.admin_mail}
ELASTIC_CACHE=${aws_elasticache_cluster.pokemon_cache.cache_nodes.0.address}
EOF

# Load environment variables
export $(cat /etc/environment | xargs)

# Create application directory and fetch Docker Compose configuration
cd /home/ec2-user/
git clone -b main https://github.com/urkorenu/pokemon-shop.git && cd pokemon-shop

# Pull latest Docker image and run application
docker-compose pull
docker-compose --env-file /etc/environment up -d

# Verify the application is running
docker ps --filter name=app --format '{{.Status}}'
EOT
)


  tags = {
    Name = "${local.env}-app-launch-template"
  }
}


resource "aws_autoscaling_group" "app_asg" {
  mixed_instances_policy {
    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.app_launch_template.id
        version            = "$Latest"
      }
    }

    # Configure distribution between On-Demand and Spot
    instances_distribution {
      on_demand_base_capacity            = 1      # Always maintain 1 On-Demand instance
      on_demand_percentage_above_base_capacity = 0 # Additional instances will be Spot
      spot_allocation_strategy           = "capacity-optimized" # Use Spot for scaling
    }
  }

  min_size         = 1  # Start with 1 On-Demand instance
  max_size         = 5  # Allow up to 5 instances
  desired_capacity = 1  # Initial capacity is 1 On-Demand instance

  vpc_zone_identifier = [aws_subnet.private_zone1.id, aws_subnet.private_zone2.id]

  target_group_arns = [aws_lb_target_group.app_target_group.arn] # Attach the target group

  tag {
    key                 = "Name"
    value               = "${local.env}-app-instance"
    propagate_at_launch = true
  }
}





# Auto Scaling Policy for Scaling Out
resource "aws_autoscaling_policy" "scale_out" {
  name                   = "${local.env}-scale-out"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.app_asg.name
}

# Auto Scaling Policy for Scaling In
resource "aws_autoscaling_policy" "scale_in" {
  name                   = "${local.env}-scale-in"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.app_asg.name
}

# Define an IAM role for the application instance
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

# Attach the AmazonS3FullAccess policy to the IAM role
resource "aws_iam_role_policy_attachment" "s3_policy" {
  role       = aws_iam_role.app_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# Define an IAM instance profile for the application instance
resource "aws_iam_instance_profile" "app_profile" {
  name = "app-instance-profile"
  role = aws_iam_role.app_instance_role.name
}
